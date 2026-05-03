from typing import Final

# Dataset "orcamento":
# 1 linha por orcamento, pensado para o fluxo principal de ML.
# Usa atributos conhecidos no inicio do projeto/orcamento e targets de custo
# real agregado por componente. As colunas orcadas tambem saem no CSV para
# auditoria, mas sao removidas no treino para evitar leakage.
ORCAMENTO_QUERY: Final[str] = """
WITH real_materiais AS (
    SELECT
        dmo.id_orcamento,
        SUM(rm.custo_total_real) AS total,
        COUNT(*) AS registos
    FROM realizado_material rm
    JOIN detalhe_material_orcamento dmo
        ON rm.id_linha_material = dmo.id_linha_material
    GROUP BY dmo.id_orcamento
),
real_operacoes AS (
    SELECT
        doo.id_orcamento,
        SUM(ro.custo_total_real) AS total,
        COUNT(*) AS registos
    FROM realizado_operacao ro
    JOIN detalhe_operacao_orcamento doo
        ON ro.id_linha_operacao = doo.id_linha_operacao
    GROUP BY doo.id_orcamento
),
real_servicos AS (
    SELECT
        dso.id_orcamento,
        SUM(rs.custo_total_real) AS total,
        COUNT(*) AS registos
    FROM realizado_servico rs
    JOIN detalhe_servico_orcamento dso
        ON rs.id_linha_servico = dso.id_linha_servico
    GROUP BY dso.id_orcamento
)
SELECT
    p.tipologia,
    p.complexidade,
    p.peso_total_kg,
    p.numero_pecas,
    p.material_principal,
    p.tratamento_superficie,
    COALESCE(
        p.lead_time,
        CASE
            WHEN p.data_inicio IS NOT NULL
             AND p.data_entrega_prevista IS NOT NULL
            THEN (p.data_entrega_prevista - p.data_inicio)
            ELSE NULL
        END
    ) AS lead_time,
    o.custo_total_materiais,
    o.custo_total_operacoes,
    o.custo_total_servicos,
    COALESCE(rm.total, 0) AS real_materiais,
    COALESCE(ro.total, 0) AS real_operacoes,
    COALESCE(rs.total, 0) AS real_servicos
FROM orcamento o
JOIN projeto p
    ON p.id_projeto = o.id_projeto
LEFT JOIN real_materiais rm
    ON rm.id_orcamento = o.id_orcamento
LEFT JOIN real_operacoes ro
    ON ro.id_orcamento = o.id_orcamento
LEFT JOIN real_servicos rs
    ON rs.id_orcamento = o.id_orcamento
WHERE o.custo_total_orcado > 0
  AND (
      COALESCE(rm.registos, 0)
    + COALESCE(ro.registos, 0)
    + COALESCE(rs.registos, 0)
  ) > 0
ORDER BY o.id_orcamento;
"""
