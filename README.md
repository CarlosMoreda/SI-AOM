# SI-AOM

Sistema de Informacao para Apoio a Orcamentacao e Monitorizacao de fabrico.

O SI-AOM e uma aplicacao web para gerir clientes, projetos, orcamentos,
materiais, operacoes, servicos, custos realizados e previsoes de custo com ML.

## Funcionalidades

- Autenticacao com JWT
- Gestao de clientes
- Gestao de utilizadores e perfis
- Gestao de projetos
- Criacao e acompanhamento de orcamentos
- Registo de materiais, operacoes e servicos
- Registo de custos realizados
- Comparacao entre valores orcados e realizados
- Dashboard operacional
- Modulo ML para previsao de custos

## Tecnologias

### Frontend

- React
- Vite
- JavaScript
- CSS
- Node test runner
- ESLint

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Alembic
- Pytest

### Base De Dados

- PostgreSQL

### Machine Learning

- pandas
- scikit-learn
- joblib

## Estrutura Do Projeto

```text
SI-AOM/
|-- backend/
|   |-- app/
|   |   |-- etl/
|   |   |-- ml/
|   |   |-- models/
|   |   |-- routers/
|   |   |-- schemas/
|   |   `-- services/
|   |-- alembic/
|   |-- ml/
|   |-- sql/
|   `-- tests/
|-- frontend/
|   |-- public/
|   |-- src/
|   |   |-- components/
|   |   |-- hooks/
|   |   |-- modules/
|   |   |-- services/
|   |   |-- style/
|   |   `-- utils/
|   `-- test/
`-- README.md
```

## Requisitos

- Python 3.12+
- Node.js
- npm
- PostgreSQL

## Configuracao

### Backend

Cria o ficheiro `backend/.env` com base em `backend/.env.example`.

```env
DATABASE_URL=postgresql+psycopg://postgres:password@localhost:5432/SI_AOM
DEBUG=True
JWT_SECRET=dev-only-secret
JWT_EXPIRE_MINUTES=480
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### Frontend

Cria o ficheiro `frontend/.env` com base em `frontend/.env.example`, se precisares de alterar a URL da API.

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Instalar E Correr

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Documentacao da API:

```text
http://127.0.0.1:8000/docs
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Aplicacao:

```text
http://localhost:5173
```

## Testes E Checks

### Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m pip check
```

### Frontend

```powershell
cd frontend
npm test
npm run lint
npm run build
```

## Base De Dados

O backend usa PostgreSQL atraves da variavel `DATABASE_URL`.

Para popular a base de dados local com dados de teste:

```powershell
psql -U postgres -d SI_AOM -f backend/sql/reset_seed_500_orcamentos.sql
```

Utilizadores de teste:

```text
admin@siaom.local    / Admin@123
gestor@siaom.local   / Gestor@123
orc@siaom.local      / Orc@123
producao@siaom.local / Prod@123
```

## Modulo ML

Exportar dataset a partir da base de dados:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.etl.dataset --output ml/dataset_orcamento.csv
```

Treinar modelos:

```powershell
cd backend
.\.venv\Scripts\python.exe -m app.ml.train_random_forest
```

## Perfis

- `administrador`: acesso global e gestao de utilizadores
- `gestor`: acompanhamento e consulta operacional
- `orcamentista`: gestao de clientes, projetos, orcamentos e previsoes
- `producao`: registo de custos realizados

## Estado

Projeto em desenvolvimento academico.

## Licenca

Este projeto nao tem uma licenca definida.
