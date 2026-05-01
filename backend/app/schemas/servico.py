from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ServicoBase(BaseModel):
    codigo: str
    nome: str
    unidade: str
    preco_unitario_default: Decimal
    ativo: bool = True


class ServicoCreate(ServicoBase):
    pass


class ServicoUpdate(BaseModel):
    codigo: str | None = None
    nome: str | None = None
    unidade: str | None = None
    preco_unitario_default: Decimal | None = None
    ativo: bool | None = None


class ServicoResponse(ServicoBase):
    id_servico: int

    model_config = ConfigDict(from_attributes=True)