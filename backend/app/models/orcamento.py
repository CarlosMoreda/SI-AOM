from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Orcamento(Base):
    __tablename__ = "orcamento"
    __table_args__ = (
        UniqueConstraint("id_projeto", "versao", name="uq_orcamento_projeto_versao"),
    )

    id_orcamento: Mapped[int] = mapped_column(primary_key=True)

    id_projeto: Mapped[int] = mapped_column(
        ForeignKey("projeto.id_projeto", onupdate="RESTRICT", ondelete="CASCADE"),
        nullable=False,
    )

    versao: Mapped[str] = mapped_column(String(20), nullable=False)

    criado_por: Mapped[int] = mapped_column(
        ForeignKey("utilizador.id_utilizador", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )

    data_criacao: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="rascunho")
    margem_percentual: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)

    custo_total_materiais: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    custo_total_operacoes: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    custo_total_servicos: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    custo_total_orcado: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    horas_totais_previstas: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    preco_venda: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)

    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)
