from __future__ import annotations

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DetalheServicoOrcamento(Base):
    __tablename__ = "detalhe_servico_orcamento"

    id_linha_servico: Mapped[int] = mapped_column(primary_key=True)

    id_orcamento: Mapped[int] = mapped_column(
        ForeignKey("orcamento.id_orcamento", onupdate="RESTRICT", ondelete="CASCADE"),
        nullable=False,
    )

    id_servico: Mapped[int] = mapped_column(
        ForeignKey("servico.id_servico", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )

    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    preco_unitario_snapshot: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    custo_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)