from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
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
from app.schemas.orcamento import OrcamentoCreate, OrcamentoResponse, OrcamentoUpdate
from app.services.orcamento_service import recalcular_totais_orcamento
from app.services.pdf_service import gerar_pdf_orcamento

# Producao precisa de LER orcamentos para escolher para qual registar realizado,
# mas nao pode CRIAR/EDITAR/APAGAR orcamentos.
READ_DEPS = [Depends(require_roles(
    ROLE_ORCAMENTISTA, ROLE_GESTOR, ROLE_PRODUCAO, ROLE_ADMIN,
))]
WRITE_DEPS = [Depends(require_roles(
    ROLE_ORCAMENTISTA, ROLE_GESTOR, ROLE_ADMIN,
))]

router = APIRouter()


@router.get("/", response_model=list[OrcamentoResponse], dependencies=READ_DEPS)
def listar_orcamentos(
    limit: int = Query(
        default=500,
        gt=0,
        le=10000,
        description="Maximo de registos a devolver (mais recentes primeiro)",
    ),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Orcamento)
        .order_by(Orcamento.id_orcamento.desc())
        .limit(limit)
    )
    return db.scalars(stmt).all()


@router.get("/{id_orcamento}", response_model=OrcamentoResponse, dependencies=READ_DEPS)
def obter_orcamento(id_orcamento: int, db: Session = Depends(get_db)):
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")
    return orcamento


@router.post(
    "/",
    response_model=OrcamentoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_DEPS,
)
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


@router.put("/{id_orcamento}", response_model=OrcamentoResponse, dependencies=WRITE_DEPS)
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


@router.get(
    "/{id_orcamento}/pdf",
    dependencies=READ_DEPS,
    responses={200: {"content": {"application/pdf": {}}}},
)
def exportar_orcamento_pdf(id_orcamento: int, db: Session = Depends(get_db)):
    """Gera e devolve o PDF da proposta comercial deste orcamento."""
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orçamento não encontrado",
        )
    try:
        pdf_bytes = gerar_pdf_orcamento(db, id_orcamento)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

    # `versao` pode ja vir com o prefixo "v" (ex: "v1"). Normaliza para evitar
    # ficheiros com nome tipo "v_v1.pdf".
    versao_norm = orcamento.versao if orcamento.versao.startswith("v") else f"v{orcamento.versao}"
    filename = f"orcamento_{id_orcamento}_{versao_norm}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete(
    "/{id_orcamento}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=WRITE_DEPS,
)
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
