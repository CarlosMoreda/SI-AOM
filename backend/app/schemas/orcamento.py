from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class OrcamentoBase(BaseModel):
    id_projeto: int
    versao: str
    estado: str = "rascunho"
    margem_percentual: Decimal | None = None
    observacoes: str | None = None


class OrcamentoCreate(OrcamentoBase):
    pass


# Apenas campos editáveis manualmente. Totais e preco_venda são calculados
# automaticamente por recalcular_totais_orcamento.
class OrcamentoUpdate(BaseModel):
    versao: str | None = None
    estado: str | None = None
    margem_percentual: Decimal | None = None
    # preco_venda pode ser definido manualmente quando margem_percentual é None
    preco_venda: Decimal | None = None
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
