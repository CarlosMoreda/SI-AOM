from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ProjetoBase(BaseModel):
    referencia: str
    designacao: str
    tipologia: str | None = None
    estado: str = "em_analise"
    data_inicio: date | None = None
    data_entrega_prevista: date | None = None
    peso_total_kg: Decimal | None = None
    numero_pecas: int | None = None
    complexidade: str | None = None
    material_principal: str | None = None
    tratamento_superficie: str | None = None
    processo_corte: str | None = None
    lead_time: int | None = None
    observacoes: str | None = None
    id_cliente: int | None = None


class ProjetoCreate(ProjetoBase):
    pass


class ProjetoUpdate(BaseModel):
    referencia: str | None = None
    designacao: str | None = None
    tipologia: str | None = None
    estado: str | None = None
    data_inicio: date | None = None
    data_entrega_prevista: date | None = None
    peso_total_kg: Decimal | None = None
    numero_pecas: int | None = None
    complexidade: str | None = None
    material_principal: str | None = None
    tratamento_superficie: str | None = None
    processo_corte: str | None = None
    lead_time: int | None = None
    observacoes: str | None = None
    id_cliente: int | None = None


class ProjetoResponse(ProjetoBase):
    id_projeto: int
    criado_por: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
