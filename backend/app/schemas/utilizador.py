from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UtilizadorBase(BaseModel):
    nome: str
    email: str
    perfil: str
    ativo: bool = True


class UtilizadorCreate(UtilizadorBase):
    password: str


class UtilizadorUpdate(BaseModel):
    nome: str | None = None
    email: str | None = None
    password: str | None = None
    perfil: str | None = None
    ativo: bool | None = None


class UtilizadorResponse(UtilizadorBase):
    id_utilizador: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
