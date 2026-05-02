from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClienteBase(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    nif: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    telefone: str | None = Field(default=None, max_length=30)
    morada: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None
    ativo: bool = True


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=150)
    nif: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    telefone: str | None = Field(default=None, max_length=30)
    morada: str | None = Field(default=None, max_length=255)
    observacoes: str | None = None
    ativo: bool | None = None


class ClienteResponse(ClienteBase):
    id_cliente: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
