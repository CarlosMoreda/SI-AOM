from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.dependencies import ROLE_ADMIN, get_current_user, get_db
from app.main import app
from app.models.cliente import Cliente  # noqa: F401
from app.models.detalhe_material_orcamento import DetalheMaterialOrcamento  # noqa: F401
from app.models.detalhe_operacao_orcamento import DetalheOperacaoOrcamento  # noqa: F401
from app.models.detalhe_servico_orcamento import DetalheServicoOrcamento  # noqa: F401
from app.models.material import Material  # noqa: F401
from app.models.operacao import Operacao  # noqa: F401
from app.models.orcamento import Orcamento  # noqa: F401
from app.models.previsao_ml import PrevisaoML  # noqa: F401
from app.models.projeto import Projeto  # noqa: F401
from app.models.realizado_material import RealizadoMaterial  # noqa: F401
from app.models.realizado_operacao import RealizadoOperacao  # noqa: F401
from app.models.realizado_servico import RealizadoServico  # noqa: F401
from app.models.servico import Servico  # noqa: F401
from app.models.utilizador import Utilizador
from app.routers.auth import hash_password


@asynccontextmanager
async def _noop_lifespan(_app):
    yield


@pytest.fixture()
def db_session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )

    with TestingSessionLocal() as db:
        db.add_all(
            [
                Utilizador(
                    id_utilizador=1,
                    nome="Admin Teste",
                    email="admin@siaom.local",
                    password_hash=hash_password("Admin@123"),
                    perfil="administrador",
                    ativo=True,
                ),
                Utilizador(
                    id_utilizador=2,
                    nome="Produção Teste",
                    email="producao@siaom.local",
                    password_hash=hash_password("Prod@123"),
                    perfil="producao",
                    ativo=True,
                ),
            ]
        )
        db.commit()

    try:
        yield TestingSessionLocal
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def api_client(db_session_factory):
    current_user = {
        "id_utilizador": 1,
        "perfil": ROLE_ADMIN,
    }

    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    def override_current_user():
        return SimpleNamespace(
            id_utilizador=current_user["id_utilizador"],
            perfil=current_user["perfil"],
            ativo=True,
        )

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    client = TestClient(app)

    try:
        yield client, current_user
    finally:
        client.close()
        app.dependency_overrides.clear()
        app.router.lifespan_context = original_lifespan


@pytest.fixture()
def real_auth_client(db_session_factory):
    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    original_lifespan = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    try:
        yield client
    finally:
        client.close()
        app.dependency_overrides.clear()
        app.router.lifespan_context = original_lifespan
