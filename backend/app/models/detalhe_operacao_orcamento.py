from __future__ import annotations

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DetalheOperacaoOrcamento(Base):
    __tablename__ = "detalhe_operacao_orcamento"

    id_linha_operacao: Mapped[int] = mapped_column(primary_key=True)

    id_orcamento: Mapped[int] = mapped_column(
        ForeignKey("orcamento.id_orcamento", onupdate="RESTRICT", ondelete="CASCADE"),
        nullable=False,
    )

    id_operacao: Mapped[int] = mapped_column(
        ForeignKey("operacao.id_operacao", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )

    horas: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tempo_setup_h: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    custo_hora_snapshot: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    custo_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)