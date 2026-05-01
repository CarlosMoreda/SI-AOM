from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# =========================
# REALIZADO MATERIAL
# =========================

class RealizadoMaterialCreate(BaseModel):
    id_linha_material: int
    quantidade: Decimal
    peso_kg: Decimal | None = None
    custo_unitario_real: Decimal | None = None
    observacoes: str | None = None


class RealizadoMaterialUpdate(BaseModel):
    quantidade: Decimal | None = None
    peso_kg: Decimal | None = None
    custo_unitario_real: Decimal | None = None
    observacoes: str | None = None


class RealizadoMaterialResponse(BaseModel):
    id_realizado_material: int
    id_linha_material: int
    data_registo: datetime
    quantidade: Decimal
    peso_kg: Decimal | None = None
    custo_unitario_real: Decimal
    custo_total_real: Decimal
    observacoes: str | None = None

    model_config = ConfigDict(from_attributes=True)


# =========================
# REALIZADO OPERAÇÃO
# =========================

class RealizadoOperacaoCreate(BaseModel):
    id_linha_operacao: int
    horas: Decimal
    tempo_setup_h: Decimal = Decimal("0")
    custo_hora_real: Decimal | None = None
    observacoes: str | None = None


class RealizadoOperacaoUpdate(BaseModel):
    horas: Decimal | None = None
    tempo_setup_h: Decimal | None = None
    custo_hora_real: Decimal | None = None
    observacoes: str | None = None


class RealizadoOperacaoResponse(BaseModel):
    id_realizado_operacao: int
    id_linha_operacao: int
    data_registo: datetime
    horas: Decimal
    tempo_setup_h: Decimal
    custo_hora_real: Decimal
    custo_total_real: Decimal
    observacoes: str | None = None

    model_config = ConfigDict(from_attributes=True)


# =========================
# REALIZADO SERVIÇO
# =========================

class RealizadoServicoCreate(BaseModel):
    id_linha_servico: int
    quantidade: Decimal
    preco_unitario_real: Decimal | None = None
    observacoes: str | None = None


class RealizadoServicoUpdate(BaseModel):
    quantidade: Decimal | None = None
    preco_unitario_real: Decimal | None = None
    observacoes: str | None = None


class RealizadoServicoResponse(BaseModel):
    id_realizado_servico: int
    id_linha_servico: int
    data_registo: datetime
    quantidade: Decimal
    preco_unitario_real: Decimal
    custo_total_real: Decimal
    observacoes: str | None = None

    model_config = ConfigDict(from_attributes=True)


# =========================
# RESUMO POR ORÇAMENTO
# =========================

class RealizadoResumoOrcamentoResponse(BaseModel):
    id_orcamento: int
    custo_total_real_materiais: Decimal
    custo_total_real_operacoes: Decimal
    custo_total_real_servicos: Decimal
    custo_total_real: Decimal
    horas_reais_totais: Decimal


class RealizadoResumoBatchRequest(BaseModel):
    ids_orcamento: list[int]
