import re
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.detalhe_material_orcamento import DetalheMaterialOrcamento
from app.models.detalhe_operacao_orcamento import DetalheOperacaoOrcamento
from app.models.detalhe_servico_orcamento import DetalheServicoOrcamento
from app.models.orcamento import Orcamento
from app.models.projeto import Projeto
from app.models.realizado_material import RealizadoMaterial
from app.models.realizado_operacao import RealizadoOperacao
from app.models.realizado_servico import RealizadoServico

# Realizado pode ser registado/corrigido durante a execucao e tambem depois
# da conclusao (correcoes pos-fecho); nos restantes estados esta bloqueado.
ESTADOS_REALIZADO_PERMITIDOS = frozenset({"em_execucao", "concluido"})

# Linhas de detalhe (materiais/operacoes/servicos) so podem ser alteradas
# enquanto o orcamento esta em elaboracao. A partir de "validado" o documento
# fica imutavel (relatorio 3.5): alteracoes implicam criar nova versao.
ESTADOS_LINHAS_EDITAVEIS = frozenset({"em_preparacao", "em_revisao"})

# Transicoes validas do ciclo de vida do orcamento (relatorio, Figura 4).
# Chave = estado atual; valor = conjunto de estados seguintes permitidos.
TRANSICOES_ESTADO_ORCAMENTO: dict[str, frozenset[str]] = {
    "em_preparacao": frozenset({"em_revisao"}),
    "em_revisao": frozenset({"em_preparacao", "validado"}),
    "validado": frozenset({"enviado"}),
    "enviado": frozenset({"adjudicado", "rejeitado"}),
    "adjudicado": frozenset({"em_execucao"}),
    "em_execucao": frozenset({"concluido"}),
    "concluido": frozenset({"arquivado"}),
    "rejeitado": frozenset({"em_preparacao", "arquivado"}),
    "arquivado": frozenset(),
}
ESTADO_ORCAMENTO_ATIVO_POR_PROJETO = {
    "em_analise": "em_preparacao",
    "planeado": "enviado",
    "aprovado": "adjudicado",
    "em_execucao": "em_execucao",
    "concluido": "concluido",
    "cancelado": "arquivado",
}
ESTADO_PROJETO_POR_ORCAMENTO_ATIVO = {
    "em_preparacao": "em_analise",
    "em_revisao": "em_analise",
    "validado": "em_analise",
    "enviado": "planeado",
    "adjudicado": "aprovado",
    "rejeitado": "cancelado",
    "em_execucao": "em_execucao",
    "concluido": "concluido",
    "arquivado": "cancelado",
}
ESTADOS_ORCAMENTO_HISTORICO = frozenset({"rejeitado", "arquivado"})


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _q2(value: Decimal) -> Decimal:
    return _to_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _numero_versao(versao: str | None) -> int:
    match = re.search(r"\d+", str(versao or ""))
    return int(match.group(0)) if match else 0


def estado_projeto_para_estado_orcamento(estado_projeto: str) -> str:
    return ESTADO_ORCAMENTO_ATIVO_POR_PROJETO.get(
        estado_projeto,
        "em_preparacao",
    )


def estado_orcamento_para_estado_projeto(estado_orcamento: str) -> str:
    return ESTADO_PROJETO_POR_ORCAMENTO_ATIVO.get(
        estado_orcamento,
        "em_analise",
    )


def _orcamentos_ordenados_do_projeto(db: Session, id_projeto: int) -> list[Orcamento]:
    orcamentos = list(db.scalars(
        select(Orcamento)
        .where(Orcamento.id_projeto == id_projeto)
    ).all())
    return sorted(
        orcamentos,
        key=lambda orc: (_numero_versao(orc.versao), orc.id_orcamento or 0),
    )


def sincronizar_orcamentos_do_projeto(db: Session, projeto: Projeto) -> None:
    """Mantem o estado dos orcamentos coerente com o estado do projeto.

    Usado quando o utilizador altera diretamente o estado do projeto.
    O orcamento ativo e a versao mais recente; versoes anteriores ficam
    historicas para evitar varios orcamentos ativos no mesmo projeto.
    """
    orcamentos = _orcamentos_ordenados_do_projeto(db, projeto.id_projeto)
    if not orcamentos:
        return

    ativo = orcamentos[-1]

    for antigo in orcamentos[:-1]:
        if antigo.estado not in ESTADOS_ORCAMENTO_HISTORICO:
            antigo.estado = "rejeitado"

    ativo.estado = estado_projeto_para_estado_orcamento(projeto.estado)
    db.flush()


def sincronizar_projeto_por_orcamentos(db: Session, projeto: Projeto) -> None:
    """Mantem o projeto coerente com o estado escolhido no orcamento ativo.

    Usado quando o utilizador cria/edita orcamentos. Aqui o estado do orcamento
    e preservado: validado, enviado, rejeitado, etc. continuam possiveis.
    """
    orcamentos = _orcamentos_ordenados_do_projeto(db, projeto.id_projeto)
    if not orcamentos:
        return

    ativo = orcamentos[-1]

    for antigo in orcamentos[:-1]:
        if antigo.estado not in ESTADOS_ORCAMENTO_HISTORICO:
            antigo.estado = "rejeitado"

    projeto.estado = estado_orcamento_para_estado_projeto(ativo.estado)
    db.flush()


def recalcular_totais_orcamento(db: Session, id_orcamento: int) -> Orcamento:
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        raise ValueError("Orçamento não encontrado")

    total_materiais = db.scalar(
        select(func.coalesce(func.sum(DetalheMaterialOrcamento.custo_total), 0)).where(
            DetalheMaterialOrcamento.id_orcamento == id_orcamento
        )
    )

    total_operacoes = db.scalar(
        select(func.coalesce(func.sum(DetalheOperacaoOrcamento.custo_total), 0)).where(
            DetalheOperacaoOrcamento.id_orcamento == id_orcamento
        )
    )

    total_servicos = db.scalar(
        select(func.coalesce(func.sum(DetalheServicoOrcamento.custo_total), 0)).where(
            DetalheServicoOrcamento.id_orcamento == id_orcamento
        )
    )

    horas_totais = db.scalar(
        select(
            func.coalesce(
                func.sum(
                    DetalheOperacaoOrcamento.horas + DetalheOperacaoOrcamento.tempo_setup_h
                ),
                0,
            )
        ).where(DetalheOperacaoOrcamento.id_orcamento == id_orcamento)
    )

    peso_total = db.scalar(
        select(func.sum(DetalheMaterialOrcamento.peso_kg)).where(
            DetalheMaterialOrcamento.id_orcamento == id_orcamento
        )
    )

    area_total = db.scalar(
        select(func.sum(DetalheMaterialOrcamento.area_m2)).where(
            DetalheMaterialOrcamento.id_orcamento == id_orcamento
        )
    )

    # As linhas representam UMA estrutura. Os custos/horas totais do cabecalho
    # sao a soma por unidade multiplicada pelo nº de estruturas encomendadas.
    # O peso e a area mantem-se POR ESTRUTURA (nao sao multiplicados).
    qtd = orcamento.quantidade_unidades or 1
    qtd_dec = _to_decimal(qtd)

    total_materiais = _q2(_to_decimal(total_materiais) * qtd_dec)
    total_operacoes = _q2(_to_decimal(total_operacoes) * qtd_dec)
    total_servicos = _q2(_to_decimal(total_servicos) * qtd_dec)
    horas_totais = _q2(_to_decimal(horas_totais) * qtd_dec)

    custo_total_orcado = _q2(
        total_materiais + total_operacoes + total_servicos
    )

    orcamento.custo_total_materiais = total_materiais
    orcamento.custo_total_operacoes = total_operacoes
    orcamento.custo_total_servicos = total_servicos
    orcamento.custo_total_orcado = custo_total_orcado
    orcamento.horas_totais_previstas = horas_totais
    orcamento.peso_total_kg = _q2(peso_total) if peso_total is not None else None
    orcamento.area_total_m2 = _q2(area_total) if area_total is not None else None

    # Recalcula preco_venda quando margem_percentual esta definida.
    if orcamento.margem_percentual is not None:
        margem = _to_decimal(orcamento.margem_percentual) / Decimal("100")
        orcamento.preco_venda = _q2(
            custo_total_orcado * (Decimal("1") + margem)
        )

    db.flush()
    return orcamento


def validar_estado_para_realizado(
    db: Session,
    id_orcamento: int,
) -> tuple[bool, str | None]:
    """Valida se o projeto e o orçamento já permitem registar realizado.

    Pelo ciclo de vida definido no relatório, custos reais só fazem sentido
    durante a execução ou depois da conclusão do trabalho.
    """
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        return False, "Orçamento não encontrado"

    projeto = db.get(Projeto, orcamento.id_projeto)
    if not projeto:
        return False, "Projeto não encontrado"

    if projeto.estado not in ESTADOS_REALIZADO_PERMITIDOS:
        return (
            False,
            "Só é possível registar realizado em projetos em execução ou concluídos",
        )

    if orcamento.estado not in ESTADOS_REALIZADO_PERMITIDOS:
        return (
            False,
            "Só é possível registar realizado em orçamentos em execução ou concluídos",
        )

    return True, None


def validar_transicao_estado_orcamento(
    estado_atual: str,
    estado_novo: str,
) -> tuple[bool, str | None]:
    """Valida uma mudanca de estado pedida pelo utilizador.

    Aplica o ciclo de vida do relatorio (Figura 4): nao permite saltar
    estados nem retroceder fora dos retornos documentados (em_revisao ->
    em_preparacao e rejeitado -> em_preparacao).
    """
    if estado_novo == estado_atual:
        return True, None

    permitidos = TRANSICOES_ESTADO_ORCAMENTO.get(estado_atual, frozenset())
    if estado_novo in permitidos:
        return True, None

    if not permitidos:
        return False, (
            f"O estado '{estado_atual}' é terminal: não permite transições."
        )
    return False, (
        f"Transição inválida: '{estado_atual}' -> '{estado_novo}'. "
        f"Estados seguintes permitidos: {', '.join(sorted(permitidos))}."
    )


def validar_linhas_editaveis(
    db: Session,
    id_orcamento: int,
) -> tuple[bool, str | None]:
    """Valida se as linhas de detalhe do orcamento ainda podem ser alteradas.

    A partir de 'validado' o orcamento e imutavel (qualquer alteracao implica
    criar uma nova versao), pelo que linhas so se editam em preparacao/revisao.
    """
    orcamento = db.get(Orcamento, id_orcamento)
    if not orcamento:
        return False, "Orçamento não encontrado"

    if orcamento.estado not in ESTADOS_LINHAS_EDITAVEIS:
        return False, (
            "As linhas só podem ser alteradas com o orçamento em preparação "
            f"ou em revisão (estado atual: {orcamento.estado}). "
            "Para alterar, crie uma nova versão do orçamento."
        )
    return True, None


# ---------------------------------------------------------------------------
# Transicao automatica de estado em_execucao -> concluido
# ---------------------------------------------------------------------------

def _todas_linhas_tem_realizado(db: Session, id_orcamento: int) -> bool:
    """Devolve True se TODAS as linhas do orcamento tiverem pelo menos um
    registo de realizado correspondente.

    - Se nao houver linhas em alguma categoria, essa categoria conta como
      satisfeita (vacuosamente verdadeira).
    - Se nao houver linha alguma em nenhuma categoria, devolve False: nao
      faz sentido concluir um orcamento vazio.
    """
    # Linhas por categoria
    total_mat = db.scalar(
        select(func.count(DetalheMaterialOrcamento.id_linha_material))
        .where(DetalheMaterialOrcamento.id_orcamento == id_orcamento)
    ) or 0
    total_op = db.scalar(
        select(func.count(DetalheOperacaoOrcamento.id_linha_operacao))
        .where(DetalheOperacaoOrcamento.id_orcamento == id_orcamento)
    ) or 0
    total_svc = db.scalar(
        select(func.count(DetalheServicoOrcamento.id_linha_servico))
        .where(DetalheServicoOrcamento.id_orcamento == id_orcamento)
    ) or 0

    if total_mat == 0 and total_op == 0 and total_svc == 0:
        return False  # orcamento sem linhas: nao concluir

    if total_mat > 0:
        com_real_mat = db.scalar(
            select(func.count(distinct(
                DetalheMaterialOrcamento.id_linha_material,
            )))
            .join(
                RealizadoMaterial,
                RealizadoMaterial.id_linha_material
                == DetalheMaterialOrcamento.id_linha_material,
            )
            .where(DetalheMaterialOrcamento.id_orcamento == id_orcamento)
        ) or 0
        if com_real_mat < total_mat:
            return False

    if total_op > 0:
        com_real_op = db.scalar(
            select(func.count(distinct(
                DetalheOperacaoOrcamento.id_linha_operacao,
            )))
            .join(
                RealizadoOperacao,
                RealizadoOperacao.id_linha_operacao
                == DetalheOperacaoOrcamento.id_linha_operacao,
            )
            .where(DetalheOperacaoOrcamento.id_orcamento == id_orcamento)
        ) or 0
        if com_real_op < total_op:
            return False

    if total_svc > 0:
        com_real_svc = db.scalar(
            select(func.count(distinct(
                DetalheServicoOrcamento.id_linha_servico,
            )))
            .join(
                RealizadoServico,
                RealizadoServico.id_linha_servico
                == DetalheServicoOrcamento.id_linha_servico,
            )
            .where(DetalheServicoOrcamento.id_orcamento == id_orcamento)
        ) or 0
        if com_real_svc < total_svc:
            return False

    return True


def tentar_transicionar_para_concluido(
    db: Session, id_orcamento: int,
) -> bool:
    """Se o orcamento estiver em 'em_execucao' e TODAS as linhas tiverem
    pelo menos um realizado registado, transita o estado para 'concluido'.

    Devolve True se houve transicao, False caso contrario. NAO faz commit:
    o caller e responsavel pela transacao.
    """
    orc = db.get(Orcamento, id_orcamento)
    if not orc or orc.estado != "em_execucao":
        return False
    if not _todas_linhas_tem_realizado(db, id_orcamento):
        return False
    orc.estado = "concluido"
    projeto = db.get(Projeto, orc.id_projeto)
    if projeto and projeto.estado == "em_execucao":
        projeto.estado = "concluido"
    db.flush()
    return True
