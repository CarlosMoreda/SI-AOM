# Migracoes

Este scaffold usa os modelos SQLAlchemy em `app/models` e a `DATABASE_URL` do
ficheiro `.env`.

Com uma BD existente, cria primeiro uma revisao de baseline e marca-a como
aplicada depois de confirmares que o autogenerate nao quer recriar tabelas ja
existentes:

```bash
alembic revision --autogenerate -m "baseline"
alembic stamp head
```

Para alterações futuras:

```bash
alembic revision --autogenerate -m "descricao da alteracao"
alembic upgrade head
```
