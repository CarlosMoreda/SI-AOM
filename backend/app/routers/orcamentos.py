from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    ROLE_GESTOR,
    ROLE_ORCAMENTISTA,
    get_current_user,
    get_db,
    require_roles,
)
from app.models.orcamento import Orcamento
from app.schemas.orcamento import OrcamentoCreate, OrcamentoResponse, OrcamentoUpdate
from app.services.orcamento_service import recalcular_totais_orcamento

router = APIRouter(
    dependencies=[Depends(require_roles(ROLE_ORCAMENTISTA, ROLE_GESTOR, ROLE_ADMIN))]
)


@router.get("/", response_model=list[OrcamentoResponse])
def listar_orcamentos(db: Session = Depends(get_db)):
    stmt = select(Orcamento).order_by(Orcamento.id_orcamento.desc())
    return db.scalars(stmt).all()


@router.get("/{id_orcamento}", response_model=OrcamentoResponse)
def obter_orcamento(id_orcamento: int, db: Session = Depends(get_db)):
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")
    return orcamento


@router.post("/", response_model=OrcamentoResponse, status_code=status.HTTP_201_CREATED)
def criar_orcamento(
    payload: OrcamentoCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    orcamento = Orcamento(**payload.model_dump(), criado_por=current_user.id_utilizador)

    db.add(orcamento)
    try:
        db.commit()
        db.refresh(orcamento)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade: projeto inválido ou versão duplicada",
        )

    return orcamento


@router.put("/{id_orcamento}", response_model=OrcamentoResponse)
def atualizar_orcamento(id_orcamento: int, payload: OrcamentoUpdate, db: Session = Depends(get_db)):
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")

    dados = payload.model_dump(exclude_unset=True)
    for campo, valor in dados.items():
        setattr(orcamento, campo, valor)

    # Se margem_percentual foi alterada, recalcula preco_venda automaticamente.
    if "margem_percentual" in dados:
        recalcular_totais_orcamento(db, id_orcamento)

    try:
        db.commit()
        db.refresh(orcamento)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar o orçamento",
        )

    return orcamento


@router.delete("/{id_orcamento}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_orcamento(id_orcamento: int, db: Session = Depends(get_db)):
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")

    db.delete(orcamento)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao e possivel eliminar: orcamento com registos dependentes",
        )
    return None
