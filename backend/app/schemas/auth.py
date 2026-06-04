from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UtilizadorMe(BaseModel):
    id_utilizador: int
    nome: str
    email: str
    perfil: str
    ativo: bool

    model_config = ConfigDict(from_attributes=True)
