-- Reset + seed massiva para SI-AOM
-- Objetivos:
-- 1) Apagar todos os dados
-- 2) Criar dados base realistas (catalogos amplos de materiais, operacoes, servicos)
-- 3) Criar ~5250 orcamentos: 95% dos projetos so v1, 5% com v1+v2
-- 4) Garantir >= 15 linhas por orcamento (8 materiais + 5 operacoes + 2 servicos)
-- 5) Popular tabelas de realizados (apenas para projetos em execucao/concluidos)
-- 6) Cap de custo: nenhum orcamento ultrapassa 50.000 EUR
-- 7) Espalhar datas por 3 anos (2024-2026) com coerencia entre estado e idade
-- 8) Introduzir outliers realistas nos realizados (~10% derrapas/folgas anormais)

-- Se a sessao anterior ficou em erro, limpa o estado antes de iniciar.
ROLLBACK;
BEGIN;

-- Evita conflito ao reexecutar o script na mesma sessao SQL.
DROP TABLE IF EXISTS tmp_orcamento_scale;
DROP TABLE IF EXISTS tmp_orcamento_target;
DROP TABLE IF EXISTS tmp_orcamento_target_raw;

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

-- Utilizadores base (password em texto apenas para ambiente seed/dev):
-- admin@siaom.com        -> password: admin
-- gestor@siaom.com       -> password: gestor
-- orcamentista@siaom.com -> password: orcamentista
-- producao@siaom.com     -> password: producao
INSERT INTO public.utilizador (nome, email, password_hash, perfil, ativo)
VALUES
    -- password: admin
    ('Admin', 'admin@siaom.com', '$2b$12$GgVp5e4zbPMGs9pcH/Qo6.cr8eukcYDysakisK1vVvnt04ac0cZc2', 'administrador', true),
    -- password: gestor
    ('Gestor', 'gestor@siaom.com', '$2b$12$g0kRJndOBN9k8qZp/NfOtOBXiskkWajczcgjgEs9Knw51TKJcZEc.', 'gestor', true),
    -- password: orcamentista
    ('Orçamentista', 'orcamentista@siaom.com', '$2b$12$Ccff3YcLJLStVXq9eM6IS.gkQ4rF8pmrl4tXJp1CFD4D3Xvkfice.', 'orcamentista', true),
    -- password: producao
    ('Produção', 'producao@siaom.com', '$2b$12$m0pQuMG1MPmfpFJk9Yflyei1elP5/tgZefV84.F/xkk0AuF9pOgTi', 'producao', true);

INSERT INTO public.cliente (nome, nif, email, telefone, morada, observacoes, ativo)
WITH cliente_base (ord, nome_base, dominio, zona, concelho, segmento) AS (
    VALUES
        (1,  'Metalúrgica Vale do Ave',        'metalave.pt',        'Zona Industrial de Celeiros',        'Braga',          'Metalomecânica e estruturas ligeiras'),
        (2,  'Serralharia Técnica Minho',      'serralhariaminho.pt','Parque Empresarial de Gualtar',      'Braga',          'Serralharia técnica para indústria'),
        (3,  'Construções Atlântico Norte',    'constratlantico.pt', 'Zona Industrial da Maia I',          'Maia',           'Construção civil e obras metálicas'),
        (4,  'Engenharia Modular Centro',      'modularcentro.pt',   'Zona Industrial de Taveiro',         'Coimbra',        'Módulos industriais e plataformas'),
        (5,  'Logística Tejo Sul',             'logisticatejo.pt',   'Parque Industrial do Seixal',        'Seixal',         'Logística, armazéns e manutenção'),
        (6,  'Equipamentos Industriais Oeste', 'eioeste.pt',         'Zona Industrial das Caldas',         'Caldas da Rainha','Equipamentos e linhas de produção'),
        (7,  'Infraestruturas Ribatejo',       'infraribatejo.pt',   'Zona Industrial de Santarém',        'Santarém',       'Obras públicas e infraestruturas'),
        (8,  'Manutenção Fabril Douro',        'mfdouro.pt',         'Zona Industrial de Lordelo',         'Paredes',        'Manutenção fabril e acessos técnicos'),
        (9,  'Alumínios Costa Verde',          'alucostaverde.pt',   'Zona Industrial de Ovar',            'Ovar',           'Caixilharia técnica e alumínio'),
        (10, 'Inox Marinha Grande',            'inoxmg.pt',          'Zona Industrial da Marinha Grande',  'Marinha Grande', 'Componentes inox para indústria'),
        (11, 'Obras Industriais Lisboa',       'oil.pt',             'Parque Empresarial de Loures',       'Loures',         'Empreitadas industriais'),
        (12, 'Tecnometal Setúbal',             'tecnometalsetubal.pt','Zona Industrial da Mitrena',        'Setúbal',        'Estruturas metálicas pesadas'),
        (13, 'Energia e Processos Alentejo',   'epalentejo.pt',      'Zona Industrial de Beja',            'Beja',           'Energia, processo e suportes metálicos'),
        (14, 'Madeira Industrial Norte',       'minorte.pt',         'Zona Industrial do Caniçal',         'Machico',        'Indústria e manutenção insular'),
        (15, 'Acessos Metálicos Algarve',      'amalgarve.pt',       'Parque Empresarial de Loulé',        'Loulé',          'Escadas, passarelas e guarda-corpos'),
        (16, 'Fábrica Modular Mondego',        'fmm.pt',             'Zona Industrial da Figueira da Foz', 'Figueira da Foz','Fabrico modular e mezaninos'),
        (17, 'Portões e Gradeamentos Norte',   'pgnorte.pt',         'Zona Industrial de Vila Verde',      'Vila Verde',     'Portões, gradeamentos e corrimãos'),
        (18, 'Passarelas Técnicas Lusitânia',  'passarelaslus.pt',   'Parque Industrial de Viseu',         'Viseu',          'Passarelas, passerelles e acessos'),
        (19, 'Guardas e Corrimãos Atlântico',  'gcatlantico.pt',     'Zona Industrial de Perafita',        'Matosinhos',     'Guarda-corpos, corrimãos e proteções'),
        (20, 'Coberturas Metálicas Centro',    'coberturascentro.pt','Zona Industrial de Leiria',          'Leiria',         'Coberturas e estruturas de apoio'),
        (21, 'Plataformas Industriais Aveiro', 'piaveiro.pt',        'Zona Industrial de Taboeira',        'Aveiro',         'Plataformas técnicas e manutenção'),
        (22, 'Mezaninos e Estruturas Sul',     'mesul.pt',           'Zona Industrial de Palmela',         'Palmela',        'Mezaninos e estruturas industriais'),
        (23, 'Metalworks Export Portugal',     'metalworksexport.pt','Parque Industrial de Vila Nova',     'Famalicão',      'Subcontratação metalomecânica exportadora'),
        (24, 'Serviços Técnicos Industriais',  'stiportugal.pt',     'Zona Industrial de Albergaria',      'Albergaria-a-Velha','Serviços técnicos e montagem')
),
cliente_indexado AS (
    SELECT
        row_number() OVER (ORDER BY ord) AS idx,
        count(*) OVER () AS total,
        nome_base,
        dominio,
        zona,
        concelho,
        segmento
    FROM cliente_base
)
SELECT
    CASE
        WHEN ((gs - 1) / ci.total) = 0 THEN ci.nome_base
        ELSE format('%s - Filial %s', ci.nome_base, 1 + ((gs - 1) / ci.total))
    END,
    (500000000 + gs)::text,
    format(
        '%s.%s@%s',
        CASE
            WHEN gs % 4 = 0 THEN 'orcamentos'
            WHEN gs % 4 = 1 THEN 'compras'
            WHEN gs % 4 = 2 THEN 'engenharia'
            ELSE 'aprovisionamento'
        END,
        lpad(gs::text, 3, '0'),
        ci.dominio
    ),
    format('+351 2%s %s %s', 1 + (gs % 8), lpad(((gs * 37) % 1000)::text, 3, '0'), lpad(((gs * 91) % 1000)::text, 3, '0')),
    format('%s, Lote %s, %s, Portugal', ci.zona, 1 + (gs % 80), ci.concelho),
    format('%s. Cliente com compras recorrentes de estruturas metálicas, acessos técnicos e manutenção industrial.', ci.segmento),
    true
FROM generate_series(1, 350) AS gs
JOIN cliente_indexado ci ON ci.idx = ((gs - 1) % ci.total) + 1;

INSERT INTO public.material (codigo, nome, unidade, tipo, custo_unitario_default, ativo, qualidade_material)
VALUES
    -- Tubos S235JR quadrados (do mais pequeno ao maior)
    ('TQ20-S235',   'Tubo quadrado 20x20x2 S235JR',   'm', 'tubo', 5.2000,  true, 'S235JR'),
    ('TQ25-S235',   'Tubo quadrado 25x25x2 S235JR',   'm', 'tubo', 6.2000,  true, 'S235JR'),
    ('TQ30-S235',   'Tubo quadrado 30x30x2 S235JR',   'm', 'tubo', 7.2000,  true, 'S235JR'),
    ('TQ35-S235',   'Tubo quadrado 35x35x2 S235JR',   'm', 'tubo', 8.5000,  true, 'S235JR'),
    ('TQ40-S235',   'Tubo quadrado 40x40x2 S235JR',   'm', 'tubo', 9.8000,  true, 'S235JR'),
    ('TQ40-3-S235', 'Tubo quadrado 40x40x3 S235JR',   'm', 'tubo', 11.2000, true, 'S235JR'),
    ('TQ45-S235',   'Tubo quadrado 45x45x3 S235JR',   'm', 'tubo', 12.8000, true, 'S235JR'),
    ('TQ50-S235',   'Tubo quadrado 50x50x3 S235JR',   'm', 'tubo', 14.5000, true, 'S235JR'),
    ('TQ60-S235',   'Tubo quadrado 60x60x3 S235JR',   'm', 'tubo', 17.2000, true, 'S235JR'),
    ('TQ70-S235',   'Tubo quadrado 70x70x4 S235JR',   'm', 'tubo', 26.5000, true, 'S235JR'),
    ('TQ80-S235',   'Tubo quadrado 80x80x4 S235JR',   'm', 'tubo', 30.5000, true, 'S235JR'),
    ('TQ100-S235',  'Tubo quadrado 100x100x5 S235JR', 'm', 'tubo', 47.5000, true, 'S235JR'),
    -- Tubos S235JR retangulares
    ('TR50-S235',   'Tubo retangular 50x30x2 S235JR',  'm', 'tubo', 11.5000, true, 'S235JR'),
    ('TR60-S235',   'Tubo retangular 60x40x3 S235JR',  'm', 'tubo', 14.5000, true, 'S235JR'),
    ('TR80-S235',   'Tubo retangular 80x40x3 S235JR',  'm', 'tubo', 18.5000, true, 'S235JR'),
    ('TR100-S235',  'Tubo retangular 100x50x4 S235JR', 'm', 'tubo', 28.5000, true, 'S235JR'),
    ('TR120-S235',  'Tubo retangular 120x60x4 S235JR', 'm', 'tubo', 34.5000, true, 'S235JR'),
    -- Tubos S235JR redondos
    ('RD21-S235',    'Tubo redondo 21.3x2 S235JR',      'm', 'tubo', 4.8000,  true, 'S235JR'),
    ('RD27-S235',    'Tubo redondo 26.9x3 S235JR',      'm', 'tubo', 6.2000,  true, 'S235JR'),
    ('RD33-S235',    'Tubo redondo 33.7x3 S235JR',      'm', 'tubo', 7.8000,  true, 'S235JR'),
    -- Tubos S355JR quadrados e retangulares (alta resistencia)
    ('TQ35-S355',   'Tubo quadrado 35x35x3 S355JR',    'm', 'tubo', 12.5000, true, 'S355JR'),
    ('TQ45-S355',   'Tubo quadrado 45x45x4 S355JR',    'm', 'tubo', 18.5000, true, 'S355JR'),
    ('TQ50-S355',   'Tubo quadrado 50x50x3 S355JR',    'm', 'tubo', 15.9000, true, 'S355JR'),
    ('TQ60-S355',   'Tubo quadrado 60x60x3 S355JR',    'm', 'tubo', 19.5000, true, 'S355JR'),
    ('TQ70-S355',   'Tubo quadrado 70x70x4 S355JR',    'm', 'tubo', 28.8000, true, 'S355JR'),
    ('TQ80-S355',   'Tubo quadrado 80x80x5 S355JR',    'm', 'tubo', 38.2000, true, 'S355JR'),
    ('TQ100-S355',  'Tubo quadrado 100x100x6 S355JR',  'm', 'tubo', 56.5000, true, 'S355JR'),
    ('TR80-S355',   'Tubo retangular 80x40x3 S355JR',  'm', 'tubo', 18.7000, true, 'S355JR'),
    ('TR100-S355',  'Tubo retangular 100x50x4 S355JR', 'm', 'tubo', 29.4000, true, 'S355JR'),
    ('TR120-S355',  'Tubo retangular 120x80x5 S355JR', 'm', 'tubo', 47.5000, true, 'S355JR'),
    ('TR150-S355',  'Tubo retangular 150x100x6 S355JR','m', 'tubo', 72.5000, true, 'S355JR'),
    -- Tubos S355JR redondos
    ('RD48-S355',    'Tubo redondo 48.3x3.2 S355JR',    'm', 'tubo', 12.6000, true, 'S355JR'),
    ('RD60-S355',    'Tubo redondo 60.3x3.6 S355JR',    'm', 'tubo', 17.5000, true, 'S355JR'),
    ('RD89-S355',    'Tubo redondo 88.9x4 S355JR',      'm', 'tubo', 28.5000, true, 'S355JR'),
    -- Tubos AISI304 (inox)
    ('TQ20-304', 'Tubo quadrado inox 20x20x2 AISI 304',  'm', 'tubo', 11.2000, true, 'AISI304'),
    ('TQ25-304', 'Tubo quadrado inox 25x25x2 AISI 304',  'm', 'tubo', 14.5000, true, 'AISI304'),
    ('TQ30-304', 'Tubo quadrado inox 30x30x2 AISI 304',  'm', 'tubo', 18.6000, true, 'AISI304'),
    ('TQ40-304', 'Tubo quadrado inox 40x40x2 AISI 304',  'm', 'tubo', 22.8000, true, 'AISI304'),
    ('TQ50-304', 'Tubo quadrado inox 50x50x3 AISI 304',  'm', 'tubo', 38.5000, true, 'AISI304'),
    ('TQ60-304', 'Tubo quadrado inox 60x60x3 AISI 304',  'm', 'tubo', 45.5000, true, 'AISI304'),
    ('TR50-304', 'Tubo retangular inox 50x30x2 AISI 304','m', 'tubo', 24.8000, true, 'AISI304'),
    ('TR80-304', 'Tubo retangular inox 80x40x3 AISI 304','m', 'tubo', 41.5000, true, 'AISI304'),
    -- Tubos AL6060 (alumínio)
    ('TQ20-AL',  'Tubo quadrado alumínio 20x20x2 6060',  'm', 'tubo', 5.8000,  true, 'AL6060'),
    ('TQ25-AL',  'Tubo quadrado alumínio 25x25x2 6060',  'm', 'tubo', 7.2000,  true, 'AL6060'),
    ('TQ30-AL',  'Tubo quadrado alumínio 30x30x2 6060',  'm', 'tubo', 8.9000,  true, 'AL6060'),
    ('TQ40-AL',  'Tubo quadrado alumínio 40x40x2 6060',  'm', 'tubo', 10.5000, true, 'AL6060'),
    ('TQ40-3AL', 'Tubo quadrado alumínio 40x40x3 6060',  'm', 'tubo', 14.5000, true, 'AL6060'),
    ('TQ60-AL',  'Tubo quadrado alumínio 60x60x3 6060',  'm', 'tubo', 21.5000, true, 'AL6060'),
    ('TR50-AL',  'Tubo retangular alumínio 50x30x2 6060','m', 'tubo', 11.7000, true, 'AL6060'),
    ('TR80-AL',  'Tubo retangular alumínio 80x40x3 6060','m', 'tubo', 18.2000, true, 'AL6060'),
    ('TR100-AL', 'Tubo retangular alumínio 100x50x4 6060','m','tubo', 35.8000, true, 'AL6060'),
    ('CH3-S235', 'Chapa laser 3mm S235JR', 'kg', 'chapa_laser', 1.5800, true, 'S235JR'),
    ('CH5-S235', 'Chapa laser 5mm S235JR', 'kg', 'chapa_laser', 1.6900, true, 'S235JR'),
    ('CH6-S355', 'Chapa laser 6mm S355JR', 'kg', 'chapa_laser', 1.9200, true, 'S355JR'),
    ('CH10-S355', 'Chapa laser 10mm S355JR', 'kg', 'chapa_laser', 2.1500, true, 'S355JR'),
    ('CH3-304', 'Chapa laser inox 3mm AISI 304', 'kg', 'chapa_laser', 5.9000, true, 'AISI304'),
    ('CH5-304', 'Chapa laser inox 5mm AISI 304', 'kg', 'chapa_laser', 6.2500, true, 'AISI304'),
    ('CH8-304', 'Chapa laser inox 8mm AISI 304', 'kg', 'chapa_laser', 6.8500, true, 'AISI304'),
    ('CH3-AL', 'Chapa laser alumínio 3mm 5754', 'kg', 'chapa_laser', 4.2000, true, 'AL5754'),
    ('CH5-AL', 'Chapa laser alumínio 5mm 5754', 'kg', 'chapa_laser', 4.5500, true, 'AL5754'),
    ('CH8-AL', 'Chapa laser alumínio 8mm 5754', 'kg', 'chapa_laser', 4.9000, true, 'AL5754'),
    ('PAR-M8-88', 'Parafuso sextavado M8 classe 8.8 zincado', 'un', 'parafusaria', 0.0900, true, 'ACO 8.8'),
    ('PAR-M10-88', 'Parafuso sextavado M10 classe 8.8 zincado', 'un', 'parafusaria', 0.1600, true, 'ACO 8.8'),
    ('PAR-M12-88', 'Parafuso sextavado M12 classe 8.8 zincado', 'un', 'parafusaria', 0.2800, true, 'ACO 8.8'),
    ('POR-M12', 'Porca sextavada M12 classe 8 zincada', 'un', 'parafusaria', 0.0800, true, 'ACO 8'),
    ('ANI-M12', 'Anilha lisa M12 zincada', 'un', 'parafusaria', 0.0300, true, 'ACO'),
    ('PAR-M8-A2', 'Parafuso sextavado inox M8 A2', 'un', 'parafusaria', 0.2200, true, 'AISI304'),
    ('REB-M6-A2', 'Rebite roscado inox M6 A2', 'un', 'parafusaria', 0.3500, true, 'AISI304'),
    ('DOB-80', 'Dobradiça comercial aço 80mm', 'un', 'peca_comercio', 2.4000, true, 'S235JR'),
    ('FECHO', 'Fecho rápido aço zincado', 'un', 'peca_comercio', 7.8000, true, 'S235JR'),
    ('PE-M12', 'Pé nivelador M12 aço zincado', 'un', 'peca_comercio', 3.6000, true, 'S235JR'),
    ('SUP-304', 'Suporte comercial inox 304', 'un', 'peca_comercio', 5.2000, true, 'AISI304'),
    ('PERF-AL', 'Perfil comercial alumínio 6060', 'un', 'peca_comercio', 9.4000, true, 'AL6060'),
    ('CHDOB-AL', 'Chapa dobrada comercial alumínio 5754', 'un', 'peca_comercio', 6.8000, true, 'AL5754');

INSERT INTO public.operacao (codigo, nome, categoria, custo_hora_default, setup_hora_default, ativo)
VALUES
    ('LASER', 'Corte laser', 'corte', 42.00, 0.50, true),
    ('CORTE', 'Corte', 'corte', 32.00, 0.30, true),
    ('FUR', 'Furação', 'furacao', 34.00, 0.25, true),
    ('MAQ', 'Maquinação', 'maquinacao', 46.00, 0.60, true),
    ('CAL', 'Calandragem', 'calandragem', 48.00, 0.75, true),
    ('QUIN', 'Quinagem', 'quinagem', 45.00, 0.55, true),
    ('SOLD', 'Soldadura', 'soldadura', 39.00, 0.45, true),
    ('PING', 'Pingamento', 'pingamento', 34.00, 0.25, true),
    ('REB', 'Rebarbagem', 'acabamento', 31.00, 0.25, true),
    ('MONT', 'Montagem', 'montagem', 30.00, 0.30, true),
    ('QUAL', 'Qualidade', 'qualidade', 28.00, 0.20, true),
    ('ACAB', 'Acabamento', 'acabamento', 33.00, 0.25, true),
    ('EXP', 'Expedição', 'expedicao', 24.00, 0.15, true);

INSERT INTO public.servico (codigo, nome, unidade, preco_unitario_default, ativo)
VALUES
    ('GALV', 'Galvanização', 'kg', 1.20, true),
    ('PINT', 'Pintura líquida', 'm2', 14.80, true),
    ('LAC', 'Lacagem', 'm2', 16.50, true),
    ('ANOD', 'Anodização alumínio', 'm2', 18.00, true),
    ('POL', 'Polimento inox', 'm2', 22.00, true),
    ('TRANS', 'Transporte', 'viag', 380.00, true),
    ('GRUA', 'Grua', 'dia', 920.00, true),
    ('ENSAIO', 'Ensaios qualidade', 'hora', 68.00, true),
    ('CERT', 'Certificação', 'lote', 650.00, true),
    ('EMB', 'Embalagem', 'lote', 240.00, true),
    ('MONTEXT', 'Montagem externa', 'hora', 42.00, true);

INSERT INTO public.projeto (
    referencia,
    designacao,
    tipologia,
    estado,
    data_inicio,
    data_entrega_prevista,
    numero_pecas,
    complexidade,
    material_principal,
    tratamento_superficie,
    lead_time,
    observacoes,
    criado_por,
    id_cliente
)
SELECT
    format('PRJ-2026-%s', lpad(gs::text, 5, '0')),
    CASE (gs % 12)
        WHEN 0 THEN format('Pavilhão metálico %s', gs)
        WHEN 1 THEN format('Passadiço metálico %s', gs)
        WHEN 2 THEN format('Cobertura metálica %s', gs)
        WHEN 3 THEN format('Mezanino industrial %s', gs)
        WHEN 4 THEN format('Plataforma técnica %s', gs)
        WHEN 5 THEN format('Escadaria metálica %s', gs)
        WHEN 6 THEN format('Guarda-corpos metálico %s', gs)
        WHEN 7 THEN format('Passarela técnica %s', gs)
        WHEN 8 THEN format('Passerelle metálica %s', gs)
        WHEN 9 THEN format('Corrimão metálico %s', gs)
        WHEN 10 THEN format('Gradeamento metálico %s', gs)
        ELSE format('Portão metálico %s', gs)
    END,
    CASE (gs % 12)
        WHEN 0 THEN 'pavilhao'
        WHEN 1 THEN 'passadico'
        WHEN 2 THEN 'cobertura'
        WHEN 3 THEN 'mezanino'
        WHEN 4 THEN 'plataforma'
        WHEN 5 THEN 'escadaria'
        WHEN 6 THEN 'guarda-corpos'
        WHEN 7 THEN 'passarela'
        WHEN 8 THEN 'passerelle'
        WHEN 9 THEN 'corrimao'
        WHEN 10 THEN 'gradeamento'
        ELSE 'portao'
    END,
    -- Distribuicao alvo (gs % 100):
    --   2%  cancelado
    --   50% concluido    <- metade completamente fechada, com realizado
    --   15% em_execucao
    --   12% aprovado
    --   9%  planeado
    --   12% em_analise
    CASE
        WHEN gs % 100 < 2  THEN 'cancelado'
        WHEN gs % 100 < 52 THEN 'concluido'
        WHEN gs % 100 < 67 THEN 'em_execucao'
        WHEN gs % 100 < 79 THEN 'aprovado'
        WHEN gs % 100 < 88 THEN 'planeado'
        ELSE                    'em_analise'
    END,
    -- data_inicio: distribuida por 3 anos (2024-2026) coerentemente com o estado.
    -- Concluidos sao mais antigos (2024 - meio 2025), em_execucao em 2025-Q3 a meio 2026,
    -- aprovados/planeados/em_analise mais recentes (2026).
    CASE
        WHEN gs % 100 < 2  THEN (DATE '2024-06-01' + ((gs * 7) % 730))   -- cancelado: pode ser de qualquer epoca
        WHEN gs % 100 < 52 THEN (DATE '2024-01-01' + ((gs * 5) % 540))   -- concluido: 2024 a meio 2025
        WHEN gs % 100 < 67 THEN (DATE '2025-06-01' + ((gs * 3) % 270))   -- em_execucao: 2025-Q3 a meio 2026
        WHEN gs % 100 < 79 THEN (DATE '2025-12-01' + ((gs * 2) % 200))   -- aprovado: fim 2025 a meio 2026
        WHEN gs % 100 < 88 THEN (DATE '2026-04-01' + ((gs * 4) % 200))   -- planeado: futuro proximo
        ELSE                    (DATE '2026-06-01' + ((gs * 4) % 150))   -- em_analise: mais recente
    END,
    CASE
        WHEN gs % 100 < 2  THEN (DATE '2024-06-01' + ((gs * 7) % 730) + (25 + (gs % 45)))
        WHEN gs % 100 < 52 THEN (DATE '2024-01-01' + ((gs * 5) % 540) + (35 + (gs % 55)))
        WHEN gs % 100 < 67 THEN (DATE '2025-06-01' + ((gs * 3) % 270) + (55 + (gs % 70)))
        WHEN gs % 100 < 79 THEN (DATE '2025-12-01' + ((gs * 2) % 200) + (45 + (gs % 65)))
        WHEN gs % 100 < 88 THEN (DATE '2026-04-01' + ((gs * 4) % 200) + (45 + (gs % 70)))
        ELSE                    (DATE '2026-06-01' + ((gs * 4) % 150) + (45 + (gs % 70)))
    END,
    CASE
        WHEN gs % 40 = 0 THEN 400 + (random() * 600)::int
        WHEN gs % 25 = 0 THEN 250 + (random() * 450)::int
        WHEN gs % 6 = 0 THEN 150 + (random() * 500)::int
        WHEN gs % 6 = 2 THEN 90 + (random() * 380)::int
        WHEN gs % 6 = 3 THEN 60 + (random() * 280)::int
        WHEN gs % 6 = 4 THEN 35 + (random() * 200)::int
        WHEN gs % 6 = 1 THEN 20 + (random() * 130)::int
        ELSE 15 + (random() * 160)::int
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
        WHEN gs % 40 = 0 THEN 120 + (gs % 90)
        WHEN gs % 25 = 0 THEN 90 + (gs % 75)
        WHEN gs % 6 = 0 THEN 75 + (gs % 65)
        WHEN gs % 6 = 2 THEN 55 + (gs % 55)
        WHEN gs % 6 = 3 THEN 45 + (gs % 50)
        WHEN gs % 6 = 4 THEN 35 + (gs % 45)
        ELSE 20 + (gs % 40)
    END,
    format('Projeto gerado automaticamente com escala, material e tratamento coerentes. Item %s.', gs),
    CASE
        WHEN gs % 6 = 0 THEN 2
        WHEN gs % 5 = 0 THEN 4
        ELSE 1
    END,
    ((gs - 1) % 350) + 1
FROM generate_series(1, 5000) AS gs;

-- 5000 projetos com versoes controladas:
--   95% so v1                  -> 4750 orcamentos
--   5% v1+v2                   -> 500 orcamentos
--   total ~5250 orcamentos
-- Reflete a realidade pretendida: so uma pequena minoria precisa de revisao.
--
-- peso_por_projeto: peso_total_kg agora vive no orcamento (uma feature por
-- versao), mas para coerencia entre versoes do mesmo projeto pre-computamos
-- um valor unico por projeto e replicamo-lo em todas as suas versoes. AISI304
-- e AL ficam mais leves (0.45/0.55) porque tem EUR/kg mais elevado e isso
-- ajuda a manter o cap de 50.000 EUR.
WITH peso_por_projeto AS (
    SELECT
        p.id_projeto,
        round((
            CASE
                WHEN p.id_projeto % 40 = 0 THEN 9000 + random() * 7000   -- grandes (9-16k kg)
                WHEN p.id_projeto % 25 = 0 THEN 5500 + random() * 6500   -- medio-grandes (5.5-12k)
                WHEN p.id_projeto % 6 = 0 THEN 4000 + random() * 8000    -- medios (4-12k)
                WHEN p.id_projeto % 6 = 2 THEN 2500 + random() * 5500    -- pequeno-medios (2.5-8k)
                WHEN p.id_projeto % 6 = 3 THEN 1500 + random() * 4500    -- pequenos (1.5-6k)
                WHEN p.id_projeto % 6 = 4 THEN 1000 + random() * 3000    -- pequenos (1-4k)
                WHEN p.id_projeto % 6 = 1 THEN 500 + random() * 2500     -- minis (0.5-3k)
                ELSE 400 + random() * 2000                               -- minis (0.4-2.4k)
            END
            * CASE
                WHEN p.id_projeto % 10 IN (1, 2) THEN 0.55  -- AL e AISI ficam mais leves
                WHEN p.id_projeto % 10 = 0 THEN 0.45        -- AISI ainda mais leve (preco/kg alto)
                ELSE 1.00
              END
        )::numeric, 2) AS peso_total_kg
    FROM public.projeto p
),
-- area_por_projeto: area_total_m2 e a area de superficie a tratar. Depende
-- principalmente da tipologia (coberturas tem muita area por kg; mezaninos
-- pouca) e do material (chapas finas de inox/alumínio tem mais area por kg
-- que perfis em aco). Mantida por projeto para coerencia entre versoes.
area_por_projeto AS (
    SELECT
        p.id_projeto,
        round((
            pp.peso_total_kg
            * CASE p.tipologia
                WHEN 'cobertura'  THEN 0.10  -- grande superficie por kg
                WHEN 'guarda-corpos' THEN 0.09
                WHEN 'gradeamento' THEN 0.09
                WHEN 'corrimao'    THEN 0.085
                WHEN 'passadico'  THEN 0.08
                WHEN 'passarela'   THEN 0.08
                WHEN 'passerelle'  THEN 0.08
                WHEN 'portao'      THEN 0.075
                WHEN 'escadaria'  THEN 0.07
                WHEN 'plataforma' THEN 0.06
                WHEN 'mezanino'   THEN 0.05
                WHEN 'pavilhao'   THEN 0.04  -- mais estrutural, menos chapa
                ELSE                    0.05
              END
            * CASE
                WHEN p.material_principal = 'AISI304' THEN 1.20  -- chapa fina
                WHEN p.material_principal IN ('AL5754', 'AL6060') THEN 1.30
                ELSE 1.00
              END
            * (0.85 + random() * 0.30)
        )::numeric, 2) AS area_total_m2
    FROM public.projeto p
    JOIN peso_por_projeto pp ON pp.id_projeto = p.id_projeto
),
versoes AS (
    SELECT
        p.id_projeto,
        p.estado AS projeto_estado,
        p.tipologia,
        p.data_inicio,
        pp.peso_total_kg,
        ap.area_total_m2,
        v.nr AS versao_num,
        format('v%s', v.nr) AS versao,
        -- Numero da ultima versao deste projeto. Usamos (id_projeto/10)%20
        -- para descorrelacionar do material (que usa id_projeto%10), evitando
        -- que AISI/AL fiquem so em projetos com 1 versao.
        CASE
            WHEN ((p.id_projeto / 10) % 20) = 5 THEN 2  -- 5% projetos: 2 versoes
            ELSE 1                                      -- 95% projetos: so v1
        END AS last_versao_num
    FROM public.projeto p
    JOIN peso_por_projeto pp ON pp.id_projeto = p.id_projeto
    JOIN area_por_projeto ap ON ap.id_projeto = p.id_projeto
    CROSS JOIN (VALUES (1), (2)) AS v(nr)
    WHERE
        v.nr = 1
        OR (v.nr = 2 AND ((p.id_projeto / 10) % 20) = 5)
)
INSERT INTO public.orcamento (
    id_projeto,
    versao,
    criado_por,
    data_criacao,
    estado,
    margem_percentual,
    peso_total_kg,
    area_total_m2,
    observacoes
)
SELECT
    id_projeto,
    versao,
    CASE
        WHEN versao_num = 1 THEN 3
        ELSE 2
    END,
    data_inicio::timestamp
        - ((CASE versao_num WHEN 1 THEN 45 ELSE 25 END) * INTERVAL '1 day')
        - ((id_projeto % 12) * INTERVAL '1 day'),
    -- Estado do orcamento conforme ciclo de vida do relatorio (3.5):
    -- em_preparacao, em_revisao, validado, enviado, adjudicado, rejeitado,
    -- em_execucao, concluido, arquivado.
    --
    -- Logica geral: a ULTIMA versao do projeto (versao_num = last_versao_num)
    -- recebe o estado "vivo" coerente com o estado do projeto. As versoes
    -- anteriores que foram superadas ficam 'rejeitado' (v1) ou 'em_revisao'
    -- (penultima). Se o projeto so tem v1, essa unica versao recebe o estado
    -- final diretamente.
    CASE
        -- Projeto cancelado: ultima versao arquivada, anteriores rejeitadas
        WHEN projeto_estado = 'cancelado' AND versao_num = last_versao_num THEN 'arquivado'
        WHEN projeto_estado = 'cancelado' THEN 'rejeitado'
        -- Projeto concluido: ultima versao concluida, anteriores rejeitadas
        WHEN projeto_estado = 'concluido' AND versao_num = last_versao_num THEN 'concluido'
        WHEN projeto_estado = 'concluido' THEN 'rejeitado'
        -- Projeto em_execucao: ultima versao em producao, anteriores rejeitadas
        WHEN projeto_estado = 'em_execucao' AND versao_num = last_versao_num THEN 'em_execucao'
        WHEN projeto_estado = 'em_execucao' THEN 'rejeitado'
        -- Projeto aprovado: cliente adjudicou ultima versao
        WHEN projeto_estado = 'aprovado' AND versao_num = last_versao_num THEN 'adjudicado'
        WHEN projeto_estado = 'aprovado' AND versao_num = last_versao_num - 1 AND last_versao_num > 1 THEN 'em_revisao'
        WHEN projeto_estado = 'aprovado' THEN 'rejeitado'
        -- Projeto planeado: ultima versao foi enviada ao cliente
        WHEN projeto_estado = 'planeado' AND versao_num = last_versao_num THEN 'enviado'
        WHEN projeto_estado = 'planeado' AND versao_num = last_versao_num - 1 AND last_versao_num > 1 THEN 'em_revisao'
        WHEN projeto_estado = 'planeado' THEN 'rejeitado'
        -- Projeto em_analise: ultima versao em preparacao
        WHEN projeto_estado = 'em_analise' AND versao_num = last_versao_num THEN 'em_preparacao'
        WHEN projeto_estado = 'em_analise' AND versao_num = last_versao_num - 1 AND last_versao_num > 1 THEN 'em_revisao'
        ELSE 'rejeitado'
    END,
    -- Margem comercial varia por tipologia: trabalhos mais tecnicos (mezanino,
    -- plataforma, passarela/passerelle) tipicamente tem margens maiores;
    -- trabalhos mais comoditizados (pavilhao, escadaria, corrimao) mais baixas.
    -- Reflecte praxis de mercado.
    round((
        CASE tipologia
            WHEN 'mezanino'   THEN 18 + random() * 14   -- 18-32% (engenharia)
            WHEN 'plataforma' THEN 16 + random() * 12   -- 16-28%
            WHEN 'passarela'  THEN 15 + random() * 12   -- 15-27%
            WHEN 'passerelle' THEN 15 + random() * 12   -- 15-27%
            WHEN 'cobertura'  THEN 14 + random() * 11   -- 14-25%
            WHEN 'passadico'  THEN 14 + random() * 10   -- 14-24%
            WHEN 'guarda-corpos' THEN 14 + random() * 10 -- 14-24%
            WHEN 'gradeamento' THEN 13 + random() * 11  -- 13-24%
            WHEN 'portao'     THEN 13 + random() * 10   -- 13-23%
            WHEN 'escadaria'  THEN 12 + random() * 12   -- 12-24%
            WHEN 'corrimao'   THEN 12 + random() * 10   -- 12-22%
            WHEN 'pavilhao'   THEN 11 + random() * 9    -- 11-20% (mais comoditizado)
            ELSE 13 + random() * 12
        END
    )::numeric, 2),
    peso_total_kg,
    area_total_m2,
    format('Orçamento %s do projeto %s - estrutura metálica.', versao, id_projeto)
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
            -- Tubos S235JR quadrados
            WHEN 'TQ20-S235'   THEN 1.10
            WHEN 'TQ25-S235'   THEN 1.41
            WHEN 'TQ30-S235'   THEN 1.76
            WHEN 'TQ35-S235'   THEN 2.07
            WHEN 'TQ40-S235'   THEN 2.39
            WHEN 'TQ40-3-S235' THEN 3.41
            WHEN 'TQ45-S235'   THEN 3.88
            WHEN 'TQ50-S235'   THEN 4.43
            WHEN 'TQ60-S235'   THEN 5.39
            WHEN 'TQ70-S235'   THEN 8.28
            WHEN 'TQ80-S235'   THEN 9.54
            WHEN 'TQ100-S235'  THEN 14.93
            -- Tubos S235JR retangulares
            WHEN 'TR50-S235'   THEN 2.39
            WHEN 'TR60-S235'   THEN 4.43
            WHEN 'TR80-S235'   THEN 5.20
            WHEN 'TR100-S235'  THEN 8.78
            WHEN 'TR120-S235'  THEN 10.80
            -- Tubos S235JR redondos
            WHEN 'RD21-S235'   THEN 0.95
            WHEN 'RD27-S235'   THEN 1.76
            WHEN 'RD33-S235'   THEN 1.99
            -- Tubos S355JR
            WHEN 'TQ35-S355'   THEN 3.05
            WHEN 'TQ45-S355'   THEN 4.99
            WHEN 'TQ50-S355'   THEN 4.43
            WHEN 'TQ60-S355'   THEN 5.39
            WHEN 'TQ70-S355'   THEN 8.28
            WHEN 'TQ80-S355'   THEN 11.65
            WHEN 'TQ100-S355'  THEN 17.66
            WHEN 'TR80-S355'   THEN 5.20
            WHEN 'TR100-S355'  THEN 8.78
            WHEN 'TR120-S355'  THEN 14.79
            WHEN 'TR150-S355'  THEN 22.51
            WHEN 'RD48-S355'   THEN 3.56
            WHEN 'RD60-S355'   THEN 5.04
            WHEN 'RD89-S355'   THEN 8.38
            -- Tubos AISI304 (inox tem densidade ~7.93, similar ao aco para esta seccao)
            WHEN 'TQ20-304' THEN 1.10
            WHEN 'TQ25-304' THEN 1.41
            WHEN 'TQ30-304' THEN 1.77
            WHEN 'TQ40-304' THEN 2.39
            WHEN 'TQ50-304' THEN 4.43
            WHEN 'TQ60-304' THEN 5.39
            WHEN 'TR50-304' THEN 2.37
            WHEN 'TR80-304' THEN 5.34
            -- Tubos AL6060 (alumínio densidade ~2.70 — ~1/3 do aco)
            WHEN 'TQ20-AL'  THEN 0.38
            WHEN 'TQ25-AL'  THEN 0.49
            WHEN 'TQ30-AL'  THEN 0.60
            WHEN 'TQ40-AL'  THEN 0.81
            WHEN 'TQ40-3AL' THEN 1.18
            WHEN 'TQ60-AL'  THEN 1.86
            WHEN 'TR50-AL'  THEN 0.80
            WHEN 'TR80-AL'  THEN 1.85
            WHEN 'TR100-AL' THEN 3.13
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
        mb.unidade,
        CASE
            WHEN mb.unidade = 'kg' THEN mb.quantidade
            WHEN mb.unidade = 'm' THEN round((mb.quantidade * mb.kg_por_m)::numeric, 2)
            WHEN mb.unidade = 'm2' THEN round((mb.quantidade * (2.8 + random() * 1.2))::numeric, 2)
            ELSE NULL::numeric
        END AS peso_kg,
        -- area_m2 por linha:
        -- 'm2' (chapa): area = quantidade
        -- 'm'  (tubo):  area = quantidade x perimetro estimado (~0.10-0.25 m2/m)
        -- 'kg'/'un':    NULL (parafusaria / peca de comercio sem superficie a tratar)
        CASE
            WHEN mb.unidade = 'm2' THEN mb.quantidade
            WHEN mb.unidade = 'm' THEN round((mb.quantidade * (0.10 + random() * 0.15))::numeric, 2)
            ELSE NULL::numeric
        END AS area_m2,
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
    area_m2,
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
    area_m2,
    desperdicio_percent,
    preco_unitario_snapshot,
    round((quantidade * preco_unitario_snapshot * (1 + (desperdicio_percent / 100.0)))::numeric, 2),
    format('Material aplicado: %s', nome_material)
FROM mat_dados
ORDER BY id_orcamento, id_material;

-- 5 linhas de operacao por orcamento.
-- Coerencia de processo: projetos em aco (S235JR/S355JR/AISI304) sao soldados,
-- pelo que tem SEMPRE soldadura (SOLD), pingamento (PING) e rebarbagem (REB),
-- mais o corte inicial e uma operacao associada variavel. Projetos em aluminio
-- (AL6060/AL5754) sao tipicamente montados mecanicamente (nao soldados) e
-- recebem corte, conformacao, furacao, montagem e acabamento/qualidade.
WITH orc_info AS (
    SELECT
        o.id_orcamento,
        (pr.material_principal IN ('S235JR', 'S355JR', 'AISI304')) AS soldado,
        pr.complexidade
    FROM public.orcamento o
    JOIN public.projeto pr ON pr.id_projeto = o.id_projeto
),
op_picks AS (
    SELECT
        oi.id_orcamento,
        gs.idx,
        CASE
            WHEN oi.soldado THEN
                CASE gs.idx
                    WHEN 1 THEN CASE WHEN oi.complexidade = 'alta' THEN 'LASER' ELSE 'CORTE' END
                    WHEN 2 THEN 'SOLD'   -- soldadura (sempre presente em projeto soldado)
                    WHEN 3 THEN 'PING'   -- pingamento (sempre presente)
                    WHEN 4 THEN 'REB'    -- rebarbagem (sempre presente)
                    ELSE                 -- operacao associada variavel
                        CASE (oi.id_orcamento % 5)
                            WHEN 0 THEN 'MONT'
                            WHEN 1 THEN 'QUAL'
                            WHEN 2 THEN 'ACAB'
                            WHEN 3 THEN 'FUR'
                            ELSE 'EXP'
                        END
                END
            ELSE  -- aluminio: montagem mecanica, sem soldadura
                CASE gs.idx
                    WHEN 1 THEN 'CORTE'
                    WHEN 2 THEN CASE WHEN oi.complexidade = 'alta' THEN 'MAQ' ELSE 'QUIN' END
                    WHEN 3 THEN 'FUR'
                    WHEN 4 THEN 'MONT'
                    ELSE
                        CASE (oi.id_orcamento % 3)
                            WHEN 0 THEN 'ACAB'
                            WHEN 1 THEN 'QUAL'
                            ELSE 'CAL'
                        END
                END
        END AS codigo_operacao
    FROM orc_info oi
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
    JOIN public.operacao op ON op.codigo = p.codigo_operacao
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
    format('Operação prevista: %s', nome_operacao)
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
                          (pr.tratamento_superficie = 'galvanizacao' AND s.codigo = 'GALV')
                          OR (pr.tratamento_superficie = 'pintura_liquida' AND s.codigo = 'PINT')
                          OR (pr.tratamento_superficie = 'lacagem' AND s.codigo = 'LAC')
                          OR (pr.tratamento_superficie = 'anodizacao' AND s.codigo = 'ANOD')
                          OR (pr.tratamento_superficie = 'polimento' AND s.codigo = 'POL')
                          OR (pr.tratamento_superficie = 'sem_tratamento' AND s.codigo IN ('TRANS', 'ENSAIO', 'CERT', 'EMB', 'MONTEXT'))
                      )
                  )
                  OR (
                      gs.idx = 2
                      AND s.codigo IN ('TRANS', 'ENSAIO', 'CERT', 'EMB', 'MONTEXT')
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
    format('Serviço externo: %s', nome_servico)
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
-- Targets brutos por categoria (antes do cap final de 50k EUR)
CREATE TEMP TABLE tmp_orcamento_target_raw ON COMMIT DROP AS
SELECT
    o.id_orcamento,
    -- Materiais: peso x EUR/kg(material) x tipologia x ruido
    GREATEST(500::numeric,
        round((o.peso_total_kg
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
                WHEN 'portao'      THEN 0.95
                WHEN 'mezanino'   THEN 0.95
                WHEN 'passarela'   THEN 0.92
                WHEN 'passerelle'  THEN 0.92
                WHEN 'passadico'  THEN 0.90
                WHEN 'guarda-corpos' THEN 0.88
                WHEN 'gradeamento' THEN 0.86
                WHEN 'escadaria'  THEN 0.85
                WHEN 'corrimao'    THEN 0.82
                ELSE                  1.00
              END
            * (0.93 + random() * 0.14)
        )::numeric, 2)
    ) AS target_materiais,
    -- Operacoes: peso/escala x complexidade x ruido
    -- (peso/6 ~ EUR-equivalente; depois aplicam-se multiplicadores)
    GREATEST(300::numeric,
        round((o.peso_total_kg / 6.0
            * CASE p.complexidade
                WHEN 'alta'  THEN 1.90
                WHEN 'media' THEN 1.40
                ELSE              1.00
              END
            * (1.0 + (p.numero_pecas::numeric * 0.0008))  -- mais pecas = mais montagem
            * (0.90 + random() * 0.20)
        )::numeric, 2)
    ) AS target_operacoes,
    -- Servicos: tratamentos por m2 usam area_total; galvanizacao usa peso
    -- (e facturada por kg). Sem tratamento mantem base minima.
    -- Preco/m2 alinhado com o catalogo (svc): pintura ~14.80, lacagem 16.50,
    -- anodizacao 18.00, polimento 22.00. Galvanizacao 1.20 EUR/kg.
    GREATEST(200::numeric,
        round((
            CASE p.tratamento_superficie
                WHEN 'pintura_liquida' THEN o.area_total_m2 * 14.80
                WHEN 'lacagem'         THEN o.area_total_m2 * 16.50
                WHEN 'anodizacao'      THEN o.area_total_m2 * 18.00
                WHEN 'polimento'       THEN o.area_total_m2 * 22.00
                WHEN 'galvanizacao'    THEN o.peso_total_kg * 1.20
                WHEN 'sem_tratamento'  THEN o.peso_total_kg * 0.10
                ELSE                        o.peso_total_kg * 0.20
            END
            * (0.90 + random() * 0.20)
        )::numeric, 2)
    ) AS target_servicos
FROM public.orcamento o
JOIN public.projeto p ON p.id_projeto = o.id_projeto;

-- Cap final: nenhum orcamento ultrapassa 50.000 EUR. Quando o total excede o
-- cap, escala-se proporcionalmente os 3 componentes para manter a relacao
-- materiais/operacoes/servicos. Aplica-se um valor entre 40k e 49.5k para
-- evitar uma "parede" estatistica em exatamente 50k.
CREATE TEMP TABLE tmp_orcamento_target ON COMMIT DROP AS
WITH com_fator AS (
    SELECT
        id_orcamento,
        target_materiais,
        target_operacoes,
        target_servicos,
        (target_materiais + target_operacoes + target_servicos) AS total_raw,
        -- Fator de cap: aplica-se SEM excecao mas so reduz se total_raw > 50k.
        -- O alvo capado fica entre 40k e 49.5k para evitar parede em 50k.
        (40000 + random() * 9500) AS total_capped
    FROM tmp_orcamento_target_raw
),
com_escala AS (
    SELECT
        id_orcamento,
        target_materiais,
        target_operacoes,
        target_servicos,
        CASE WHEN total_raw > 50000
             THEN total_capped / total_raw
             ELSE 1::numeric END AS fator_cap
    FROM com_fator
)
SELECT
    id_orcamento,
    round((target_materiais * fator_cap)::numeric, 2) AS target_materiais,
    round((target_operacoes * fator_cap)::numeric, 2) AS target_operacoes,
    round((target_servicos * fator_cap)::numeric, 2) AS target_servicos
FROM com_escala;

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

-- peso_total_kg do orcamento e gerado no INSERT (CTE peso_por_projeto), nao
-- derivado das linhas de material. Mantemos uma feature de INPUT estavel para
-- o ML em vez de uma variavel circular calculada a partir do proprio orcamento.

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
    WHERE o.estado IN ('em_execucao', 'concluido')
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
    'Consumo real de material em produção.'
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
    WHERE o.estado IN ('em_execucao', 'concluido')
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
    'Execução real de operação.'
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
    WHERE o.estado IN ('em_execucao', 'concluido')
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
    'Serviço externo realizado.'
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
    format('peso=%s; peças=%s; tipologia=%s', o.peso_total_kg, p.numero_pecas, p.tipologia),
    'Previsão automática para análise de desvio.'
FROM public.orcamento o
JOIN public.projeto p ON p.id_projeto = o.id_projeto
WHERE o.estado NOT IN ('rejeitado', 'arquivado')
  AND random() < 0.80;

-- Validacoes de integridade pedidas
DO $$
DECLARE
    v_total_orc integer;
    v_total_projetos integer;
    v_projetos_multiversao integer;
    v_projetos_concluidos integer;
    v_orc_concluidos integer;
    v_min_linhas integer;
    v_orc_max numeric;
    v_orc_5k integer;
    v_orc_15k integer;
    v_orc_30k integer;
    v_orc_45k integer;
    v_orc_cancelado_fora_projeto integer;
    v_projetos_ativos_sem_aprovado integer;
    v_projetos_analise_com_aprovado integer;
    v_orc_aco integer;
    v_orc_alumínio integer;
    v_orc_inox integer;
    v_pct_aco numeric;
    v_pct_alumínio numeric;
    v_pct_inox numeric;
BEGIN
    SELECT count(*) INTO v_total_orc FROM public.orcamento;
    SELECT count(*) INTO v_total_projetos FROM public.projeto;
    SELECT count(*) INTO v_projetos_concluidos FROM public.projeto WHERE estado = 'concluido';
    SELECT count(*) INTO v_orc_concluidos FROM public.orcamento WHERE estado = 'concluido';

    SELECT count(*)
    INTO v_projetos_multiversao
    FROM (
        SELECT id_projeto
        FROM public.orcamento
        GROUP BY id_projeto
        HAVING count(*) > 1
    ) t;

    -- Distribuicao de custos: novo cap e 50.000 EUR.
    SELECT
        max(custo_total_orcado),
        count(*) FILTER (WHERE custo_total_orcado BETWEEN 1 AND 5000),
        count(*) FILTER (WHERE custo_total_orcado BETWEEN 5000 AND 15000),
        count(*) FILTER (WHERE custo_total_orcado BETWEEN 15000 AND 30000),
        count(*) FILTER (WHERE custo_total_orcado BETWEEN 30000 AND 50000)
    INTO v_orc_max, v_orc_5k, v_orc_15k, v_orc_30k, v_orc_45k
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

    -- v_orc_cancelado_fora_projeto: orcamentos arquivados que nao estao
    -- em projetos cancelados (arquivado e o estado terminal usado para
    -- versoes superseded em projetos cancelados).
    SELECT count(*)
    INTO v_orc_cancelado_fora_projeto
    FROM public.orcamento o
    JOIN public.projeto p ON p.id_projeto = o.id_projeto
    WHERE o.estado = 'arquivado'
      AND p.estado <> 'cancelado';

    -- Projetos ativos (planeado/aprovado/em_execucao/concluido) tem de ter
    -- pelo menos um orcamento que tenha avancado (enviado/adjudicado/
    -- em_execucao/concluido), ou seja, passou validacao interna.
    SELECT count(*)
    INTO v_projetos_ativos_sem_aprovado
    FROM public.projeto p
    WHERE p.estado IN ('planeado', 'aprovado', 'em_execucao', 'concluido')
      AND NOT EXISTS (
          SELECT 1
          FROM public.orcamento o
          WHERE o.id_projeto = p.id_projeto
            AND o.estado IN ('enviado', 'adjudicado', 'em_execucao', 'concluido')
      );

    -- Projetos em analise NAO devem ter orcamentos ja avancados (validado/
    -- enviado/adjudicado/em_execucao/concluido) — esses estados implicam
    -- que o orcamento ja saiu da fase de analise.
    SELECT count(*)
    INTO v_projetos_analise_com_aprovado
    FROM public.projeto p
    WHERE p.estado = 'em_analise'
      AND EXISTS (
          SELECT 1
          FROM public.orcamento o
          WHERE o.id_projeto = p.id_projeto
            AND o.estado IN ('validado', 'enviado', 'adjudicado', 'em_execucao', 'concluido')
      );

    SELECT
        count(*) FILTER (WHERE p.material_principal IN ('S235JR', 'S355JR')),
        count(*) FILTER (WHERE p.material_principal IN ('AL6060', 'AL5754')),
        count(*) FILTER (WHERE p.material_principal = 'AISI304')
    INTO v_orc_aco, v_orc_alumínio, v_orc_inox
    FROM public.orcamento o
    JOIN public.projeto p ON p.id_projeto = o.id_projeto;

    v_pct_aco := round((v_orc_aco::numeric / NULLIF(v_total_orc, 0)) * 100, 2);
    v_pct_alumínio := round((v_orc_alumínio::numeric / NULLIF(v_total_orc, 0)) * 100, 2);
    v_pct_inox := round((v_orc_inox::numeric / NULLIF(v_total_orc, 0)) * 100, 2);

    IF v_total_orc <> (v_total_projetos + v_projetos_multiversao) THEN
        RAISE EXCEPTION
            'Seed invalida: total orcamentos = % (esperado projetos + multiversao = %)',
            v_total_orc,
            (v_total_projetos + v_projetos_multiversao);
    END IF;

    IF v_projetos_multiversao <> round(v_total_projetos::numeric * 0.05)::int THEN
        RAISE EXCEPTION
            'Seed invalida: projetos multiversao = % (esperado 5%% de % = %)',
            v_projetos_multiversao,
            v_total_projetos,
            round(v_total_projetos::numeric * 0.05)::int;
    END IF;

    IF v_projetos_concluidos <> round(v_total_projetos::numeric * 0.50)::int THEN
        RAISE EXCEPTION
            'Seed invalida: projetos concluidos = % (esperado 50%% de % = %)',
            v_projetos_concluidos,
            v_total_projetos,
            round(v_total_projetos::numeric * 0.50)::int;
    END IF;

    IF v_orc_concluidos <> v_projetos_concluidos THEN
        RAISE EXCEPTION
            'Seed invalida: orcamentos concluidos = % (esperado um por projeto concluido = %)',
            v_orc_concluidos,
            v_projetos_concluidos;
    END IF;

    IF v_min_linhas < 15 THEN
        RAISE EXCEPTION 'Seed invalida: minimo linhas por orcamento = % (esperado >= 15)', v_min_linhas;
    END IF;

    IF v_orc_cancelado_fora_projeto > 0 THEN
        RAISE EXCEPTION 'Seed invalida: existem % orcamentos arquivados fora de projetos cancelados', v_orc_cancelado_fora_projeto;
    END IF;

    IF v_projetos_ativos_sem_aprovado > 0 THEN
        RAISE EXCEPTION 'Seed invalida: existem % projetos ativos sem orcamento avancado (enviado/adjudicado/em_execucao/concluido)', v_projetos_ativos_sem_aprovado;
    END IF;

    IF v_projetos_analise_com_aprovado > 0 THEN
        RAISE EXCEPTION 'Seed invalida: existem % projetos em_analise com orcamento ja avancado (validado/enviado/adjudicado/em_execucao/concluido)', v_projetos_analise_com_aprovado;
    END IF;

    IF v_pct_aco NOT BETWEEN 69 AND 71
       OR v_pct_alumínio NOT BETWEEN 19 AND 21
       OR v_pct_inox NOT BETWEEN 9 AND 11 THEN
        RAISE EXCEPTION
            'Seed invalida: distribuicao material fora do alvo. aco=% alumínio=% inox=%',
            v_pct_aco, v_pct_alumínio, v_pct_inox;
    END IF;

    -- Cap de custo deve ser respeitado: nenhum orcamento acima de 50.000 EUR.
    IF v_orc_max > 50000 THEN
        RAISE EXCEPTION 'Seed invalida: orcamento com custo % EUR (esperado <= 50.000)', v_orc_max;
    END IF;

    IF v_orc_5k < 100 OR v_orc_15k < 100 OR v_orc_30k < 100 OR v_orc_45k < 100 THEN
        RAISE NOTICE
            'Distribuicao abaixo do alvo (minimo 100 por faixa): 0-5k=% 5-15k=% 15-30k=% 30-50k=% (max=%)',
            v_orc_5k, v_orc_15k, v_orc_30k, v_orc_45k, v_orc_max;
    END IF;
END $$;

COMMIT;

-- Resumo rapido
SELECT 'orcamentos' AS metrica, count(*)::text AS valor FROM public.orcamento
UNION ALL
SELECT 'projetos', count(*)::text FROM public.projeto
UNION ALL
SELECT 'projetos_multiversao_5pct', count(*)::text
FROM (
    SELECT id_projeto
    FROM public.orcamento
    GROUP BY id_projeto
    HAVING count(*) > 1
) t
UNION ALL
SELECT 'projetos_concluidos_50pct', count(*)::text FROM public.projeto WHERE estado = 'concluido'
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
        WHEN p.material_principal IN ('AL6060', 'AL5754') THEN 'alumínio'
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

-- Distribuicao de custos por faixa (cap de 50.000 EUR aplicado).
SELECT
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 0 AND 5000)      AS faixa_ate_5k,
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 5000 AND 15000)  AS faixa_5k_15k,
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 15000 AND 30000) AS faixa_15k_30k,
    count(*) FILTER (WHERE custo_total_orcado BETWEEN 30000 AND 50000) AS faixa_30k_50k,
    count(*) FILTER (WHERE custo_total_orcado > 50000)                 AS faixa_acima_50k_INVALIDO,
    round(min(custo_total_orcado)::numeric, 2) AS custo_min,
    round(avg(custo_total_orcado)::numeric, 2) AS custo_medio,
    round(max(custo_total_orcado)::numeric, 2) AS custo_max
FROM public.orcamento;

-- Distribuicao de versoes por projeto (alvo: 50/50 entre v1 e v1+v2)
SELECT
    versoes_por_projeto,
    count(*) AS projetos,
    round(count(*) * 100.0 / sum(count(*)) OVER (), 1) AS pct
FROM (
    SELECT id_projeto, count(*) AS versoes_por_projeto
    FROM public.orcamento
    GROUP BY id_projeto
) t
GROUP BY versoes_por_projeto
ORDER BY versoes_por_projeto;

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

-- Diagnostico de relacao peso/custo ao nivel do orcamento (v1)
SELECT
    round(min(ratio_kg_por_euro)::numeric, 4) AS min_kg_por_euro,
    round(percentile_cont(0.25) WITHIN GROUP (ORDER BY ratio_kg_por_euro)::numeric, 4) AS p25_kg_por_euro,
    round(percentile_cont(0.50) WITHIN GROUP (ORDER BY ratio_kg_por_euro)::numeric, 4) AS mediana_kg_por_euro,
    round(percentile_cont(0.75) WITHIN GROUP (ORDER BY ratio_kg_por_euro)::numeric, 4) AS p75_kg_por_euro,
    round(max(ratio_kg_por_euro)::numeric, 4) AS max_kg_por_euro
FROM (
    SELECT
        o.id_orcamento,
        CASE
            WHEN o.custo_total_orcado > 0 THEN o.peso_total_kg / o.custo_total_orcado
            ELSE NULL
        END AS ratio_kg_por_euro
    FROM public.orcamento o
    WHERE o.versao = 'v1'
) t;
