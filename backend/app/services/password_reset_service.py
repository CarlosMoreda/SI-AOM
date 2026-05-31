from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.utilizador import Utilizador

logger = logging.getLogger(__name__)

TOKEN_VALIDITY_MINUTES = 30
TOKEN_PURPOSE = "password_reset"


def _build_reset_url(token: str) -> str:
    # Frontend default em desenvolvimento. Em producao deve vir de config.
    base_url = "http://localhost:5173"
    return f"{base_url}/?reset_token={token}"


def _send_reset_email(email: str, reset_url: str) -> None:
    # Sem SMTP configurado: o link e impresso no log do servidor.
    # Em producao, integrar com SendGrid/Mailgun/SES.
    logger.warning(
        "[PASSWORD RESET] Envia este link ao utilizador %s : %s",
        email,
        reset_url,
    )


def _issue_reset_token(id_utilizador: int) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_VALIDITY_MINUTES)
    payload = {
        "sub": str(id_utilizador),
        "purpose": TOKEN_PURPOSE,
        "exp": expira,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_reset_token(token: str) -> int | None:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return None

    if payload.get("purpose") != TOKEN_PURPOSE:
        return None

    sub = payload.get("sub")
    try:
        return int(sub) if sub is not None else None
    except (TypeError, ValueError):
        return None


def create_reset_token(db: Session, email: str) -> None:
    """Gera um token de reset (JWT) e dispara o envio (simulado) por email.

    Nao revela ao caller se o email existe -- politica anti-enumeracao.
    Sem qualquer persistencia: o token e auto-contido (assinatura + expiracao).
    """
    utilizador = db.scalar(select(Utilizador).where(Utilizador.email == email))
    if not utilizador or not utilizador.ativo:
        return

    token = _issue_reset_token(utilizador.id_utilizador)
    _send_reset_email(utilizador.email, _build_reset_url(token))


def confirm_reset(db: Session, token: str, nova_password: str) -> bool:
    """Valida o token JWT e troca a password do utilizador."""
    from app.routers.auth import hash_password  # evita import circular

    id_utilizador = _decode_reset_token(token)
    if id_utilizador is None:
        return False

    utilizador = db.get(Utilizador, id_utilizador)
    if not utilizador or not utilizador.ativo:
        return False

    try:
        utilizador.password_hash = hash_password(nova_password)
    except ValueError:
        return False

    db.commit()
    return True
