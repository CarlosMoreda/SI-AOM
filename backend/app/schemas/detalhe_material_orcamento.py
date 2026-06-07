from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

# Limites de seguranca (mesmos do realizado): folga larga, mas impedem
# valores claramente absurdos (ex: milhoes de kg ou EUR por unidade).
MAX_QTD = Decimal("1000000")
MAX_PESO_KG = Decimal("10000000")
MAX_AREA_M2 = Decimal("1000000")
MAX_PRECO_UNIT = Decimal("1000000")


class DetalheMaterialOrcamentoCreate(BaseModel):
    id_material: int = Field(gt=0)
    quantidade: Decimal = Field(gt=0, le=MAX_QTD)
    peso_kg: Decimal | None = Field(default=None, ge=0, le=MAX_PESO_KG)
    area_m2: Decimal | None = Field(default=None, ge=0, le=MAX_AREA_M2)
    desperdicio_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    preco_unitario_snapshot: Decimal | None = Field(
        default=None, ge=0, le=MAX_PRECO_UNIT,
    )
    observacoes: str | None = None


class DetalheMaterialOrcamentoUpdate(BaseModel):
    id_material: int | None = Field(default=None, gt=0)
    quantidade: Decimal | None = Field(default=None, gt=0, le=MAX_QTD)
    peso_kg: Decimal | None = Field(default=None, ge=0, le=MAX_PESO_KG)
    area_m2: Decimal | None = Field(default=None, ge=0, le=MAX_AREA_M2)
    desperdicio_percent: Decimal | None = Field(default=None, ge=0, le=100)
    preco_unitario_snapshot: Decimal | None = Field(
        default=None, ge=0, le=MAX_PRECO_UNIT,
    )
    observacoes: str | None = None


class DetalheMaterialOrcamentoResponse(BaseModel):
    id_linha_material: int
    id_orcamento: int
    id_material: int
    quantidade: Decimal
    peso_kg: Decimal | None = None
    area_m2: Decimal | None = None
    desperdicio_percent: Decimal
    preco_unitario_snapshot: Decimal
    custo_total: Decimal
    observacoes: str | None = None

    model_config = ConfigDict(from_attributes=True)
