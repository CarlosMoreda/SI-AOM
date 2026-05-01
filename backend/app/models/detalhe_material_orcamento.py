from __future__ import annotations

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DetalheMaterialOrcamento(Base):
    __tablename__ = "detalhe_material_orcamento"

    id_linha_material: Mapped[int] = mapped_column(primary_key=True)

    id_orcamento: Mapped[int] = mapped_column(
        ForeignKey("orcamento.id_orcamento", onupdate="RESTRICT", ondelete="CASCADE"),
        nullable=False,
    )

    id_material: Mapped[int] = mapped_column(
        ForeignKey("material.id_material", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )

    quantidade: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    peso_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    desperdicio_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    preco_unitario_snapshot: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    custo_total: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)