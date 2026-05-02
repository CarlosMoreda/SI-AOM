from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OperacaoBase(BaseModel):
    codigo: str = Field(min_length=1, max_length=50)
    nome: str = Field(min_length=1, max_length=255)
    categoria: str | None = Field(default=None, max_length=100)
    custo_hora_default: Decimal = Field(ge=0)
    setup_hora_default: Decimal = Field(default=Decimal("0"), ge=0)
    ativo: bool = True


class OperacaoCreate(OperacaoBase):
    pass


class OperacaoUpdate(BaseModel):
    codigo: str | None = Field(default=None, min_length=1, max_length=50)
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    categoria: str | None = Field(default=None, max_length=100)
    custo_hora_default: Decimal | None = Field(default=None, ge=0)
    setup_hora_default: Decimal | None = Field(default=None, ge=0)
    ativo: bool | None = None


class OperacaoResponse(OperacaoBase):
    id_operacao: int

    model_config = ConfigDict(from_attributes=True)
