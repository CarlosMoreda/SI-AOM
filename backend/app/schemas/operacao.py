from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OperacaoBase(BaseModel):
    codigo: str
    nome: str
    categoria: str | None = None
    custo_hora_default: Decimal
    setup_hora_default: Decimal = Decimal("0")
    ativo: bool = True


class OperacaoCreate(OperacaoBase):
    pass


class OperacaoUpdate(BaseModel):
    codigo: str | None = None
    nome: str | None = None
    categoria: str | None = None
    custo_hora_default: Decimal | None = None
    setup_hora_default: Decimal | None = None
    ativo: bool | None = None


class OperacaoResponse(OperacaoBase):
    id_operacao: int

    model_config = ConfigDict(from_attributes=True)