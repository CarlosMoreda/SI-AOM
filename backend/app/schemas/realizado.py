from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Limites de seguranca aplicados as quantidades e precos monetarios.
# Sao folgas largas mas suficientes para impedir a entrada de valores
# evidentemente erroneos (ex: 23 milhoes de kg ou 19 mil milhoes de EUR).
MAX_QTD = Decimal("1000000")          # 1 milhao de unidades
MAX_PESO_KG = Decimal("10000000")     # 10 mil toneladas
MAX_PRECO_UNIT = Decimal("1000000")   # 1 milhao EUR por unidade
MAX_HORAS = Decimal("100000")         # 100 mil horas


class RealizadoMaterialCreate(BaseModel):
    id_linha_material: int = Field(gt=0)
    quantidade: Decimal = Field(gt=0, le=MAX_QTD)
    peso_kg: Decimal | None = Field(default=None, ge=0, le=MAX_PESO_KG)
    custo_unitario_real: Decimal | None = Field(
        default=None, ge=0, le=MAX_PRECO_UNIT,
    )
    observacoes: str | None = None


class RealizadoMaterialUpdate(BaseModel):
    quantidade: Decimal | None = Field(default=None, gt=0, le=MAX_QTD)
    peso_kg: Decimal | None = Field(default=None, ge=0, le=MAX_PESO_KG)
    custo_unitario_real: Decimal | None = Field(
        default=None, ge=0, le=MAX_PRECO_UNIT,
    )
    observacoes: str | None = None


class RealizadoMaterialResponse(BaseModel):
    id_realizado_material: int
    id_linha_material: int
    data_registo: datetime
    quantidade: Decimal
    peso_kg: Decimal | None = None
    custo_unitario_real: Decimal
    custo_total_real: Decimal
    observacoes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RealizadoOperacaoCreate(BaseModel):
    id_linha_operacao: int = Field(gt=0)
    horas: Decimal = Field(gt=0, le=MAX_HORAS)
    tempo_setup_h: Decimal = Field(default=Decimal("0"), ge=0, le=MAX_HORAS)
    custo_hora_real: Decimal | None = Field(
        default=None, ge=0, le=MAX_PRECO_UNIT,
    )
    observacoes: str | None = None


class RealizadoOperacaoUpdate(BaseModel):
    horas: Decimal | None = Field(default=None, gt=0, le=MAX_HORAS)
    tempo_setup_h: Decimal | None = Field(default=None, ge=0, le=MAX_HORAS)
    custo_hora_real: Decimal | None = Field(
        default=None, ge=0, le=MAX_PRECO_UNIT,
    )
    observacoes: str | None = None


class RealizadoOperacaoResponse(BaseModel):
    id_realizado_operacao: int
    id_linha_operacao: int
    data_registo: datetime
    horas: Decimal
    tempo_setup_h: Decimal
    custo_hora_real: Decimal
    custo_total_real: Decimal
    observacoes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RealizadoServicoCreate(BaseModel):
    id_linha_servico: int = Field(gt=0)
    quantidade: Decimal = Field(gt=0, le=MAX_QTD)
    preco_unitario_real: Decimal | None = Field(
        default=None, ge=0, le=MAX_PRECO_UNIT,
    )
    observacoes: str | None = None


class RealizadoServicoUpdate(BaseModel):
    quantidade: Decimal | None = Field(default=None, gt=0, le=MAX_QTD)
    preco_unitario_real: Decimal | None = Field(
        default=None, ge=0, le=MAX_PRECO_UNIT,
    )
    observacoes: str | None = None


class RealizadoServicoResponse(BaseModel):
    id_realizado_servico: int
    id_linha_servico: int
    data_registo: datetime
    quantidade: Decimal
    preco_unitario_real: Decimal
    custo_total_real: Decimal
    observacoes: str | None = None

    model_config = ConfigDict(from_attributes=True)


class RealizadoResumoOrcamentoResponse(BaseModel):
    id_orcamento: int
    custo_total_real_materiais: Decimal
    custo_total_real_operacoes: Decimal
    custo_total_real_servicos: Decimal
    custo_total_real: Decimal
    horas_reais_totais: Decimal


class RealizadoResumoBatchRequest(BaseModel):
    ids_orcamento: list[int] = Field(default_factory=list, max_length=500)

    @field_validator("ids_orcamento")
    @classmethod
    def validar_ids_orcamento(cls, value: list[int]) -> list[int]:
        if any(id_orcamento <= 0 for id_orcamento in value):
            raise ValueError("Todos os ids_orcamento devem ser positivos")
        return value
