from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MaterialBase(BaseModel):
    codigo: str = Field(min_length=1, max_length=50)
    nome: str = Field(min_length=1, max_length=255)
    unidade: str = Field(min_length=1, max_length=20)
    tipo: str | None = Field(default=None, max_length=100)
    qualidade_material: str | None = Field(default=None, max_length=100)
    custo_unitario_default: Decimal = Field(ge=0)
    ativo: bool = True


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    unidade: str | None = Field(default=None, min_length=1, max_length=20)
    tipo: str | None = Field(default=None, max_length=100)
    qualidade_material: str | None = Field(default=None, max_length=100)
    custo_unitario_default: Decimal | None = Field(default=None, ge=0)
    ativo: bool | None = None


class MaterialResponse(MaterialBase):
    id_material: int

    model_config = ConfigDict(from_attributes=True)
