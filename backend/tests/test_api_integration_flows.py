from decimal import Decimal

from app.dependencies import ROLE_GESTOR, ROLE_ORCAMENTISTA, ROLE_PRODUCAO


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _create_budget_with_catalogs(client):
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
    assert _money(material_line["custo_total"]) == Decimal("22.00")
    assert _money(operation_line["custo_total"]) == Decimal("100.00")
    assert _money(service_line["custo_total"]) == Decimal("30.00")
    assert _money(updated_budget["custo_total_orcado"]) == Decimal("152.00")
    assert _money(updated_budget["preco_venda"]) == Decimal("182.40")
    assert _money(updated_budget["horas_totais_previstas"]) == Decimal("4.00")
    assert _money(updated_budget["peso_total_kg"]) == Decimal("5.00")

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

    current_user["perfil"] = ROLE_GESTOR
    resumo = client.get(f"/realizado/orcamento/{id_orcamento}/resumo").json()
    comparacao = client.get(f"/comparacao/orcamento/{id_orcamento}").json()

    assert _money(resumo["custo_total_real"]) == Decimal("144.00")
    assert _money(resumo["horas_reais_totais"]) == Decimal("3.00")
    assert _money(comparacao["total"]["orcado"]) == Decimal("152.00")
    assert _money(comparacao["total"]["real"]) == Decimal("144.00")
    assert _money(comparacao["total"]["desvio_abs"]) == Decimal("-8.00")


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
