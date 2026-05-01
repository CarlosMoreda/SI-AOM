from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.utilizador import Utilizador
from app.schemas.auth import LoginRequest, TokenResponse, UtilizadorMe

router = APIRouter()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return _pwd_context.verify(password, password_hash)
    except Exception:
        # Fallback para passwords em texto simples (dados de desenvolvimento)
        return password == password_hash


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def criar_token(data: dict) -> str:
    payload = data.copy()
    expira = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload["exp"] = expira
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    utilizador = db.scalar(
        select(Utilizador).where(Utilizador.email == payload.email)
    )

    if not utilizador or not verificar_password(payload.password, utilizador.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou password incorretos",
        )

    if not utilizador.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada",
        )

    token = criar_token({
        "sub": str(utilizador.id_utilizador),
        "perfil": utilizador.perfil,
    })

    return TokenResponse(access_token=token)


@router.get("/me", response_model=UtilizadorMe)
def me(current_user: Utilizador = Depends(get_current_user)):
    return current_user
