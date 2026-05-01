from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DetalheServicoOrcamentoCreate(BaseModel):
    id_servico: int
    quantidade: Decimal
    preco_unitario_snapshot: Decimal | None = None
    observacoes: str | None = None


class DetalheServicoOrcamentoUpdate(BaseModel):
    id_servico: int | None = None
    quantidade: Decimal | None = None
    preco_unitario_snapshot: Decimal | None = None
    observacoes: str | None = None


class DetalheServicoOrcamentoResponse(BaseModel):
    id_linha_servico: int
    id_orcamento: int
    id_servico: int
    quantidade: Decimal
    preco_unitario_snapshot: Decimal
    custo_total: Decimal
    observacoes: str | None = None

    model_config = ConfigDict(from_attributes=True)