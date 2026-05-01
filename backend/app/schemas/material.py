from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class MaterialBase(BaseModel):
    codigo: str
    nome: str
    unidade: str
    tipo: str | None = None
    qualidade_material: str | None = None
    custo_unitario_default: Decimal
    ativo: bool = True


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    codigo: str | None = None
    nome: str | None = None
    unidade: str | None = None
    tipo: str | None = None
    qualidade_material: str | None = None
    custo_unitario_default: Decimal | None = None
    ativo: bool | None = None


class MaterialResponse(MaterialBase):
    id_material: int

    model_config = ConfigDict(from_attributes=True)