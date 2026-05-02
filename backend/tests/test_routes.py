from app.main import app


def test_frontend_required_routes_are_registered():
    paths = {route.path for route in app.routes}

    assert "/clientes/" in paths
    assert "/utilizadores/" in paths
    assert "/realizado/orcamentos/resumo" in paths
