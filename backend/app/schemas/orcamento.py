from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

OrcamentoEstado = Literal["rascunho", "em_revisao", "aprovado", "rejeitado", "cancelado"]


class OrcamentoBase(BaseModel):
    id_projeto: int = Field(gt=0)
    versao: str = Field(min_length=1, max_length=20)
    estado: OrcamentoEstado = "rascunho"
    margem_percentual: Decimal | None = Field(default=None, ge=0, le=100)
    observacoes: str | None = None


class OrcamentoCreate(OrcamentoBase):
    pass


class OrcamentoUpdate(BaseModel):
    versao: str | None = Field(default=None, min_length=1, max_length=20)
    estado: OrcamentoEstado | None = None
    margem_percentual: Decimal | None = Field(default=None, ge=0, le=100)
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
