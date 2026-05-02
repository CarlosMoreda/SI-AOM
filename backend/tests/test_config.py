import pytest
from pydantic import ValidationError

from app.config import DEFAULT_JWT_SECRET, Settings


def test_production_requires_custom_jwt_secret():
    with pytest.raises(ValidationError):
        Settings(
            database_url="postgresql+psycopg://user:pass@localhost:5432/db",
            debug=False,
            jwt_secret=DEFAULT_JWT_SECRET,
            allow_plaintext_password_fallback=False,
        )
