from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# Limites: ate 100 mil horas por linha (folga absurda) e 1 milhao EUR/h.
MAX_HORAS = Decimal("100000")
MAX_CUSTO_HORA = Decimal("1000000")


class DetalheOperacaoOrcamentoCreate(BaseModel):
    id_operacao: int = Field(gt=0)
    horas: Decimal = Field(gt=0, le=MAX_HORAS)
    tempo_setup_h: Decimal = Field(default=Decimal("0"), ge=0, le=MAX_HORAS)
    custo_hora_snapshot: Decimal | None = Field(
        default=None, ge=0, le=MAX_CUSTO_HORA,
    )
    observacoes: str | None = None


class DetalheOperacaoOrcamentoUpdate(BaseModel):
    id_operacao: int | None = Field(default=None, gt=0)
    horas: Decimal | None = Field(default=None, gt=0, le=MAX_HORAS)
    tempo_setup_h: Decimal | None = Field(default=None, ge=0, le=MAX_HORAS)
    custo_hora_snapshot: Decimal | None = Field(
        default=None, ge=0, le=MAX_CUSTO_HORA,
    )
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
