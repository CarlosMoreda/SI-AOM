from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    ROLE_ORCAMENTISTA,
    get_db,
    require_roles,
)
from app.models.detalhe_material_orcamento import DetalheMaterialOrcamento
from app.models.detalhe_operacao_orcamento import DetalheOperacaoOrcamento
from app.models.detalhe_servico_orcamento import DetalheServicoOrcamento
from app.models.material import Material
from app.models.operacao import Operacao
from app.models.orcamento import Orcamento
from app.models.servico import Servico
from app.schemas.detalhe_material_orcamento import (
    DetalheMaterialOrcamentoCreate,
    DetalheMaterialOrcamentoResponse,
    DetalheMaterialOrcamentoUpdate,
)
from app.schemas.detalhe_operacao_orcamento import (
    DetalheOperacaoOrcamentoCreate,
    DetalheOperacaoOrcamentoResponse,
    DetalheOperacaoOrcamentoUpdate,
)
from app.schemas.detalhe_servico_orcamento import (
    DetalheServicoOrcamentoCreate,
    DetalheServicoOrcamentoResponse,
    DetalheServicoOrcamentoUpdate,
)
from app.services.orcamento_service import recalcular_totais_orcamento

router = APIRouter(
    dependencies=[Depends(require_roles(ROLE_ORCAMENTISTA, ROLE_ADMIN))]
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


def _obter_orcamento_404(db: Session, id_orcamento: int) -> Orcamento:
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Orçamento não encontrado")
    return orcamento


def _calc_custo_material(quantidade: Decimal, preco: Decimal, desperdicio_percent: Decimal) -> Decimal:
    fator = Decimal("1") + (_to_decimal(desperdicio_percent) / Decimal("100"))
    return _q2(_to_decimal(quantidade) * _to_decimal(preco) * fator)


def _calc_custo_operacao(horas: Decimal, tempo_setup_h: Decimal, custo_hora: Decimal) -> Decimal:
    return _q2((_to_decimal(horas) + _to_decimal(tempo_setup_h)) * _to_decimal(custo_hora))


def _calc_custo_servico(quantidade: Decimal, preco: Decimal) -> Decimal:
    return _q2(_to_decimal(quantidade) * _to_decimal(preco))


# =========================
# MATERIAIS DO ORÇAMENTO
# =========================

@router.get(
    "/{id_orcamento}/materiais",
    response_model=list[DetalheMaterialOrcamentoResponse],
)
def listar_materiais_orcamento(id_orcamento: int, db: Session = Depends(get_db)):
    _obter_orcamento_404(db, id_orcamento)

    stmt = (
        select(DetalheMaterialOrcamento)
        .where(DetalheMaterialOrcamento.id_orcamento == id_orcamento)
        .order_by(DetalheMaterialOrcamento.id_linha_material.asc())
    )
    return db.scalars(stmt).all()


@router.post(
    "/{id_orcamento}/materiais",
    response_model=DetalheMaterialOrcamentoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_material_orcamento(
    id_orcamento: int,
    payload: DetalheMaterialOrcamentoCreate,
    db: Session = Depends(get_db),
):
    _obter_orcamento_404(db, id_orcamento)

    material = db.get(Material, payload.id_material)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material não encontrado")

    preco_snapshot = payload.preco_unitario_snapshot
    if preco_snapshot is None:
        preco_snapshot = material.custo_unitario_default

    linha = DetalheMaterialOrcamento(
        id_orcamento=id_orcamento,
        id_material=payload.id_material,
        quantidade=payload.quantidade,
        peso_kg=payload.peso_kg,
        desperdicio_percent=payload.desperdicio_percent,
        preco_unitario_snapshot=_q4(preco_snapshot),
        custo_total=_calc_custo_material(
            payload.quantidade,
            preco_snapshot,
            payload.desperdicio_percent,
        ),
        observacoes=payload.observacoes,
    )

    db.add(linha)
    try:
        db.flush()
        recalcular_totais_orcamento(db, id_orcamento)
        db.commit()
        db.refresh(linha)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível criar a linha de material",
        )

    return linha


@router.put(
    "/materiais/{id_linha_material}",
    response_model=DetalheMaterialOrcamentoResponse,
)
def atualizar_material_orcamento(
    id_linha_material: int,
    payload: DetalheMaterialOrcamentoUpdate,
    db: Session = Depends(get_db),
):
    linha = db.get(DetalheMaterialOrcamento, id_linha_material)
    if not linha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linha de material não encontrada")

    dados = payload.model_dump(exclude_unset=True)

    material = None
    if "id_material" in dados:
        material = db.get(Material, dados["id_material"])
        if not material:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material não encontrado")
        linha.id_material = dados["id_material"]

    if "quantidade" in dados:
        linha.quantidade = dados["quantidade"]
    if "peso_kg" in dados:
        linha.peso_kg = dados["peso_kg"]
    if "desperdicio_percent" in dados:
        linha.desperdicio_percent = dados["desperdicio_percent"]
    if "observacoes" in dados:
        linha.observacoes = dados["observacoes"]

    if "preco_unitario_snapshot" in dados and dados["preco_unitario_snapshot"] is not None:
        linha.preco_unitario_snapshot = _q4(dados["preco_unitario_snapshot"])
    elif material is not None:
        linha.preco_unitario_snapshot = _q4(material.custo_unitario_default)

    linha.custo_total = _calc_custo_material(
        linha.quantidade,
        linha.preco_unitario_snapshot,
        linha.desperdicio_percent,
    )

    try:
        recalcular_totais_orcamento(db, linha.id_orcamento)
        db.commit()
        db.refresh(linha)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar a linha de material",
        )

    return linha


@router.delete("/materiais/{id_linha_material}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_material_orcamento(id_linha_material: int, db: Session = Depends(get_db)):
    linha = db.get(DetalheMaterialOrcamento, id_linha_material)
    if not linha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linha de material não encontrada")

    id_orcamento = linha.id_orcamento

    db.delete(linha)
    try:
        db.flush()
        recalcular_totais_orcamento(db, id_orcamento)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao e possivel eliminar: linha com registos realizados",
        )
    return None


# =========================
# OPERAÇÕES DO ORÇAMENTO
# =========================

@router.get(
    "/{id_orcamento}/operacoes",
    response_model=list[DetalheOperacaoOrcamentoResponse],
)
def listar_operacoes_orcamento(id_orcamento: int, db: Session = Depends(get_db)):
    _obter_orcamento_404(db, id_orcamento)

    stmt = (
        select(DetalheOperacaoOrcamento)
        .where(DetalheOperacaoOrcamento.id_orcamento == id_orcamento)
        .order_by(DetalheOperacaoOrcamento.id_linha_operacao.asc())
    )
    return db.scalars(stmt).all()


@router.post(
    "/{id_orcamento}/operacoes",
    response_model=DetalheOperacaoOrcamentoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_operacao_orcamento(
    id_orcamento: int,
    payload: DetalheOperacaoOrcamentoCreate,
    db: Session = Depends(get_db),
):
    _obter_orcamento_404(db, id_orcamento)

    operacao = db.get(Operacao, payload.id_operacao)
    if not operacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operação não encontrada")

    custo_hora_snapshot = payload.custo_hora_snapshot
    if custo_hora_snapshot is None:
        custo_hora_snapshot = operacao.custo_hora_default

    linha = DetalheOperacaoOrcamento(
        id_orcamento=id_orcamento,
        id_operacao=payload.id_operacao,
        horas=payload.horas,
        tempo_setup_h=payload.tempo_setup_h,
        custo_hora_snapshot=_q2(custo_hora_snapshot),
        custo_total=_calc_custo_operacao(
            payload.horas,
            payload.tempo_setup_h,
            custo_hora_snapshot,
        ),
        observacoes=payload.observacoes,
    )

    db.add(linha)
    try:
        db.flush()
        recalcular_totais_orcamento(db, id_orcamento)
        db.commit()
        db.refresh(linha)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível criar a linha de operação",
        )

    return linha


@router.put(
    "/operacoes/{id_linha_operacao}",
    response_model=DetalheOperacaoOrcamentoResponse,
)
def atualizar_operacao_orcamento(
    id_linha_operacao: int,
    payload: DetalheOperacaoOrcamentoUpdate,
    db: Session = Depends(get_db),
):
    linha = db.get(DetalheOperacaoOrcamento, id_linha_operacao)
    if not linha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linha de operação não encontrada")

    dados = payload.model_dump(exclude_unset=True)

    operacao = None
    if "id_operacao" in dados:
        operacao = db.get(Operacao, dados["id_operacao"])
        if not operacao:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operação não encontrada")
        linha.id_operacao = dados["id_operacao"]

    if "horas" in dados:
        linha.horas = dados["horas"]
    if "tempo_setup_h" in dados:
        linha.tempo_setup_h = dados["tempo_setup_h"]
    if "observacoes" in dados:
        linha.observacoes = dados["observacoes"]

    if "custo_hora_snapshot" in dados and dados["custo_hora_snapshot"] is not None:
        linha.custo_hora_snapshot = _q2(dados["custo_hora_snapshot"])
    elif operacao is not None:
        linha.custo_hora_snapshot = _q2(operacao.custo_hora_default)

    linha.custo_total = _calc_custo_operacao(
        linha.horas,
        linha.tempo_setup_h,
        linha.custo_hora_snapshot,
    )

    try:
        recalcular_totais_orcamento(db, linha.id_orcamento)
        db.commit()
        db.refresh(linha)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar a linha de operação",
        )

    return linha


@router.delete("/operacoes/{id_linha_operacao}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_operacao_orcamento(id_linha_operacao: int, db: Session = Depends(get_db)):
    linha = db.get(DetalheOperacaoOrcamento, id_linha_operacao)
    if not linha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linha de operação não encontrada")

    id_orcamento = linha.id_orcamento

    db.delete(linha)
    try:
        db.flush()
        recalcular_totais_orcamento(db, id_orcamento)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao e possivel eliminar: linha com registos realizados",
        )
    return None


# =========================
# SERVIÇOS DO ORÇAMENTO
# =========================

@router.get(
    "/{id_orcamento}/servicos",
    response_model=list[DetalheServicoOrcamentoResponse],
)
def listar_servicos_orcamento(id_orcamento: int, db: Session = Depends(get_db)):
    _obter_orcamento_404(db, id_orcamento)

    stmt = (
        select(DetalheServicoOrcamento)
        .where(DetalheServicoOrcamento.id_orcamento == id_orcamento)
        .order_by(DetalheServicoOrcamento.id_linha_servico.asc())
    )
    return db.scalars(stmt).all()


@router.post(
    "/{id_orcamento}/servicos",
    response_model=DetalheServicoOrcamentoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_servico_orcamento(
    id_orcamento: int,
    payload: DetalheServicoOrcamentoCreate,
    db: Session = Depends(get_db),
):
    _obter_orcamento_404(db, id_orcamento)

    servico = db.get(Servico, payload.id_servico)
    if not servico:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serviço não encontrado")

    preco_snapshot = payload.preco_unitario_snapshot
    if preco_snapshot is None:
        preco_snapshot = servico.preco_unitario_default

    linha = DetalheServicoOrcamento(
        id_orcamento=id_orcamento,
        id_servico=payload.id_servico,
        quantidade=payload.quantidade,
        preco_unitario_snapshot=_q2(preco_snapshot),
        custo_total=_calc_custo_servico(payload.quantidade, preco_snapshot),
        observacoes=payload.observacoes,
    )

    db.add(linha)
    try:
        db.flush()
        recalcular_totais_orcamento(db, id_orcamento)
        db.commit()
        db.refresh(linha)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível criar a linha de serviço",
        )

    return linha


@router.put(
    "/servicos/{id_linha_servico}",
    response_model=DetalheServicoOrcamentoResponse,
)
def atualizar_servico_orcamento(
    id_linha_servico: int,
    payload: DetalheServicoOrcamentoUpdate,
    db: Session = Depends(get_db),
):
    linha = db.get(DetalheServicoOrcamento, id_linha_servico)
    if not linha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linha de serviço não encontrada")

    dados = payload.model_dump(exclude_unset=True)

    servico = None
    if "id_servico" in dados:
        servico = db.get(Servico, dados["id_servico"])
        if not servico:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Serviço não encontrado")
        linha.id_servico = dados["id_servico"]

    if "quantidade" in dados:
        linha.quantidade = dados["quantidade"]
    if "observacoes" in dados:
        linha.observacoes = dados["observacoes"]

    if "preco_unitario_snapshot" in dados and dados["preco_unitario_snapshot"] is not None:
        linha.preco_unitario_snapshot = _q2(dados["preco_unitario_snapshot"])
    elif servico is not None:
        linha.preco_unitario_snapshot = _q2(servico.preco_unitario_default)

    linha.custo_total = _calc_custo_servico(
        linha.quantidade,
        linha.preco_unitario_snapshot,
    )

    try:
        recalcular_totais_orcamento(db, linha.id_orcamento)
        db.commit()
        db.refresh(linha)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar a linha de serviço",
        )

    return linha


@router.delete("/servicos/{id_linha_servico}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_servico_orcamento(id_linha_servico: int, db: Session = Depends(get_db)):
    linha = db.get(DetalheServicoOrcamento, id_linha_servico)
    if not linha:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linha de serviço não encontrada")

    id_orcamento = linha.id_orcamento

    db.delete(linha)
    try:
        db.flush()
        recalcular_totais_orcamento(db, id_orcamento)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao e possivel eliminar: linha com registos realizados",
        )
    return None
