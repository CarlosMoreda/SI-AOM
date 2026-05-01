from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ClienteBase(BaseModel):
    nome: str
    nif: str | None = None
    email: str | None = None
    telefone: str | None = None
    morada: str | None = None
    observacoes: str | None = None
    ativo: bool = True


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(BaseModel):
    nome: str | None = None
    nif: str | None = None
    email: str | None = None
    telefone: str | None = None
    morada: str | None = None
    observacoes: str | None = None
    ativo: bool | None = None


class ClienteResponse(ClienteBase):
    id_cliente: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
