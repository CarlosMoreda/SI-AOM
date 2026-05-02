from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.detalhe_material_orcamento import DetalheMaterialOrcamento
from app.models.detalhe_operacao_orcamento import DetalheOperacaoOrcamento
from app.models.detalhe_servico_orcamento import DetalheServicoOrcamento
from app.models.orcamento import Orcamento


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

    # Recalcula preco_venda quando margem_percentual esta definida.
    if orcamento.margem_percentual is not None:
        margem = _to_decimal(orcamento.margem_percentual) / Decimal("100")
        orcamento.preco_venda = _q2(
            custo_total_orcado * (Decimal("1") + margem)
        )

    db.flush()
    return orcamento
