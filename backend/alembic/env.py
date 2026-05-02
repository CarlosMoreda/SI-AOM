from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.database import Base

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
from app.models.utilizador import Utilizador  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = settings.database_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
