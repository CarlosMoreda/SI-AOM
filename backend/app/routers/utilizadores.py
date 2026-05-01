from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    get_current_user,
    get_db,
    require_roles,
)
from app.models.utilizador import Utilizador
from app.routers.auth import hash_password
from app.schemas.utilizador import (
    UtilizadorCreate,
    UtilizadorResponse,
    UtilizadorUpdate,
)

router = APIRouter(dependencies=[Depends(require_roles(ROLE_ADMIN))])


def _normalize_email(email: str) -> str:
    return email.strip().lower()


@router.get("/", response_model=list[UtilizadorResponse])
def listar_utilizadores(db: Session = Depends(get_db)):
    stmt = select(Utilizador).order_by(Utilizador.ativo.desc(), Utilizador.nome.asc())
    return db.scalars(stmt).all()


@router.get("/{id_utilizador}", response_model=UtilizadorResponse)
def obter_utilizador(id_utilizador: int, db: Session = Depends(get_db)):
    utilizador = db.get(Utilizador, id_utilizador)
    if not utilizador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador nao encontrado",
        )
    return utilizador


@router.post("/", response_model=UtilizadorResponse, status_code=status.HTTP_201_CREATED)
def criar_utilizador(payload: UtilizadorCreate, db: Session = Depends(get_db)):
    dados = payload.model_dump()
    password = dados.pop("password", "").strip()

    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password obrigatoria",
        )

    dados["email"] = _normalize_email(dados["email"])
    utilizador = Utilizador(**dados, password_hash=hash_password(password))

    db.add(utilizador)
    try:
        db.commit()
        db.refresh(utilizador)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao foi possivel criar utilizador: email duplicado ou dados invalidos",
        )

    return utilizador


@router.put("/{id_utilizador}", response_model=UtilizadorResponse)
def atualizar_utilizador(
    id_utilizador: int,
    payload: UtilizadorUpdate,
    db: Session = Depends(get_db),
):
    utilizador = db.get(Utilizador, id_utilizador)
    if not utilizador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador nao encontrado",
        )

    dados = payload.model_dump(exclude_unset=True)
    password = dados.pop("password", None)

    if "email" in dados and dados["email"] is not None:
        dados["email"] = _normalize_email(dados["email"])

    for campo, valor in dados.items():
        setattr(utilizador, campo, valor)

    if password:
        utilizador.password_hash = hash_password(password.strip())

    try:
        db.commit()
        db.refresh(utilizador)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao foi possivel atualizar utilizador",
        )

    return utilizador


@router.delete("/{id_utilizador}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_utilizador(
    id_utilizador: int,
    db: Session = Depends(get_db),
    current_user: Utilizador = Depends(get_current_user),
):
    if id_utilizador == current_user.id_utilizador:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao pode eliminar o utilizador autenticado",
        )

    utilizador = db.get(Utilizador, id_utilizador)
    if not utilizador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilizador nao encontrado",
        )

    db.delete(utilizador)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao e possivel eliminar: utilizador associado a registos historicos. Desative o utilizador.",
        )

    return None
