"""Cache em memoria dos modelos de Machine Learning.

Carrega os 4 sub-modelos (materiais, operacoes, servicos, horas) uma unica
vez durante o arranque da aplicacao via FastAPI lifespan e mantem-nos em
memoria para todas as previsoes subsequentes. Evita o I/O e a desserializacao
do joblib (~82 MB por modelo) a cada chamada.
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

import joblib

from app.ml.train_random_forest import ORCAMENTO_SUB_MODELS

logger = logging.getLogger(__name__)

BACKEND_ROOT = Path(__file__).resolve().parents[1]
MODEL_BASE_DIR = BACKEND_ROOT / "ml" / "models" / "random_forest"


class MLModelCache:
    """Mantem em memoria os sub-modelos e respectivas metricas.

    A leitura dos modelos do disco e custosa (>1 s no arranque para os 4
    sub-modelos). Este objecto e instanciado uma unica vez no lifespan
    da FastAPI e disponibilizado via `app.state.ml_cache`.
    """

    def __init__(self, model_base_dir: Path = MODEL_BASE_DIR) -> None:
        self.model_base_dir = model_base_dir
        self._models: dict[str, Any] = {}
        self._metrics: dict[str, dict[str, Any]] = {}
        self._loaded = False

    def load_all(self) -> None:
        """Carrega todos os sub-modelos definidos em ORCAMENTO_SUB_MODELS."""
        inicio = time.perf_counter()
        loaded = 0
        for sub_model in ORCAMENTO_SUB_MODELS:
            model_path = self.model_base_dir / sub_model / "model.joblib"
            metrics_path = self.model_base_dir / sub_model / "metrics.json"
            if not model_path.exists() or not metrics_path.exists():
                logger.warning(
                    "[ml_cache] Sub-modelo '%s' nao encontrado em %s. "
                    "A previsao continuara a tentar carregar do disco.",
                    sub_model,
                    model_path,
                )
                continue
            try:
                self._models[sub_model] = joblib.load(model_path)
                import json
                with open(metrics_path, encoding="utf-8") as fh:
                    self._metrics[sub_model] = json.load(fh)
                loaded += 1
            except Exception:  # noqa: BLE001
                logger.exception("[ml_cache] Falha ao carregar '%s'", sub_model)
        elapsed = time.perf_counter() - inicio
        self._loaded = True
        logger.info(
            "[ml_cache] %d/%d sub-modelos carregados em %.2f s",
            loaded,
            len(ORCAMENTO_SUB_MODELS),
            elapsed,
        )

    def reload(self) -> None:
        """Limpa e recarrega tudo (util apos re-treino sem reiniciar)."""
        self._models.clear()
        self._metrics.clear()
        self._loaded = False
        self.load_all()

    def clear(self) -> None:
        """Liberta a memoria ocupada pelos modelos."""
        self._models.clear()
        self._metrics.clear()
        self._loaded = False

    def get_model(self, sub_model: str) -> Any | None:
        """Devolve o pipeline carregado ou None se nao estiver em cache."""
        return self._models.get(sub_model)

    def get_metrics(self, sub_model: str) -> dict[str, Any] | None:
        return self._metrics.get(sub_model)

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def size(self) -> int:
        return len(self._models)
