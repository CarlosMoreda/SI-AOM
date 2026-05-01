from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DetalheMaterialOrcamentoCreate(BaseModel):
    id_material: int
    quantidade: Decimal
    peso_kg: Decimal | None = None
    desperdicio_percent: Decimal = Decimal("0")
    preco_unitario_snapshot: Decimal | None = None
    observacoes: str | None = None


class DetalheMaterialOrcamentoUpdate(BaseModel):
    id_material: int | None = None
    quantidade: Decimal | None = None
    peso_kg: Decimal | None = None
    desperdicio_percent: Decimal | None = None
    preco_unitario_snapshot: Decimal | None = None
    observacoes: str | None = None


class DetalheMaterialOrcamentoResponse(BaseModel):
    id_linha_material: int
    id_orcamento: int
    id_material: int
    quantidade: Decimal
    peso_kg: Decimal | None = None
    desperdicio_percent: Decimal
    preco_unitario_snapshot: Decimal
    custo_total: Decimal
    observacoes: str | None = None

    model_config = ConfigDict(from_attributes=True)