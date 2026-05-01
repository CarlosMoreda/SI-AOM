from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.detalhe_material_orcamento import DetalheMaterialOrcamento
from app.models.detalhe_operacao_orcamento import DetalheOperacaoOrcamento
from app.models.detalhe_servico_orcamento import DetalheServicoOrcamento
from app.models.orcamento import Orcamento
from app.models.realizado_material import RealizadoMaterial
from app.models.realizado_operacao import RealizadoOperacao
from app.models.realizado_servico import RealizadoServico
from app.schemas.comparacao import (
    ComparacaoBlocoResponse,
    ComparacaoHorasResponse,
    ComparacaoOrcamentoResponse,
)


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _q2(value: Decimal) -> Decimal:
    return _to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calc_percent(real: Decimal, orcado: Decimal) -> Decimal:
    orcado = _to_decimal(orcado)
    real = _to_decimal(real)

    if orcado == 0:
        if real == 0:
            return Decimal("0.00")
        return Decimal("100.00")

    return _q2(((real - orcado) / orcado) * Decimal("100"))


def _bloco(orcado: Decimal, real: Decimal) -> ComparacaoBlocoResponse:
    orcado = _q2(orcado)
    real = _q2(real)
    desvio_abs = _q2(real - orcado)
    desvio_percent = _calc_percent(real, orcado)

    return ComparacaoBlocoResponse(
        orcado=orcado,
        real=real,
        desvio_abs=desvio_abs,
        desvio_percent=desvio_percent,
    )


def _horas(previstas: Decimal, reais: Decimal) -> ComparacaoHorasResponse:
    previstas = _q2(previstas)
    reais = _q2(reais)
    desvio_abs = _q2(reais - previstas)
    desvio_percent = _calc_percent(reais, previstas)

    return ComparacaoHorasResponse(
        previstas=previstas,
        reais=reais,
        desvio_abs=desvio_abs,
        desvio_percent=desvio_percent,
    )


def obter_comparacao_orcamento(db: Session, id_orcamento: int) -> ComparacaoOrcamentoResponse | None:
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        return None

    real_materiais = db.scalar(
        select(func.coalesce(func.sum(RealizadoMaterial.custo_total_real), 0))
        .join(
            DetalheMaterialOrcamento,
            RealizadoMaterial.id_linha_material == DetalheMaterialOrcamento.id_linha_material,
        )
        .where(DetalheMaterialOrcamento.id_orcamento == id_orcamento)
    )

    real_operacoes = db.scalar(
        select(func.coalesce(func.sum(RealizadoOperacao.custo_total_real), 0))
        .join(
            DetalheOperacaoOrcamento,
            RealizadoOperacao.id_linha_operacao == DetalheOperacaoOrcamento.id_linha_operacao,
        )
        .where(DetalheOperacaoOrcamento.id_orcamento == id_orcamento)
    )

    real_servicos = db.scalar(
        select(func.coalesce(func.sum(RealizadoServico.custo_total_real), 0))
        .join(
            DetalheServicoOrcamento,
            RealizadoServico.id_linha_servico == DetalheServicoOrcamento.id_linha_servico,
        )
        .where(DetalheServicoOrcamento.id_orcamento == id_orcamento)
    )

    horas_reais = db.scalar(
        select(
            func.coalesce(
                func.sum(RealizadoOperacao.horas + RealizadoOperacao.tempo_setup_h),
                0,
            )
        )
        .join(
            DetalheOperacaoOrcamento,
            RealizadoOperacao.id_linha_operacao == DetalheOperacaoOrcamento.id_linha_operacao,
        )
        .where(DetalheOperacaoOrcamento.id_orcamento == id_orcamento)
    )

    real_materiais = _q2(real_materiais)
    real_operacoes = _q2(real_operacoes)
    real_servicos = _q2(real_servicos)
    horas_reais = _q2(horas_reais)

    total_real = _q2(real_materiais + real_operacoes + real_servicos)

    return ComparacaoOrcamentoResponse(
        id_orcamento=id_orcamento,
        materiais=_bloco(orcamento.custo_total_materiais, real_materiais),
        operacoes=_bloco(orcamento.custo_total_operacoes, real_operacoes),
        servicos=_bloco(orcamento.custo_total_servicos, real_servicos),
        total=_bloco(orcamento.custo_total_orcado, total_real),
        horas=_horas(orcamento.horas_totais_previstas, horas_reais),
    )