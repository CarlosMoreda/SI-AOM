from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    ROLE_GESTOR,
    ROLE_ORCAMENTISTA,
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
    RealizadoResumoBatchRequest,
    RealizadoResumoOrcamentoResponse,
    RealizadoServicoCreate,
    RealizadoServicoResponse,
    RealizadoServicoUpdate,
)

router = APIRouter()

WRITE_DEPENDENCIES = [Depends(require_roles(ROLE_PRODUCAO, ROLE_ADMIN))]
SUMMARY_DEPENDENCIES = [
    Depends(require_roles(ROLE_ORCAMENTISTA, ROLE_GESTOR, ROLE_PRODUCAO, ROLE_ADMIN))
]


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _q2(value) -> Decimal:
    return _to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _q4(value) -> Decimal:
    return _to_decimal(value).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _calc_custo_material(quantidade: Decimal, custo_unitario_real: Decimal) -> Decimal:
    return _q2(_to_decimal(quantidade) * _to_decimal(custo_unitario_real))


def _calc_custo_operacao(
    horas: Decimal,
    tempo_setup_h: Decimal,
    custo_hora_real: Decimal,
) -> Decimal:
    return _q2(
        (_to_decimal(horas) + _to_decimal(tempo_setup_h))
        * _to_decimal(custo_hora_real)
    )


def _calc_custo_servico(quantidade: Decimal, preco_unitario_real: Decimal) -> Decimal:
    return _q2(_to_decimal(quantidade) * _to_decimal(preco_unitario_real))


def _build_resumo_response(
    id_orcamento: int,
    total_materiais,
    total_operacoes,
    total_servicos,
    horas_reais_totais,
) -> RealizadoResumoOrcamentoResponse:
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


def _rows_to_decimal_dict(rows) -> dict[int, Decimal]:
    return {id_orcamento: _to_decimal(total) for id_orcamento, total in rows}


def _obter_resumos_realizados(
    db: Session,
    ids_orcamento: list[int],
) -> dict[int, RealizadoResumoOrcamentoResponse]:
    ids_unicos = sorted(set(ids_orcamento))
    if not ids_unicos:
        return {}

    total_materiais = _rows_to_decimal_dict(
        db.execute(
            select(
                DetalheMaterialOrcamento.id_orcamento,
                func.coalesce(func.sum(RealizadoMaterial.custo_total_real), 0),
            )
            .join(
                RealizadoMaterial,
                RealizadoMaterial.id_linha_material
                == DetalheMaterialOrcamento.id_linha_material,
            )
            .where(DetalheMaterialOrcamento.id_orcamento.in_(ids_unicos))
            .group_by(DetalheMaterialOrcamento.id_orcamento)
        ).all()
    )
    total_operacoes = _rows_to_decimal_dict(
        db.execute(
            select(
                DetalheOperacaoOrcamento.id_orcamento,
                func.coalesce(func.sum(RealizadoOperacao.custo_total_real), 0),
            )
            .join(
                RealizadoOperacao,
                RealizadoOperacao.id_linha_operacao
                == DetalheOperacaoOrcamento.id_linha_operacao,
            )
            .where(DetalheOperacaoOrcamento.id_orcamento.in_(ids_unicos))
            .group_by(DetalheOperacaoOrcamento.id_orcamento)
        ).all()
    )
    total_servicos = _rows_to_decimal_dict(
        db.execute(
            select(
                DetalheServicoOrcamento.id_orcamento,
                func.coalesce(func.sum(RealizadoServico.custo_total_real), 0),
            )
            .join(
                RealizadoServico,
                RealizadoServico.id_linha_servico
                == DetalheServicoOrcamento.id_linha_servico,
            )
            .where(DetalheServicoOrcamento.id_orcamento.in_(ids_unicos))
            .group_by(DetalheServicoOrcamento.id_orcamento)
        ).all()
    )
    horas_reais = _rows_to_decimal_dict(
        db.execute(
            select(
                DetalheOperacaoOrcamento.id_orcamento,
                func.coalesce(
                    func.sum(RealizadoOperacao.horas + RealizadoOperacao.tempo_setup_h),
                    0,
                ),
            )
            .join(
                RealizadoOperacao,
                RealizadoOperacao.id_linha_operacao
                == DetalheOperacaoOrcamento.id_linha_operacao,
            )
            .where(DetalheOperacaoOrcamento.id_orcamento.in_(ids_unicos))
            .group_by(DetalheOperacaoOrcamento.id_orcamento)
        ).all()
    )

    return {
        id_orcamento: _build_resumo_response(
            id_orcamento=id_orcamento,
            total_materiais=total_materiais.get(id_orcamento, Decimal("0")),
            total_operacoes=total_operacoes.get(id_orcamento, Decimal("0")),
            total_servicos=total_servicos.get(id_orcamento, Decimal("0")),
            horas_reais_totais=horas_reais.get(id_orcamento, Decimal("0")),
        )
        for id_orcamento in ids_unicos
    }


@router.get(
    "/material/linha/{id_linha_material}",
    response_model=list[RealizadoMaterialResponse],
    dependencies=WRITE_DEPENDENCIES,
)
def listar_realizado_material_por_linha(
    id_linha_material: int,
    db: Session = Depends(get_db),
):
    stmt = (
        select(RealizadoMaterial)
        .where(RealizadoMaterial.id_linha_material == id_linha_material)
        .order_by(RealizadoMaterial.id_realizado_material.asc())
    )
    return db.scalars(stmt).all()


@router.post(
    "/material",
    response_model=RealizadoMaterialResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_DEPENDENCIES,
)
def criar_realizado_material(
    payload: RealizadoMaterialCreate,
    db: Session = Depends(get_db),
):
    linha = db.get(DetalheMaterialOrcamento, payload.id_linha_material)
    if not linha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linha de material nao encontrada",
        )

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
            detail="Nao foi possivel criar o realizado de material",
        )

    return registo


@router.put(
    "/material/{id_realizado_material}",
    response_model=RealizadoMaterialResponse,
    dependencies=WRITE_DEPENDENCIES,
)
def atualizar_realizado_material(
    id_realizado_material: int,
    payload: RealizadoMaterialUpdate,
    db: Session = Depends(get_db),
):
    registo = db.get(RealizadoMaterial, id_realizado_material)
    if not registo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registo realizado de material nao encontrado",
        )

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
            detail="Nao foi possivel atualizar o realizado de material",
        )

    return registo


@router.delete(
    "/material/{id_realizado_material}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=WRITE_DEPENDENCIES,
)
def eliminar_realizado_material(
    id_realizado_material: int,
    db: Session = Depends(get_db),
):
    registo = db.get(RealizadoMaterial, id_realizado_material)
    if not registo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registo realizado de material nao encontrado",
        )

    db.delete(registo)
    db.commit()
    return None


@router.get(
    "/operacao/linha/{id_linha_operacao}",
    response_model=list[RealizadoOperacaoResponse],
    dependencies=WRITE_DEPENDENCIES,
)
def listar_realizado_operacao_por_linha(
    id_linha_operacao: int,
    db: Session = Depends(get_db),
):
    stmt = (
        select(RealizadoOperacao)
        .where(RealizadoOperacao.id_linha_operacao == id_linha_operacao)
        .order_by(RealizadoOperacao.id_realizado_operacao.asc())
    )
    return db.scalars(stmt).all()


@router.post(
    "/operacao",
    response_model=RealizadoOperacaoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_DEPENDENCIES,
)
def criar_realizado_operacao(
    payload: RealizadoOperacaoCreate,
    db: Session = Depends(get_db),
):
    linha = db.get(DetalheOperacaoOrcamento, payload.id_linha_operacao)
    if not linha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linha de operacao nao encontrada",
        )

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
            detail="Nao foi possivel criar o realizado de operacao",
        )

    return registo


@router.put(
    "/operacao/{id_realizado_operacao}",
    response_model=RealizadoOperacaoResponse,
    dependencies=WRITE_DEPENDENCIES,
)
def atualizar_realizado_operacao(
    id_realizado_operacao: int,
    payload: RealizadoOperacaoUpdate,
    db: Session = Depends(get_db),
):
    registo = db.get(RealizadoOperacao, id_realizado_operacao)
    if not registo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registo realizado de operacao nao encontrado",
        )

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
            detail="Nao foi possivel atualizar o realizado de operacao",
        )

    return registo


@router.delete(
    "/operacao/{id_realizado_operacao}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=WRITE_DEPENDENCIES,
)
def eliminar_realizado_operacao(
    id_realizado_operacao: int,
    db: Session = Depends(get_db),
):
    registo = db.get(RealizadoOperacao, id_realizado_operacao)
    if not registo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registo realizado de operacao nao encontrado",
        )

    db.delete(registo)
    db.commit()
    return None


@router.get(
    "/servico/linha/{id_linha_servico}",
    response_model=list[RealizadoServicoResponse],
    dependencies=WRITE_DEPENDENCIES,
)
def listar_realizado_servico_por_linha(
    id_linha_servico: int,
    db: Session = Depends(get_db),
):
    stmt = (
        select(RealizadoServico)
        .where(RealizadoServico.id_linha_servico == id_linha_servico)
        .order_by(RealizadoServico.id_realizado_servico.asc())
    )
    return db.scalars(stmt).all()


@router.post(
    "/servico",
    response_model=RealizadoServicoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_DEPENDENCIES,
)
def criar_realizado_servico(
    payload: RealizadoServicoCreate,
    db: Session = Depends(get_db),
):
    linha = db.get(DetalheServicoOrcamento, payload.id_linha_servico)
    if not linha:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Linha de servico nao encontrada",
        )

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
            detail="Nao foi possivel criar o realizado de servico",
        )

    return registo


@router.put(
    "/servico/{id_realizado_servico}",
    response_model=RealizadoServicoResponse,
    dependencies=WRITE_DEPENDENCIES,
)
def atualizar_realizado_servico(
    id_realizado_servico: int,
    payload: RealizadoServicoUpdate,
    db: Session = Depends(get_db),
):
    registo = db.get(RealizadoServico, id_realizado_servico)
    if not registo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registo realizado de servico nao encontrado",
        )

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
            detail="Nao foi possivel atualizar o realizado de servico",
        )

    return registo


@router.delete(
    "/servico/{id_realizado_servico}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=WRITE_DEPENDENCIES,
)
def eliminar_realizado_servico(
    id_realizado_servico: int,
    db: Session = Depends(get_db),
):
    registo = db.get(RealizadoServico, id_realizado_servico)
    if not registo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registo realizado de servico nao encontrado",
        )

    db.delete(registo)
    db.commit()
    return None


@router.get(
    "/orcamento/{id_orcamento}/resumo",
    response_model=RealizadoResumoOrcamentoResponse,
    dependencies=SUMMARY_DEPENDENCIES,
)
def resumo_realizado_orcamento(
    id_orcamento: int,
    db: Session = Depends(get_db),
):
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orcamento nao encontrado",
        )

    return _obter_resumos_realizados(db, [id_orcamento])[id_orcamento]


@router.post(
    "/orcamentos/resumo",
    response_model=list[RealizadoResumoOrcamentoResponse],
    dependencies=SUMMARY_DEPENDENCIES,
)
def resumo_realizado_orcamentos(
    payload: RealizadoResumoBatchRequest,
    db: Session = Depends(get_db),
):
    ids_unicos = sorted(set(payload.ids_orcamento))
    if not ids_unicos:
        return []

    ids_existentes = set(
        db.scalars(
            select(Orcamento.id_orcamento).where(Orcamento.id_orcamento.in_(ids_unicos))
        ).all()
    )
    resumos = _obter_resumos_realizados(db, list(ids_existentes))

    return [
        resumos[id_orcamento]
        for id_orcamento in ids_unicos
        if id_orcamento in resumos
    ]
