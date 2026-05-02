from app.main import app


def _methods_for(path: str) -> set[str]:
    methods: set[str] = set()
    for route in app.routes:
        if route.path == path and getattr(route, "methods", None):
            methods.update(route.methods)
    return methods


def test_frontend_required_routes_are_registered():
    paths = {route.path for route in app.routes}

    assert "/clientes/" in paths
    assert "/utilizadores/" in paths
    assert "/realizado/orcamentos/resumo" in paths


def test_frontend_required_routes_have_expected_methods():
    assert {"GET", "POST"}.issubset(_methods_for("/clientes/"))
    assert {"GET", "POST"}.issubset(_methods_for("/utilizadores/"))
    assert "POST" in _methods_for("/realizado/orcamentos/resumo")
