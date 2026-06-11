# Carregamento da Base de Dados

Esta pasta contém scripts SQL separados por área para carregar dados realistas na base de dados. Os scripts assumem que a estrutura da base de dados já existe e que as migrações da aplicação já foram aplicadas.

## Ordem de execução

Executar os ficheiros pela numeração:

1. `00_truncate_restart.sql`
2. `01_utilizadores.sql`
3. `02_clientes.sql`
4. `03_material.sql`
5. `04_operacoes.sql`
6. `05_servicos.sql`
7. `06_projetos.sql`
8. `07_orcamentos.sql`
9. `08_realizado.sql`

O script `00_truncate_restart.sql` limpa as tabelas principais e reinicia as sequências. Deve ser usado quando se pretende carregar uma base de dados limpa.

## Utilizadores

O ficheiro `01_utilizadores.sql` cria quatro utilizadores base:

- Administrador
- Gestor
- Orçamentista
- Produção

As passwords estão indicadas em comentário no próprio script. Os emails são usados pelos scripts seguintes para associar projetos e orçamentos aos utilizadores corretos.

## Clientes

O ficheiro `02_clientes.sql` cria pelo menos 25 clientes ligados à área da metalomecânica e indústria:

- empresas de estruturas metálicas;
- serralharia técnica;
- acessos industriais;
- inox e alumínio;
- manutenção fabril;
- logística, portos, indústria química, papel, vidro e componentes industriais.

Os clientes têm NIF, email, telefone, morada e observações curtas em português.

## Materiais

O ficheiro `03_material.sql` carrega um catálogo amplo de materiais usados em orçamentação metalomecânica:

- tubos quadrados, retangulares e redondos;
- perfis HEA, IPE, UPN, barras e cantoneiras;
- chapas laser em aço S235JR, S355JR, inox e alumínio;
- piso grelhado;
- parafusaria, buchas, chumbadouros e ferragens;
- consumíveis de corte, soldadura e acabamento;
- materiais de embalamento, como filme, cinta, paletes e espuma.

Os códigos são curtos e descritivos, para serem fáceis de identificar nas linhas dos orçamentos.

## Operações

O ficheiro `04_operacoes.sql` cria operações reais de produção industrial, com custo por hora e tempo de setup:

- engenharia e planeamento;
- corte laser, serra, plasma e guilhotina;
- furação, roscagem, fresagem e torneamento;
- quinagem e calandragem;
- pingamento, ponteamento, soldadura MIG/MAG e TIG;
- montagem em bancada e em obra;
- rebarbagem, lixagem, escovagem e retoques;
- controlo dimensional, ensaios, embalamento e expedição.

Cada orçamento criado depois recebe sempre as fases essenciais: engenharia, pingamento, soldadura, rebarbagem e qualidade. Outras operações entram conforme a tipologia, material, complexidade e versão.

## Serviços

O ficheiro `05_servicos.sql` cria serviços externos comuns:

- galvanização, zincagem, pintura, lacagem e anodização;
- decapagem, passivação e polimento inox;
- corte laser externo, quinagem externa e maquinação externa;
- ensaios, certificações, projeto técnico externo;
- montagem externa, grua, empilhador, transporte e embalagem especial.

Os serviços escolhidos para cada orçamento respeitam o tipo de tratamento superficial, material e dimensão do projeto.

## Projetos

O ficheiro `06_projetos.sql` cria 5000 projetos com referências no formato:

```text
PRJ-2026-00001
```

As designações ficam com nomes normais e legíveis, por exemplo:

```text
Passadiço metálico - PRJ-2026-00001
Guarda-corpos industrial - PRJ-2026-00004
Estrutura de pavilhão - PRJ-2026-00010
```

As tipologias incluem passadiços, passarelas, passerelles, guarda-corpos, corrimãos, escadarias, plataformas, mezaninos, coberturas, pavilhões, portões, gradeamentos, bastidores, subestruturas, proteções de máquina e chassis.

Os estados são distribuídos de forma controlada:

- 50% concluído;
- 20% em execução;
- 10% aprovado;
- 8% planeado;
- 8% em análise;
- 4% cancelado.

A escolha do material principal respeita a lógica industrial. Estruturas pesadas usam S235JR ou S355JR. Acessos, guarda-corpos e corrimãos podem usar aço, inox ou alumínio conforme o caso.

## Orçamentos

O ficheiro `07_orcamentos.sql` cria os orçamentos dos projetos.

Regras principais:

- são gerados 5250 orçamentos no total;
- existem 5000 projetos;
- 5% dos projetos têm mais de uma versão;
- os projetos multiversão recebem `v1` e `v2`;
- os restantes recebem apenas `v1`;
- o campo `quantidade_unidades` é criado se ainda não existir;
- as observações do orçamento e das suas linhas ficam sem texto, com `NULL`.

O estado do último orçamento acompanha o estado do projeto:

- projeto `em_analise` -> orçamento `em_preparacao`;
- projeto `planeado` -> orçamento `enviado`;
- projeto `aprovado` -> orçamento `adjudicado`;
- projeto `em_execucao` -> orçamento `em_execucao`;
- projeto `concluido` -> orçamento `concluido`;
- projeto `cancelado` -> orçamento `arquivado`.

Quando um projeto tem mais de uma versão, as versões antigas ficam em `rejeitado`, tal como a aplicação faz quando é criada uma nova versão. Assim preservam histórico, ficam com as linhas bloqueadas e não aparecem como a versão ativa do projeto.

Cada orçamento é completo. Não são criadas folhas com poucas linhas apenas para preencher dados.

Cada orçamento recebe:

- 8 linhas de material;
- no mínimo 12 linhas de operações;
- algumas operações extra quando fizer sentido;
- 3 linhas de serviços.

Os totais do orçamento são recalculados a partir das linhas:

- custo de materiais;
- custo de operações;
- custo de serviços;
- custo total orçado;
- preço de venda;
- peso total;
- área total.

O peso total e a área total do orçamento são a soma das linhas de material. Os custos de materiais, operações e serviços consideram a quantidade de unidades do orçamento.

## Realizado

O ficheiro `08_realizado.sql` cria custos reais para parte dos orçamentos.

São gerados registos reais para:

- materiais;
- operações;
- serviços.

No carregamento inicial, o realizado respeita a fase do trabalho:

- orçamentos `concluido` ficam com todas as linhas reais preenchidas, porque representam trabalhos fechados;
- parte dos orçamentos `em_execucao` fica com realizado parcial;
- parte dos orçamentos `em_execucao` fica ainda sem realizado, simulando trabalhos que arrancaram mas ainda não tiveram custos registados.

Não é criado realizado para orçamentos em `em_preparacao`, `enviado`, `em_revisao`, `rejeitado` ou `arquivado`, porque esses estados ainda não representam trabalho adjudicado e executado. Também não é criado realizado para `adjudicado` sem execução, para não simular custos de produção antes do arranque do trabalho.

Na aplicação, novos registos de realizado podem ser introduzidos em orçamentos `em_execucao` e `concluido` (este último para correções pós-fecho). Os restantes estados ficam bloqueados.

Os desvios são gerados face ao custo orçado (sem margem), que é a base usada pela Comparação: a maioria dos orçamentos concluídos fica dentro do custo orçado, cerca de 20% fica com derrapagem (até +20%) e alguns ficam com folga grande. O desvio entra pelas quantidades e horas reais (os preços reais ficam próximos do snapshot), pelo que o desvio das horas acompanha o desvio do custo das operações.

## Validações incluídas

Os scripts de projetos, orçamentos e realizado têm validações internas com `RAISE EXCEPTION`. Se a carga ficar incoerente, o script falha em vez de deixar dados incompletos.

As validações verificam, entre outros pontos:

- quantidade de projetos carregados;
- clientes disponíveis;
- projetos multiversão;
- número esperado de orçamentos;
- mínimo de linhas por orçamento;
- existência das fases obrigatórias;
- coerência entre peso/área do orçamento e soma das linhas;
- existência de realizado para os orçamentos esperados.

## Observação importante

Estes scripts são para popular a base de dados. Não substituem as migrações nem criam todo o modelo da aplicação.
