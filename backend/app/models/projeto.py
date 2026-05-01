from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Projeto(Base):
    __tablename__ = "projeto"

    id_projeto: Mapped[int] = mapped_column(primary_key=True)
    referencia: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    designacao: Mapped[str] = mapped_column(String(255), nullable=False)
    tipologia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    estado: Mapped[str] = mapped_column(String(50), nullable=False, default="em_analise")
    data_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    data_entrega_prevista: Mapped[date | None] = mapped_column(Date, nullable=True)
    peso_total_kg: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    numero_pecas: Mapped[int | None] = mapped_column(Integer, nullable=True)
    complexidade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    material_principal: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tratamento_superficie: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processo_corte: Mapped[str | None] = mapped_column(String(100), nullable=True)
    lead_time: Mapped[int | None] = mapped_column(Integer, nullable=True)
    observacoes: Mapped[str | None] = mapped_column(Text, nullable=True)

    id_cliente: Mapped[int | None] = mapped_column(
        ForeignKey("cliente.id_cliente", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=True,
    )

    criado_por: Mapped[int] = mapped_column(
        ForeignKey("utilizador.id_utilizador", onupdate="RESTRICT", ondelete="RESTRICT"),
        nullable=False,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
