import json
from decimal import Decimal

from sqlalchemy import select

from app.models.previsao_ml import PrevisaoML


def test_ml_prediction_endpoint_uses_model_params_and_persists_prediction(
    api_client,
    db_session_factory,
    monkeypatch,
):
    client, current_user = api_client
    current_user["perfil"] = "orcamentista"
    captured = {}

    def fake_predict_custo_from_params(parametros, cache=None):
        captured["parametros"] = parametros
        captured["cache"] = cache
        return {
            "custo_materiais": 100.0,
            "custo_operacoes": 50.0,
            "custo_servicos": 25.0,
            "custo_total": 175.0,
            "tempo_previsto": 8.5,
            "modelo_utilizado": "random_forest",
            "modelo_versao": "teste",
            "qualidade_modelo": "boa",
            "r2_medio_holdout": 0.91,
            "aviso_qualidade": None,
            "confianca_percentual": 91,
            "fora_faixa_treino": False,
            "aviso_faixa_treino": None,
            "alertas_faixa_treino": [],
        }

    monkeypatch.setattr(
        "app.routers.ml.predict_custo_from_params",
        fake_predict_custo_from_params,
    )

    response = client.post(
        "/ml/orcamento/prever",
        json={
            "tipologia": "pavilhao",
            "complexidade": "media",
            "peso_total_kg": 1500.0,
            "area_total_m2": 120.0,
            "numero_pecas": 80,
            "material_principal": "S355JR",
            "tratamento_superficie": "galvanizacao",
            "lead_time": 45,
            "id_orcamento": None,
            "observacoes": "simulacao teste",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id_previsao"] is not None
    assert Decimal(str(payload["custo_total"])) == Decimal("175.0")
    assert "id_orcamento" not in captured["parametros"]
    assert "observacoes" not in captured["parametros"]

    with db_session_factory() as db:
        previsao = db.scalar(
            select(PrevisaoML).where(PrevisaoML.id_previsao == payload["id_previsao"])
        )

    assert previsao is not None
    assert previsao.modelo_utilizado == "random_forest"
    assert previsao.custo_previsto == Decimal("175.00")
    inputs_chave = json.loads(previsao.inputs_chave)
    assert inputs_chave["parametros"]["tipologia"] == "pavilhao"
    assert inputs_chave["custo_materiais"] == 100.0
