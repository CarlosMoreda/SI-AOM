from collections.abc import Generator
import unicodedata

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal

_bearer = HTTPBearer()

ROLE_ADMIN = "administrador"
ROLE_ORCAMENTISTA = "orcamentista"
ROLE_PRODUCAO = "producao"
ROLE_GESTOR = "gestor"


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
):
    from app.models.utilizador import Utilizador

    credenciais_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        id_utilizador = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise credenciais_invalidas

    utilizador = db.get(Utilizador, id_utilizador)
    if not utilizador or not utilizador.ativo:
        raise credenciais_invalidas

    return utilizador


def _normalize_role(role: str | None) -> str:
    if not role:
        return ""
    normalized = unicodedata.normalize("NFKD", role)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "admin": ROLE_ADMIN,
        "administrator": ROLE_ADMIN,
        "orcamentacao": ROLE_ORCAMENTISTA,
        "orcamentista": ROLE_ORCAMENTISTA,
        "producao": ROLE_PRODUCAO,
        "producao_": ROLE_PRODUCAO,
        "gestao": ROLE_GESTOR,
        "gestor": ROLE_GESTOR,
    }
    return aliases.get(normalized, normalized)


def require_roles(*allowed_roles: str):
    normalized_allowed = {_normalize_role(role) for role in allowed_roles}

    def _role_dependency(current_user=Depends(get_current_user)):
        perfil_utilizador = _normalize_role(getattr(current_user, "perfil", ""))
        if perfil_utilizador not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissao para executar esta operacao",
            )
        return current_user

    return _role_dependency
