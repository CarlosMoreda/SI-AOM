from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.detalhe_material_orcamento import DetalheMaterialOrcamento
from app.models.detalhe_operacao_orcamento import DetalheOperacaoOrcamento
from app.models.detalhe_servico_orcamento import DetalheServicoOrcamento
from app.models.orcamento import Orcamento
from app.models.realizado_material import RealizadoMaterial
from app.models.realizado_operacao import RealizadoOperacao
from app.models.realizado_servico import RealizadoServico
from app.schemas.comparacao import (
    AlertaDesvioResponse,
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


def _construir_alertas(
    blocos: Iterable[tuple[str, Decimal, Decimal, Decimal]],
    limiar_percent: Decimal,
) -> list[AlertaDesvioResponse]:
    """Gera um alerta por categoria cujo desvio (em modulo) excede o limiar.

    blocos: iteravel de (categoria, real, desvio_abs, desvio_percent).
    Quando `real == 0` a categoria e ignorada porque significa que ainda nao
    foi registado realizado para essa categoria (evita falso positivo de
    -100% quando a execucao ainda nao comecou).

    Severidade fica 'alta' quando o desvio passa o dobro do limiar.
    """
    alertas: list[AlertaDesvioResponse] = []
    limiar_alta = limiar_percent * Decimal("2")

    for categoria, real, desvio_abs, desvio_percent in blocos:
        # Sem realizado registado nesta categoria -> nao gera alerta.
        if real == 0:
            continue
        if abs(desvio_percent) < limiar_percent:
            continue
        severidade = "alta" if abs(desvio_percent) >= limiar_alta else "media"
        alertas.append(
            AlertaDesvioResponse(
                categoria=categoria,
                desvio_abs=desvio_abs,
                desvio_percent=desvio_percent,
                limiar_aplicado=limiar_percent,
                severidade=severidade,
            )
        )
    return alertas


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

    materiais = _bloco(orcamento.custo_total_materiais, real_materiais)
    operacoes = _bloco(orcamento.custo_total_operacoes, real_operacoes)
    servicos = _bloco(orcamento.custo_total_servicos, real_servicos)
    total = _bloco(orcamento.custo_total_orcado, total_real)
    horas = _horas(orcamento.horas_totais_previstas, horas_reais)

    limiar = _q2(_to_decimal(settings.limiar_desvio_default_percent))
    alertas = _construir_alertas(
        [
            ("materiais", materiais.real, materiais.desvio_abs, materiais.desvio_percent),
            ("operacoes", operacoes.real, operacoes.desvio_abs, operacoes.desvio_percent),
            ("servicos", servicos.real, servicos.desvio_abs, servicos.desvio_percent),
            ("total", total.real, total.desvio_abs, total.desvio_percent),
            ("horas", horas.reais, horas.desvio_abs, horas.desvio_percent),
        ],
        limiar_percent=limiar,
    )

    return ComparacaoOrcamentoResponse(
        id_orcamento=id_orcamento,
        materiais=materiais,
        operacoes=operacoes,
        servicos=servicos,
        total=total,
        horas=horas,
        limiar_aplicado_percent=limiar,
        alertas=alertas,
    )