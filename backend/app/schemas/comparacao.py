from decimal import Decimal

from pydantic import BaseModel


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


class ComparacaoOrcamentoResponse(BaseModel):
    id_orcamento: int

    materiais: ComparacaoBlocoResponse
    operacoes: ComparacaoBlocoResponse
    servicos: ComparacaoBlocoResponse

    total: ComparacaoBlocoResponse
    horas: ComparacaoHorasResponse