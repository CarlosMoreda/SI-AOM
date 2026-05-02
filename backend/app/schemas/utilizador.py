from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PerfilUtilizador = Literal["administrador", "orcamentista", "producao", "gestor"]


class UtilizadorBase(BaseModel):
    nome: str = Field(min_length=1, max_length=150)
    email: str = Field(min_length=3, max_length=255)
    perfil: PerfilUtilizador
    ativo: bool = True


class UtilizadorCreate(UtilizadorBase):
    password: str = Field(min_length=8, max_length=72)


class UtilizadorUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=150)
    email: str | None = Field(default=None, min_length=3, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=72)
    perfil: PerfilUtilizador | None = None
    ativo: bool | None = None


class UtilizadorResponse(UtilizadorBase):
    id_utilizador: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
