from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RealizadoMaterialCreate(BaseModel):
    id_linha_material: int = Field(gt=0)
    quantidade: Decimal = Field(gt=0)
    peso_kg: Decimal | None = Field(default=None, ge=0)
    custo_unitario_real: Decimal | None = Field(default=None, ge=0)
    observacoes: str | None = None


class RealizadoMaterialUpdate(BaseModel):
    quantidade: Decimal | None = Field(default=None, gt=0)
    peso_kg: Decimal | None = Field(default=None, ge=0)
    custo_unitario_real: Decimal | None = Field(default=None, ge=0)
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
    horas: Decimal = Field(gt=0)
    tempo_setup_h: Decimal = Field(default=Decimal("0"), ge=0)
    custo_hora_real: Decimal | None = Field(default=None, ge=0)
    observacoes: str | None = None


class RealizadoOperacaoUpdate(BaseModel):
    horas: Decimal | None = Field(default=None, gt=0)
    tempo_setup_h: Decimal | None = Field(default=None, ge=0)
    custo_hora_real: Decimal | None = Field(default=None, ge=0)
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
    quantidade: Decimal = Field(gt=0)
    preco_unitario_real: Decimal | None = Field(default=None, ge=0)
    observacoes: str | None = None


class RealizadoServicoUpdate(BaseModel):
    quantidade: Decimal | None = Field(default=None, gt=0)
    preco_unitario_real: Decimal | None = Field(default=None, ge=0)
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
