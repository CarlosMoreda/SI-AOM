from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RealizadoServico(Base):
    __tablename__ = "realizado_servico"

    id_realizado_servico: Mapped[int] = mapped_column(primary_key=True)

    id_linha_servico: Mapped[int] = mapped_column(
        ForeignKey(
            "detalhe_servico_orcamento.id_linha_servico",
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

    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    preco_unitario_real: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    custo_total_real: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)