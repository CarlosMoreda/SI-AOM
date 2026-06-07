from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.detalhe_material_orcamento import DetalheMaterialOrcamento
from app.models.detalhe_operacao_orcamento import DetalheOperacaoOrcamento
from app.models.detalhe_servico_orcamento import DetalheServicoOrcamento
from app.models.orcamento import Orcamento
from app.models.realizado_material import RealizadoMaterial
from app.models.realizado_operacao import RealizadoOperacao
from app.models.realizado_servico import RealizadoServico


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _q2(value: Decimal) -> Decimal:
    return _to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def recalcular_totais_orcamento(db: Session, id_orcamento: int) -> Orcamento:
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        raise ValueError("Orçamento não encontrado")

    total_materiais = db.scalar(
        select(func.coalesce(func.sum(DetalheMaterialOrcamento.custo_total), 0)).where(
            DetalheMaterialOrcamento.id_orcamento == id_orcamento
        )
    )

    total_operacoes = db.scalar(
        select(func.coalesce(func.sum(DetalheOperacaoOrcamento.custo_total), 0)).where(
            DetalheOperacaoOrcamento.id_orcamento == id_orcamento
        )
    )

    total_servicos = db.scalar(
        select(func.coalesce(func.sum(DetalheServicoOrcamento.custo_total), 0)).where(
            DetalheServicoOrcamento.id_orcamento == id_orcamento
        )
    )

    horas_totais = db.scalar(
        select(
            func.coalesce(
                func.sum(
                    DetalheOperacaoOrcamento.horas + DetalheOperacaoOrcamento.tempo_setup_h
                ),
                0,
            )
        ).where(DetalheOperacaoOrcamento.id_orcamento == id_orcamento)
    )

    peso_total = db.scalar(
        select(func.sum(DetalheMaterialOrcamento.peso_kg)).where(
            DetalheMaterialOrcamento.id_orcamento == id_orcamento
        )
    )

    area_total = db.scalar(
        select(func.sum(DetalheMaterialOrcamento.area_m2)).where(
            DetalheMaterialOrcamento.id_orcamento == id_orcamento
        )
    )

    total_materiais = _q2(total_materiais)
    total_operacoes = _q2(total_operacoes)
    total_servicos = _q2(total_servicos)
    horas_totais = _q2(horas_totais)

    custo_total_orcado = _q2(
        total_materiais + total_operacoes + total_servicos
    )

    orcamento.custo_total_materiais = total_materiais
    orcamento.custo_total_operacoes = total_operacoes
    orcamento.custo_total_servicos = total_servicos
    orcamento.custo_total_orcado = custo_total_orcado
    orcamento.horas_totais_previstas = horas_totais
    orcamento.peso_total_kg = _q2(peso_total) if peso_total is not None else None
    orcamento.area_total_m2 = _q2(area_total) if area_total is not None else None

    # Recalcula preco_venda quando margem_percentual esta definida.
    if orcamento.margem_percentual is not None:
        margem = _to_decimal(orcamento.margem_percentual) / Decimal("100")
        orcamento.preco_venda = _q2(
            custo_total_orcado * (Decimal("1") + margem)
        )

    db.flush()
    return orcamento


# ---------------------------------------------------------------------------
# Transicao automatica de estado em_execucao -> concluido
# ---------------------------------------------------------------------------

def _todas_linhas_tem_realizado(db: Session, id_orcamento: int) -> bool:
    """Devolve True se TODAS as linhas do orcamento tiverem pelo menos um
    registo de realizado correspondente.

    - Se nao houver linhas em alguma categoria, essa categoria conta como
      satisfeita (vacuosamente verdadeira).
    - Se nao houver linha alguma em nenhuma categoria, devolve False: nao
      faz sentido concluir um orcamento vazio.
    """
    # Linhas por categoria
    total_mat = db.scalar(
        select(func.count(DetalheMaterialOrcamento.id_linha_material))
        .where(DetalheMaterialOrcamento.id_orcamento == id_orcamento)
    ) or 0
    total_op = db.scalar(
        select(func.count(DetalheOperacaoOrcamento.id_linha_operacao))
        .where(DetalheOperacaoOrcamento.id_orcamento == id_orcamento)
    ) or 0
    total_svc = db.scalar(
        select(func.count(DetalheServicoOrcamento.id_linha_servico))
        .where(DetalheServicoOrcamento.id_orcamento == id_orcamento)
    ) or 0

    if total_mat == 0 and total_op == 0 and total_svc == 0:
        return False  # orcamento sem linhas: nao concluir

    if total_mat > 0:
        com_real_mat = db.scalar(
            select(func.count(distinct(
                DetalheMaterialOrcamento.id_linha_material,
            )))
            .join(
                RealizadoMaterial,
                RealizadoMaterial.id_linha_material
                == DetalheMaterialOrcamento.id_linha_material,
            )
            .where(DetalheMaterialOrcamento.id_orcamento == id_orcamento)
        ) or 0
        if com_real_mat < total_mat:
            return False

    if total_op > 0:
        com_real_op = db.scalar(
            select(func.count(distinct(
                DetalheOperacaoOrcamento.id_linha_operacao,
            )))
            .join(
                RealizadoOperacao,
                RealizadoOperacao.id_linha_operacao
                == DetalheOperacaoOrcamento.id_linha_operacao,
            )
            .where(DetalheOperacaoOrcamento.id_orcamento == id_orcamento)
        ) or 0
        if com_real_op < total_op:
            return False

    if total_svc > 0:
        com_real_svc = db.scalar(
            select(func.count(distinct(
                DetalheServicoOrcamento.id_linha_servico,
            )))
            .join(
                RealizadoServico,
                RealizadoServico.id_linha_servico
                == DetalheServicoOrcamento.id_linha_servico,
            )
            .where(DetalheServicoOrcamento.id_orcamento == id_orcamento)
        ) or 0
        if com_real_svc < total_svc:
            return False

    return True


def tentar_transicionar_para_concluido(
    db: Session, id_orcamento: int,
) -> bool:
    """Se o orcamento estiver em 'em_execucao' e TODAS as linhas tiverem
    pelo menos um realizado registado, transita o estado para 'concluido'.

    Devolve True se houve transicao, False caso contrario. NAO faz commit:
    o caller e responsavel pela transacao.
    """
    orc = db.get(Orcamento, id_orcamento)
    if not orc or orc.estado != "em_execucao":
        return False
    if not _todas_linhas_tem_realizado(db, id_orcamento):
        return False
    orc.estado = "concluido"
    db.flush()
    return True
