from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class ComparacaoBlocoResponse(BaseModel):
    orcado: Decimal
    real: Decimal
    desvio_abs: Decimal
    desvio_percent: Decimal


class ComparacaoHorasResponse(BaseModel):
    previstas: Decimal
    reais: Decimal
    desvio_abs: Decimal
    desvio_percent: Decimal


class AlertaDesvioResponse(BaseModel):
    """Alerta gerado quando o desvio numa categoria excede o limiar."""
    categoria: Literal["materiais", "operacoes", "servicos", "total", "horas"]
    desvio_abs: Decimal
    desvio_percent: Decimal
    limiar_aplicado: Decimal
    severidade: Literal["media", "alta"]


class ComparacaoOrcamentoResponse(BaseModel):
    id_orcamento: int

    materiais: ComparacaoBlocoResponse
    operacoes: ComparacaoBlocoResponse
    servicos: ComparacaoBlocoResponse

    total: ComparacaoBlocoResponse
    horas: ComparacaoHorasResponse

    limiar_aplicado_percent: Decimal
    alertas: list[AlertaDesvioResponse] = Field(default_factory=list)
