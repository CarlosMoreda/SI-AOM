from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Operacao(Base):
    __tablename__ = "operacao"

    id_operacao: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(100), nullable=True)
    custo_hora_default: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    setup_hora_default: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)