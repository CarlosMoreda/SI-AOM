from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, cross_validate, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

# Sub-modelos do dataset "orcamento": preveem o custo REAL (verificado em
# producao) a partir das features tecnicas do projeto. Esta abordagem treina
# contra a verdade observada (real_*) e nao contra a estimativa do orcamentista
# (custo_total_*), o que torna a previsao mais util e a validacao mais honesta.
DEFAULT_TARGETS: Final[dict[str, str]] = {
    "orcamento_materiais": "real_materiais",
    "orcamento_operacoes": "real_operacoes",
    "orcamento_servicos": "real_servicos",
}

# Colunas removidas no treino para evitar leakage. Todos os custo_total_*
# (orcados) sao leakage porque na inferencia o orcamentista so tem features
# tecnicas do projeto. Tambem se excluem os outros dois reals para nao haver
# fuga entre componentes.
LEAKAGE_COLUMNS: Final[dict[str, set[str]]] = {
    "orcamento_materiais": {
        "custo_total_materiais", "custo_total_operacoes", "custo_total_servicos",
        "real_operacoes", "real_servicos",
    },
    "orcamento_operacoes": {
        "custo_total_materiais", "custo_total_operacoes", "custo_total_servicos",
        "real_materiais", "real_servicos",
    },
    "orcamento_servicos": {
        "custo_total_materiais", "custo_total_operacoes", "custo_total_servicos",
        "real_materiais", "real_operacoes",
    },
}

# Os 3 sub-modelos partilham o mesmo CSV de origem (dataset_orcamento.csv),
# gerado pela query orcamento_query.
DATASET_CSV_SOURCE: Final[dict[str, str]] = {
    "orcamento_materiais": "orcamento",
    "orcamento_operacoes": "orcamento",
    "orcamento_servicos": "orcamento",
}

ORCAMENTO_SUB_MODELS: Final[tuple[str, ...]] = (
    "orcamento_materiais",
    "orcamento_operacoes",
    "orcamento_servicos",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Treino RandomForest dos sub-modelos de orcamento (materiais/operacoes/servicos)"
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=Path("ml"),
        help="Diretoria onde esta o dataset_orcamento.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("ml/models/random_forest"),
        help="Diretoria de saida dos modelos e metricas",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.25,
        help="Percentagem para teste",
    )
    parser.add_argument(
        "--random-state",
        type=int,
        default=42,
        help="Seed",
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=400,
        help="Numero de arvores",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=None,
        help="Profundidade maxima (None = sem limite)",
    )
    parser.add_argument(
        "--min-samples-leaf",
        type=int,
        default=1,
        help="Minimo de amostras por folha",
    )
    parser.add_argument(
        "--csv-delimiter",
        type=str,
        default=";",
        help="Separador CSV",
    )
    parser.add_argument(
        "--csv-encoding",
        type=str,
        default="utf-8-sig",
        help="Encoding CSV",
    )
    return parser.parse_args()


def dataset_csv_path(dataset_dir: Path, dataset_type: str) -> Path:
    csv_source = DATASET_CSV_SOURCE.get(dataset_type, dataset_type)
    return dataset_dir / f"dataset_{csv_source}.csv"


def resolve_target(dataset_type: str) -> str:
    return DEFAULT_TARGETS[dataset_type]


def build_preprocessor(df_features: pd.DataFrame) -> ColumnTransformer:
    numeric_cols = df_features.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = [c for c in df_features.columns if c not in numeric_cols]

    transformers = []
    if numeric_cols:
        transformers.append(
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                    ]
                ),
                numeric_cols,
            )
        )

    if categorical_cols:
        transformers.append(
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_cols,
            )
        )

    return ColumnTransformer(transformers=transformers, remainder="drop")


def _evaluate_regression(y_true, y_pred) -> tuple[float, float, float]:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(mean_squared_error(y_true, y_pred) ** 0.5)
    r2 = float(r2_score(y_true, y_pred))
    return mae, rmse, r2


def _quality_status(
    r2: float | None,
    model_beats_baseline: bool | None,
    cv_r2_mean: float | None = None,
) -> str:
    if r2 is None or model_beats_baseline is None:
        return "insufficient_data"
    cv_is_stable = cv_r2_mean is None or cv_r2_mean >= 0
    if model_beats_baseline and r2 >= 0.25 and cv_is_stable:
        return "good"
    if model_beats_baseline and r2 >= 0 and cv_is_stable:
        return "acceptable"
    return "weak"


def _feature_ranges(df_features: pd.DataFrame) -> dict[str, dict[str, float]]:
    ranges: dict[str, dict[str, float]] = {}
    numeric_cols = df_features.select_dtypes(include=["number"]).columns.tolist()
    for col in numeric_cols:
        series = pd.to_numeric(df_features[col], errors="coerce").dropna()
        if series.empty:
            continue
        ranges[col] = {
            "min": float(series.min()),
            "max": float(series.max()),
        }
    return ranges


def _categorical_values(df_features: pd.DataFrame) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    numeric_cols = set(df_features.select_dtypes(include=["number"]).columns.tolist())
    categorical_cols = [c for c in df_features.columns if c not in numeric_cols]
    for col in categorical_cols:
        series = df_features[col].dropna().astype(str).str.strip()
        series = series[series != ""]
        if series.empty:
            continue
        values[col] = sorted(series.unique().tolist())
    return values


def train_one_dataset(
    dataset_type: str,
    dataset_dir: Path,
    output_dir: Path,
    target: str,
    test_size: float,
    random_state: int,
    n_estimators: int,
    max_depth: int | None,
    min_samples_leaf: int,
    csv_delimiter: str,
    csv_encoding: str,
) -> None:
    csv_path = dataset_csv_path(dataset_dir, dataset_type)
    if not csv_path.exists():
        raise FileNotFoundError(f"Ficheiro nao encontrado: {csv_path}")

    df = pd.read_csv(csv_path, sep=csv_delimiter, encoding=csv_encoding)
    if df.empty:
        raise ValueError(f"{dataset_type}: dataset vazio, sem dados para treinar")
    if target not in df.columns:
        raise ValueError(f"{dataset_type}: target '{target}' nao existe no dataset")

    dropped_cols = {target}
    dropped_cols.update(LEAKAGE_COLUMNS.get(dataset_type, set()))
    dropped_cols = [c for c in dropped_cols if c in df.columns]

    y = pd.to_numeric(df[target], errors="coerce")
    X = df.drop(columns=dropped_cols)

    valid_mask = y.notna()
    X = X.loc[valid_mask].copy()
    y = y.loc[valid_mask].copy()

    if len(X) < 2:
        raise ValueError(f"{dataset_type}: linhas insuficientes ({len(X)}).")

    # Com poucos dados, treinamos com todas as linhas para nao bloquear o fluxo.
    use_holdout = len(X) >= 12
    if use_holdout:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
        )
    else:
        X_train, y_train = X, y
        X_test, y_test = None, None

    preprocessor = build_preprocessor(X_train)
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", model),
        ]
    )
    pipeline.fit(X_train, y_train)

    baseline_mae = None
    baseline_rmse = None
    baseline_r2 = None
    model_beats_baseline = None
    cv_folds = None
    cv_mae_mean = None
    cv_mae_std = None
    cv_r2_mean = None
    cv_r2_std = None

    if use_holdout and X_test is not None and y_test is not None:
        y_pred = pipeline.predict(X_test)
        mae, rmse, r2 = _evaluate_regression(y_test, y_pred)

        # Baseline simples para termos comparacao objetiva da qualidade.
        baseline = DummyRegressor(strategy="median")
        baseline.fit(X_train, y_train)
        y_pred_baseline = baseline.predict(X_test)
        baseline_mae, baseline_rmse, baseline_r2 = _evaluate_regression(
            y_test,
            y_pred_baseline,
        )
        model_beats_baseline = mae <= baseline_mae
        rows_test = int(len(X_test))
    else:
        mae = None
        rmse = None
        r2 = None
        rows_test = 0

    # Cross-validation adiciona uma nocao de estabilidade da metrica.
    if len(X) >= 25:
        cv_folds = min(5, max(3, len(X) // 10))
        cv = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
        cv_scores = cross_validate(
            pipeline,
            X,
            y,
            cv=cv,
            scoring={"mae": "neg_mean_absolute_error", "r2": "r2"},
            n_jobs=1,
            error_score="raise",
        )
        cv_mae = -cv_scores["test_mae"]
        cv_r2 = cv_scores["test_r2"]
        cv_mae_mean = float(cv_mae.mean())
        cv_mae_std = float(cv_mae.std())
        cv_r2_mean = float(cv_r2.mean())
        cv_r2_std = float(cv_r2.std())

    metrics = {
        "dataset_type": dataset_type,
        "dataset_source": DATASET_CSV_SOURCE.get(dataset_type, dataset_type),
        "target": target,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "rows_total": int(len(X)),
        "rows_train": int(len(X_train)),
        "rows_test": rows_test,
        "evaluation_mode": "holdout" if use_holdout else "train_only_small_dataset",
        "features_used": list(X.columns),
        "feature_ranges": _feature_ranges(X),
        "categorical_values": _categorical_values(X),
        "dropped_columns": dropped_cols,
        "mae": mae,
        "rmse": rmse,
        "r2": r2,
        "baseline_mae": baseline_mae,
        "baseline_rmse": baseline_rmse,
        "baseline_r2": baseline_r2,
        "model_beats_baseline": model_beats_baseline,
        "cv_folds": cv_folds,
        "cv_mae_mean": cv_mae_mean,
        "cv_mae_std": cv_mae_std,
        "cv_r2_mean": cv_r2_mean,
        "cv_r2_std": cv_r2_std,
        "quality_status": _quality_status(r2, model_beats_baseline, cv_r2_mean),
        "params": {
            "n_estimators": n_estimators,
            "max_depth": max_depth,
            "min_samples_leaf": min_samples_leaf,
            "test_size": test_size,
            "random_state": random_state,
        },
    }

    out_dir = output_dir / dataset_type
    out_dir.mkdir(parents=True, exist_ok=True)

    model_path = out_dir / "model.joblib"
    metrics_path = out_dir / "metrics.json"
    joblib.dump(pipeline, model_path)
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    if use_holdout:
        baseline_info = ""
        if baseline_mae is not None and baseline_r2 is not None:
            baseline_info = (
                f" | BASELINE_MAE={baseline_mae:.4f} BASELINE_R2={baseline_r2:.4f}"
            )
        print(
            f"[RF] {dataset_type}: modelo guardado em {model_path} | "
            f"MAE={metrics['mae']:.4f} RMSE={metrics['rmse']:.4f} "
            f"R2={metrics['r2']:.4f}{baseline_info} "
            f"QUALITY={metrics['quality_status']}"
        )
    else:
        print(
            f"[RF] {dataset_type}: modelo guardado em {model_path} | "
            "avaliacao=sem holdout (dataset pequeno)"
        )


def main() -> None:
    args = parse_args()
    for dataset_type in ORCAMENTO_SUB_MODELS:
        try:
            train_one_dataset(
                dataset_type=dataset_type,
                dataset_dir=args.dataset_dir,
                output_dir=args.output_dir,
                target=resolve_target(dataset_type),
                test_size=args.test_size,
                random_state=args.random_state,
                n_estimators=args.n_estimators,
                max_depth=args.max_depth,
                min_samples_leaf=args.min_samples_leaf,
                csv_delimiter=args.csv_delimiter,
                csv_encoding=args.csv_encoding,
            )
        except Exception as exc:
            print(f"[RF] {dataset_type}: falhou ({exc})")


if __name__ == "__main__":
    main()
