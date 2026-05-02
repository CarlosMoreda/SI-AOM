-- Reset + seed massiva para SI-AOM
-- Objetivos:
-- 1) Apagar todos os dados
-- 2) Criar dados base realistas (materiais, operacoes, servicos)
-- 3) Criar >= 500 orcamentos
-- 4) Garantir >= 15 linhas por orcamento (8 materiais + 5 operacoes + 2 servicos)
-- 5) Popular tabelas de realizados
-- 6) Distribuir custos em torno de 5k / 20k / 50k / 70k + valores dispersos

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

-- Utilizadores base (passwords em texto para login):
-- admin@siaom.local    -> Admin@123
-- gestor@siaom.local   -> Gestor@123
-- orc@siaom.local      -> Orc@123
-- producao@siaom.local -> Prod@123
INSERT INTO public.utilizador (nome, email, password_hash, perfil, ativo)
VALUES
    ('Administrador SI-AOM', 'admin@siaom.local', '$2b$12$h1oVlIzipBQoxaVuiJq/Vur7tTcZxjzfEFk0Rh5QKr5I5tOX3ZKXK', 'administrador', true),
    ('Gestor Fabrico', 'gestor@siaom.local', '$2b$12$St0lCdIfTqz71VTcJtKAaOEnKISvhOd5T0dYepb2izPnXvYJ/K5iW', 'gestor', true),
    ('Orcamentista Senior', 'orc@siaom.local', '$2b$12$qNq.28u.aCdWnmZcrEr2j.FQLzAEVBlbACxX8huTjEg7T6nb4n82O', 'orcamentista', true),
    ('Tecnico Producao', 'producao@siaom.local', '$2b$12$l/xbsoY90.X9qtaJqVpPyeQnKpRPzs457qDYwf/3pQ3j5LyoWsEta', 'producao', true);

INSERT INTO public.cliente (nome, nif, email, telefone, morada, observacoes, ativo)
SELECT
    format('Cliente %s Metalworks', gs),
    lpad((200000000 + gs)::text, 9, '0'),
    format('compras%02s@cliente.pt', gs),
    format('+351 91%07s', lpad((gs * 271)::text, 7, '0')),
    format('Zona Industrial Lote %s, Portugal', gs),
    'Cliente gerado automaticamente para seed.',
    true
FROM generate_series(1, 35) AS gs;

INSERT INTO public.material (codigo, nome, unidade, tipo, custo_unitario_default, ativo, qualidade_material)
VALUES
    ('MAT-TUBO-20X20X2', 'Tubo 20x20x2 S275JR', 'm', 'tubo', 6.2000, true, 'S275JR'),
    ('MAT-TUBO-30X30X2', 'Tubo 30x30x2 S275JR', 'm', 'tubo', 7.8000, true, 'S275JR'),
    ('MAT-TUBO-40X40X3', 'Tubo 40x40x3 S275JR', 'm', 'tubo', 12.4000, true, 'S275JR'),
    ('MAT-TUBO-60X40X3', 'Tubo 60x40x3 S275JR', 'm', 'tubo', 14.9000, true, 'S275JR'),
    ('MAT-CHAPA-3MM', 'Chapa S275JR 3mm', 'kg', 'chapa', 1.4500, true, 'S275JR'),
    ('MAT-CHAPA-5MM', 'Chapa S275JR 5mm', 'kg', 'chapa', 1.6200, true, 'S275JR'),
    ('MAT-CHAPA-8MM', 'Chapa S275JR 8mm', 'kg', 'chapa', 1.8800, true, 'S275JR'),
    ('MAT-PERFIL-UPN120', 'Perfil UPN 120', 'm', 'perfil', 13.5000, true, 'S275JR'),
    ('MAT-PERFIL-IPE160', 'Perfil IPE 160', 'm', 'perfil', 19.4000, true, 'S275JR'),
    ('MAT-CANT-50X5', 'Cantoneira 50x5', 'm', 'perfil', 4.9000, true, 'S275JR'),
    ('MAT-PLAT-80X8', 'Platina 80x8', 'm', 'perfil', 7.1000, true, 'S275JR'),
    ('MAT-HEA200', 'Perfil HEA 200', 'm', 'perfil', 42.5000, true, 'S355JR'),
    ('MAT-HEB240', 'Perfil HEB 240', 'm', 'perfil', 58.9000, true, 'S355JR'),
    ('MAT-PARAF-M16', 'Parafuso sextavado M16', 'un', 'fixacao', 0.6500, true, '8.8 zincado'),
    ('MAT-ANCORA-M20', 'Chumbador quimico M20', 'un', 'fixacao', 3.2000, true, 'A4'),
    ('MAT-REDE-MESH', 'Rede eletrossoldada 100x100', 'm2', 'malha', 5.8000, true, 'B500'),
    ('MAT-TUBO-INOX-30X2', 'Tubo inox 30x2 AISI304', 'm', 'tubo', 14.8000, true, 'AISI304'),
    ('MAT-GRIT-SA25', 'Abrasivo jateamento SA2.5', 'kg', 'consumivel', 0.4200, true, 'G25'),
    ('MAT-PRIM-EPOXI', 'Primario epoxi rico em zinco', 'kg', 'pintura', 4.2000, true, 'Classe C4'),
    ('MAT-TINTA-PU', 'Tinta acabamento PU', 'kg', 'pintura', 7.9000, true, 'RAL variavel'),
    ('MAT-ARAME-MAG10', 'Arame MAG 1.0mm', 'kg', 'consumivel', 3.6000, true, 'ER70S-6'),
    ('MAT-GAS-M21', 'Gas mistura M21', 'm3', 'consumivel', 2.8500, true, 'M21'),
    ('MAT-DISCO-125', 'Disco corte 125mm', 'un', 'consumivel', 1.1000, true, 'Inox/aco'),
    ('MAT-ELET-7018', 'Eletrodo E7018', 'kg', 'consumivel', 4.4000, true, 'E7018');

INSERT INTO public.operacao (codigo, nome, categoria, custo_hora_default, setup_hora_default, ativo)
VALUES
    ('OP-CORTE-LASER', 'Corte laser CNC', 'corte', 42.00, 0.50, true),
    ('OP-CORTE-SERRA', 'Corte em serra de fita', 'corte', 29.00, 0.30, true),
    ('OP-FURACAO', 'Furacao e escareacao', 'usinagem', 31.00, 0.25, true),
    ('OP-QUINAGEM', 'Quinagem CNC', 'conformacao', 45.00, 0.60, true),
    ('OP-CALANDRAGEM', 'Calandragem', 'conformacao', 48.00, 0.75, true),
    ('OP-SOLD-MIG', 'Soldadura MIG/MAG', 'soldadura', 38.00, 0.50, true),
    ('OP-SOLD-TIG', 'Soldadura TIG', 'soldadura', 46.00, 0.50, true),
    ('OP-PINGAMENTO', 'Pingamento e acabamento de solda', 'acabamento', 34.00, 0.40, true),
    ('OP-JATEAMENTO', 'Jateamento SA2.5', 'acabamento', 32.00, 0.35, true),
    ('OP-PINTURA-LIQ', 'Pintura liquida PU', 'acabamento', 30.00, 0.45, true),
    ('OP-MONTAGEM', 'Montagem em bancada', 'montagem', 28.00, 0.25, true),
    ('OP-QA', 'Controlo dimensional e QA', 'qualidade', 26.00, 0.20, true);

INSERT INTO public.servico (codigo, nome, unidade, preco_unitario_default, ativo)
VALUES
    ('SVC-GALV-HOT', 'Galvanizacao a quente', 'kg', 1.25, true),
    ('SVC-ZINCAGEM', 'Zincagem eletrolitica', 'kg', 0.95, true),
    ('SVC-TRANSPORTE', 'Transporte nacional', 'viag', 380.00, true),
    ('SVC-GRUAS', 'Aluguer de grua 40T', 'dia', 920.00, true),
    ('SVC-END', 'Ensaios nao destrutivos (LP/UT)', 'hora', 68.00, true),
    ('SVC-CORTE-EXT', 'Corte plasma externo', 'hora', 74.00, true),
    ('SVC-METALIZACAO', 'Metalizacao por arco', 'm2', 22.00, true),
    ('SVC-PINT-PO', 'Pintura a po externa', 'm2', 14.50, true),
    ('SVC-EMBALAGEM', 'Embalagem e acondicionamento', 'lote', 240.00, true),
    ('SVC-CERT-1090', 'Certificacao EN1090', 'lote', 650.00, true);

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
    format('PRJ-2026-%s', lpad(gs::text, 3, '0')),
    CASE (gs % 6)
        WHEN 0 THEN format('Pavilhao industrial modulo %s', gs)
        WHEN 1 THEN format('Passadico metalico lote %s', gs)
        WHEN 2 THEN format('Estrutura cobertura logistica %s', gs)
        WHEN 3 THEN format('Mezanino industrial fase %s', gs)
        WHEN 4 THEN format('Plataforma tecnica setor %s', gs)
        ELSE format('Escadaria e guardas projeto %s', gs)
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
        WHEN gs % 7 = 0 THEN 'em_execucao'
        WHEN gs % 5 = 0 THEN 'planeado'
        ELSE 'em_analise'
    END,
    (DATE '2026-01-01' + ((gs * 5) % 180)),
    (DATE '2026-01-01' + ((gs * 5) % 180) + (45 + (gs % 70))),
    round((800 + random() * 34200)::numeric, 2),
    (25 + (random() * 420)::int),
    CASE
        WHEN gs % 4 = 0 THEN 'alta'
        WHEN gs % 3 = 0 THEN 'media'
        ELSE 'baixa'
    END,
    CASE
        WHEN gs % 5 = 0 THEN 'S355JR'
        WHEN gs % 3 = 0 THEN 'AISI304'
        ELSE 'S275JR'
    END,
    CASE
        WHEN gs % 4 = 0 THEN 'galvanizacao'
        WHEN gs % 3 = 0 THEN 'pintura_pu'
        ELSE 'jateamento_pintura'
    END,
    CASE
        WHEN gs % 2 = 0 THEN 'laser'
        ELSE 'serra'
    END,
    (20 + (gs % 45)),
    format('Projeto seedado automaticamente. Faixa estrutural realista 0.8k-35k kg. Item %s.', gs),
    CASE
        WHEN gs % 6 = 0 THEN 2
        WHEN gs % 5 = 0 THEN 4
        ELSE 1
    END,
    ((gs - 1) % 35) + 1
FROM generate_series(1, 170) AS gs;

-- 170 projetos x 3 versoes = 510 orcamentos
WITH versoes AS (
    SELECT
        p.id_projeto,
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
    CURRENT_TIMESTAMP - ((170 - id_projeto) * INTERVAL '1 day') - (versao_num * INTERVAL '3 day'),
    CASE
        WHEN versao_num = 1 THEN 'aprovado'
        WHEN versao_num = 2 THEN 'em_revisao'
        ELSE 'rascunho'
    END,
    round((14 + random() * 22)::numeric, 2),
    format('Orcamento %s do projeto %s - estrutura metalica.', versao, id_projeto)
FROM versoes
ORDER BY id_projeto, versao_num;

-- 8 linhas de material por orcamento
WITH mat_count AS (
    SELECT count(*)::int AS total FROM public.material
),
mat_picks AS (
    SELECT
        o.id_orcamento,
        gs.idx,
        ((o.id_orcamento * 11 + gs.idx * 7) % mc.total + 1)::int AS id_material
    FROM public.orcamento o
    CROSS JOIN mat_count mc
    CROSS JOIN generate_series(1, 8) AS gs(idx)
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
            WHEN 'MAT-TUBO-20X20X2' THEN 1.16
            WHEN 'MAT-TUBO-30X30X2' THEN 1.79
            WHEN 'MAT-TUBO-40X40X3' THEN 3.55
            WHEN 'MAT-TUBO-60X40X3' THEN 4.33
            WHEN 'MAT-PERFIL-UPN120' THEN 13.40
            WHEN 'MAT-PERFIL-IPE160' THEN 15.80
            WHEN 'MAT-CANT-50X5' THEN 3.77
            WHEN 'MAT-PLAT-80X8' THEN 5.02
            WHEN 'MAT-HEA200' THEN 42.30
            WHEN 'MAT-HEB240' THEN 93.00
            WHEN 'MAT-TUBO-INOX-30X2' THEN 1.41
            ELSE 4.50
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
            WHEN op.categoria = 'soldadura' THEN round((18 + random() * 102)::numeric, 2)
            WHEN op.categoria = 'corte' THEN round((10 + random() * 55)::numeric, 2)
            WHEN op.categoria = 'acabamento' THEN round((8 + random() * 47)::numeric, 2)
            ELSE round((6 + random() * 44)::numeric, 2)
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
WITH svc_count AS (
    SELECT count(*)::int AS total FROM public.servico
),
svc_picks AS (
    SELECT
        o.id_orcamento,
        gs.idx,
        ((o.id_orcamento * 17 + gs.idx * 3) % sc.total + 1)::int AS id_servico
    FROM public.orcamento o
    CROSS JOIN svc_count sc
    CROSS JOIN generate_series(1, 2) AS gs(idx)
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
--   * mat_eur_per_kg: 1.55 (S275JR) ate 5.80 (AISI304)
--   * trat_eur_per_kg: 0.42 (jateamento) ate 0.85 (galvanizacao)
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
                WHEN 'S355JR'  THEN 1.85
                ELSE                1.55
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
                WHEN 'laser' THEN 1.10
                ELSE              1.00
              END
            * (1.0 + (p.numero_pecas::numeric * 0.0008))  -- mais pecas = mais montagem
            * (0.90 + random() * 0.20)
        )::numeric, 2)
    ) AS target_operacoes,
    -- Servicos: peso x EUR/kg(tratamento) x ruido
    GREATEST(200::numeric,
        round((p.peso_total_kg
            * CASE p.tratamento_superficie
                WHEN 'galvanizacao'      THEN 0.85
                WHEN 'pintura_pu'        THEN 0.55
                WHEN 'jateamento_pintura' THEN 0.42
                ELSE                          0.42
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

-- Realizados de material
WITH rm_base AS (
    SELECT
        d.id_linha_material,
        d.id_orcamento,
        d.quantidade,
        d.peso_kg,
        d.preco_unitario_snapshot,
        (0.95 + random() * 0.16) AS f_qtd,
        (0.97 + random() * 0.22) AS f_preco
    FROM public.detalhe_material_orcamento d
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

-- Realizados de operacao
WITH ro_base AS (
    SELECT
        d.id_linha_operacao,
        d.id_orcamento,
        d.horas,
        d.tempo_setup_h,
        d.custo_hora_snapshot,
        (0.90 + random() * 0.25) AS f_horas,
        (0.90 + random() * 0.30) AS f_setup,
        (0.95 + random() * 0.20) AS f_custo
    FROM public.detalhe_operacao_orcamento d
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
    'Execucao real de operacao (soldadura/pingamento/corte).'
FROM ro_base r
JOIN public.orcamento o ON o.id_orcamento = r.id_orcamento;

-- Realizados de servico
WITH rs_base AS (
    SELECT
        d.id_linha_servico,
        d.id_orcamento,
        d.quantidade,
        d.preco_unitario_snapshot,
        (0.90 + random() * 0.30) AS f_qtd,
        (0.95 + random() * 0.22) AS f_preco
    FROM public.detalhe_servico_orcamento d
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
WHERE random() < 0.80;

-- Validacoes de integridade pedidas
DO $$
DECLARE
    v_total_orc integer;
    v_min_linhas integer;
    v_orc_5k integer;
    v_orc_20k integer;
    v_orc_50k integer;
    v_orc_70k integer;
BEGIN
    SELECT count(*) INTO v_total_orc FROM public.orcamento;

    SELECT
        count(*) FILTER (WHERE custo_total_orcado BETWEEN 4500 AND 6500),
        count(*) FILTER (WHERE custo_total_orcado BETWEEN 17000 AND 23000),
        count(*) FILTER (WHERE custo_total_orcado BETWEEN 43000 AND 57000),
        count(*) FILTER (WHERE custo_total_orcado BETWEEN 60000 AND 78000)
    INTO v_orc_5k, v_orc_20k, v_orc_50k, v_orc_70k
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

    IF v_total_orc < 500 THEN
        RAISE EXCEPTION 'Seed invalida: total orcamentos = % (esperado >= 500)', v_total_orc;
    END IF;

    IF v_min_linhas < 15 THEN
        RAISE EXCEPTION 'Seed invalida: minimo linhas por orcamento = % (esperado >= 15)', v_min_linhas;
    END IF;

    IF v_orc_5k < 40 OR v_orc_20k < 40 OR v_orc_50k < 40 OR v_orc_70k < 40 THEN
        RAISE NOTICE
            'Distribuicao abaixo do alvo (minimo 40 por faixa): 5k=% 20k=% 50k=% 70k=%',
            v_orc_5k, v_orc_20k, v_orc_50k, v_orc_70k;
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
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 4500 AND 6500) AS orcamentos_faixa_5k,
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 17000 AND 23000) AS orcamentos_faixa_20k,
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 43000 AND 57000) AS orcamentos_faixa_50k,
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 60000 AND 78000) AS orcamentos_faixa_70k,
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 5000 AND 75000) AS orcamentos_entre_5k_75k
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
