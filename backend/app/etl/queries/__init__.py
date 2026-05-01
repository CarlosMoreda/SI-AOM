from typing import Final

from app.etl.queries.orcamento_query import ORCAMENTO_QUERY

DATASET_QUERIES: Final[dict[str, str]] = {
    "orcamento": ORCAMENTO_QUERY,
}

__all__ = [
    "ORCAMENTO_QUERY",
    "DATASET_QUERIES",
]
