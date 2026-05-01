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
from app.models.projeto import Projeto
from app.schemas.orcamento import OrcamentoResponse
from app.schemas.projeto import ProjetoCreate, ProjetoResponse, ProjetoUpdate

router = APIRouter(
    dependencies=[Depends(require_roles(ROLE_ORCAMENTISTA, ROLE_GESTOR, ROLE_ADMIN))]
)


@router.get("/", response_model=list[ProjetoResponse])
def listar_projetos(db: Session = Depends(get_db)):
    stmt = select(Projeto).order_by(Projeto.id_projeto.desc())
    return db.scalars(stmt).all()


@router.get("/{id_projeto}", response_model=ProjetoResponse)
def obter_projeto(id_projeto: int, db: Session = Depends(get_db)):
    projeto = db.get(Projeto, id_projeto)
    if not projeto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")
    return projeto


@router.get("/{id_projeto}/orcamentos", response_model=list[OrcamentoResponse])
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


@router.post("/", response_model=ProjetoResponse, status_code=status.HTTP_201_CREATED)
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


@router.put("/{id_projeto}", response_model=ProjetoResponse)
def atualizar_projeto(id_projeto: int, payload: ProjetoUpdate, db: Session = Depends(get_db)):
    projeto = db.get(Projeto, id_projeto)
    if not projeto:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")

    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(projeto, campo, valor)

    try:
        db.commit()
        db.refresh(projeto)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar o projeto",
        )

    return projeto


@router.delete("/{id_projeto}", status_code=status.HTTP_204_NO_CONTENT)
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
