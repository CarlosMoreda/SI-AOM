from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    ROLE_PRODUCAO,
    get_db,
    require_roles,
)
from app.models.detalhe_material_orcamento import DetalheMaterialOrcamento
from app.models.detalhe_operacao_orcamento import DetalheOperacaoOrcamento
from app.models.detalhe_servico_orcamento import DetalheServicoOrcamento
from app.models.orcamento import Orcamento
from app.models.realizado_material import RealizadoMaterial
from app.models.realizado_operacao import RealizadoOperacao
from app.models.realizado_servico import RealizadoServico
from app.schemas.realizado import (
    RealizadoMaterialCreate,
    RealizadoMaterialResponse,
    RealizadoMaterialUpdate,
    RealizadoOperacaoCreate,
    RealizadoOperacaoResponse,
    RealizadoOperacaoUpdate,
    RealizadoResumoOrcamentoResponse,
    RealizadoServicoCreate,
    RealizadoServicoResponse,
    RealizadoServicoUpdate,
)

router = APIRouter(
    dependencies=[Depends(require_roles(ROLE_PRODUCAO, ROLE_ADMIN))]
)


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _q2(value: Decimal) -> Decimal:
    return _to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _q4(value: Decimal) -> Decimal:
    return _to_decimal(value).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _calc_custo_material(quantidade: Decimal, custo_unitario_real: Decimal) -> Decimal:
    return _q2(_to_decimal(quantidade) * _to_decimal(custo_unitario_real))


def _calc_custo_operacao(horas: Decimal, tempo_setup_h: Decimal, custo_hora_real: Decimal) -> Decimal:
    return _q2((_to_decimal(horas) + _to_decimal(tempo_setup_h)) * _to_decimal(custo_hora_real))


def _calc_custo_servico(quantidade: Decimal, preco_unitario_real: Decimal) -> Decimal:
    return _q2(_to_decimal(quantidade) * _to_decimal(preco_unitario_real))


# =========================
# REALIZADO MATERIAL
# =========================

@router.get("/material/linha/{id_linha_material}", response_model=list[RealizadoMaterialResponse])
def listar_realizado_material_por_linha(id_linha_material: int, db: Session = Depends(get_db)):
    stmt = (
        select(RealizadoMaterial)
        .where(RealizadoMaterial.id_linha_material == id_linha_material)
        .order_by(RealizadoMaterial.id_realizado_material.asc())
    )
    return db.scalars(stmt).all()


@router.post("/material", response_model=RealizadoMaterialResponse, status_code=status.HTTP_201_CREATED)
def criar_realizado_material(payload: RealizadoMaterialCreate, db: Session = Depends(get_db)):
    linha = db.get(DetalheMaterialOrcamento, payload.id_linha_material)
    if not linha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linha de material não encontrada")

    custo_unitario_real = payload.custo_unitario_real
    if custo_unitario_real is None:
        custo_unitario_real = linha.preco_unitario_snapshot

    registo = RealizadoMaterial(
        id_linha_material=payload.id_linha_material,
        quantidade=payload.quantidade,
        peso_kg=payload.peso_kg,
        custo_unitario_real=_q4(custo_unitario_real),
        custo_total_real=_calc_custo_material(payload.quantidade, custo_unitario_real),
        observacoes=payload.observacoes,
    )

    db.add(registo)
    try:
        db.commit()
        db.refresh(registo)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível criar o registo realizado de material",
        )

    return registo


@router.put("/material/{id_realizado_material}", response_model=RealizadoMaterialResponse)
def atualizar_realizado_material(
    id_realizado_material: int,
    payload: RealizadoMaterialUpdate,
    db: Session = Depends(get_db),
):
    registo = db.get(RealizadoMaterial, id_realizado_material)
    if not registo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registo realizado de material não encontrado")

    dados = payload.model_dump(exclude_unset=True)

    if "quantidade" in dados:
        registo.quantidade = dados["quantidade"]
    if "peso_kg" in dados:
        registo.peso_kg = dados["peso_kg"]
    if "observacoes" in dados:
        registo.observacoes = dados["observacoes"]
    if "custo_unitario_real" in dados and dados["custo_unitario_real"] is not None:
        registo.custo_unitario_real = _q4(dados["custo_unitario_real"])

    registo.custo_total_real = _calc_custo_material(
        registo.quantidade,
        registo.custo_unitario_real,
    )

    try:
        db.commit()
        db.refresh(registo)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar o realizado de material",
        )

    return registo


@router.delete("/material/{id_realizado_material}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_realizado_material(id_realizado_material: int, db: Session = Depends(get_db)):
    registo = db.get(RealizadoMaterial, id_realizado_material)
    if not registo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registo realizado de material não encontrado")

    db.delete(registo)
    db.commit()
    return None


# =========================
# REALIZADO OPERAÇÃO
# =========================

@router.get("/operacao/linha/{id_linha_operacao}", response_model=list[RealizadoOperacaoResponse])
def listar_realizado_operacao_por_linha(id_linha_operacao: int, db: Session = Depends(get_db)):
    stmt = (
        select(RealizadoOperacao)
        .where(RealizadoOperacao.id_linha_operacao == id_linha_operacao)
        .order_by(RealizadoOperacao.id_realizado_operacao.asc())
    )
    return db.scalars(stmt).all()


@router.post("/operacao", response_model=RealizadoOperacaoResponse, status_code=status.HTTP_201_CREATED)
def criar_realizado_operacao(payload: RealizadoOperacaoCreate, db: Session = Depends(get_db)):
    linha = db.get(DetalheOperacaoOrcamento, payload.id_linha_operacao)
    if not linha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linha de operação não encontrada")

    custo_hora_real = payload.custo_hora_real
    if custo_hora_real is None:
        custo_hora_real = linha.custo_hora_snapshot

    registo = RealizadoOperacao(
        id_linha_operacao=payload.id_linha_operacao,
        horas=payload.horas,
        tempo_setup_h=payload.tempo_setup_h,
        custo_hora_real=_q2(custo_hora_real),
        custo_total_real=_calc_custo_operacao(
            payload.horas,
            payload.tempo_setup_h,
            custo_hora_real,
        ),
        observacoes=payload.observacoes,
    )

    db.add(registo)
    try:
        db.commit()
        db.refresh(registo)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível criar o registo realizado de operação",
        )

    return registo


@router.put("/operacao/{id_realizado_operacao}", response_model=RealizadoOperacaoResponse)
def atualizar_realizado_operacao(
    id_realizado_operacao: int,
    payload: RealizadoOperacaoUpdate,
    db: Session = Depends(get_db),
):
    registo = db.get(RealizadoOperacao, id_realizado_operacao)
    if not registo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registo realizado de operação não encontrado")

    dados = payload.model_dump(exclude_unset=True)

    if "horas" in dados:
        registo.horas = dados["horas"]
    if "tempo_setup_h" in dados:
        registo.tempo_setup_h = dados["tempo_setup_h"]
    if "observacoes" in dados:
        registo.observacoes = dados["observacoes"]
    if "custo_hora_real" in dados and dados["custo_hora_real"] is not None:
        registo.custo_hora_real = _q2(dados["custo_hora_real"])

    registo.custo_total_real = _calc_custo_operacao(
        registo.horas,
        registo.tempo_setup_h,
        registo.custo_hora_real,
    )

    try:
        db.commit()
        db.refresh(registo)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar o realizado de operação",
        )

    return registo


@router.delete("/operacao/{id_realizado_operacao}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_realizado_operacao(id_realizado_operacao: int, db: Session = Depends(get_db)):
    registo = db.get(RealizadoOperacao, id_realizado_operacao)
    if not registo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registo realizado de operação não encontrado")

    db.delete(registo)
    db.commit()
    return None


# =========================
# REALIZADO SERVIÇO
# =========================

@router.get("/servico/linha/{id_linha_servico}", response_model=list[RealizadoServicoResponse])
def listar_realizado_servico_por_linha(id_linha_servico: int, db: Session = Depends(get_db)):
    stmt = (
        select(RealizadoServico)
        .where(RealizadoServico.id_linha_servico == id_linha_servico)
        .order_by(RealizadoServico.id_realizado_servico.asc())
    )
    return db.scalars(stmt).all()


@router.post("/servico", response_model=RealizadoServicoResponse, status_code=status.HTTP_201_CREATED)
def criar_realizado_servico(payload: RealizadoServicoCreate, db: Session = Depends(get_db)):
    linha = db.get(DetalheServicoOrcamento, payload.id_linha_servico)
    if not linha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linha de serviço não encontrada")

    preco_unitario_real = payload.preco_unitario_real
    if preco_unitario_real is None:
        preco_unitario_real = linha.preco_unitario_snapshot

    registo = RealizadoServico(
        id_linha_servico=payload.id_linha_servico,
        quantidade=payload.quantidade,
        preco_unitario_real=_q2(preco_unitario_real),
        custo_total_real=_calc_custo_servico(
            payload.quantidade,
            preco_unitario_real,
        ),
        observacoes=payload.observacoes,
    )

    db.add(registo)
    try:
        db.commit()
        db.refresh(registo)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível criar o registo realizado de serviço",
        )

    return registo


@router.put("/servico/{id_realizado_servico}", response_model=RealizadoServicoResponse)
def atualizar_realizado_servico(
    id_realizado_servico: int,
    payload: RealizadoServicoUpdate,
    db: Session = Depends(get_db),
):
    registo = db.get(RealizadoServico, id_realizado_servico)
    if not registo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registo realizado de serviço não encontrado")

    dados = payload.model_dump(exclude_unset=True)

    if "quantidade" in dados:
        registo.quantidade = dados["quantidade"]
    if "observacoes" in dados:
        registo.observacoes = dados["observacoes"]
    if "preco_unitario_real" in dados and dados["preco_unitario_real"] is not None:
        registo.preco_unitario_real = _q2(dados["preco_unitario_real"])

    registo.custo_total_real = _calc_custo_servico(
        registo.quantidade,
        registo.preco_unitario_real,
    )

    try:
        db.commit()
        db.refresh(registo)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar o realizado de serviço",
        )

    return registo


@router.delete("/servico/{id_realizado_servico}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_realizado_servico(id_realizado_servico: int, db: Session = Depends(get_db)):
    registo = db.get(RealizadoServico, id_realizado_servico)
    if not registo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registo realizado de serviço não encontrado")

    db.delete(registo)
    db.commit()
    return None


# =========================
# RESUMO REALIZADO POR ORÇAMENTO
# =========================

@router.get("/orcamento/{id_orcamento}/resumo", response_model=RealizadoResumoOrcamentoResponse)
def resumo_realizado_orcamento(id_orcamento: int, db: Session = Depends(get_db)):
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")

    total_materiais = db.scalar(
        select(func.coalesce(func.sum(RealizadoMaterial.custo_total_real), 0))
        .join(
            DetalheMaterialOrcamento,
            RealizadoMaterial.id_linha_material == DetalheMaterialOrcamento.id_linha_material,
        )
        .where(DetalheMaterialOrcamento.id_orcamento == id_orcamento)
    )

    total_operacoes = db.scalar(
        select(func.coalesce(func.sum(RealizadoOperacao.custo_total_real), 0))
        .join(
            DetalheOperacaoOrcamento,
            RealizadoOperacao.id_linha_operacao == DetalheOperacaoOrcamento.id_linha_operacao,
        )
        .where(DetalheOperacaoOrcamento.id_orcamento == id_orcamento)
    )

    total_servicos = db.scalar(
        select(func.coalesce(func.sum(RealizadoServico.custo_total_real), 0))
        .join(
            DetalheServicoOrcamento,
            RealizadoServico.id_linha_servico == DetalheServicoOrcamento.id_linha_servico,
        )
        .where(DetalheServicoOrcamento.id_orcamento == id_orcamento)
    )

    horas_reais_totais = db.scalar(
        select(
            func.coalesce(
                func.sum(RealizadoOperacao.horas + RealizadoOperacao.tempo_setup_h),
                0,
            )
        )
        .join(
            DetalheOperacaoOrcamento,
            RealizadoOperacao.id_linha_operacao == DetalheOperacaoOrcamento.id_linha_operacao,
        )
        .where(DetalheOperacaoOrcamento.id_orcamento == id_orcamento)
    )

    total_materiais = _q2(total_materiais)
    total_operacoes = _q2(total_operacoes)
    total_servicos = _q2(total_servicos)
    horas_reais_totais = _q2(horas_reais_totais)
    custo_total_real = _q2(total_materiais + total_operacoes + total_servicos)

    return RealizadoResumoOrcamentoResponse(
        id_orcamento=id_orcamento,
        custo_total_real_materiais=total_materiais,
        custo_total_real_operacoes=total_operacoes,
        custo_total_real_servicos=total_servicos,
        custo_total_real=custo_total_real,
        horas_reais_totais=horas_reais_totais,
    )
