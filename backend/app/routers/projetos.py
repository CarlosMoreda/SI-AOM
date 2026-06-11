from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    ROLE_GESTOR,
    ROLE_ORCAMENTISTA,
    ROLE_PRODUCAO,
    get_current_user,
    get_db,
    require_roles,
)
from app.models.orcamento import Orcamento
from app.models.projeto import Projeto
from app.schemas.orcamento import OrcamentoResponse
from app.schemas.projeto import ProjetoCreate, ProjetoResponse, ProjetoUpdate
from app.services.orcamento_service import sincronizar_orcamentos_do_projeto

# Producao precisa de LER projetos para o filtro do modulo Realizado.
READ_DEPS = [Depends(require_roles(
    ROLE_ORCAMENTISTA, ROLE_GESTOR, ROLE_PRODUCAO, ROLE_ADMIN,
))]
WRITE_DEPS = [Depends(require_roles(
    ROLE_ORCAMENTISTA, ROLE_GESTOR, ROLE_ADMIN,
))]

router = APIRouter()


@router.get("/", response_model=list[ProjetoResponse], dependencies=READ_DEPS)
def listar_projetos(
    response: Response,
    q: str | None = Query(None, description="Pesquisa por referencia ou designacao"),
    limit: int | None = Query(
        default=None, ge=1, le=500,
        description="Registos por pagina. Omitir devolve todos (dropdowns).",
    ),
    offset: int = Query(default=0, ge=0, description="Deslocamento (pagina)"),
    db: Session = Depends(get_db),
):
    base = select(Projeto)
    if q:
        termo = func.unaccent(f"%{q.lower()}%")
        base = base.where(
            or_(
                func.unaccent(func.lower(Projeto.referencia)).like(termo),
                func.unaccent(func.lower(Projeto.designacao)).like(termo),
            )
        )

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    response.headers["X-Total-Count"] = str(total)

    stmt = base.order_by(Projeto.id_projeto.desc())
    if limit is not None:
        stmt = stmt.limit(limit).offset(offset)
    return db.scalars(stmt).all()


@router.get("/{id_projeto}", response_model=ProjetoResponse, dependencies=READ_DEPS)
def obter_projeto(id_projeto: int, db: Session = Depends(get_db)):
    projeto = db.get(Projeto, id_projeto)
    if not projeto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")
    return projeto


@router.get(
    "/{id_projeto}/orcamentos",
    response_model=list[OrcamentoResponse],
    dependencies=READ_DEPS,
)
def listar_orcamentos_do_projeto(id_projeto: int, db: Session = Depends(get_db)):
    projeto = db.get(Projeto, id_projeto)
    if not projeto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")

    stmt = (
        select(Orcamento)
        .where(Orcamento.id_projeto == id_projeto)
        .order_by(Orcamento.versao.asc())
    )
    return db.scalars(stmt).all()


@router.post(
    "/",
    response_model=ProjetoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_DEPS,
)
def criar_projeto(
    payload: ProjetoCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    projeto = Projeto(**payload.model_dump(), criado_por=current_user.id_utilizador)

    db.add(projeto)
    try:
        db.commit()
        db.refresh(projeto)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade: referência duplicada",
        )

    return projeto


@router.put("/{id_projeto}", response_model=ProjetoResponse, dependencies=WRITE_DEPS)
def atualizar_projeto(id_projeto: int, payload: ProjetoUpdate, db: Session = Depends(get_db)):
    projeto = db.get(Projeto, id_projeto)
    if not projeto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")

    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(projeto, campo, valor)

    try:
        sincronizar_orcamentos_do_projeto(db, projeto)
        db.commit()
        db.refresh(projeto)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar o projeto",
        )

    return projeto


@router.delete(
    "/{id_projeto}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=WRITE_DEPS,
)
def eliminar_projeto(id_projeto: int, db: Session = Depends(get_db)):
    projeto = db.get(Projeto, id_projeto)
    if not projeto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")

    db.delete(projeto)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao e possivel eliminar: projeto com registos dependentes",
        )
    return None
