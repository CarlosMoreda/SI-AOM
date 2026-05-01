from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PrevisaoML(Base):
    __tablename__ = "previsao_ml"

    id_previsao: Mapped[int] = mapped_column(primary_key=True)

    # Nullable: permite registar previsoes exploratorias feitas antes de existir
    # um orcamento na BD (fluxo de "simular custo a partir dos parametros do projeto").
    id_orcamento: Mapped[int | None] = mapped_column(
        ForeignKey("orcamento.id_orcamento", onupdate="RESTRICT", ondelete="CASCADE"),
        nullable=True,
    )

    data_previsao: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    modelo_utilizado: Mapped[str] = mapped_column(String(150), nullable=False)
    modelo_versao: Mapped[str | None] = mapped_column(String(50), nullable=True)

    custo_previsto: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    tempo_previsto: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    desvio_esperado_percent: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)

    inputs_chave: Mapped[str | None] = mapped_column(Text, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
