from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    ROLE_GESTOR,
    ROLE_ORCAMENTISTA,
    ROLE_PRODUCAO,
    get_db,
    require_roles,
)
from app.models.operacao import Operacao
from app.schemas.operacao import OperacaoCreate, OperacaoResponse, OperacaoUpdate

READ_DEPS = [Depends(require_roles(
    ROLE_ORCAMENTISTA, ROLE_GESTOR, ROLE_PRODUCAO, ROLE_ADMIN,
))]
WRITE_DEPS = [Depends(require_roles(ROLE_ORCAMENTISTA, ROLE_ADMIN))]

router = APIRouter()


@router.get("/", response_model=list[OperacaoResponse], dependencies=READ_DEPS)
def listar_operacoes(
    response: Response,
    q: str | None = Query(None, description="Pesquisa por codigo ou nome"),
    limit: int | None = Query(
        default=None, ge=1, le=500,
        description="Registos por pagina. Omitir devolve todos (catalogo).",
    ),
    offset: int = Query(default=0, ge=0, description="Deslocamento (pagina)"),
    db: Session = Depends(get_db),
):
    base = select(Operacao)
    if q:
        termo = func.unaccent(f"%{q.lower()}%")
        base = base.where(
            or_(
                func.unaccent(func.lower(Operacao.codigo)).like(termo),
                func.unaccent(func.lower(Operacao.nome)).like(termo),
            )
        )

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    response.headers["X-Total-Count"] = str(total)

    stmt = base.order_by(Operacao.id_operacao.desc())
    if limit is not None:
        stmt = stmt.limit(limit).offset(offset)
    return db.scalars(stmt).all()


@router.get("/{id_operacao}", response_model=OperacaoResponse, dependencies=READ_DEPS)
def obter_operacao(id_operacao: int, db: Session = Depends(get_db)):
    operacao = db.get(Operacao, id_operacao)
    if not operacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operação não encontrada")
    return operacao


@router.post(
    "/",
    response_model=OperacaoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_DEPS,
)
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


@router.put("/{id_operacao}", response_model=OperacaoResponse, dependencies=WRITE_DEPS)
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


@router.delete(
    "/{id_operacao}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=WRITE_DEPS,
)
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
