from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DetalheOperacaoOrcamentoCreate(BaseModel):
    id_operacao: int
    horas: Decimal
    tempo_setup_h: Decimal = Decimal("0")
    custo_hora_snapshot: Decimal | None = None
    observacoes: str | None = None


class DetalheOperacaoOrcamentoUpdate(BaseModel):
    id_operacao: int | None = None
    horas: Decimal | None = None
    tempo_setup_h: Decimal | None = None
    custo_hora_snapshot: Decimal | None = None
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