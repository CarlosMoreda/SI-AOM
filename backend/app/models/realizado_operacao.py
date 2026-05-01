from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RealizadoOperacao(Base):
    __tablename__ = "realizado_operacao"

    id_realizado_operacao: Mapped[int] = mapped_column(primary_key=True)

    id_linha_operacao: Mapped[int] = mapped_column(
        ForeignKey(
            "detalhe_operacao_orcamento.id_linha_operacao",
            onupdate="RESTRICT",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    data_registo: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    horas: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tempo_setup_h: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    custo_hora_real: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    custo_total_real: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)