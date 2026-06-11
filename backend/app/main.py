import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import models  # noqa: F401
from app.config import settings
from app.dependencies import ROLE_ADMIN, require_roles
from app.database import engine
from app.ml_cache import MLModelCache
from app.routers import (
    auth,
    clientes,
    comparacao,
    dashboard,
    detalhes_orcamento,
    materiais,
    ml,
    operacoes,
    orcamentos,
    projetos,
    realizado,
    servicos,
    utilizadores,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-carrega os modelos de ML uma unica vez no arranque.

    Sem este cache, cada chamada a /ml/orcamento/prever liberta ~9 s a
    desserializar 4 ficheiros .joblib de ~82 MB do disco. Com cache, o
    primeiro pedido demora <300 ms e os seguintes ficam ainda mais rapidos.
    """
    cache = MLModelCache()
    cache.load_all()
    app.state.ml_cache = cache
    try:
        yield
    finally:
        cache.clear()
        logger.info("[lifespan] Cache de ML libertada no shutdown.")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Permite que o frontend leia o total de registos para a paginacao.
    expose_headers=["X-Total-Count"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(clientes.router, prefix="/clientes", tags=["Clientes"])
app.include_router(
    utilizadores.router,
    prefix="/utilizadores",
    tags=["Utilizadores"],
)
app.include_router(projetos.router, prefix="/projetos", tags=["Projetos"])
app.include_router(
    orcamentos.router,
    prefix="/orcamentos",
    tags=["Orcamentos"],
)
app.include_router(materiais.router, prefix="/materiais", tags=["Materiais"])
app.include_router(operacoes.router, prefix="/operacoes", tags=["Operacoes"])
app.include_router(servicos.router, prefix="/servicos", tags=["Servicos"])
app.include_router(
    detalhes_orcamento.router,
    prefix="/orcamentos",
    tags=["Detalhes Orcamento"],
)
app.include_router(realizado.router, prefix="/realizado", tags=["Realizado"])
app.include_router(
    comparacao.router,
    prefix="/comparacao",
    tags=["Comparacao"],
)
app.include_router(ml.router, prefix="/ml", tags=["ML"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])


@app.get("/")
def root():
    return {"app": settings.app_name, "status": "online"}


@app.get("/db-test", dependencies=[Depends(require_roles(ROLE_ADMIN))])
def db_test():
    with engine.connect() as conn:
        value = conn.execute(text("SELECT 1")).scalar()
    return {"database": "connected", "result": value}
