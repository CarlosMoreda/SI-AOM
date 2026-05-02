from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from app.database import engine
from app.etl.queries import DATASET_QUERIES


def build_dataset(dataset_type: str = "orcamento") -> pd.DataFrame:
    """Executa a query SQL do tipo pedido e devolve o DataFrame."""
    if dataset_type not in DATASET_QUERIES:
        raise ValueError(
            f"dataset_type '{dataset_type}' invalido (suportado: 'orcamento')"
        )
    return pd.read_sql_query(text(DATASET_QUERIES[dataset_type]), engine)


def export_dataset(
    output: Path,
    csv_delimiter: str,
    csv_encoding: str,
) -> None:
    dataset = build_dataset()
    csv_path = output if output.suffix.lower() == ".csv" else output.with_suffix(".csv")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(csv_path, index=False, sep=csv_delimiter, encoding=csv_encoding)
    print(f"[ETL-ML] orcamento: CSV criado: {csv_path} ({len(dataset)} linhas)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extrai dataset de treino ML (orcamento) a partir da BD",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ml/dataset_orcamento.csv"),
        help="Caminho do CSV de saida (default: ml/dataset_orcamento.csv)",
    )
    parser.add_argument("--csv-delimiter", default=";", help="Separador CSV (default: ;)")
    parser.add_argument("--csv-encoding", default="utf-8-sig", help="Encoding (default: utf-8-sig)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export_dataset(
        output=args.output,
        csv_delimiter=args.csv_delimiter,
        csv_encoding=args.csv_encoding,
    )


if __name__ == "__main__":
    main()
