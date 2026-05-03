-- Reset + seed massiva para SI-AOM
-- Objetivos:
-- 1) Apagar todos os dados
-- 2) Criar dados base realistas (materiais, operacoes, servicos)
-- 3) Criar >= 20000 orcamentos
-- 4) Garantir >= 15 linhas por orcamento (8 materiais + 5 operacoes + 2 servicos)
-- 5) Popular tabelas de realizados (apenas para projetos em execucao/concluidos)
-- 6) Distribuir custos de poucos milhares a varias centenas de milhares de euros
-- 7) Espalhar datas por 3 anos (2024-2026) com coerencia entre estado e idade
-- 8) Introduzir outliers realistas nos realizados (~10% derrapas/folgas anormais)

-- Se a sessao anterior ficou em erro, limpa o estado antes de iniciar.
ROLLBACK;
BEGIN;

-- Evita conflito ao reexecutar o script na mesma sessao SQL.
DROP TABLE IF EXISTS tmp_orcamento_scale;
DROP TABLE IF EXISTS tmp_orcamento_target;

TRUNCATE TABLE
    public.previsao_ml,
    public.realizado_material,
    public.realizado_operacao,
    public.realizado_servico,
    public.detalhe_material_orcamento,
    public.detalhe_operacao_orcamento,
    public.detalhe_servico_orcamento,
    public.orcamento,
    public.projeto,
    public.cliente,
    public.material,
    public.operacao,
    public.servico,
    public.utilizador
RESTART IDENTITY CASCADE;

-- Utilizadores base (password = nome curto do perfil):
-- admin@siaom.com        -> admin
-- gestor@siaom.com       -> gestor
-- orcamentista@siaom.com -> orcamentista
-- producao@siaom.com     -> producao
INSERT INTO public.utilizador (nome, email, password_hash, perfil, ativo)
VALUES
    ('Admin', 'admin@siaom.com', '$2b$12$GgVp5e4zbPMGs9pcH/Qo6.cr8eukcYDysakisK1vVvnt04ac0cZc2', 'administrador', true),
    ('Gestor', 'gestor@siaom.com', '$2b$12$g0kRJndOBN9k8qZp/NfOtOBXiskkWajczcgjgEs9Knw51TKJcZEc.', 'gestor', true),
    ('Orcamentista', 'orcamentista@siaom.com', '$2b$12$Ccff3YcLJLStVXq9eM6IS.gkQ4rF8pmrl4tXJp1CFD4D3Xvkfice.', 'orcamentista', true),
    ('Producao', 'producao@siaom.com', '$2b$12$m0pQuMG1MPmfpFJk9Yflyei1elP5/tgZefV84.F/xkk0AuF9pOgTi', 'producao', true);

INSERT INTO public.cliente (nome, nif, email, telefone, morada, observacoes, ativo)
SELECT
    CASE (gs % 8)
        WHEN 0 THEN format('Metalomecanica Norte %s', gs)
        WHEN 1 THEN format('Construtora Atlantico %s', gs)
        WHEN 2 THEN format('Industria Modular Centro %s', gs)
        WHEN 3 THEN format('Logistica Sul %s', gs)
        WHEN 4 THEN format('Manutencao Industrial %s', gs)
        WHEN 5 THEN format('Equipamentos Tecnicos %s', gs)
        WHEN 6 THEN format('Obras Publicas %s', gs)
        ELSE format('Cliente Industrial %s', gs)
    END,
    lpad((200000000 + gs)::text, 9, '0'),
    format('compras%s@cliente.pt', lpad(gs::text, 3, '0')),
    format('+351 91%s', lpad(((gs * 271) % 10000000)::text, 7, '0')),
    format('Zona Industrial Lote %s, Portugal', gs),
    'Cliente gerado automaticamente para seed.',
    true
FROM generate_series(1, 250) AS gs;

INSERT INTO public.material (codigo, nome, unidade, tipo, custo_unitario_default, ativo, qualidade_material)
VALUES
    ('MAT-TUBO-S235-30X30X2', 'Tubo quadrado 30x30x2 S235JR', 'm', 'tubo', 7.2000, true, 'S235JR'),
    ('MAT-TUBO-S235-40X40X2', 'Tubo quadrado 40x40x2 S235JR', 'm', 'tubo', 9.8000, true, 'S235JR'),
    ('MAT-TUBO-S235-60X40X3', 'Tubo retangular 60x40x3 S235JR', 'm', 'tubo', 14.5000, true, 'S235JR'),
    ('MAT-TUBO-S355-50X50X3', 'Tubo quadrado 50x50x3 S355JR', 'm', 'tubo', 15.9000, true, 'S355JR'),
    ('MAT-TUBO-S355-80X40X3', 'Tubo retangular 80x40x3 S355JR', 'm', 'tubo', 18.7000, true, 'S355JR'),
    ('MAT-TUBO-S355-100X50X4', 'Tubo retangular 100x50x4 S355JR', 'm', 'tubo', 29.4000, true, 'S355JR'),
    ('MAT-TUBO-S355-RD48X3', 'Tubo redondo 48.3x3.2 S355JR', 'm', 'tubo', 12.6000, true, 'S355JR'),
    ('MAT-TUBO-INOX304-30X30X2', 'Tubo quadrado inox 30x30x2 AISI 304', 'm', 'tubo', 18.6000, true, 'AISI304'),
    ('MAT-TUBO-INOX304-50X30X2', 'Tubo retangular inox 50x30x2 AISI 304', 'm', 'tubo', 24.8000, true, 'AISI304'),
    ('MAT-TUBO-INOX304-80X40X3', 'Tubo retangular inox 80x40x3 AISI 304', 'm', 'tubo', 41.5000, true, 'AISI304'),
    ('MAT-TUBO-ALU6060-30X30X2', 'Tubo quadrado aluminio 30x30x2 6060', 'm', 'tubo', 8.9000, true, 'AL6060'),
    ('MAT-TUBO-ALU6060-50X30X2', 'Tubo retangular aluminio 50x30x2 6060', 'm', 'tubo', 11.7000, true, 'AL6060'),
    ('MAT-TUBO-ALU6060-80X40X3', 'Tubo retangular aluminio 80x40x3 6060', 'm', 'tubo', 18.2000, true, 'AL6060'),
    ('MAT-CHAPA-LASER-S235-3MM', 'Chapa laser 3mm S235JR', 'kg', 'chapa_laser', 1.5800, true, 'S235JR'),
    ('MAT-CHAPA-LASER-S235-5MM', 'Chapa laser 5mm S235JR', 'kg', 'chapa_laser', 1.6900, true, 'S235JR'),
    ('MAT-CHAPA-LASER-S355-6MM', 'Chapa laser 6mm S355JR', 'kg', 'chapa_laser', 1.9200, true, 'S355JR'),
    ('MAT-CHAPA-LASER-S355-10MM', 'Chapa laser 10mm S355JR', 'kg', 'chapa_laser', 2.1500, true, 'S355JR'),
    ('MAT-CHAPA-LASER-INOX304-3MM', 'Chapa laser inox 3mm AISI 304', 'kg', 'chapa_laser', 5.9000, true, 'AISI304'),
    ('MAT-CHAPA-LASER-INOX304-5MM', 'Chapa laser inox 5mm AISI 304', 'kg', 'chapa_laser', 6.2500, true, 'AISI304'),
    ('MAT-CHAPA-LASER-INOX304-8MM', 'Chapa laser inox 8mm AISI 304', 'kg', 'chapa_laser', 6.8500, true, 'AISI304'),
    ('MAT-CHAPA-LASER-ALU5754-3MM', 'Chapa laser aluminio 3mm 5754', 'kg', 'chapa_laser', 4.2000, true, 'AL5754'),
    ('MAT-CHAPA-LASER-ALU5754-5MM', 'Chapa laser aluminio 5mm 5754', 'kg', 'chapa_laser', 4.5500, true, 'AL5754'),
    ('MAT-CHAPA-LASER-ALU5754-8MM', 'Chapa laser aluminio 8mm 5754', 'kg', 'chapa_laser', 4.9000, true, 'AL5754'),
    ('MAT-PARAF-M8-88', 'Parafuso sextavado M8 classe 8.8 zincado', 'un', 'parafusaria', 0.0900, true, 'ACO 8.8'),
    ('MAT-PARAF-M10-88', 'Parafuso sextavado M10 classe 8.8 zincado', 'un', 'parafusaria', 0.1600, true, 'ACO 8.8'),
    ('MAT-PARAF-M12-88', 'Parafuso sextavado M12 classe 8.8 zincado', 'un', 'parafusaria', 0.2800, true, 'ACO 8.8'),
    ('MAT-PORCA-M12-88', 'Porca sextavada M12 classe 8 zincada', 'un', 'parafusaria', 0.0800, true, 'ACO 8'),
    ('MAT-ANILHA-M12', 'Anilha lisa M12 zincada', 'un', 'parafusaria', 0.0300, true, 'ACO'),
    ('MAT-PARAF-INOX-M8-A2', 'Parafuso sextavado inox M8 A2', 'un', 'parafusaria', 0.2200, true, 'AISI304'),
    ('MAT-REBITE-INOX-M6-A2', 'Rebite roscado inox M6 A2', 'un', 'parafusaria', 0.3500, true, 'AISI304'),
    ('MAT-PECA-DOBRADICA-S235-80', 'Dobradica comercial aco 80mm', 'un', 'peca_comercio', 2.4000, true, 'S235JR'),
    ('MAT-PECA-FECHO-S235', 'Fecho rapido aco zincado', 'un', 'peca_comercio', 7.8000, true, 'S235JR'),
    ('MAT-PECA-PE-NIVELADOR-S235', 'Pe nivelador M12 aco zincado', 'un', 'peca_comercio', 3.6000, true, 'S235JR'),
    ('MAT-PECA-SUPORTE-INOX304', 'Suporte comercial inox 304', 'un', 'peca_comercio', 5.2000, true, 'AISI304'),
    ('MAT-PECA-PERFIL-ALU6060', 'Perfil comercial aluminio 6060', 'un', 'peca_comercio', 9.4000, true, 'AL6060'),
    ('MAT-PECA-CHAPA-DOBRADA-ALU5754', 'Chapa dobrada comercial aluminio 5754', 'un', 'peca_comercio', 6.8000, true, 'AL5754');

INSERT INTO public.operacao (codigo, nome, categoria, custo_hora_default, setup_hora_default, ativo)
VALUES
    ('OP-CORTE-LASER', 'Corte laser', 'corte', 42.00, 0.50, true),
    ('OP-CORTE', 'Corte', 'corte', 32.00, 0.30, true),
    ('OP-FURACAO', 'Furacao', 'furacao', 34.00, 0.25, true),
    ('OP-MAQUINACAO', 'Maquinacao', 'maquinacao', 46.00, 0.60, true),
    ('OP-CALANDRAGEM', 'Calandragem', 'calandragem', 48.00, 0.75, true),
    ('OP-QUINAGEM', 'Quinagem', 'quinagem', 45.00, 0.55, true),
    ('OP-SOLDADURA', 'Soldadura', 'soldadura', 39.00, 0.45, true),
    ('OP-PINGAMENTO', 'Pingamento', 'pingamento', 34.00, 0.25, true),
    ('OP-REBARBAGEM', 'Rebarbagem', 'acabamento', 31.00, 0.25, true),
    ('OP-MONTAGEM', 'Montagem', 'montagem', 30.00, 0.30, true),
    ('OP-QUALIDADE', 'Qualidade', 'qualidade', 28.00, 0.20, true),
    ('OP-ACABAMENTO', 'Acabamento', 'acabamento', 33.00, 0.25, true),
    ('OP-EXPEDICAO', 'Expedicao', 'expedicao', 24.00, 0.15, true);

INSERT INTO public.servico (codigo, nome, unidade, preco_unitario_default, ativo)
VALUES
    ('SVC-GALV', 'Galvanizacao', 'kg', 1.20, true),
    ('SVC-PINTURA-LIQUIDA', 'Pintura liquida', 'm2', 14.80, true),
    ('SVC-LACAGEM', 'Lacagem', 'm2', 16.50, true),
    ('SVC-ANODIZACAO', 'Anodizacao aluminio', 'm2', 18.00, true),
    ('SVC-POLIMENTO', 'Polimento inox', 'm2', 22.00, true),
    ('SVC-TRANSPORTE', 'Transporte', 'viag', 380.00, true),
    ('SVC-GRUA', 'Grua', 'dia', 920.00, true),
    ('SVC-ENSAIOS', 'Ensaios qualidade', 'hora', 68.00, true),
    ('SVC-CERTIFICACAO', 'Certificacao', 'lote', 650.00, true),
    ('SVC-EMBALAGEM', 'Embalagem', 'lote', 240.00, true),
    ('SVC-MONTAGEM-EXT', 'Montagem externa', 'hora', 42.00, true);

INSERT INTO public.projeto (
    referencia,
    designacao,
    tipologia,
    estado,
    data_inicio,
    data_entrega_prevista,
    peso_total_kg,
    numero_pecas,
    complexidade,
    material_principal,
    tratamento_superficie,
    processo_corte,
    lead_time,
    observacoes,
    criado_por,
    id_cliente
)
SELECT
    format('PRJ-2026-%s', lpad(gs::text, 5, '0')),
    CASE (gs % 6)
        WHEN 0 THEN format('Pavilhao metalico %s', gs)
        WHEN 1 THEN format('Passadico metalico %s', gs)
        WHEN 2 THEN format('Cobertura metalica %s', gs)
        WHEN 3 THEN format('Mezanino industrial %s', gs)
        WHEN 4 THEN format('Plataforma tecnica %s', gs)
        ELSE format('Escadaria metalica %s', gs)
    END,
    CASE (gs % 6)
        WHEN 0 THEN 'pavilhao'
        WHEN 1 THEN 'passadico'
        WHEN 2 THEN 'cobertura'
        WHEN 3 THEN 'mezanino'
        WHEN 4 THEN 'plataforma'
        ELSE 'escadaria'
    END,
    CASE
        WHEN gs % 29 = 0 THEN 'cancelado'
        WHEN gs % 7 = 0 THEN 'concluido'
        WHEN gs % 5 = 0 THEN 'em_execucao'
        WHEN gs % 4 = 0 THEN 'aprovado'
        WHEN gs % 3 = 0 THEN 'planeado'
        ELSE 'em_analise'
    END,
    -- data_inicio: distribuida por 3 anos (2024-2026) coerentemente com o estado.
    -- Concluidos sao mais antigos (2024 - meio 2025), em_execucao em 2025-Q3 a meio 2026,
    -- aprovados/planeados/em_analise mais recentes (2026).
    CASE
        WHEN gs % 29 = 0 THEN (DATE '2024-06-01' + ((gs * 7) % 730))   -- cancelado: pode ser de qualquer epoca
        WHEN gs % 7 = 0 THEN (DATE '2024-01-01' + ((gs * 5) % 540))    -- concluido: 2024 a meio 2025
        WHEN gs % 5 = 0 THEN (DATE '2025-06-01' + ((gs * 3) % 270))    -- em_execucao: 2025-Q3 a meio 2026
        WHEN gs % 4 = 0 THEN (DATE '2025-12-01' + ((gs * 2) % 200))    -- aprovado: fim 2025 a meio 2026
        WHEN gs % 3 = 0 THEN (DATE '2026-04-01' + ((gs * 4) % 200))    -- planeado: futuro proximo
        ELSE (DATE '2026-06-01' + ((gs * 4) % 150))                    -- em_analise: mais recente
    END,
    CASE
        WHEN gs % 29 = 0 THEN (DATE '2024-06-01' + ((gs * 7) % 730) + (25 + (gs % 45)))
        WHEN gs % 7 = 0 THEN (DATE '2024-01-01' + ((gs * 5) % 540) + (35 + (gs % 55)))
        WHEN gs % 5 = 0 THEN (DATE '2025-06-01' + ((gs * 3) % 270) + (55 + (gs % 70)))
        WHEN gs % 4 = 0 THEN (DATE '2025-12-01' + ((gs * 2) % 200) + (45 + (gs % 65)))
        WHEN gs % 3 = 0 THEN (DATE '2026-04-01' + ((gs * 4) % 200) + (45 + (gs % 70)))
        ELSE (DATE '2026-06-01' + ((gs * 4) % 150) + (45 + (gs % 70)))
    END,
    round((
        CASE
            WHEN gs % 40 = 0 THEN 60000 + random() * 80000
            WHEN gs % 25 = 0 THEN 35000 + random() * 55000
            WHEN gs % 6 = 0 THEN 12000 + random() * 48000
            WHEN gs % 6 = 2 THEN 6000 + random() * 30000
            WHEN gs % 6 = 3 THEN 3500 + random() * 22000
            WHEN gs % 6 = 4 THEN 2000 + random() * 16000
            WHEN gs % 6 = 1 THEN 900 + random() * 9000
            ELSE 700 + random() * 12000
        END
        * CASE
            WHEN gs % 10 IN (1, 2) THEN 0.58
            WHEN gs % 10 = 0 THEN 0.85
            ELSE 1.00
          END
    )::numeric, 2),
    CASE
        WHEN gs % 40 = 0 THEN 800 + (random() * 1600)::int
        WHEN gs % 25 = 0 THEN 500 + (random() * 900)::int
        WHEN gs % 6 = 0 THEN 220 + (random() * 900)::int
        WHEN gs % 6 = 2 THEN 120 + (random() * 650)::int
        WHEN gs % 6 = 3 THEN 80 + (random() * 500)::int
        WHEN gs % 6 = 4 THEN 45 + (random() * 300)::int
        WHEN gs % 6 = 1 THEN 25 + (random() * 180)::int
        ELSE 20 + (random() * 220)::int
    END,
    CASE
        WHEN gs % 4 = 0 THEN 'alta'
        WHEN gs % 3 = 0 THEN 'media'
        ELSE 'baixa'
    END,
    CASE
        WHEN gs % 10 = 0 THEN 'AISI304'
        WHEN gs % 10 = 1 THEN 'AL6060'
        WHEN gs % 10 = 2 THEN 'AL5754'
        WHEN gs % 10 IN (3, 5, 7) THEN 'S235JR'
        ELSE 'S355JR'
    END,
    CASE
        WHEN gs % 10 = 0 THEN
            CASE
                WHEN gs % 20 = 0 THEN 'polimento'
                ELSE 'sem_tratamento'
            END
        WHEN gs % 10 IN (1, 2) THEN
            CASE
                WHEN gs % 4 = 0 THEN 'pintura_liquida'
                WHEN gs % 3 = 0 THEN 'lacagem'
                ELSE 'anodizacao'
            END
        ELSE
            CASE
                WHEN gs % 4 = 0 THEN 'galvanizacao'
                WHEN gs % 3 = 0 THEN 'pintura_liquida'
                WHEN gs % 5 = 0 THEN 'lacagem'
                ELSE 'sem_tratamento'
            END
    END,
    CASE
        WHEN gs % 10 IN (1, 2) THEN
            CASE
                WHEN gs % 2 = 0 THEN 'laser_chapa'
                ELSE 'laser_tubo'
            END
        WHEN gs % 10 = 0 THEN 'laser_chapa'
        WHEN gs % 4 = 0 THEN 'corte'
        ELSE 'laser_chapa'
    END,
    CASE
        WHEN gs % 40 = 0 THEN 120 + (gs % 90)
        WHEN gs % 25 = 0 THEN 90 + (gs % 75)
        WHEN gs % 6 = 0 THEN 75 + (gs % 65)
        WHEN gs % 6 = 2 THEN 55 + (gs % 55)
        WHEN gs % 6 = 3 THEN 45 + (gs % 50)
        WHEN gs % 6 = 4 THEN 35 + (gs % 45)
        ELSE 20 + (gs % 40)
    END,
    format('Projeto seedado automaticamente com escala, material e tratamento coerentes. Item %s.', gs),
    CASE
        WHEN gs % 6 = 0 THEN 2
        WHEN gs % 5 = 0 THEN 4
        ELSE 1
    END,
    ((gs - 1) % 250) + 1
FROM generate_series(1, 6700) AS gs;

-- 6700 projetos x 3 versoes = 20100 orcamentos
WITH versoes AS (
    SELECT
        p.id_projeto,
        p.estado AS projeto_estado,
        p.tipologia,
        p.data_inicio,
        v.nr AS versao_num,
        format('v%s', v.nr) AS versao
    FROM public.projeto p
    CROSS JOIN (VALUES (1), (2), (3)) AS v(nr)
)
INSERT INTO public.orcamento (
    id_projeto,
    versao,
    criado_por,
    data_criacao,
    estado,
    margem_percentual,
    observacoes
)
SELECT
    id_projeto,
    versao,
    CASE
        WHEN versao_num = 1 THEN 3
        WHEN versao_num = 2 THEN 2
        ELSE 1
    END,
    data_inicio::timestamp
        - ((CASE versao_num WHEN 1 THEN 45 WHEN 2 THEN 25 ELSE 10 END) * INTERVAL '1 day')
        - ((id_projeto % 12) * INTERVAL '1 day'),
    CASE
        WHEN projeto_estado = 'cancelado' AND versao_num = 1 THEN 'rejeitado'
        WHEN projeto_estado = 'cancelado' THEN 'cancelado'
        WHEN projeto_estado IN ('concluido', 'em_execucao') AND versao_num < 3 THEN 'rejeitado'
        WHEN projeto_estado IN ('concluido', 'em_execucao') THEN 'aprovado'
        WHEN projeto_estado IN ('aprovado', 'planeado') AND versao_num = 1 THEN 'rejeitado'
        WHEN projeto_estado IN ('aprovado', 'planeado') AND versao_num = 2 THEN 'em_revisao'
        WHEN projeto_estado IN ('aprovado', 'planeado') THEN 'aprovado'
        WHEN projeto_estado = 'em_analise' AND versao_num = 1 THEN 'rejeitado'
        WHEN projeto_estado = 'em_analise' AND versao_num = 2 THEN 'em_revisao'
        ELSE 'rascunho'
    END,
    -- Margem comercial varia por tipologia: trabalhos mais tecnicos (mezanino,
    -- plataforma) tipicamente tem margens maiores; trabalhos mais comoditizados
    -- (pavilhao, escadaria) mais baixas. Reflecte praxis de mercado.
    round((
        CASE tipologia
            WHEN 'mezanino'   THEN 18 + random() * 14   -- 18-32% (engenharia)
            WHEN 'plataforma' THEN 16 + random() * 12   -- 16-28%
            WHEN 'cobertura'  THEN 14 + random() * 11   -- 14-25%
            WHEN 'passadico'  THEN 14 + random() * 10   -- 14-24%
            WHEN 'escadaria'  THEN 12 + random() * 12   -- 12-24%
            WHEN 'pavilhao'   THEN 11 + random() * 9    -- 11-20% (mais comoditizado)
            ELSE 13 + random() * 12
        END
    )::numeric, 2),
    format('Orcamento %s do projeto %s - estrutura metalica.', versao, id_projeto)
FROM versoes
ORDER BY id_projeto, versao_num;

-- 8 linhas de material por orcamento
WITH mat_picks AS (
    SELECT
        o.id_orcamento,
        gs.idx,
        mat.id_material
    FROM public.orcamento o
    JOIN public.projeto pr ON pr.id_projeto = o.id_projeto
    CROSS JOIN generate_series(1, 8) AS gs(idx)
    JOIN LATERAL (
        SELECT ranked.id_material
        FROM (
            SELECT
                m.id_material,
                row_number() OVER (
                    ORDER BY ((m.id_material * 17 + o.id_orcamento * 11 + gs.idx * 7) % 1009), m.id_material
                ) AS rn,
                count(*) OVER () AS total
            FROM public.material m
            WHERE m.ativo
              AND (
                  (
                      m.tipo IN ('tubo', 'chapa_laser')
                      AND (
                          (pr.material_principal IN ('S235JR', 'S355JR') AND m.qualidade_material = pr.material_principal)
                          OR (pr.material_principal = 'AISI304' AND m.qualidade_material = 'AISI304')
                          OR (pr.material_principal = 'AL6060' AND m.qualidade_material IN ('AL6060', 'AL5754'))
                          OR (pr.material_principal = 'AL5754' AND m.qualidade_material IN ('AL5754', 'AL6060'))
                      )
                  )
                  OR (
                      m.tipo = 'parafusaria'
                      AND (
                          (pr.material_principal IN ('S235JR', 'S355JR') AND m.qualidade_material IN ('ACO', 'ACO 8', 'ACO 8.8'))
                          OR (pr.material_principal = 'AISI304' AND m.qualidade_material = 'AISI304')
                          OR (pr.material_principal IN ('AL6060', 'AL5754') AND m.qualidade_material = 'AISI304')
                      )
                  )
                  OR (
                      m.tipo = 'peca_comercio'
                      AND (
                          (pr.material_principal IN ('S235JR', 'S355JR') AND m.qualidade_material IN ('S235JR', 'S355JR'))
                          OR (pr.material_principal = 'AISI304' AND m.qualidade_material = 'AISI304')
                          OR (pr.material_principal IN ('AL6060', 'AL5754') AND m.qualidade_material IN ('AL6060', 'AL5754'))
                      )
                  )
              )
        ) ranked
        WHERE ranked.rn = ((gs.idx - 1) % ranked.total) + 1
    ) mat ON true
),
mat_base AS (
    SELECT
        p.id_orcamento,
        m.id_material,
        m.codigo,
        m.unidade,
        m.custo_unitario_default::numeric(14,4) AS preco_unitario_snapshot,
        m.nome AS nome_material,
        CASE
            WHEN m.unidade = 'kg' THEN round((120 + random() * 1800)::numeric, 2)
            WHEN m.unidade = 'm' THEN round((15 + random() * 260)::numeric, 2)
            WHEN m.unidade = 'm2' THEN round((20 + random() * 520)::numeric, 2)
            WHEN m.unidade = 'un' THEN round((40 + random() * 700)::numeric, 2)
            ELSE round((10 + random() * 140)::numeric, 2)
        END AS quantidade,
        CASE m.codigo
            WHEN 'MAT-TUBO-S235-30X30X2' THEN 1.76
            WHEN 'MAT-TUBO-S235-40X40X2' THEN 2.39
            WHEN 'MAT-TUBO-S235-60X40X3' THEN 4.43
            WHEN 'MAT-TUBO-S355-50X50X3' THEN 4.43
            WHEN 'MAT-TUBO-S355-80X40X3' THEN 5.20
            WHEN 'MAT-TUBO-S355-100X50X4' THEN 8.78
            WHEN 'MAT-TUBO-S355-RD48X3' THEN 3.56
            WHEN 'MAT-TUBO-INOX304-30X30X2' THEN 1.77
            WHEN 'MAT-TUBO-INOX304-50X30X2' THEN 2.37
            WHEN 'MAT-TUBO-INOX304-80X40X3' THEN 5.34
            WHEN 'MAT-TUBO-ALU6060-30X30X2' THEN 0.60
            WHEN 'MAT-TUBO-ALU6060-50X30X2' THEN 0.80
            WHEN 'MAT-TUBO-ALU6060-80X40X3' THEN 1.85
            ELSE 1.00
        END AS kg_por_m,
        round((random() * 5.5)::numeric, 2) AS desperdicio_percent
    FROM mat_picks p
    JOIN public.material m ON m.id_material = p.id_material
),
mat_dados AS (
    SELECT
        mb.id_orcamento,
        mb.id_material,
        mb.quantidade,
        CASE
            WHEN mb.unidade = 'kg' THEN mb.quantidade
            WHEN mb.unidade = 'm' THEN round((mb.quantidade * mb.kg_por_m)::numeric, 2)
            WHEN mb.unidade = 'm2' THEN round((mb.quantidade * (2.8 + random() * 1.2))::numeric, 2)
            ELSE NULL::numeric
        END AS peso_kg,
        mb.desperdicio_percent,
        mb.preco_unitario_snapshot,
        mb.nome_material
    FROM mat_base mb
)
INSERT INTO public.detalhe_material_orcamento (
    id_orcamento,
    id_material,
    quantidade,
    peso_kg,
    desperdicio_percent,
    preco_unitario_snapshot,
    custo_total,
    observacoes
)
SELECT
    id_orcamento,
    id_material,
    quantidade,
    peso_kg,
    desperdicio_percent,
    preco_unitario_snapshot,
    round((quantidade * preco_unitario_snapshot * (1 + (desperdicio_percent / 100.0)))::numeric, 2),
    format('Material aplicado: %s', nome_material)
FROM mat_dados
ORDER BY id_orcamento, id_material;

-- 5 linhas de operacao por orcamento
WITH op_count AS (
    SELECT count(*)::int AS total FROM public.operacao
),
op_picks AS (
    SELECT
        o.id_orcamento,
        gs.idx,
        ((o.id_orcamento * 13 + gs.idx * 5) % oc.total + 1)::int AS id_operacao
    FROM public.orcamento o
    CROSS JOIN op_count oc
    CROSS JOIN generate_series(1, 5) AS gs(idx)
),
op_dados AS (
    SELECT
        p.id_orcamento,
        op.id_operacao,
        CASE
            WHEN op.categoria = 'soldadura' THEN round((14 + random() * 90)::numeric, 2)
            WHEN op.categoria = 'montagem' THEN round((12 + random() * 70)::numeric, 2)
            WHEN op.categoria = 'corte' THEN round((6 + random() * 45)::numeric, 2)
            WHEN op.categoria IN ('furacao', 'maquinacao') THEN round((8 + random() * 55)::numeric, 2)
            WHEN op.categoria IN ('calandragem', 'quinagem') THEN round((6 + random() * 45)::numeric, 2)
            WHEN op.categoria = 'pingamento' THEN round((4 + random() * 32)::numeric, 2)
            WHEN op.categoria = 'acabamento' THEN round((6 + random() * 38)::numeric, 2)
            WHEN op.categoria = 'qualidade' THEN round((3 + random() * 22)::numeric, 2)
            WHEN op.categoria = 'expedicao' THEN round((2 + random() * 16)::numeric, 2)
            ELSE round((5 + random() * 35)::numeric, 2)
        END AS horas,
        round((op.setup_hora_default + random() * 1.4)::numeric, 2) AS tempo_setup_h,
        round((op.custo_hora_default * (0.95 + random() * 0.20))::numeric, 2) AS custo_hora_snapshot,
        op.nome AS nome_operacao
    FROM op_picks p
    JOIN public.operacao op ON op.id_operacao = p.id_operacao
)
INSERT INTO public.detalhe_operacao_orcamento (
    id_orcamento,
    id_operacao,
    horas,
    tempo_setup_h,
    custo_hora_snapshot,
    custo_total,
    observacoes
)
SELECT
    id_orcamento,
    id_operacao,
    horas,
    tempo_setup_h,
    custo_hora_snapshot,
    round(((horas + tempo_setup_h) * custo_hora_snapshot)::numeric, 2),
    format('Operacao prevista: %s', nome_operacao)
FROM op_dados
ORDER BY id_orcamento, id_operacao;

-- 2 linhas de servico por orcamento
WITH svc_picks AS (
    SELECT
        o.id_orcamento,
        gs.idx,
        svc.id_servico
    FROM public.orcamento o
    JOIN public.projeto pr ON pr.id_projeto = o.id_projeto
    CROSS JOIN generate_series(1, 2) AS gs(idx)
    JOIN LATERAL (
        SELECT ranked.id_servico
        FROM (
            SELECT
                s.id_servico,
                row_number() OVER (
                    ORDER BY ((s.id_servico * 19 + o.id_orcamento * 17 + gs.idx * 3) % 997), s.id_servico
                ) AS rn,
                count(*) OVER () AS total
            FROM public.servico s
            WHERE s.ativo
              AND (
                  (
                      gs.idx = 1
                      AND (
                          (pr.tratamento_superficie = 'galvanizacao' AND s.codigo = 'SVC-GALV')
                          OR (pr.tratamento_superficie = 'pintura_liquida' AND s.codigo = 'SVC-PINTURA-LIQUIDA')
                          OR (pr.tratamento_superficie = 'lacagem' AND s.codigo = 'SVC-LACAGEM')
                          OR (pr.tratamento_superficie = 'anodizacao' AND s.codigo = 'SVC-ANODIZACAO')
                          OR (pr.tratamento_superficie = 'polimento' AND s.codigo = 'SVC-POLIMENTO')
                          OR (pr.tratamento_superficie = 'sem_tratamento' AND s.codigo IN ('SVC-TRANSPORTE', 'SVC-ENSAIOS', 'SVC-CERTIFICACAO', 'SVC-EMBALAGEM', 'SVC-MONTAGEM-EXT'))
                      )
                  )
                  OR (
                      gs.idx = 2
                      AND s.codigo IN ('SVC-TRANSPORTE', 'SVC-ENSAIOS', 'SVC-CERTIFICACAO', 'SVC-EMBALAGEM', 'SVC-MONTAGEM-EXT')
                  )
              )
        ) ranked
        WHERE ranked.rn = ((gs.idx - 1) % ranked.total) + 1
    ) svc ON true
),
svc_dados AS (
    SELECT
        p.id_orcamento,
        s.id_servico,
        CASE
            WHEN s.unidade = 'kg' THEN round((1500 + random() * 12000)::numeric, 2)
            WHEN s.unidade = 'm2' THEN round((80 + random() * 1400)::numeric, 2)
            WHEN s.unidade = 'hora' THEN round((8 + random() * 120)::numeric, 2)
            WHEN s.unidade = 'dia' THEN round((1 + random() * 8)::numeric, 2)
            WHEN s.unidade = 'viag' THEN round((1 + random() * 4)::numeric, 2)
            ELSE round((1 + random() * 20)::numeric, 2)
        END AS quantidade,
        round((s.preco_unitario_default * (0.94 + random() * 0.18))::numeric, 2) AS preco_unitario_snapshot,
        s.nome AS nome_servico
    FROM svc_picks p
    JOIN public.servico s ON s.id_servico = p.id_servico
)
INSERT INTO public.detalhe_servico_orcamento (
    id_orcamento,
    id_servico,
    quantidade,
    preco_unitario_snapshot,
    custo_total,
    observacoes
)
SELECT
    id_orcamento,
    id_servico,
    quantidade,
    preco_unitario_snapshot,
    round((quantidade * preco_unitario_snapshot)::numeric, 2),
    format('Servico externo: %s', nome_servico)
FROM svc_dados
ORDER BY id_orcamento, id_servico;

-- ===========================================================================
-- Targets causais por orcamento (substitui o anchor + random anterior).
-- A ideia central: o custo de cada categoria depende de features tecnicas do
-- projeto, com ruido pequeno (+/- 7-10%) para simular variabilidade realista.
-- Isto da ao ML uma relacao causal forte para aprender (peso, complexidade,
-- material e tratamento). Valores escolhidos para reproduzir ordens de
-- grandeza tipicas em metalomecanica:
--   * mat_eur_per_kg: 1.60 (S235JR) ate 5.80 (AISI304)
--   * trat_eur_per_kg: 0.10 (sem tratamento) ate 0.95 (polimento)
--   * compl_factor: 1.00 a 1.90 (afeta horas, logo custo de operacao)
--   * tipo_factor: 0.85 a 1.05 (afeta materiais conforme tipologia)
-- ===========================================================================
CREATE TEMP TABLE tmp_orcamento_target ON COMMIT DROP AS
SELECT
    o.id_orcamento,
    -- Materiais: peso x EUR/kg(material) x tipologia x ruido
    GREATEST(500::numeric,
        round((p.peso_total_kg
            * CASE p.material_principal
                WHEN 'AISI304' THEN 5.80
                WHEN 'AL5754'  THEN 4.40
                WHEN 'AL6060'  THEN 4.10
                WHEN 'S355JR'  THEN 1.90
                WHEN 'S235JR'  THEN 1.60
                ELSE                1.80
              END
            * CASE p.tipologia
                WHEN 'cobertura'  THEN 1.05
                WHEN 'pavilhao'   THEN 1.00
                WHEN 'plataforma' THEN 1.00
                WHEN 'mezanino'   THEN 0.95
                WHEN 'passadico'  THEN 0.90
                WHEN 'escadaria'  THEN 0.85
                ELSE                  1.00
              END
            * (0.93 + random() * 0.14)
        )::numeric, 2)
    ) AS target_materiais,
    -- Operacoes: peso/escala x complexidade x processo_corte x ruido
    -- (peso/6 ~ EUR-equivalente; depois aplicam-se multiplicadores)
    GREATEST(300::numeric,
        round((p.peso_total_kg / 6.0
            * CASE p.complexidade
                WHEN 'alta'  THEN 1.90
                WHEN 'media' THEN 1.40
                ELSE              1.00
              END
            * CASE p.processo_corte
                WHEN 'laser_chapa' THEN 1.08
                WHEN 'laser_tubo'  THEN 1.05
                WHEN 'corte'       THEN 1.00
                ELSE                    1.00
              END
            * (1.0 + (p.numero_pecas::numeric * 0.0008))  -- mais pecas = mais montagem
            * (0.90 + random() * 0.20)
        )::numeric, 2)
    ) AS target_operacoes,
    -- Servicos: peso x EUR/kg(tratamento) x ruido
    GREATEST(200::numeric,
        round((p.peso_total_kg
            * CASE p.tratamento_superficie
                WHEN 'galvanizacao'   THEN 0.80
                WHEN 'pintura_liquida' THEN 0.62
                WHEN 'lacagem'        THEN 0.55
                WHEN 'anodizacao'     THEN 0.70
                WHEN 'polimento'      THEN 0.95
                WHEN 'sem_tratamento' THEN 0.10
                ELSE                       0.20
              END
            * (0.90 + random() * 0.20)
        )::numeric, 2)
    ) AS target_servicos
FROM public.orcamento o
JOIN public.projeto p ON p.id_projeto = o.id_projeto;

-- Fatores de escala separados por categoria (materiais / operacoes / servicos).
-- Cada categoria escala as suas linhas independentemente para o seu target,
-- de modo a que custo_total_materiais/operacoes/servicos ficam coerentes com
-- as features tecnicas do projeto (e nao apenas o total agregado).
CREATE TEMP TABLE tmp_orcamento_scale ON COMMIT DROP AS
WITH atuais AS (
    SELECT
        o.id_orcamento,
        COALESCE((SELECT sum(custo_total) FROM public.detalhe_material_orcamento WHERE id_orcamento = o.id_orcamento), 0) AS atual_mat,
        COALESCE((SELECT sum(custo_total) FROM public.detalhe_operacao_orcamento  WHERE id_orcamento = o.id_orcamento), 0) AS atual_op,
        COALESCE((SELECT sum(custo_total) FROM public.detalhe_servico_orcamento   WHERE id_orcamento = o.id_orcamento), 0) AS atual_svc
    FROM public.orcamento o
)
SELECT
    t.id_orcamento,
    t.target_materiais,
    t.target_operacoes,
    t.target_servicos,
    CASE WHEN a.atual_mat <= 0 THEN 1::numeric
         ELSE t.target_materiais / a.atual_mat END AS fator_mat,
    CASE WHEN a.atual_op <= 0 THEN 1::numeric
         ELSE t.target_operacoes / a.atual_op END AS fator_op,
    CASE WHEN a.atual_svc <= 0 THEN 1::numeric
         ELSE t.target_servicos / a.atual_svc END AS fator_svc
FROM tmp_orcamento_target t
JOIN atuais a ON a.id_orcamento = t.id_orcamento;

-- Aplica escala por categoria (materiais)
UPDATE public.detalhe_material_orcamento dm
SET
    quantidade = round((dm.quantidade * s.fator_mat)::numeric, 2),
    peso_kg = CASE
        WHEN dm.peso_kg IS NULL THEN NULL::numeric
        ELSE round((dm.peso_kg * s.fator_mat)::numeric, 2)
    END,
    custo_total = round(((dm.quantidade * s.fator_mat) * dm.preco_unitario_snapshot * (1 + dm.desperdicio_percent / 100.0))::numeric, 2)
FROM tmp_orcamento_scale s
WHERE s.id_orcamento = dm.id_orcamento;

-- Aplica escala por categoria (operacoes)
UPDATE public.detalhe_operacao_orcamento do2
SET
    horas = round((do2.horas * s.fator_op)::numeric, 2),
    tempo_setup_h = round((do2.tempo_setup_h * s.fator_op)::numeric, 2),
    custo_total = round((((do2.horas * s.fator_op) + (do2.tempo_setup_h * s.fator_op)) * do2.custo_hora_snapshot)::numeric, 2)
FROM tmp_orcamento_scale s
WHERE s.id_orcamento = do2.id_orcamento;

-- Aplica escala por categoria (servicos)
UPDATE public.detalhe_servico_orcamento ds
SET
    quantidade = round((ds.quantidade * s.fator_svc)::numeric, 2),
    custo_total = round(((ds.quantidade * s.fator_svc) * ds.preco_unitario_snapshot)::numeric, 2)
FROM tmp_orcamento_scale s
WHERE s.id_orcamento = ds.id_orcamento;

-- Atualiza totais do orcamento para ficar coerente com as linhas
UPDATE public.orcamento o
SET
    custo_total_materiais = COALESCE((
        SELECT round(sum(dm.custo_total)::numeric, 2)
        FROM public.detalhe_material_orcamento dm
        WHERE dm.id_orcamento = o.id_orcamento
    ), 0),
    custo_total_operacoes = COALESCE((
        SELECT round(sum(do2.custo_total)::numeric, 2)
        FROM public.detalhe_operacao_orcamento do2
        WHERE do2.id_orcamento = o.id_orcamento
    ), 0),
    custo_total_servicos = COALESCE((
        SELECT round(sum(ds.custo_total)::numeric, 2)
        FROM public.detalhe_servico_orcamento ds
        WHERE ds.id_orcamento = o.id_orcamento
    ), 0),
    horas_totais_previstas = COALESCE((
        SELECT round(sum(do3.horas + do3.tempo_setup_h)::numeric, 2)
        FROM public.detalhe_operacao_orcamento do3
        WHERE do3.id_orcamento = o.id_orcamento
    ), 0),
    custo_total_orcado = round((
        COALESCE((SELECT sum(dm2.custo_total) FROM public.detalhe_material_orcamento dm2 WHERE dm2.id_orcamento = o.id_orcamento), 0) +
        COALESCE((SELECT sum(do4.custo_total) FROM public.detalhe_operacao_orcamento do4 WHERE do4.id_orcamento = o.id_orcamento), 0) +
        COALESCE((SELECT sum(ds2.custo_total) FROM public.detalhe_servico_orcamento ds2 WHERE ds2.id_orcamento = o.id_orcamento), 0)
    )::numeric, 2),
    preco_venda = round((
        (
            COALESCE((SELECT sum(dm3.custo_total) FROM public.detalhe_material_orcamento dm3 WHERE dm3.id_orcamento = o.id_orcamento), 0) +
            COALESCE((SELECT sum(do5.custo_total) FROM public.detalhe_operacao_orcamento do5 WHERE do5.id_orcamento = o.id_orcamento), 0) +
            COALESCE((SELECT sum(ds3.custo_total) FROM public.detalhe_servico_orcamento ds3 WHERE ds3.id_orcamento = o.id_orcamento), 0)
        ) * (1 + COALESCE(o.margem_percentual, 0) / 100.0)
    )::numeric, 2);

-- (Removido) Anteriormente sobrescrevia peso_total_kg do projeto a partir das
-- linhas de material. Foi removido porque o peso_total_kg deve ser uma feature
-- de INPUT (introduzida no projeto), e nao um valor derivado das linhas. Caso
-- contrario o ML treina sobre uma variavel circular (peso definido a partir
-- do que ja foi gerado para o orcamento), perdendo o sinal causal.

-- Realizados de material.
-- O f_qtd e modulado por um shock_factor por projeto que simula imprevistos:
--   * ~2.4% derrapagem grande (40-90% acima do orcado)
--   * ~1.9% folga grande (15-30% abaixo do orcado)
--   * ~5.9% derrapagem media (10-22% acima)
--   * ~89.8% normal (variacao tipica de execucao)
WITH rm_base AS (
    SELECT
        d.id_linha_material,
        d.id_orcamento,
        d.quantidade,
        d.peso_kg,
        d.preco_unitario_snapshot,
        (0.95 + random() * 0.16) *
            CASE
                WHEN p.id_projeto % 41 = 0 THEN 1.40 + random() * 0.50
                WHEN p.id_projeto % 53 = 0 THEN 0.70 + random() * 0.15
                WHEN p.id_projeto % 17 = 0 THEN 1.10 + random() * 0.12
                ELSE 1.0
            END AS f_qtd,
        (0.97 + random() * 0.22) AS f_preco
    FROM public.detalhe_material_orcamento d
    JOIN public.orcamento o ON o.id_orcamento = d.id_orcamento
    JOIN public.projeto p ON p.id_projeto = o.id_projeto
    WHERE o.estado = 'aprovado'
      AND p.estado IN ('em_execucao', 'concluido')
)
INSERT INTO public.realizado_material (
    id_linha_material,
    data_registo,
    quantidade,
    peso_kg,
    custo_unitario_real,
    custo_total_real,
    observacoes
)
SELECT
    r.id_linha_material,
    o.data_criacao + ((1 + (random() * 45)::int) * INTERVAL '1 day'),
    round((r.quantidade * r.f_qtd)::numeric, 2),
    CASE
        WHEN r.peso_kg IS NULL THEN NULL::numeric
        ELSE round((r.peso_kg * (0.94 + random() * 0.20))::numeric, 2)
    END,
    round((r.preco_unitario_snapshot * r.f_preco)::numeric, 4),
    round(((r.quantidade * r.f_qtd) * (r.preco_unitario_snapshot * r.f_preco))::numeric, 2),
    'Consumo real de material em producao.'
FROM rm_base r
JOIN public.orcamento o ON o.id_orcamento = r.id_orcamento;

-- Realizados de operacao (com mesmo shock_factor por projeto que materiais)
WITH ro_base AS (
    SELECT
        d.id_linha_operacao,
        d.id_orcamento,
        d.horas,
        d.tempo_setup_h,
        d.custo_hora_snapshot,
        (0.90 + random() * 0.25) *
            CASE
                WHEN p.id_projeto % 41 = 0 THEN 1.40 + random() * 0.50
                WHEN p.id_projeto % 53 = 0 THEN 0.70 + random() * 0.15
                WHEN p.id_projeto % 17 = 0 THEN 1.10 + random() * 0.12
                ELSE 1.0
            END AS f_horas,
        (0.90 + random() * 0.30) AS f_setup,
        (0.95 + random() * 0.20) AS f_custo
    FROM public.detalhe_operacao_orcamento d
    JOIN public.orcamento o ON o.id_orcamento = d.id_orcamento
    JOIN public.projeto p ON p.id_projeto = o.id_projeto
    WHERE o.estado = 'aprovado'
      AND p.estado IN ('em_execucao', 'concluido')
)
INSERT INTO public.realizado_operacao (
    id_linha_operacao,
    data_registo,
    horas,
    tempo_setup_h,
    custo_hora_real,
    custo_total_real,
    observacoes
)
SELECT
    r.id_linha_operacao,
    o.data_criacao + ((2 + (random() * 55)::int) * INTERVAL '1 day'),
    round((r.horas * r.f_horas)::numeric, 2),
    round((r.tempo_setup_h * r.f_setup)::numeric, 2),
    round((r.custo_hora_snapshot * r.f_custo)::numeric, 2),
    round((((r.horas * r.f_horas) + (r.tempo_setup_h * r.f_setup)) * (r.custo_hora_snapshot * r.f_custo))::numeric, 2),
    'Execucao real de operacao.'
FROM ro_base r
JOIN public.orcamento o ON o.id_orcamento = r.id_orcamento;

-- Realizados de servico (com mesmo shock_factor por projeto)
WITH rs_base AS (
    SELECT
        d.id_linha_servico,
        d.id_orcamento,
        d.quantidade,
        d.preco_unitario_snapshot,
        (0.90 + random() * 0.30) *
            CASE
                WHEN p.id_projeto % 41 = 0 THEN 1.40 + random() * 0.50
                WHEN p.id_projeto % 53 = 0 THEN 0.70 + random() * 0.15
                WHEN p.id_projeto % 17 = 0 THEN 1.10 + random() * 0.12
                ELSE 1.0
            END AS f_qtd,
        (0.95 + random() * 0.22) AS f_preco
    FROM public.detalhe_servico_orcamento d
    JOIN public.orcamento o ON o.id_orcamento = d.id_orcamento
    JOIN public.projeto p ON p.id_projeto = o.id_projeto
    WHERE o.estado = 'aprovado'
      AND p.estado IN ('em_execucao', 'concluido')
)
INSERT INTO public.realizado_servico (
    id_linha_servico,
    data_registo,
    quantidade,
    preco_unitario_real,
    custo_total_real,
    observacoes
)
SELECT
    r.id_linha_servico,
    o.data_criacao + ((3 + (random() * 65)::int) * INTERVAL '1 day'),
    round((r.quantidade * r.f_qtd)::numeric, 2),
    round((r.preco_unitario_snapshot * r.f_preco)::numeric, 2),
    round(((r.quantidade * r.f_qtd) * (r.preco_unitario_snapshot * r.f_preco))::numeric, 2),
    'Servico externo realizado.'
FROM rs_base r
JOIN public.orcamento o ON o.id_orcamento = r.id_orcamento;

-- Previsoes ML para a maioria dos orcamentos
INSERT INTO public.previsao_ml (
    id_orcamento,
    data_previsao,
    modelo_utilizado,
    modelo_versao,
    custo_previsto,
    tempo_previsto,
    desvio_esperado_percent,
    inputs_chave,
    observacoes
)
SELECT
    o.id_orcamento,
    o.data_criacao + INTERVAL '2 day',
    'random_forest_orcamento',
    'rf_v1',
    round((o.custo_total_orcado * (0.96 + random() * 0.12))::numeric, 2),
    round((o.horas_totais_previstas * (0.92 + random() * 0.18))::numeric, 2),
    round((2 + random() * 12)::numeric, 2),
    format('peso=%s; pecas=%s; processo=%s', p.peso_total_kg, p.numero_pecas, p.processo_corte),
    'Previsao automatica para analise de desvio.'
FROM public.orcamento o
JOIN public.projeto p ON p.id_projeto = o.id_projeto
WHERE o.estado <> 'cancelado'
  AND random() < 0.80;

-- Validacoes de integridade pedidas
DO $$
DECLARE
    v_total_orc integer;
    v_min_linhas integer;
    v_orc_5k integer;
    v_orc_20k integer;
    v_orc_50k integer;
    v_orc_100k integer;
    v_orc_250k integer;
    v_orc_cancelado_fora_projeto integer;
    v_projetos_ativos_sem_aprovado integer;
    v_projetos_analise_com_aprovado integer;
    v_orc_aco integer;
    v_orc_aluminio integer;
    v_orc_inox integer;
    v_pct_aco numeric;
    v_pct_aluminio numeric;
    v_pct_inox numeric;
BEGIN
    SELECT count(*) INTO v_total_orc FROM public.orcamento;

    SELECT
        count(*) FILTER (WHERE custo_total_orcado BETWEEN 4500 AND 6500),
        count(*) FILTER (WHERE custo_total_orcado BETWEEN 17000 AND 23000),
        count(*) FILTER (WHERE custo_total_orcado BETWEEN 43000 AND 57000),
        count(*) FILTER (WHERE custo_total_orcado BETWEEN 90000 AND 120000),
        count(*) FILTER (WHERE custo_total_orcado BETWEEN 200000 AND 320000)
    INTO v_orc_5k, v_orc_20k, v_orc_50k, v_orc_100k, v_orc_250k
    FROM public.orcamento;

    SELECT min(total_linhas)
    INTO v_min_linhas
    FROM (
        SELECT
            o.id_orcamento,
            COALESCE(m.cnt, 0) + COALESCE(op.cnt, 0) + COALESCE(s.cnt, 0) AS total_linhas
        FROM public.orcamento o
        LEFT JOIN (
            SELECT id_orcamento, count(*) AS cnt
            FROM public.detalhe_material_orcamento
            GROUP BY id_orcamento
        ) m ON m.id_orcamento = o.id_orcamento
        LEFT JOIN (
            SELECT id_orcamento, count(*) AS cnt
            FROM public.detalhe_operacao_orcamento
            GROUP BY id_orcamento
        ) op ON op.id_orcamento = o.id_orcamento
        LEFT JOIN (
            SELECT id_orcamento, count(*) AS cnt
            FROM public.detalhe_servico_orcamento
            GROUP BY id_orcamento
        ) s ON s.id_orcamento = o.id_orcamento
    ) t;

    SELECT count(*)
    INTO v_orc_cancelado_fora_projeto
    FROM public.orcamento o
    JOIN public.projeto p ON p.id_projeto = o.id_projeto
    WHERE o.estado = 'cancelado'
      AND p.estado <> 'cancelado';

    SELECT count(*)
    INTO v_projetos_ativos_sem_aprovado
    FROM public.projeto p
    WHERE p.estado IN ('planeado', 'aprovado', 'em_execucao', 'concluido')
      AND NOT EXISTS (
          SELECT 1
          FROM public.orcamento o
          WHERE o.id_projeto = p.id_projeto
            AND o.estado = 'aprovado'
      );

    SELECT count(*)
    INTO v_projetos_analise_com_aprovado
    FROM public.projeto p
    WHERE p.estado = 'em_analise'
      AND EXISTS (
          SELECT 1
          FROM public.orcamento o
          WHERE o.id_projeto = p.id_projeto
            AND o.estado = 'aprovado'
      );

    SELECT
        count(*) FILTER (WHERE p.material_principal IN ('S235JR', 'S355JR')),
        count(*) FILTER (WHERE p.material_principal IN ('AL6060', 'AL5754')),
        count(*) FILTER (WHERE p.material_principal = 'AISI304')
    INTO v_orc_aco, v_orc_aluminio, v_orc_inox
    FROM public.orcamento o
    JOIN public.projeto p ON p.id_projeto = o.id_projeto;

    v_pct_aco := round((v_orc_aco::numeric / NULLIF(v_total_orc, 0)) * 100, 2);
    v_pct_aluminio := round((v_orc_aluminio::numeric / NULLIF(v_total_orc, 0)) * 100, 2);
    v_pct_inox := round((v_orc_inox::numeric / NULLIF(v_total_orc, 0)) * 100, 2);

    IF v_total_orc < 20000 THEN
        RAISE EXCEPTION 'Seed invalida: total orcamentos = % (esperado >= 20000)', v_total_orc;
    END IF;

    IF v_min_linhas < 15 THEN
        RAISE EXCEPTION 'Seed invalida: minimo linhas por orcamento = % (esperado >= 15)', v_min_linhas;
    END IF;

    IF v_orc_cancelado_fora_projeto > 0 THEN
        RAISE EXCEPTION 'Seed invalida: existem % orcamentos cancelados fora de projetos cancelados', v_orc_cancelado_fora_projeto;
    END IF;

    IF v_projetos_ativos_sem_aprovado > 0 THEN
        RAISE EXCEPTION 'Seed invalida: existem % projetos ativos sem orcamento aprovado', v_projetos_ativos_sem_aprovado;
    END IF;

    IF v_projetos_analise_com_aprovado > 0 THEN
        RAISE EXCEPTION 'Seed invalida: existem % projetos em analise com orcamento aprovado', v_projetos_analise_com_aprovado;
    END IF;

    IF v_pct_aco NOT BETWEEN 69 AND 71
       OR v_pct_aluminio NOT BETWEEN 19 AND 21
       OR v_pct_inox NOT BETWEEN 9 AND 11 THEN
        RAISE EXCEPTION
            'Seed invalida: distribuicao material fora do alvo. aco=% aluminio=% inox=%',
            v_pct_aco, v_pct_aluminio, v_pct_inox;
    END IF;

    IF v_orc_5k < 40 OR v_orc_20k < 40 OR v_orc_50k < 40 OR v_orc_100k < 40 OR v_orc_250k < 40 THEN
        RAISE NOTICE
            'Distribuicao abaixo do alvo (minimo 40 por faixa): 5k=% 20k=% 50k=% 100k=% 250k=%',
            v_orc_5k, v_orc_20k, v_orc_50k, v_orc_100k, v_orc_250k;
    END IF;
END $$;

COMMIT;

-- Resumo rapido
SELECT 'orcamentos' AS metrica, count(*)::text AS valor FROM public.orcamento
UNION ALL
SELECT 'linhas_materiais', count(*)::text FROM public.detalhe_material_orcamento
UNION ALL
SELECT 'linhas_operacoes', count(*)::text FROM public.detalhe_operacao_orcamento
UNION ALL
SELECT 'linhas_servicos', count(*)::text FROM public.detalhe_servico_orcamento
UNION ALL
SELECT 'realizado_material', count(*)::text FROM public.realizado_material
UNION ALL
SELECT 'realizado_operacao', count(*)::text FROM public.realizado_operacao
UNION ALL
SELECT 'realizado_servico', count(*)::text FROM public.realizado_servico;

SELECT
    min(t.total_linhas) AS min_linhas_por_orcamento,
    max(t.total_linhas) AS max_linhas_por_orcamento,
    round(avg(t.total_linhas)::numeric, 2) AS media_linhas_por_orcamento
FROM (
    SELECT
        o.id_orcamento,
        COALESCE(m.cnt, 0) + COALESCE(op.cnt, 0) + COALESCE(s.cnt, 0) AS total_linhas
    FROM public.orcamento o
    LEFT JOIN (SELECT id_orcamento, count(*) AS cnt FROM public.detalhe_material_orcamento GROUP BY id_orcamento) m
        ON m.id_orcamento = o.id_orcamento
    LEFT JOIN (SELECT id_orcamento, count(*) AS cnt FROM public.detalhe_operacao_orcamento GROUP BY id_orcamento) op
        ON op.id_orcamento = o.id_orcamento
    LEFT JOIN (SELECT id_orcamento, count(*) AS cnt FROM public.detalhe_servico_orcamento GROUP BY id_orcamento) s
        ON s.id_orcamento = o.id_orcamento
) t;

SELECT
    p.estado AS estado_projeto,
    o.estado AS estado_orcamento,
    count(*) AS total_orcamentos
FROM public.orcamento o
JOIN public.projeto p ON p.id_projeto = o.id_projeto
GROUP BY p.estado, o.estado
ORDER BY p.estado, o.estado;

SELECT
    CASE
        WHEN p.material_principal IN ('S235JR', 'S355JR') THEN 'aco'
        WHEN p.material_principal IN ('AL6060', 'AL5754') THEN 'aluminio'
        WHEN p.material_principal = 'AISI304' THEN 'inox'
        ELSE 'outro'
    END AS familia_material,
    p.material_principal,
    count(*) AS total_orcamentos,
    round((count(*)::numeric / sum(count(*)) OVER ()) * 100, 2) AS percentagem
FROM public.orcamento o
JOIN public.projeto p ON p.id_projeto = o.id_projeto
GROUP BY 1, p.material_principal
ORDER BY 1, p.material_principal;

SELECT
    p.tratamento_superficie,
    count(*) AS total_orcamentos
FROM public.orcamento o
JOIN public.projeto p ON p.id_projeto = o.id_projeto
GROUP BY p.tratamento_superficie
ORDER BY p.tratamento_superficie;

SELECT
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 4500 AND 6500) AS orcamentos_faixa_5k,
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 17000 AND 23000) AS orcamentos_faixa_20k,
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 43000 AND 57000) AS orcamentos_faixa_50k,
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 90000 AND 120000) AS orcamentos_faixa_100k,
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 200000 AND 320000) AS orcamentos_faixa_250k,
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 5000 AND 75000) AS orcamentos_entre_5k_75k,
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 75000 AND 200000) AS orcamentos_entre_75k_200k,
    count(*) FILTER (WHERE custo_total_orcado > 200000) AS orcamentos_acima_200k
FROM public.orcamento;

-- Diagnostico de realismo por unidade de material
SELECT
    m.unidade,
    round(avg(dm.quantidade)::numeric, 2) AS qtd_media,
    round(avg(COALESCE(dm.peso_kg, 0))::numeric, 2) AS peso_medio,
    round(
        avg(
            CASE
                WHEN dm.quantidade > 0 AND dm.peso_kg IS NOT NULL THEN dm.peso_kg / dm.quantidade
                ELSE NULL
            END
        )::numeric,
        3
    ) AS peso_por_unidade_medio
FROM public.detalhe_material_orcamento dm
JOIN public.material m ON m.id_material = dm.id_material
GROUP BY m.unidade
ORDER BY m.unidade;

-- Diagnostico de relacao peso/custo ao nivel do projeto
SELECT
    round(min(ratio_kg_por_euro)::numeric, 4) AS min_kg_por_euro,
    round(percentile_cont(0.25) WITHIN GROUP (ORDER BY ratio_kg_por_euro)::numeric, 4) AS p25_kg_por_euro,
    round(percentile_cont(0.50) WITHIN GROUP (ORDER BY ratio_kg_por_euro)::numeric, 4) AS mediana_kg_por_euro,
    round(percentile_cont(0.75) WITHIN GROUP (ORDER BY ratio_kg_por_euro)::numeric, 4) AS p75_kg_por_euro,
    round(max(ratio_kg_por_euro)::numeric, 4) AS max_kg_por_euro
FROM (
    SELECT
        p.id_projeto,
        CASE
            WHEN o.custo_total_orcado > 0 THEN p.peso_total_kg / o.custo_total_orcado
            ELSE NULL
        END AS ratio_kg_por_euro
    FROM public.projeto p
    JOIN public.orcamento o
        ON o.id_projeto = p.id_projeto
       AND o.versao = 'v1'
) t;
