"""Testes da feature quantidade_unidades.

Verificam que:
- o schema valida o nº de unidades (>= 1, default 1);
- recalcular_totais_orcamento multiplica os custos do cabecalho pelo nº de
  unidades, mantendo as linhas (e o peso) como valores por estrutura.
"""
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.detalhe_material_orcamento import DetalheMaterialOrcamento
from app.models.material import Material
from app.models.orcamento import Orcamento
from app.models.projeto import Projeto
from app.schemas.orcamento import OrcamentoCreate
from app.services.orcamento_service import recalcular_totais_orcamento


def test_orcamento_schema_rejeita_quantidade_zero():
    with pytest.raises(ValidationError):
        OrcamentoCreate(id_projeto=1, versao="v1", quantidade_unidades=0)


def test_orcamento_schema_default_uma_unidade():
    orc = OrcamentoCreate(id_projeto=1, versao="v1")
    assert orc.quantidade_unidades == 1


def _criar_orcamento_com_linha(
    db, quantidade_unidades: int, custo_linha: Decimal,
) -> Orcamento:
    db.add_all([
        Projeto(
            id_projeto=1,
            referencia="P-1",
            designacao="Guarda-corpos",
            estado="aprovado",
            criado_por=1,
        ),
        Material(
            id_material=1,
            codigo="TUBO",
            nome="Tubo",
            unidade="m",
            custo_unitario_default=Decimal("5"),
        ),
    ])
    db.flush()

    orc = Orcamento(
        id_projeto=1,
        versao="v1",
        criado_por=1,
        estado="em_preparacao",
        quantidade_unidades=quantidade_unidades,
    )
    db.add(orc)
    db.flush()

    # Linha POR UNIDADE: representa o custo de uma estrutura.
    db.add(DetalheMaterialOrcamento(
        id_orcamento=orc.id_orcamento,
        id_material=1,
        quantidade=Decimal("10"),
        preco_unitario_snapshot=Decimal("10"),
        custo_total=custo_linha,
    ))
    db.flush()
    return orc


def test_recalcular_totais_multiplica_por_quantidade(db_session_factory):
    db = db_session_factory()
    try:
        orc = _criar_orcamento_com_linha(db, 3, Decimal("100"))
        recalcular_totais_orcamento(db, orc.id_orcamento)
        # 100 por unidade x 3 unidades = 300
        assert orc.custo_total_materiais == Decimal("300.00")
        assert orc.custo_total_orcado == Decimal("300.00")
    finally:
        db.close()


def test_recalcular_totais_uma_unidade_inalterado(db_session_factory):
    db = db_session_factory()
    try:
        orc = _criar_orcamento_com_linha(db, 1, Decimal("50"))
        recalcular_totais_orcamento(db, orc.id_orcamento)
        # qtd = 1 -> total igual ao da linha (comportamento antigo preservado)
        assert orc.custo_total_materiais == Decimal("50.00")
        assert orc.custo_total_orcado == Decimal("50.00")
    finally:
        db.close()
