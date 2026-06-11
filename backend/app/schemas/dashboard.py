from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProjetosPorEstadoItem(BaseModel):
    estado: str
    count: int


class DashboardKpisResponse(BaseModel):
    """KPIs globais calculados directamente em SQL.

    Todas as agregacoes correm server-side (COUNT/SUM/AVG) — payload e
    minimo (poucos bytes) e independente do volume de dados na BD.
    """
    total_projetos: int
    total_orcamentos: int
    total_orcado: Decimal
    total_real: Decimal
    ticket_medio: Decimal
    desvio_medio_percent: Decimal
    projetos_por_estado: list[ProjetosPorEstadoItem] = Field(default_factory=list)


class OrcamentoRecenteItem(BaseModel):
    id_orcamento: int
    id_projeto: int
    designacao_projeto: str | None = None
    versao: str
    estado: str
    data_criacao: datetime
    custo_total_orcado: Decimal
    custo_total_real: Decimal

    model_config = ConfigDict(from_attributes=True)
