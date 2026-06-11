from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
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
from app.schemas.orcamento import OrcamentoCreate, OrcamentoResponse, OrcamentoUpdate
from app.services.orcamento_service import (
    recalcular_totais_orcamento,
    sincronizar_projeto_por_orcamentos,
    validar_transicao_estado_orcamento,
)
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
    response: Response,
    id_projeto: int | None = Query(None, gt=0, description="Filtra por projeto"),
    limit: int | None = Query(
        default=None, ge=1, le=500,
        description="Registos por pagina. Omitir devolve todos.",
    ),
    offset: int = Query(default=0, ge=0, description="Deslocamento (pagina)"),
    db: Session = Depends(get_db),
):
    base = select(Orcamento)
    if id_projeto is not None:
        base = base.where(Orcamento.id_projeto == id_projeto)

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    response.headers["X-Total-Count"] = str(total)

    stmt = base.order_by(Orcamento.id_orcamento.desc())
    if limit is not None:
        stmt = stmt.limit(limit).offset(offset)
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
    projeto = db.get(Projeto, payload.id_projeto)
    if not projeto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade: projeto inválido ou versão duplicada",
        )

    # Ciclo de vida (Figura 4): um orcamento novo comeca sempre em preparacao;
    # os restantes estados atingem-se por transicoes validas (PUT).
    if payload.estado != "em_preparacao":
        raise HTTPException(
            status_code=422,
            detail=(
                "Um orçamento novo começa em 'em_preparacao'. "
                "Use as transições de estado para avançar no ciclo de vida."
            ),
        )

    orcamento = Orcamento(**payload.model_dump(), criado_por=current_user.id_utilizador)

    db.add(orcamento)
    try:
        db.flush()
        sincronizar_projeto_por_orcamentos(db, projeto)
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

    # Mudancas de estado pedidas pelo utilizador tem de seguir o ciclo de
    # vida (sem saltos nem retrocessos fora dos retornos documentados).
    if "estado" in dados and dados["estado"] != orcamento.estado:
        valido, detalhe = validar_transicao_estado_orcamento(
            orcamento.estado, dados["estado"],
        )
        if not valido:
            raise HTTPException(
                status_code=422,
                detail=detalhe,
            )

    for campo, valor in dados.items():
        setattr(orcamento, campo, valor)

    # Se a margem ou o nº de unidades mudou, recalcula os totais do cabecalho
    # (custos = soma por unidade x quantidade_unidades) e o preco_venda.
    if "margem_percentual" in dados or "quantidade_unidades" in dados:
        recalcular_totais_orcamento(db, id_orcamento)

    try:
        projeto = db.get(Projeto, orcamento.id_projeto)
        if projeto:
            sincronizar_projeto_por_orcamentos(db, projeto)
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
