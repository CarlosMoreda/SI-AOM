from pydantic import BaseModel, ConfigDict


class LoginRequest(BaseModel):
    email: str
    password: str


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
