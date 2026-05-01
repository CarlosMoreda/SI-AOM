from typing import Final

# Dataset "orcamento":
# 1 linha por orcamento, pensado para o fluxo principal de ML.
# Usa apenas atributos conhecidos no inicio do projeto/orcamento e targets de
# custo orcado por componente. Nao inclui realizado, preco_venda, margem, estado
# ou detalhes ja calculados, para evitar leakage e manter a previsao utilizavel
# antes de existir um orcamento detalhado.
ORCAMENTO_QUERY: Final[str] = """
SELECT
    p.tipologia,
    p.complexidade,
    p.peso_total_kg,
    p.numero_pecas,
    p.material_principal,
    p.tratamento_superficie,
    p.processo_corte,
    COALESCE(
        p.lead_time,
        CASE
            WHEN p.data_inicio IS NOT NULL
             AND p.data_entrega_prevista IS NOT NULL
            THEN (p.data_entrega_prevista - p.data_inicio)
            ELSE NULL
        END
    ) AS lead_time,
    CASE
        WHEN p.numero_pecas IS NULL OR p.numero_pecas = 0
         OR p.peso_total_kg IS NULL
        THEN NULL
        ELSE p.peso_total_kg / p.numero_pecas
    END AS peso_por_peca_kg,
    CASE
        WHEN p.peso_total_kg IS NULL OR p.peso_total_kg = 0
         OR COALESCE(
                p.lead_time,
                CASE
                    WHEN p.data_inicio IS NOT NULL
                     AND p.data_entrega_prevista IS NOT NULL
                    THEN (p.data_entrega_prevista - p.data_inicio)
                    ELSE NULL
                END
            ) IS NULL
        THEN NULL
        ELSE COALESCE(
            p.lead_time,
            CASE
                WHEN p.data_inicio IS NOT NULL
                 AND p.data_entrega_prevista IS NOT NULL
                THEN (p.data_entrega_prevista - p.data_inicio)
                ELSE NULL
            END
        ) / (p.peso_total_kg / 1000.0)
    END AS lead_time_por_tonelada,
    o.custo_total_materiais,
    o.custo_total_operacoes,
    o.custo_total_servicos,
    -- Custos reais agregados (verdade observada em producao). Sao os targets do
    -- treino quando se quer prever o que realmente vai custar, em vez de o que
    -- um orcamentista teria estimado.
    COALESCE((
        SELECT SUM(rm.custo_total_real)
        FROM realizado_material rm
        JOIN detalhe_material_orcamento dmo
            ON rm.id_linha_material = dmo.id_linha_material
        WHERE dmo.id_orcamento = o.id_orcamento
    ), 0) AS real_materiais,
    COALESCE((
        SELECT SUM(ro.custo_total_real)
        FROM realizado_operacao ro
        JOIN detalhe_operacao_orcamento doo
            ON ro.id_linha_operacao = doo.id_linha_operacao
        WHERE doo.id_orcamento = o.id_orcamento
    ), 0) AS real_operacoes,
    COALESCE((
        SELECT SUM(rs.custo_total_real)
        FROM realizado_servico rs
        JOIN detalhe_servico_orcamento dso
            ON rs.id_linha_servico = dso.id_linha_servico
        WHERE dso.id_orcamento = o.id_orcamento
    ), 0) AS real_servicos
FROM orcamento o
JOIN projeto p
    ON p.id_projeto = o.id_projeto
WHERE o.custo_total_orcado > 0
ORDER BY o.id_orcamento;
"""
