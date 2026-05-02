from app.routers.auth import hash_password, verificar_password


def test_bcrypt_password_is_accepted():
    password_hash = hash_password("Admin@123")

    assert verificar_password("Admin@123", password_hash)
    assert not verificar_password("wrong-password", password_hash)


def test_plaintext_password_is_not_accepted_by_default_verifier():
    assert not verificar_password("Admin@123", "Admin@123")
