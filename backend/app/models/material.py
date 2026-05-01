from decimal import Decimal

from sqlalchemy import Boolean, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Material(Base):
    __tablename__ = "material"

    id_material: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    unidade: Mapped[str] = mapped_column(String(20), nullable=False)
    tipo: Mapped[str | None] = mapped_column(String(100), nullable=True)
    qualidade_material: Mapped[str | None] = mapped_column(String(100), nullable=True)
    custo_unitario_default: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)