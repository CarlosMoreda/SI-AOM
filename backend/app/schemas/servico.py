from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ServicoBase(BaseModel):
    codigo: str = Field(min_length=1, max_length=50)
    nome: str = Field(min_length=1, max_length=255)
    unidade: str = Field(min_length=1, max_length=20)
    preco_unitario_default: Decimal = Field(ge=0)
    ativo: bool = True


class ServicoCreate(ServicoBase):
    pass


class ServicoUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    unidade: str | None = Field(default=None, min_length=1, max_length=20)
    preco_unitario_default: Decimal | None = Field(default=None, ge=0)
    ativo: bool | None = None


class ServicoResponse(ServicoBase):
    id_servico: int

    model_config = ConfigDict(from_attributes=True)
