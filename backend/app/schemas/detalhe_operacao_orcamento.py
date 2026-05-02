from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DetalheOperacaoOrcamentoCreate(BaseModel):
    id_operacao: int = Field(gt=0)
    horas: Decimal = Field(gt=0)
    tempo_setup_h: Decimal = Field(default=Decimal("0"), ge=0)
    custo_hora_snapshot: Decimal | None = Field(default=None, ge=0)
    observacoes: str | None = None


class DetalheOperacaoOrcamentoUpdate(BaseModel):
    id_operacao: int | None = Field(default=None, gt=0)
    horas: Decimal | None = Field(default=None, gt=0)
    tempo_setup_h: Decimal | None = Field(default=None, ge=0)
    custo_hora_snapshot: Decimal | None = Field(default=None, ge=0)
    observacoes: str | None = None


class DetalheOperacaoOrcamentoResponse(BaseModel):
    id_linha_operacao: int
    id_orcamento: int
    id_operacao: int
    horas: Decimal
    tempo_setup_h: Decimal
    custo_hora_snapshot: Decimal
    custo_total: Decimal
    observacoes: str | None = None

    model_config = ConfigDict(from_attributes=True)
