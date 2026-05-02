from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MLPredictCustoRequest(BaseModel):
    """Parametros do projeto para previsao de custo real."""
    tipologia: str | None = Field(default=None, max_length=100)
    complexidade: str | None = Field(default=None, max_length=50)
    peso_total_kg: float | None = Field(default=None, gt=0)
    numero_pecas: int | None = Field(default=None, ge=1)
    material_principal: str | None = Field(default=None, max_length=100)
    tratamento_superficie: str | None = Field(default=None, max_length=100)
    processo_corte: str | None = Field(default=None, max_length=100)
    lead_time: int | None = Field(default=None, ge=1)
    # Opcionais: ligacao a um orcamento ja existente e nota livre.
    # Sao usados apenas para persistir a previsao em previsao_ml.
    id_orcamento: int | None = Field(default=None, gt=0)
    observacoes: str | None = None

    @model_validator(mode="after")
    def validate_model_inputs(self):
        required_fields = (
            "tipologia",
            "complexidade",
            "peso_total_kg",
            "numero_pecas",
            "material_principal",
            "tratamento_superficie",
            "processo_corte",
            "lead_time",
        )
        missing = []
        for field in required_fields:
            value = getattr(self, field)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(field)

        if missing:
            raise ValueError(
                "Parametros obrigatorios em falta: " + ", ".join(missing)
            )

        return self


class MLPredictCustoResponse(BaseModel):
    custo_materiais: float
    custo_operacoes: float
    custo_servicos: float
    custo_total: float
    modelo_utilizado: str
    modelo_versao: str | None = None
    qualidade_modelo: Literal["boa", "aceitavel", "fraca", "indeterminada"] = "indeterminada"
    r2_medio_holdout: float | None = None
    aviso_qualidade: str | None = None
    confianca_percentual: int = 0
    fora_faixa_treino: bool = False
    aviso_faixa_treino: str | None = None
    alertas_faixa_treino: list[str] = Field(default_factory=list)
    id_previsao: int | None = None


class MLPredictOptionsResponse(BaseModel):
    tipologias: list[str] = Field(default_factory=list)
    complexidades: list[str] = Field(default_factory=list)
    materiais: list[str] = Field(default_factory=list)
    tratamentos: list[str] = Field(default_factory=list)
    processos_corte: list[str] = Field(default_factory=list)
    feature_ranges: dict[str, dict[str, float]] = Field(default_factory=dict)
    features_usadas: list[str] = Field(default_factory=list)
    dataset_linhas: int | None = None
    source: str = "indisponivel"


class MLTrainOrcamentoRequest(BaseModel):
    dataset_dir: str = "ml"
    output_dir: str = "ml/models/random_forest"
    refresh_dataset: bool = True
    test_size: float = Field(default=0.25, gt=0, lt=1)
    random_state: int = 42
    n_estimators: int = Field(default=400, ge=10)
    max_depth: int | None = Field(default=None, ge=1)
    min_samples_leaf: int = Field(default=1, ge=1)
    csv_delimiter: str = ";"
    csv_encoding: str = "utf-8-sig"


class MLTrainResultItem(BaseModel):
    dataset_type: str
    status: Literal["ok", "error"]
    detail: str


class MLTrainResponse(BaseModel):
    total: int
    success: int
    failure: int
    results: list[MLTrainResultItem]

    model_config = ConfigDict(from_attributes=True)
