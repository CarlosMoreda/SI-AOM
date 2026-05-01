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
from app.models.operacao import Operacao
from app.schemas.operacao import OperacaoCreate, OperacaoResponse, OperacaoUpdate

router = APIRouter(
    dependencies=[Depends(require_roles(ROLE_ORCAMENTISTA, ROLE_ADMIN))]
)


@router.get("/", response_model=list[OperacaoResponse])
def listar_operacoes(db: Session = Depends(get_db)):
    stmt = select(Operacao).order_by(Operacao.id_operacao.desc())
    return db.scalars(stmt).all()


@router.get("/{id_operacao}", response_model=OperacaoResponse)
def obter_operacao(id_operacao: int, db: Session = Depends(get_db)):
    operacao = db.get(Operacao, id_operacao)
    if not operacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operação não encontrada")
    return operacao


@router.post("/", response_model=OperacaoResponse, status_code=status.HTTP_201_CREATED)
def criar_operacao(payload: OperacaoCreate, db: Session = Depends(get_db)):
    operacao = Operacao(**payload.model_dump())
    db.add(operacao)

    try:
        db.commit()
        db.refresh(operacao)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de operação duplicado ou dados inválidos",
        )

    return operacao


@router.put("/{id_operacao}", response_model=OperacaoResponse)
def atualizar_operacao(id_operacao: int, payload: OperacaoUpdate, db: Session = Depends(get_db)):
    operacao = db.get(Operacao, id_operacao)
    if not operacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operação não encontrada")

    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(operacao, campo, valor)

    try:
        db.commit()
        db.refresh(operacao)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar a operação",
        )

    return operacao


@router.delete("/{id_operacao}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_operacao(id_operacao: int, db: Session = Depends(get_db)):
    operacao = db.get(Operacao, id_operacao)
    if not operacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operação não encontrada")

    db.delete(operacao)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao e possivel eliminar: operacao associada a orcamentos",
        )
    return None
