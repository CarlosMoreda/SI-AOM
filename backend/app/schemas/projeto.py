from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ProjetoEstado = Literal[
    "em_analise",
    "planeado",
    "aprovado",
    "em_execucao",
    "concluido",
    "cancelado",
]


class ProjetoBase(BaseModel):
    referencia: str = Field(min_length=1, max_length=50)
    designacao: str = Field(min_length=1, max_length=255)
    tipologia: str | None = Field(default=None, max_length=100)
    estado: ProjetoEstado = "em_analise"
    data_inicio: date | None = None
    data_entrega_prevista: date | None = None
    peso_total_kg: Decimal | None = Field(default=None, ge=0)
    numero_pecas: int | None = Field(default=None, ge=0)
    complexidade: str | None = Field(default=None, max_length=50)
    material_principal: str | None = Field(default=None, max_length=100)
    tratamento_superficie: str | None = Field(default=None, max_length=100)
    processo_corte: str | None = Field(default=None, max_length=100)
    lead_time: int | None = Field(default=None, ge=0)
    observacoes: str | None = None
    id_cliente: int | None = Field(default=None, gt=0)


class ProjetoCreate(ProjetoBase):
    pass


class ProjetoUpdate(BaseModel):
    referencia: str | None = Field(default=None, min_length=1, max_length=50)
    designacao: str | None = Field(default=None, min_length=1, max_length=255)
    tipologia: str | None = Field(default=None, max_length=100)
    estado: ProjetoEstado | None = None
    data_inicio: date | None = None
    data_entrega_prevista: date | None = None
    peso_total_kg: Decimal | None = Field(default=None, ge=0)
    numero_pecas: int | None = Field(default=None, ge=0)
    complexidade: str | None = Field(default=None, max_length=50)
    material_principal: str | None = Field(default=None, max_length=100)
    tratamento_superficie: str | None = Field(default=None, max_length=100)
    processo_corte: str | None = Field(default=None, max_length=100)
    lead_time: int | None = Field(default=None, ge=0)
    observacoes: str | None = None
    id_cliente: int | None = Field(default=None, gt=0)


class ProjetoResponse(ProjetoBase):
    id_projeto: int
    criado_por: int
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
