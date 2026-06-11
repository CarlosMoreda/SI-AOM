from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    ROLE_GESTOR,
    ROLE_ORCAMENTISTA,
    get_db,
    require_roles,
)
from app.models.detalhe_material_orcamento import DetalheMaterialOrcamento
from app.models.detalhe_operacao_orcamento import DetalheOperacaoOrcamento
from app.models.detalhe_servico_orcamento import DetalheServicoOrcamento
from app.models.orcamento import Orcamento
from app.models.projeto import Projeto
from app.models.realizado_material import RealizadoMaterial
from app.models.realizado_operacao import RealizadoOperacao
from app.models.realizado_servico import RealizadoServico
from app.schemas.dashboard import (
    DashboardKpisResponse,
    OrcamentoRecenteItem,
    ProjetosPorEstadoItem,
)

router = APIRouter(
    dependencies=[Depends(require_roles(ROLE_ORCAMENTISTA, ROLE_GESTOR, ROLE_ADMIN))]
)


def _q2(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _real_total_por_orcamento_subquery(db: Session):
    """Subquery que devolve (id_orcamento, custo_total_real) somando as 3 tabelas
    de realizado (material/operacao/servico).
    """
    mat = (
        select(
            DetalheMaterialOrcamento.id_orcamento.label("id_orcamento"),
            func.coalesce(
                func.sum(RealizadoMaterial.custo_total_real), 0
            ).label("total"),
        )
        .join(
            DetalheMaterialOrcamento,
            RealizadoMaterial.id_linha_material
            == DetalheMaterialOrcamento.id_linha_material,
        )
        .group_by(DetalheMaterialOrcamento.id_orcamento)
    ).subquery()

    op = (
        select(
            DetalheOperacaoOrcamento.id_orcamento.label("id_orcamento"),
            func.coalesce(
                func.sum(RealizadoOperacao.custo_total_real), 0
            ).label("total"),
        )
        .join(
            DetalheOperacaoOrcamento,
            RealizadoOperacao.id_linha_operacao
            == DetalheOperacaoOrcamento.id_linha_operacao,
        )
        .group_by(DetalheOperacaoOrcamento.id_orcamento)
    ).subquery()

    svc = (
        select(
            DetalheServicoOrcamento.id_orcamento.label("id_orcamento"),
            func.coalesce(
                func.sum(RealizadoServico.custo_total_real), 0
            ).label("total"),
        )
        .join(
            DetalheServicoOrcamento,
            RealizadoServico.id_linha_servico
            == DetalheServicoOrcamento.id_linha_servico,
        )
        .group_by(DetalheServicoOrcamento.id_orcamento)
    ).subquery()

    return mat, op, svc


@router.get("/kpis", response_model=DashboardKpisResponse)
def dashboard_kpis(db: Session = Depends(get_db)):
    """Devolve metricas globais agregadas para o dashboard.

    Todas as agregacoes correm em SQL (COUNT/SUM/AVG), independentes do volume
    de dados. Substitui o calculo client-side que dependia da lista paginada.
    """
    total_projetos = db.scalar(select(func.count(Projeto.id_projeto))) or 0
    total_orcamentos = db.scalar(select(func.count(Orcamento.id_orcamento))) or 0

    # total_orcado considera apenas a ULTIMA versao de cada projeto, evitando
    # contar duas vezes o orcamento de projetos que tiveram revisao (v1 + v2).
    # "Ultima versao" = a mais recentemente criada por projeto.
    _rn_versao = func.row_number().over(
        partition_by=Orcamento.id_projeto,
        order_by=(
            Orcamento.data_criacao.desc(),
            Orcamento.id_orcamento.desc(),
        ),
    ).label("rn")
    ultima_versao_sq = select(
        Orcamento.custo_total_orcado.label("custo"),
        _rn_versao,
    ).subquery()

    total_orcado = db.scalar(
        select(func.coalesce(func.sum(ultima_versao_sq.c.custo), 0)).where(
            ultima_versao_sq.c.rn == 1
        )
    ) or 0
    num_ultimas_versoes = db.scalar(
        select(func.count())
        .select_from(ultima_versao_sq)
        .where(ultima_versao_sq.c.rn == 1)
    ) or 0

    # Total real: soma das 3 tabelas de realizado.
    real_materiais = db.scalar(
        select(func.coalesce(func.sum(RealizadoMaterial.custo_total_real), 0))
    ) or 0
    real_operacoes = db.scalar(
        select(func.coalesce(func.sum(RealizadoOperacao.custo_total_real), 0))
    ) or 0
    real_servicos = db.scalar(
        select(func.coalesce(func.sum(RealizadoServico.custo_total_real), 0))
    ) or 0
    total_real = Decimal(str(real_materiais)) + Decimal(str(real_operacoes)) + Decimal(str(real_servicos))

    # Custo medio = custo orcado medio por projeto, usando a mesma base
    # (ultima versao de cada projeto) que o total_orcado, para coerencia.
    ticket_medio = (
        Decimal(str(total_orcado)) / Decimal(num_ultimas_versoes)
        if num_ultimas_versoes > 0
        else Decimal("0")
    )

    # Desvio medio real: compara orcado vs real APENAS sobre os orcamentos que
    # ja tem realizado registado. Caso contrario, o denominador incluiria o
    # orcado de orcamentos ainda sem execucao (real = 0), distorcendo o valor
    # para fortemente negativo sem significado de negocio.
    mat_sq, op_sq, svc_sq = _real_total_por_orcamento_subquery(db)
    real_por_orcamento = (
        select(
            Orcamento.custo_total_orcado.label("orcado"),
            (
                func.coalesce(mat_sq.c.total, 0)
                + func.coalesce(op_sq.c.total, 0)
                + func.coalesce(svc_sq.c.total, 0)
            ).label("real"),
        )
        .outerjoin(mat_sq, mat_sq.c.id_orcamento == Orcamento.id_orcamento)
        .outerjoin(op_sq, op_sq.c.id_orcamento == Orcamento.id_orcamento)
        .outerjoin(svc_sq, svc_sq.c.id_orcamento == Orcamento.id_orcamento)
    ).subquery()

    orcado_com_real = db.scalar(
        select(func.coalesce(func.sum(real_por_orcamento.c.orcado), 0)).where(
            real_por_orcamento.c.real > 0
        )
    ) or 0
    real_com_orcado = db.scalar(
        select(func.coalesce(func.sum(real_por_orcamento.c.real), 0)).where(
            real_por_orcamento.c.real > 0
        )
    ) or 0

    desvio_medio_percent = (
        (
            (Decimal(str(real_com_orcado)) - Decimal(str(orcado_com_real)))
            / Decimal(str(orcado_com_real))
        )
        * Decimal("100")
        if Decimal(str(orcado_com_real)) > 0
        else Decimal("0")
    )

    estados_rows = db.execute(
        select(Projeto.estado, func.count(Projeto.id_projeto))
        .group_by(Projeto.estado)
        .order_by(func.count(Projeto.id_projeto).desc())
    ).all()

    projetos_por_estado = [
        ProjetosPorEstadoItem(estado=row[0] or "sem_estado", count=row[1])
        for row in estados_rows
    ]

    return DashboardKpisResponse(
        total_projetos=total_projetos,
        total_orcamentos=total_orcamentos,
        total_orcado=_q2(total_orcado),
        total_real=_q2(total_real),
        ticket_medio=_q2(ticket_medio),
        desvio_medio_percent=_q2(desvio_medio_percent),
        projetos_por_estado=projetos_por_estado,
    )


@router.get(
    "/orcamentos_recentes",
    response_model=list[OrcamentoRecenteItem],
)
def dashboard_orcamentos_recentes(
    limit: int = Query(
        default=5,
        gt=0,
        le=50,
        description="Numero de orcamentos recentes a devolver",
    ),
    db: Session = Depends(get_db),
):
    """Devolve os N orcamentos mais recentes com totais real ja calculados.

    Usado pelo grafico "Orcado vs Real" do dashboard sem precisar de carregar
    a lista completa nem fazer batch de realizado client-side.
    """
    mat_sq, op_sq, svc_sq = _real_total_por_orcamento_subquery(db)

    stmt = (
        select(
            Orcamento.id_orcamento,
            Orcamento.id_projeto,
            Projeto.designacao.label("designacao_projeto"),
            Orcamento.versao,
            Orcamento.estado,
            Orcamento.data_criacao,
            Orcamento.custo_total_orcado,
            (
                func.coalesce(mat_sq.c.total, 0)
                + func.coalesce(op_sq.c.total, 0)
                + func.coalesce(svc_sq.c.total, 0)
            ).label("custo_total_real"),
        )
        .outerjoin(Projeto, Projeto.id_projeto == Orcamento.id_projeto)
        .outerjoin(mat_sq, mat_sq.c.id_orcamento == Orcamento.id_orcamento)
        .outerjoin(op_sq, op_sq.c.id_orcamento == Orcamento.id_orcamento)
        .outerjoin(svc_sq, svc_sq.c.id_orcamento == Orcamento.id_orcamento)
        .order_by(Orcamento.id_orcamento.desc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()
    # Ordem cronologica ascendente (mais antigo primeiro) para o grafico ler
    # da esquerda para a direita.
    return [
        OrcamentoRecenteItem(
            id_orcamento=row.id_orcamento,
            id_projeto=row.id_projeto,
            designacao_projeto=row.designacao_projeto,
            versao=row.versao,
            estado=row.estado,
            data_criacao=row.data_criacao,
            custo_total_orcado=_q2(row.custo_total_orcado),
            custo_total_real=_q2(row.custo_total_real),
        )
        for row in reversed(rows)
    ]
