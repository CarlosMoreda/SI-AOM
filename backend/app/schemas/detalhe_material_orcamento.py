from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DetalheMaterialOrcamentoCreate(BaseModel):
    id_material: int = Field(gt=0)
    quantidade: Decimal = Field(gt=0)
    peso_kg: Decimal | None = Field(default=None, ge=0)
    desperdicio_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    preco_unitario_snapshot: Decimal | None = Field(default=None, ge=0)
    observacoes: str | None = None


class DetalheMaterialOrcamentoUpdate(BaseModel):
    id_material: int | None = Field(default=None, gt=0)
    quantidade: Decimal | None = Field(default=None, gt=0)
    peso_kg: Decimal | None = Field(default=None, ge=0)
    desperdicio_percent: Decimal | None = Field(default=None, ge=0, le=100)
    preco_unitario_snapshot: Decimal | None = Field(default=None, ge=0)
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
