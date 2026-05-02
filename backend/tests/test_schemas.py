from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.detalhe_material_orcamento import DetalheMaterialOrcamentoCreate
from app.schemas.orcamento import OrcamentoCreate
from app.schemas.projeto import ProjetoCreate
from app.schemas.realizado import RealizadoResumoBatchRequest
from app.schemas.utilizador import UtilizadorCreate


def test_material_detail_rejects_negative_quantity():
    with pytest.raises(ValidationError):
        DetalheMaterialOrcamentoCreate(
            id_material=1,
            quantidade=Decimal("-1"),
        )


def test_orcamento_rejects_unknown_state():
    with pytest.raises(ValidationError):
        OrcamentoCreate(
            id_projeto=1,
            versao="v1",
            estado="em_execucao",
        )


def test_project_accepts_frontend_states():
    projeto = ProjetoCreate(
        referencia="P-001",
        designacao="Estrutura",
        estado="aprovado",
    )

    assert projeto.estado == "aprovado"


def test_user_rejects_unknown_profile():
    with pytest.raises(ValidationError):
        UtilizadorCreate(
            nome="Teste",
            email="teste@example.com",
            perfil="financeiro",
            password="Admin@123",
        )


def test_batch_summary_rejects_non_positive_ids():
    with pytest.raises(ValidationError):
        RealizadoResumoBatchRequest(ids_orcamento=[1, 0, 2])
