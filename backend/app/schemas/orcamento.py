from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Estados do orcamento conforme o ciclo de vida definido no relatorio (3.5).
# em_preparacao -> em_revisao -> validado -> enviado -> {adjudicado | rejeitado}
# adjudicado -> em_execucao -> concluido -> arquivado (terminal)
# rejeitado -> arquivado (terminal) ou regressa a em_preparacao com nova versao.
OrcamentoEstado = Literal[
    "em_preparacao",
    "em_revisao",
    "validado",
    "enviado",
    "adjudicado",
    "rejeitado",
    "em_execucao",
    "concluido",
    "arquivado",
]


class OrcamentoBase(BaseModel):
    id_projeto: int = Field(gt=0)
    versao: str = Field(min_length=1, max_length=20)
    estado: OrcamentoEstado = "em_preparacao"
    margem_percentual: Decimal | None = Field(default=None, ge=0, le=100)
    peso_total_kg: Decimal | None = Field(default=None, ge=0)
    area_total_m2: Decimal | None = Field(default=None, ge=0)
    observacoes: str | None = None


class OrcamentoCreate(OrcamentoBase):
    pass


class OrcamentoUpdate(BaseModel):
    versao: str | None = Field(default=None, min_length=1, max_length=20)
    estado: OrcamentoEstado | None = None
    margem_percentual: Decimal | None = Field(default=None, ge=0, le=100)
    peso_total_kg: Decimal | None = Field(default=None, ge=0)
    area_total_m2: Decimal | None = Field(default=None, ge=0)
    preco_venda: Decimal | None = Field(default=None, ge=0)
    observacoes: str | None = None


class OrcamentoResponse(OrcamentoBase):
    id_orcamento: int
    criado_por: int
    data_criacao: datetime
    custo_total_materiais: Decimal
    custo_total_operacoes: Decimal
    custo_total_servicos: Decimal
    custo_total_orcado: Decimal
    horas_totais_previstas: Decimal
    preco_venda: Decimal

    model_config = ConfigDict(from_attributes=True)
