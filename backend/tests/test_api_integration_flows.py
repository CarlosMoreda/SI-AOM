from decimal import Decimal

from app.dependencies import ROLE_GESTOR, ROLE_ORCAMENTISTA, ROLE_PRODUCAO

# Cadeia principal do ciclo de vida (relatorio, Figura 4).
_CADEIA_ESTADOS = [
    "em_preparacao",
    "em_revisao",
    "validado",
    "enviado",
    "adjudicado",
    "em_execucao",
    "concluido",
]


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _avancar_orcamento(client, id_orcamento: int, alvo: str) -> None:
    """Avanca o orcamento pela cadeia de transicoes validas ate `alvo`.

    Para 'rejeitado', avanca ate 'enviado' e rejeita.
    """
    atual = client.get(f"/orcamentos/{id_orcamento}").json()["estado"]

    if alvo == "rejeitado":
        _avancar_orcamento(client, id_orcamento, "enviado")
        resposta = client.put(
            f"/orcamentos/{id_orcamento}", json={"estado": "rejeitado"},
        )
        assert resposta.status_code == 200, resposta.json()
        return

    idx_atual = _CADEIA_ESTADOS.index(atual)
    idx_alvo = _CADEIA_ESTADOS.index(alvo)
    for proximo in _CADEIA_ESTADOS[idx_atual + 1: idx_alvo + 1]:
        resposta = client.put(
            f"/orcamentos/{id_orcamento}", json={"estado": proximo},
        )
        assert resposta.status_code == 200, resposta.json()


def _create_budget_with_catalogs(client):
    """Cria cliente, projeto, orcamento (em_preparacao) e catalogos base."""
    cliente = client.post("/clientes/", json={"nome": "Metal Norte"}).json()
    projeto = client.post(
        "/projetos/",
        json={
            "referencia": "P-INT-001",
            "designacao": "Estrutura integração",
            "estado": "em_analise",
            "id_cliente": cliente["id_cliente"],
        },
    ).json()
    orcamento = client.post(
        "/orcamentos/",
        json={
            "id_projeto": projeto["id_projeto"],
            "versao": "v1",
            "estado": "em_preparacao",
            "margem_percentual": 20,
        },
    ).json()
    material = client.post(
        "/materiais/",
        json={
            "codigo": "MAT-INT",
            "nome": "Aço S355",
            "unidade": "kg",
            "custo_unitario_default": 10,
        },
    ).json()
    operacao = client.post(
        "/operacoes/",
        json={
            "codigo": "OP-INT",
            "nome": "Soldadura MIG",
            "categoria": "soldadura",
            "custo_hora_default": 25,
            "setup_hora_default": 0,
        },
    ).json()
    servico = client.post(
        "/servicos/",
        json={
            "codigo": "SVC-INT",
            "nome": "Lacagem",
            "unidade": "un",
            "preco_unitario_default": 7.5,
        },
    ).json()
    return {
        "cliente": cliente,
        "projeto": projeto,
        "orcamento": orcamento,
        "material": material,
        "operacao": operacao,
        "servico": servico,
    }


def test_auth_login_and_me_validate_jwt_flow(real_auth_client):
    login = real_auth_client.post(
        "/auth/login",
        json={"email": "admin@siaom.local", "password": "Admin@123"},
    )

    assert login.status_code == 200
    token = login.json()["access_token"]
    assert login.json()["token_type"] == "bearer"

    me = real_auth_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me.status_code == 200
    assert me.json()["email"] == "admin@siaom.local"
    assert me.json()["perfil"] == "administrador"

    wrong_password = real_auth_client.post(
        "/auth/login",
        json={"email": "admin@siaom.local", "password": "errada"},
    )

    assert wrong_password.status_code == 401


def test_budget_realizado_and_comparison_flow(api_client):
    client, current_user = api_client
    data = _create_budget_with_catalogs(client)
    id_orcamento = data["orcamento"]["id_orcamento"]

    # Linhas adicionadas em em_preparacao (unico periodo editavel).
    material_line = client.post(
        f"/orcamentos/{id_orcamento}/materiais",
        json={
            "id_material": data["material"]["id_material"],
            "quantidade": 2,
            "peso_kg": 5,
            "area_m2": 1.5,
            "desperdicio_percent": 10,
        },
    ).json()
    operation_line = client.post(
        f"/orcamentos/{id_orcamento}/operacoes",
        json={
            "id_operacao": data["operacao"]["id_operacao"],
            "horas": 3,
            "tempo_setup_h": 1,
        },
    ).json()
    service_line = client.post(
        f"/orcamentos/{id_orcamento}/servicos",
        json={
            "id_servico": data["servico"]["id_servico"],
            "quantidade": 4,
        },
    ).json()

    updated_budget = client.get(f"/orcamentos/{id_orcamento}").json()
    assert _money(material_line["custo_total"]) == Decimal("55.00")
    assert _money(operation_line["custo_total"]) == Decimal("100.00")
    assert _money(service_line["custo_total"]) == Decimal("30.00")
    assert _money(updated_budget["custo_total_orcado"]) == Decimal("185.00")
    assert _money(updated_budget["preco_venda"]) == Decimal("222.00")
    assert _money(updated_budget["horas_totais_previstas"]) == Decimal("4.00")
    assert _money(updated_budget["peso_total_kg"]) == Decimal("5.00")

    # Percorre o ciclo de vida ate execucao (transicoes validas).
    _avancar_orcamento(client, id_orcamento, "em_execucao")

    current_user["perfil"] = ROLE_PRODUCAO
    realized_material = client.post(
        "/realizado/material",
        json={
            "id_linha_material": material_line["id_linha_material"],
            "quantidade": 2,
            "custo_unitario_real": 11,
        },
    )
    realized_operation = client.post(
        "/realizado/operacao",
        json={
            "id_linha_operacao": operation_line["id_linha_operacao"],
            "horas": 2,
            "tempo_setup_h": 1,
            "custo_hora_real": 30,
        },
    )
    realized_service = client.post(
        "/realizado/servico",
        json={
            "id_linha_servico": service_line["id_linha_servico"],
            "quantidade": 4,
            "preco_unitario_real": 8,
        },
    )

    assert realized_material.status_code == 201
    assert realized_operation.status_code == 201
    assert realized_service.status_code == 201

    # Transicao automatica: todas as linhas com realizado -> concluido.
    updated_budget = client.get(f"/orcamentos/{id_orcamento}").json()
    updated_project = client.get(
        f"/projetos/{data['projeto']['id_projeto']}"
    ).json()
    assert updated_budget["estado"] == "concluido"
    assert updated_project["estado"] == "concluido"

    # Correcoes pos-conclusao continuam possiveis (em_execucao e concluido).
    delete_after_finished = client.delete(
        f"/realizado/material/{realized_material.json()['id_realizado_material']}"
    )
    assert delete_after_finished.status_code == 204

    reposicao = client.post(
        "/realizado/material",
        json={
            "id_linha_material": material_line["id_linha_material"],
            "quantidade": 2,
            "custo_unitario_real": 11,
        },
    )
    assert reposicao.status_code == 201

    current_user["perfil"] = ROLE_GESTOR
    resumo = client.get(f"/realizado/orcamento/{id_orcamento}/resumo").json()
    comparacao = client.get(f"/comparacao/orcamento/{id_orcamento}").json()

    assert _money(resumo["custo_total_real"]) == Decimal("144.00")
    assert _money(resumo["horas_reais_totais"]) == Decimal("3.00")
    assert _money(comparacao["total"]["orcado"]) == Decimal("185.00")
    assert _money(comparacao["total"]["real"]) == Decimal("144.00")
    assert _money(comparacao["total"]["desvio_abs"]) == Decimal("-41.00")


def test_realizado_rejeita_projeto_fora_de_execucao(api_client):
    client, current_user = api_client
    data = _create_budget_with_catalogs(client)
    id_orcamento = data["orcamento"]["id_orcamento"]

    material_line = client.post(
        f"/orcamentos/{id_orcamento}/materiais",
        json={
            "id_material": data["material"]["id_material"],
            "quantidade": 1,
        },
    ).json()

    # Avanca apenas ate adjudicado (projeto fica 'aprovado' por sincronizacao).
    _avancar_orcamento(client, id_orcamento, "adjudicado")

    current_user["perfil"] = ROLE_PRODUCAO
    resposta = client.post(
        "/realizado/material",
        json={
            "id_linha_material": material_line["id_linha_material"],
            "quantidade": 1,
        },
    )

    assert resposta.status_code == 409
    assert "projetos em execução" in resposta.json()["detail"]


def test_transicoes_de_estado_e_bloqueio_de_linhas(api_client):
    client, _current_user = api_client
    data = _create_budget_with_catalogs(client)
    id_orcamento = data["orcamento"]["id_orcamento"]

    # Saltar estados e invalido (em_preparacao -> concluido).
    salto = client.put(
        f"/orcamentos/{id_orcamento}", json={"estado": "concluido"},
    )
    assert salto.status_code == 422
    assert "Transição inválida" in salto.json()["detail"]

    # Retorno documentado em_revisao -> em_preparacao e valido.
    _avancar_orcamento(client, id_orcamento, "em_revisao")
    retorno = client.put(
        f"/orcamentos/{id_orcamento}", json={"estado": "em_preparacao"},
    )
    assert retorno.status_code == 200

    # A partir de validado, as linhas ficam bloqueadas.
    _avancar_orcamento(client, id_orcamento, "validado")
    linha_bloqueada = client.post(
        f"/orcamentos/{id_orcamento}/materiais",
        json={
            "id_material": data["material"]["id_material"],
            "quantidade": 1,
        },
    )
    assert linha_bloqueada.status_code == 409
    assert "preparação" in linha_bloqueada.json()["detail"]

    # Retroceder validado -> em_preparacao nao esta no ciclo de vida.
    retrocesso = client.put(
        f"/orcamentos/{id_orcamento}", json={"estado": "em_preparacao"},
    )
    assert retrocesso.status_code == 422

    # Criar orcamento ja concluido tambem e invalido.
    criar_concluido = client.post(
        "/orcamentos/",
        json={
            "id_projeto": data["projeto"]["id_projeto"],
            "versao": "v9",
            "estado": "concluido",
        },
    )
    assert criar_concluido.status_code == 422


def test_orcamento_preserva_estado_e_atualiza_projeto(api_client):
    client, _current_user = api_client
    cliente = client.post("/clientes/", json={"nome": "Metal Centro"}).json()
    projeto = client.post(
        "/projetos/",
        json={
            "referencia": "P-FLOW-001",
            "designacao": "Fluxo de orçamento",
            "estado": "em_analise",
            "id_cliente": cliente["id_cliente"],
        },
    )
    orcamento = client.post(
        "/orcamentos/",
        json={
            "id_projeto": projeto.json()["id_projeto"],
            "versao": "v1",
            "estado": "em_preparacao",
        },
    )

    assert orcamento.status_code == 201
    id_orcamento = orcamento.json()["id_orcamento"]

    _avancar_orcamento(client, id_orcamento, "validado")
    assert client.get(f"/orcamentos/{id_orcamento}").json()["estado"] == "validado"
    assert client.get(
        f"/projetos/{projeto.json()['id_projeto']}"
    ).json()["estado"] == "em_analise"

    enviado = client.put(
        f"/orcamentos/{id_orcamento}",
        json={"estado": "enviado"},
    )
    assert enviado.status_code == 200
    assert enviado.json()["estado"] == "enviado"
    assert client.get(
        f"/projetos/{projeto.json()['id_projeto']}"
    ).json()["estado"] == "planeado"

    rejeitado = client.put(
        f"/orcamentos/{id_orcamento}",
        json={"estado": "rejeitado"},
    )
    assert rejeitado.status_code == 200
    assert rejeitado.json()["estado"] == "rejeitado"
    assert client.get(
        f"/projetos/{projeto.json()['id_projeto']}"
    ).json()["estado"] == "cancelado"


def test_atualizar_projeto_sincroniza_orcamento_ativo(api_client):
    client, _current_user = api_client
    data = _create_budget_with_catalogs(client)
    id_projeto = data["projeto"]["id_projeto"]
    id_orcamento = data["orcamento"]["id_orcamento"]

    assert data["orcamento"]["estado"] == "em_preparacao"

    resposta = client.put(
        f"/projetos/{id_projeto}",
        json={
            "estado": "aprovado",
        },
    )

    assert resposta.status_code == 200
    orcamento = client.get(f"/orcamentos/{id_orcamento}").json()
    assert orcamento["estado"] == "adjudicado"


def test_nova_versao_mantem_apenas_orcamento_mais_recente_ativo(api_client):
    client, _current_user = api_client
    data = _create_budget_with_catalogs(client)
    id_projeto = data["projeto"]["id_projeto"]

    _avancar_orcamento(
        client, data["orcamento"]["id_orcamento"], "em_execucao",
    )

    nova_versao = client.post(
        "/orcamentos/",
        json={
            "id_projeto": id_projeto,
            "versao": "v2",
            "estado": "em_preparacao",
        },
    )
    orcamentos = client.get(f"/projetos/{id_projeto}/orcamentos").json()
    estados_por_versao = {orc["versao"]: orc["estado"] for orc in orcamentos}

    assert nova_versao.status_code == 201
    assert nova_versao.json()["estado"] == "em_preparacao"
    assert estados_por_versao == {
        "v1": "rejeitado",
        "v2": "em_preparacao",
    }


def test_role_permissions_for_budget_and_realizado_endpoints(api_client):
    client, current_user = api_client

    current_user["perfil"] = ROLE_PRODUCAO
    assert client.get("/orcamentos/").status_code == 200

    create_budget = client.post(
        "/orcamentos/",
        json={"id_projeto": 1, "versao": "v1", "estado": "em_preparacao"},
    )
    assert create_budget.status_code == 403

    current_user["perfil"] = ROLE_ORCAMENTISTA
    write_realizado = client.post(
        "/realizado/material",
        json={"id_linha_material": 1, "quantidade": 1},
    )
    assert write_realizado.status_code == 403
