from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.utilizador import Utilizador
from app.schemas.auth import LoginRequest, TokenResponse, UtilizadorMe

router = APIRouter()


def _password_bytes(password: str) -> bytes:
    encoded = password.encode("utf-8")
    if len(encoded) > 72:
        raise ValueError("Password demasiado longa")
    return encoded


def verificar_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            _password_bytes(password),
            password_hash.encode("utf-8"),
        )
    except (TypeError, ValueError):
        return False


def _password_legacy_texto_simples(password: str, password_hash: str) -> bool:
    return settings.allow_plaintext_password_fallback and password == password_hash


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode("utf-8")


def _password_precisa_rehash(password_hash: str) -> bool:
    return not password_hash.startswith(("$2a$", "$2b$", "$2y$"))


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

    if not utilizador:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou password incorretos",
        )

    password_valida = verificar_password(payload.password, utilizador.password_hash)
    password_legacy = False

    if not password_valida and _password_legacy_texto_simples(
        payload.password,
        utilizador.password_hash,
    ):
        password_valida = True
        password_legacy = True

    if not password_valida:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou password incorretos",
        )

    if not utilizador.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada",
        )

    if password_legacy or _password_precisa_rehash(utilizador.password_hash):
        try:
            utilizador.password_hash = hash_password(payload.password)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            )
        db.commit()

    token = criar_token({
        "sub": str(utilizador.id_utilizador),
        "perfil": utilizador.perfil,
    })

    return TokenResponse(access_token=token)


@router.get("/me", response_model=UtilizadorMe)
def me(current_user: Utilizador = Depends(get_current_user)):
    return current_user
