from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    ROLE_ORCAMENTISTA,
    get_db,
    require_roles,
)
from app.models.servico import Servico
from app.schemas.servico import ServicoCreate, ServicoResponse, ServicoUpdate

router = APIRouter(
    dependencies=[Depends(require_roles(ROLE_ORCAMENTISTA, ROLE_ADMIN))]
)


@router.get("/", response_model=list[ServicoResponse])
def listar_servicos(db: Session = Depends(get_db)):
    stmt = select(Servico).order_by(Servico.id_servico.desc())
    return db.scalars(stmt).all()


@router.get("/{id_servico}", response_model=ServicoResponse)
def obter_servico(id_servico: int, db: Session = Depends(get_db)):
    servico = db.get(Servico, id_servico)
    if not servico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serviço não encontrado")
    return servico


@router.post("/", response_model=ServicoResponse, status_code=status.HTTP_201_CREATED)
def criar_servico(payload: ServicoCreate, db: Session = Depends(get_db)):
    servico = Servico(**payload.model_dump())
    db.add(servico)

    try:
        db.commit()
        db.refresh(servico)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de serviço duplicado ou dados inválidos",
        )

    return servico


@router.put("/{id_servico}", response_model=ServicoResponse)
def atualizar_servico(id_servico: int, payload: ServicoUpdate, db: Session = Depends(get_db)):
    servico = db.get(Servico, id_servico)
    if not servico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serviço não encontrado")

    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(servico, campo, valor)

    try:
        db.commit()
        db.refresh(servico)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar o serviço",
        )

    return servico


@router.delete("/{id_servico}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_servico(id_servico: int, db: Session = Depends(get_db)):
    servico = db.get(Servico, id_servico)
    if not servico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serviço não encontrado")

    db.delete(servico)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao e possivel eliminar: servico associado a orcamentos",
        )
    return None
