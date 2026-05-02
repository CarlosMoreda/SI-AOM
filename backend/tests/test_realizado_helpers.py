from decimal import Decimal

from app.routers.realizado import (
    _build_resumo_response,
    _calc_custo_material,
    _calc_custo_operacao,
    _calc_custo_servico,
    _rows_to_decimal_dict,
)


def test_realizado_cost_helpers_quantize_values():
    assert _calc_custo_material(Decimal("2"), Decimal("10.1234")) == Decimal("20.25")
    assert _calc_custo_operacao(
        Decimal("1.5"),
        Decimal("0.5"),
        Decimal("30"),
    ) == Decimal("60.00")
    assert _calc_custo_servico(Decimal("3"), Decimal("7.335")) == Decimal("22.01")


def test_build_resumo_response_sums_components():
    resumo = _build_resumo_response(
        id_orcamento=10,
        total_materiais=Decimal("100.126"),
        total_operacoes=Decimal("20.224"),
        total_servicos=Decimal("3"),
        horas_reais_totais=Decimal("2.345"),
    )

    assert resumo.id_orcamento == 10
    assert resumo.custo_total_real_materiais == Decimal("100.13")
    assert resumo.custo_total_real_operacoes == Decimal("20.22")
    assert resumo.custo_total_real_servicos == Decimal("3.00")
    assert resumo.custo_total_real == Decimal("123.35")
    assert resumo.horas_reais_totais == Decimal("2.35")


def test_rows_to_decimal_dict_handles_none_as_zero():
    rows = [(1, Decimal("10.50")), (2, None)]

    assert _rows_to_decimal_dict(rows) == {
        1: Decimal("10.50"),
        2: Decimal("0"),
    }
