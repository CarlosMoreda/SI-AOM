from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sqlalchemy.orm import Session

from app.etl.dataset import build_dataset
from app.ml.train_random_forest import (
    DATASET_CSV_SOURCE,
    DEFAULT_TARGETS,
    ORCAMENTO_SUB_MODELS,
    train_one_dataset,
)
from app.models.previsao_ml import PrevisaoML

MODEL_NAME = "random_forest"
BACKEND_ROOT = Path(__file__).resolve().parents[2]
MODEL_BASE_DIR = BACKEND_ROOT / "ml" / "models" / "random_forest"
ORCAMENTO_REQUIRED_FEATURES: tuple[str, ...] = (
    "tipologia",
    "complexidade",
    "peso_total_kg",
    "numero_pecas",
    "material_principal",
    "tratamento_superficie",
    "processo_corte",
    "lead_time",
)
ORCAMENTO_REQUIRED_LABELS: dict[str, str] = {
    "tipologia": "tipologia",
    "complexidade": "complexidade",
    "peso_total_kg": "peso_total_kg",
    "numero_pecas": "numero_pecas",
    "material_principal": "material_principal",
    "tratamento_superficie": "tratamento_superficie",
    "processo_corte": "processo_corte",
    "lead_time": "lead_time",
}
ORCAMENTO_OPTION_FIELDS: dict[str, str] = {
    "tipologia": "tipologias",
    "complexidade": "complexidades",
    "material_principal": "materiais",
    "tratamento_superficie": "tratamentos",
    "processo_corte": "processos_corte",
}


def _resolve_backend_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return (BACKEND_ROOT / candidate).resolve()


def _model_paths(dataset_type: str, model_base_dir: Path = MODEL_BASE_DIR) -> tuple[Path, Path]:
    model_path = model_base_dir / dataset_type / "model.joblib"
    metrics_path = model_base_dir / dataset_type / "metrics.json"
    return model_path, metrics_path


def _load_metrics(metrics_path: Path) -> dict[str, Any]:
    return json.loads(metrics_path.read_text(encoding="utf-8"))


def _model_version_from_path(model_path: Path) -> str:
    ts = model_path.stat().st_mtime
    return pd.Timestamp.fromtimestamp(ts).strftime("%Y%m%d%H%M%S")


def _align_features(model, features_used: list[str], dataset_df: pd.DataFrame) -> pd.DataFrame:
    for col in features_used:
        if col not in dataset_df.columns:
            dataset_df[col] = None

    X = dataset_df[features_used].copy()

    preprocess = model.named_steps.get("preprocess")
    if preprocess is None:
        return X

    numeric_cols: list[str] = []
    categorical_cols: list[str] = []

    for transformer_name, _transformer, cols in preprocess.transformers_:
        if transformer_name == "num":
            numeric_cols.extend([c for c in cols if c in X.columns])
        elif transformer_name == "cat":
            categorical_cols.extend([c for c in cols if c in X.columns])

    for col in numeric_cols:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    for col in categorical_cols:
        X[col] = X[col].astype("object")
        X[col] = X[col].where(X[col].notna(), None)

    return X


def _to_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _quality_rank(quality_status: str) -> int:
    ranking = {
        "good": 3,
        "acceptable": 2,
        "weak": 1,
        "insufficient_data": 0,
    }
    return ranking.get(quality_status, 0)


def _status_from_metrics(metrics: dict[str, Any]) -> str:
    status = metrics.get("quality_status")
    if isinstance(status, str) and status:
        return status

    r2 = metrics.get("r2")
    beats_baseline = metrics.get("model_beats_baseline")
    if r2 is None:
        return "insufficient_data"

    try:
        r2_value = float(r2)
    except (TypeError, ValueError):
        return "insufficient_data"

    # Fallback para modelos antigos sem campo model_beats_baseline.
    if beats_baseline is None:
        if r2_value >= 0.25:
            return "good"
        if r2_value >= 0:
            return "acceptable"
        return "weak"

    if bool(beats_baseline) and r2_value >= 0.25:
        return "good"
    if bool(beats_baseline) and r2_value >= 0:
        return "acceptable"
    return "weak"


def _aggregate_quality(submodel_metrics: list[dict[str, Any]]) -> tuple[str, float | None, str | None]:
    statuses = [_status_from_metrics(m) for m in submodel_metrics]
    if not statuses:
        return "indeterminada", None, None

    worst = min(statuses, key=_quality_rank)
    r2_values = [float(m["r2"]) for m in submodel_metrics if m.get("r2") is not None]
    r2_medio = float(sum(r2_values) / len(r2_values)) if r2_values else None

    mapping = {
        "good": "boa",
        "acceptable": "aceitavel",
        "weak": "fraca",
        "insufficient_data": "indeterminada",
    }
    qualidade = mapping.get(worst, "indeterminada")
    aviso = None
    if qualidade == "fraca":
        aviso = (
            "Qualidade preditiva fraca: use o valor apenas como estimativa inicial "
            "e valide com dados historicos e contexto tecnico."
        )
    elif qualidade == "indeterminada":
        aviso = (
            "Qualidade ainda indeterminada: faltam dados suficientes para avaliar "
            "o desempenho com confianca."
        )
    return qualidade, r2_medio, aviso


def _confidence_percent(qualidade: str, r2_medio: float | None) -> int:
    # Confidence is a user-facing signal (0-100), not a statistical probability.
    if r2_medio is not None:
        try:
            r2 = max(-1.0, min(1.0, float(r2_medio)))
            base = int(round((r2 + 1.0) * 50.0))  # -1 -> 0, 0 -> 50, 1 -> 100
        except (TypeError, ValueError):
            base = 25
    else:
        base = 25

    if qualidade == "boa":
        return max(70, min(95, base))
    if qualidade == "aceitavel":
        return max(45, min(75, base))
    if qualidade == "fraca":
        return min(45, base)
    return min(40, base)


def _feature_ranges_from_metrics(metrics: dict[str, Any]) -> dict[str, dict[str, float]]:
    ranges_raw = metrics.get("feature_ranges")
    if not isinstance(ranges_raw, dict):
        return {}

    normalized: dict[str, dict[str, float]] = {}
    for feature, row in ranges_raw.items():
        if not isinstance(row, dict):
            continue
        min_value = row.get("min")
        max_value = row.get("max")
        try:
            if min_value is None or max_value is None:
                continue
            normalized[str(feature)] = {
                "min": float(min_value),
                "max": float(max_value),
            }
        except (TypeError, ValueError):
            continue
    return normalized


def _dataset_csv_for_type(dataset_type: str) -> Path:
    csv_source = DATASET_CSV_SOURCE.get(dataset_type, dataset_type)
    return BACKEND_ROOT / "ml" / f"dataset_{csv_source}.csv"


def _missing_param(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _validate_orcamento_parametros(parametros: dict[str, Any]) -> None:
    for field in ORCAMENTO_REQUIRED_FEATURES:
        value = parametros.get(field)
        if isinstance(value, str):
            parametros[field] = value.strip()

    missing = [
        ORCAMENTO_REQUIRED_LABELS[field]
        for field in ORCAMENTO_REQUIRED_FEATURES
        if _missing_param(parametros.get(field))
    ]
    if missing:
        raise ValueError("Parametros obrigatorios em falta: " + ", ".join(missing))

    try:
        if float(parametros["peso_total_kg"]) <= 0:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("peso_total_kg deve ser um numero maior que zero")

    try:
        if int(parametros["numero_pecas"]) < 1:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("numero_pecas deve ser um inteiro maior ou igual a 1")

    try:
        if int(parametros["lead_time"]) < 1:
            raise ValueError
    except (TypeError, ValueError):
        raise ValueError("lead_time deve ser um inteiro maior ou igual a 1")


def _augment_orcamento_features(parametros: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(parametros)
    peso_total = _to_float(enriched.get("peso_total_kg"))
    numero_pecas = _to_float(enriched.get("numero_pecas"))
    lead_time = _to_float(enriched.get("lead_time"))

    if peso_total is not None and numero_pecas and numero_pecas > 0:
        enriched["peso_por_peca_kg"] = peso_total / numero_pecas
    else:
        enriched["peso_por_peca_kg"] = None

    if peso_total is not None and peso_total > 0 and lead_time is not None:
        enriched["lead_time_por_tonelada"] = lead_time / (peso_total / 1000.0)
    else:
        enriched["lead_time_por_tonelada"] = None

    return enriched


def _feature_ranges_from_dataset(
    dataset_type: str,
    features_used: list[str],
) -> dict[str, dict[str, float]]:
    dataset_csv = _dataset_csv_for_type(dataset_type)
    if not dataset_csv.exists():
        return {}

    df = pd.read_csv(dataset_csv, sep=";", encoding="utf-8-sig")
    ranges: dict[str, dict[str, float]] = {}
    for feature in features_used:
        if feature not in df.columns:
            continue
        series = pd.to_numeric(df[feature], errors="coerce").dropna()
        if series.empty:
            continue
        ranges[feature] = {
            "min": float(series.min()),
            "max": float(series.max()),
        }
    return ranges


def _range_alerts(
    parametros: dict[str, Any],
    feature_ranges: dict[str, dict[str, float]],
) -> list[str]:
    alerts: list[str] = []
    for feature, limits in feature_ranges.items():
        value = parametros.get(feature)
        if value is None:
            continue
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            continue

        min_value = float(limits["min"])
        max_value = float(limits["max"])
        if numeric_value < min_value or numeric_value > max_value:
            alerts.append(
                f"{feature}={numeric_value} fora da faixa de treino [{min_value}, {max_value}]"
            )
    return alerts


def _categorical_alerts(model, parametros: dict[str, Any]) -> list[str]:
    alerts: list[str] = []
    preprocess = model.named_steps.get("preprocess")
    if preprocess is None:
        return alerts

    for transformer_name, transformer, cols in preprocess.transformers_:
        if transformer_name != "cat":
            continue

        onehot = getattr(transformer, "named_steps", {}).get("onehot")
        categories = getattr(onehot, "categories_", None)
        if categories is None:
            continue

        for col, allowed_values in zip(cols, categories):
            value = parametros.get(col)
            if _missing_param(value):
                continue

            normalized_value = str(value).strip()
            allowed = {str(item) for item in allowed_values}
            if normalized_value not in allowed:
                alerts.append(
                    f"{col}='{normalized_value}' fora dos valores vistos no treino"
                )

    return alerts


def _empty_orcamento_options() -> dict[str, Any]:
    return {
        "tipologias": [],
        "complexidades": [],
        "materiais": [],
        "tratamentos": [],
        "processos_corte": [],
        "feature_ranges": {},
        "features_usadas": [],
        "dataset_linhas": None,
        "source": "indisponivel",
    }


def _options_from_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    options = _empty_orcamento_options()
    categorical_values = metrics.get("categorical_values")
    if isinstance(categorical_values, dict):
        for feature, option_key in ORCAMENTO_OPTION_FIELDS.items():
            values = categorical_values.get(feature)
            if isinstance(values, list):
                options[option_key] = sorted({str(v) for v in values if str(v).strip()})

    options["feature_ranges"] = _feature_ranges_from_metrics(metrics)
    features_used = metrics.get("features_used")
    if isinstance(features_used, list):
        options["features_usadas"] = [str(feature) for feature in features_used]
    options["dataset_linhas"] = metrics.get("rows_total")
    options["source"] = "modelo"
    return options


def _options_from_dataset(dataset: pd.DataFrame, source: str) -> dict[str, Any]:
    options = _empty_orcamento_options()
    for feature, option_key in ORCAMENTO_OPTION_FIELDS.items():
        if feature not in dataset.columns:
            continue
        values = dataset[feature].dropna().astype(str).str.strip()
        values = values[values != ""]
        options[option_key] = sorted(values.unique().tolist())

    ranges: dict[str, dict[str, float]] = {}
    for feature in (
        "peso_total_kg",
        "numero_pecas",
        "lead_time",
        "peso_por_peca_kg",
        "lead_time_por_tonelada",
    ):
        if feature not in dataset.columns:
            continue
        series = pd.to_numeric(dataset[feature], errors="coerce").dropna()
        if series.empty:
            continue
        ranges[feature] = {
            "min": float(series.min()),
            "max": float(series.max()),
        }

    options["feature_ranges"] = ranges
    options["features_usadas"] = [
        feature
        for feature in (
            "tipologia",
            "complexidade",
            "peso_total_kg",
            "numero_pecas",
            "material_principal",
            "tratamento_superficie",
            "processo_corte",
            "lead_time",
            "peso_por_peca_kg",
            "lead_time_por_tonelada",
        )
        if feature in dataset.columns
    ]
    options["dataset_linhas"] = int(len(dataset))
    options["source"] = source
    return options


def get_orcamento_options(model_base_dir: Path = MODEL_BASE_DIR) -> dict[str, Any]:
    _model_path, metrics_path = _model_paths("orcamento_materiais", model_base_dir=model_base_dir)
    if metrics_path.exists():
        options = _options_from_metrics(_load_metrics(metrics_path))
        if any(options[key] for key in ORCAMENTO_OPTION_FIELDS.values()):
            return options

    dataset_csv = _dataset_csv_for_type("orcamento_materiais")
    if dataset_csv.exists():
        dataset = pd.read_csv(dataset_csv, sep=";", encoding="utf-8-sig")
        return _options_from_dataset(dataset, source="dataset_csv")

    dataset = build_dataset("orcamento")
    if not dataset.empty:
        return _options_from_dataset(dataset, source="base_dados")

    return _empty_orcamento_options()


def predict_custo_from_params(
    parametros: dict[str, Any],
    model_base_dir: Path = MODEL_BASE_DIR,
) -> dict[str, Any]:
    """
    Preve os custos orcados (materiais, operacoes, servicos) a partir de
    parametros do projeto, sem necessidade de um orcamento existente na BD.
    """
    parametros = dict(parametros)
    _validate_orcamento_parametros(parametros)
    parametros = _augment_orcamento_features(parametros)

    resultados: dict[str, Any] = {}
    versoes: list[str] = []
    quality_rows: list[dict[str, Any]] = []
    range_alerts: list[str] = []

    for sub_model in ORCAMENTO_SUB_MODELS:
        model_path, metrics_path = _model_paths(sub_model, model_base_dir=model_base_dir)
        if not model_path.exists() or not metrics_path.exists():
            raise FileNotFoundError(
                "Os modelos de previsao de orcamento ainda nao foram treinados. "
                "Um administrador deve ir a 'Treinar Modelos' e selecionar 'orcamento'."
            )

        model = joblib.load(model_path)
        metrics = _load_metrics(metrics_path)
        features_used = metrics.get("features_used", [])
        if not features_used:
            raise ValueError(f"Metricas de '{sub_model}' sem 'features_used'")

        feature_ranges = _feature_ranges_from_metrics(metrics)
        if not feature_ranges:
            # Compatibilidade com modelos antigos treinados sem "feature_ranges".
            feature_ranges = _feature_ranges_from_dataset(sub_model, features_used)
        range_alerts.extend(_range_alerts(parametros, feature_ranges))
        range_alerts.extend(_categorical_alerts(model, parametros))

        dataset_df = pd.DataFrame([parametros])
        X = _align_features(model=model, features_used=features_used, dataset_df=dataset_df)
        y_pred = model.predict(X)
        valor = max(0.0, float(y_pred[0]))  # custo nunca negativo

        componente = sub_model.replace("orcamento_", "")  # materiais / operacoes / servicos
        resultados[componente] = valor
        versoes.append(_model_version_from_path(model_path))
        quality_rows.append(metrics)

    custo_total = resultados.get("materiais", 0) + resultados.get("operacoes", 0) + resultados.get("servicos", 0)
    qualidade_modelo, r2_medio_holdout, aviso_qualidade = _aggregate_quality(quality_rows)
    confianca_percentual = _confidence_percent(qualidade_modelo, r2_medio_holdout)
    if range_alerts:
        confianca_percentual = min(confianca_percentual, 30)

    unique_range_alerts = sorted(set(range_alerts))
    aviso_faixa_treino = None
    if unique_range_alerts:
        aviso_faixa_treino = (
            "Alguns parametros estao fora da faixa de treino; a previsao pode ficar "
            "menos fiavel para estes valores."
        )

    return {
        "custo_materiais": resultados.get("materiais", 0.0),
        "custo_operacoes": resultados.get("operacoes", 0.0),
        "custo_servicos": resultados.get("servicos", 0.0),
        "custo_total": custo_total,
        "modelo_utilizado": MODEL_NAME,
        "modelo_versao": versoes[0] if versoes else None,
        "qualidade_modelo": qualidade_modelo,
        "r2_medio_holdout": r2_medio_holdout,
        "aviso_qualidade": aviso_qualidade,
        "confianca_percentual": confianca_percentual,
        "fora_faixa_treino": bool(unique_range_alerts),
        "aviso_faixa_treino": aviso_faixa_treino,
        "alertas_faixa_treino": unique_range_alerts,
    }


def save_custo_prediction(
    db: Session,
    *,
    id_orcamento: int | None,
    parametros: dict[str, Any],
    resultado: dict[str, Any],
    observacoes: str | None = None,
) -> int | None:
    """Persiste uma previsao do endpoint /ml/orcamento/prever em previsao_ml.

    id_orcamento pode ser None (previsao exploratoria pre-orcamento). Em caso
    de falha de BD devolve None e faz rollback, sem propagar a excecao -- a
    previsao em si continua valida para o utilizador, so nao fica registada.
    O breakdown materiais/operacoes/servicos vai em inputs_chave para retraining
    e analise de drift posteriores.
    """
    inputs_chave = {
        "parametros": parametros,
        "custo_materiais": resultado.get("custo_materiais"),
        "custo_operacoes": resultado.get("custo_operacoes"),
        "custo_servicos": resultado.get("custo_servicos"),
        "qualidade_modelo": resultado.get("qualidade_modelo"),
        "confianca_percentual": resultado.get("confianca_percentual"),
        "fora_faixa_treino": resultado.get("fora_faixa_treino"),
        "alertas_faixa_treino": resultado.get("alertas_faixa_treino"),
    }
    registo = PrevisaoML(
        id_orcamento=id_orcamento,
        modelo_utilizado=resultado.get("modelo_utilizado") or MODEL_NAME,
        modelo_versao=resultado.get("modelo_versao"),
        custo_previsto=resultado.get("custo_total"),
        tempo_previsto=None,
        desvio_esperado_percent=None,
        inputs_chave=json.dumps(inputs_chave, ensure_ascii=False, default=str),
        observacoes=observacoes,
    )
    try:
        db.add(registo)
        db.commit()
        db.refresh(registo)
        return registo.id_previsao
    except Exception:
        db.rollback()
        return None


def _refresh_training_dataset(
    *,
    dataset_dir_path: Path,
    csv_delimiter: str,
    csv_encoding: str,
) -> dict[str, Any]:
    dataset = build_dataset("orcamento")
    if dataset.empty:
        raise ValueError("Sem orcamentos com custo_total_orcado > 0 para treinar.")

    dataset_dir_path.mkdir(parents=True, exist_ok=True)
    csv_path = dataset_dir_path / "dataset_orcamento.csv"
    dataset.to_csv(csv_path, index=False, sep=csv_delimiter, encoding=csv_encoding)
    return {"path": csv_path, "rows": len(dataset)}


def train_models(
    *,
    dataset_dir: str,
    output_dir: str,
    refresh_dataset: bool,
    test_size: float,
    random_state: int,
    n_estimators: int,
    max_depth: int | None,
    min_samples_leaf: int,
    csv_delimiter: str,
    csv_encoding: str,
) -> list[dict[str, str]]:
    """Treina os 3 sub-modelos de orcamento (materiais/operacoes/servicos).

    Se refresh_dataset=True, regenera primeiro o dataset_orcamento.csv a partir
    da BD para garantir que treina com os dados mais recentes.
    """
    dataset_dir_path = _resolve_backend_path(dataset_dir)
    output_dir_path = _resolve_backend_path(output_dir)

    results: list[dict[str, str]] = []
    refreshed: dict[str, Any] | None = None

    if refresh_dataset:
        try:
            refreshed = _refresh_training_dataset(
                dataset_dir_path=dataset_dir_path,
                csv_delimiter=csv_delimiter,
                csv_encoding=csv_encoding,
            )
        except Exception as exc:
            for current in ORCAMENTO_SUB_MODELS:
                results.append({
                    "dataset_type": current,
                    "status": "error",
                    "detail": f"Erro ao atualizar dataset_orcamento.csv da BD: {exc}",
                })
            return results

    for current in ORCAMENTO_SUB_MODELS:
        try:
            train_one_dataset(
                dataset_type=current,
                dataset_dir=dataset_dir_path,
                output_dir=output_dir_path,
                target=DEFAULT_TARGETS[current],
                test_size=test_size,
                random_state=random_state,
                n_estimators=n_estimators,
                max_depth=max_depth,
                min_samples_leaf=min_samples_leaf,
                csv_delimiter=csv_delimiter,
                csv_encoding=csv_encoding,
            )
            detail = "Treino concluido"
            if refreshed:
                detail += f"; dataset_orcamento.csv atualizado ({refreshed['rows']} linhas)"
            results.append({"dataset_type": current, "status": "ok", "detail": detail})
        except Exception as exc:
            results.append({"dataset_type": current, "status": "error", "detail": str(exc)})

    return results
