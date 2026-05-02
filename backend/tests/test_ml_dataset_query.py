from app.etl.queries.orcamento_query import ORCAMENTO_QUERY


def test_orcamento_dataset_filters_rows_without_realizado():
    assert "WITH real_materiais AS" in ORCAMENTO_QUERY
    assert "COALESCE(rm.registos, 0)" in ORCAMENTO_QUERY
    assert ") > 0" in ORCAMENTO_QUERY
