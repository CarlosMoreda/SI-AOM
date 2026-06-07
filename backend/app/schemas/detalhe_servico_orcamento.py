from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

MAX_QTD = Decimal("1000000")
MAX_PRECO_UNIT = Decimal("1000000")


class DetalheServicoOrcamentoCreate(BaseModel):
    id_servico: int = Field(gt=0)
    quantidade: Decimal = Field(gt=0, le=MAX_QTD)
    preco_unitario_snapshot: Decimal | None = Field(
        default=None, ge=0, le=MAX_PRECO_UNIT,
    )
    observacoes: str | None = None


class DetalheServicoOrcamentoUpdate(BaseModel):
    id_servico: int | None = Field(default=None, gt=0)
    quantidade: Decimal | None = Field(default=None, gt=0, le=MAX_QTD)
    preco_unitario_snapshot: Decimal | None = Field(
        default=None, ge=0, le=MAX_PRECO_UNIT,
    )
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
