"""Geracao de PDFs do or\xe7amento via xhtml2pdf + Jinja2.

xhtml2pdf foi escolhido por ser puro Python e funcionar no Windows sem
dependencias de sistema (ao contrario do WeasyPrint que precisa de GTK).
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Iterable

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.orm import Session
from xhtml2pdf import pisa

from app.models.cliente import Cliente
from app.models.detalhe_material_orcamento import DetalheMaterialOrcamento
from app.models.detalhe_operacao_orcamento import DetalheOperacaoOrcamento
from app.models.detalhe_servico_orcamento import DetalheServicoOrcamento
from app.models.material import Material
from app.models.operacao import Operacao
from app.models.orcamento import Orcamento
from app.models.projeto import Projeto
from app.models.servico import Servico

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
)


def _linhas_materiais(db: Session, id_orcamento: int) -> list[dict]:
    """Linhas de material enriquecidas com codigo/nome do catalogo."""
    stmt = (
        select(DetalheMaterialOrcamento, Material)
        .join(Material, Material.id_material == DetalheMaterialOrcamento.id_material)
        .where(DetalheMaterialOrcamento.id_orcamento == id_orcamento)
        .order_by(DetalheMaterialOrcamento.id_linha_material.asc())
    )
    rows = db.execute(stmt).all()
    return [
        {
            "codigo": mat.codigo,
            "nome": mat.nome,
            "quantidade": linha.quantidade,
            "preco_unitario_snapshot": linha.preco_unitario_snapshot,
            "custo_total": linha.custo_total,
        }
        for linha, mat in rows
    ]


def _linhas_operacoes(db: Session, id_orcamento: int) -> list[dict]:
    stmt = (
        select(DetalheOperacaoOrcamento, Operacao)
        .join(Operacao, Operacao.id_operacao == DetalheOperacaoOrcamento.id_operacao)
        .where(DetalheOperacaoOrcamento.id_orcamento == id_orcamento)
        .order_by(DetalheOperacaoOrcamento.id_linha_operacao.asc())
    )
    rows = db.execute(stmt).all()
    return [
        {
            "codigo": op.codigo,
            "nome": op.nome,
            "horas": linha.horas,
            "tempo_setup_h": linha.tempo_setup_h,
            "custo_hora_snapshot": linha.custo_hora_snapshot,
            "custo_total": linha.custo_total,
        }
        for linha, op in rows
    ]


def _linhas_servicos(db: Session, id_orcamento: int) -> list[dict]:
    stmt = (
        select(DetalheServicoOrcamento, Servico)
        .join(Servico, Servico.id_servico == DetalheServicoOrcamento.id_servico)
        .where(DetalheServicoOrcamento.id_orcamento == id_orcamento)
        .order_by(DetalheServicoOrcamento.id_linha_servico.asc())
    )
    rows = db.execute(stmt).all()
    return [
        {
            "codigo": svc.codigo,
            "nome": svc.nome,
            "quantidade": linha.quantidade,
            "preco_unitario_snapshot": linha.preco_unitario_snapshot,
            "custo_total": linha.custo_total,
        }
        for linha, svc in rows
    ]


def gerar_pdf_orcamento(db: Session, id_orcamento: int) -> bytes:
    """Gera o PDF do or\xe7amento e devolve os bytes prontos para download.

    Levanta `ValueError` se o or\xe7amento n\xe3o existir.
    """
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        raise ValueError("Or\xe7amento n\xe3o encontrado")

    projeto = db.get(Projeto, orcamento.id_projeto)
    cliente = (
        db.get(Cliente, projeto.id_cliente)
        if projeto and projeto.id_cliente
        else None
    )

    # versao pode ja vir como "v1" ou apenas "1". Normaliza para "v1" sem
    # duplicar o prefixo (evita "vv1" no cabecalho e no rodape).
    versao_label = (
        orcamento.versao
        if orcamento.versao.startswith("v")
        else f"v{orcamento.versao}"
    )

    materiais = _linhas_materiais(db, id_orcamento)
    operacoes = _linhas_operacoes(db, id_orcamento)
    servicos = _linhas_servicos(db, id_orcamento)

    # As linhas (e respetivos custos) sao POR UNIDADE. Os subtotais por unidade
    # somam diretamente as linhas; os totais do cabecalho ja vem x quantidade.
    qtd = orcamento.quantidade_unidades or 1
    sub_mat_unit = sum((l["custo_total"] for l in materiais), Decimal("0"))
    sub_op_unit = sum((l["custo_total"] for l in operacoes), Decimal("0"))
    sub_svc_unit = sum((l["custo_total"] for l in servicos), Decimal("0"))
    horas_unit = (
        Decimal(str(orcamento.horas_totais_previstas)) / qtd
        if qtd else Decimal(str(orcamento.horas_totais_previstas))
    )
    custo_unitario = (
        Decimal(str(orcamento.custo_total_orcado)) / qtd
        if qtd else Decimal(str(orcamento.custo_total_orcado))
    )

    contexto = {
        "orcamento": orcamento,
        "projeto": projeto,
        "cliente": cliente,
        "materiais": materiais,
        "operacoes": operacoes,
        "servicos": servicos,
        "data_emissao": date.today().strftime("%d/%m/%Y"),
        "versao_label": versao_label,
        "quantidade_unidades": qtd,
        "sub_mat_unit": sub_mat_unit,
        "sub_op_unit": sub_op_unit,
        "sub_svc_unit": sub_svc_unit,
        "horas_unit": horas_unit,
        "custo_unitario": custo_unitario,
    }

    template = _env.get_template("orcamento.html")
    html_str = template.render(**contexto)

    buffer = BytesIO()
    resultado = pisa.CreatePDF(src=html_str, dest=buffer, encoding="utf-8")
    if resultado.err:
        raise RuntimeError(
            f"Falha ao gerar PDF do or\xe7amento {id_orcamento}: "
            f"{resultado.err} erro(s)"
        )
    return buffer.getvalue()
