from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Servico(Base):
    __tablename__ = "servico"

    id_servico: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade: Mapped[str] = mapped_column(String(20), nullable=False)
    preco_unitario_default: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)