import pytest
from fastapi import HTTPException

from app.dependencies import ROLE_ADMIN, ROLE_ORCAMENTISTA, require_roles


class DummyUser:
    def __init__(self, perfil: str):
        self.perfil = perfil


def test_require_roles_accepts_aliases():
    dependency = require_roles(ROLE_ADMIN)

    user = dependency(current_user=DummyUser("admin"))

    assert user.perfil == "admin"


def test_require_roles_rejects_unallowed_profile():
    dependency = require_roles(ROLE_ORCAMENTISTA)

    with pytest.raises(HTTPException) as exc:
        dependency(current_user=DummyUser("producao"))

    assert exc.value.status_code == 403
