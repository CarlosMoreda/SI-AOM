from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    ROLE_GESTOR,
    ROLE_ORCAMENTISTA,
    get_db,
    require_roles,
)
from app.schemas.ml import (
    MLPredictCustoRequest,
    MLPredictCustoResponse,
    MLPredictOptionsResponse,
    MLTrainOrcamentoRequest,
    MLTrainResponse,
)
from app.services.ml_service import (
    get_orcamento_options,
    predict_custo_from_params,
    save_custo_prediction,
    train_models,
)

router = APIRouter(
    dependencies=[Depends(require_roles(ROLE_ORCAMENTISTA, ROLE_GESTOR, ROLE_ADMIN))]
)


@router.post("/orcamento/prever", response_model=MLPredictCustoResponse)
def ml_orcamento_prever(
    payload: MLPredictCustoRequest,
    db: Session = Depends(get_db),
):
    """Preve o custo real de um projeto a partir das suas features tecnicas.

    A previsao e persistida em previsao_ml para permitir feedback loop
    (comparar previsto vs orcado/realizado posterior).
    """
    parametros_modelo = payload.model_dump(exclude={"id_orcamento", "observacoes"})

    try:
        resultado = predict_custo_from_params(parametros=parametros_modelo)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    resultado["id_previsao"] = save_custo_prediction(
        db=db,
        id_orcamento=payload.id_orcamento,
        parametros=parametros_modelo,
        resultado=resultado,
        observacoes=payload.observacoes,
    )
    return resultado


@router.get("/orcamento/opcoes", response_model=MLPredictOptionsResponse)
def ml_orcamento_opcoes():
    """Valores e faixas conhecidos pelo modelo (preenche dropdowns no frontend)."""
    return get_orcamento_options()


@router.post(
    "/orcamento/treinar",
    response_model=MLTrainResponse,
    dependencies=[Depends(require_roles(ROLE_ADMIN))],
)
def ml_orcamento_treinar(payload: MLTrainOrcamentoRequest):
    """Treina os 3 sub-modelos de previsao de custo (materiais/operacoes/servicos)."""
    results = train_models(
        dataset_dir=payload.dataset_dir,
        output_dir=payload.output_dir,
        refresh_dataset=payload.refresh_dataset,
        test_size=payload.test_size,
        random_state=payload.random_state,
        n_estimators=payload.n_estimators,
        max_depth=payload.max_depth,
        min_samples_leaf=payload.min_samples_leaf,
        csv_delimiter=payload.csv_delimiter,
        csv_encoding=payload.csv_encoding,
    )
    success = sum(1 for row in results if row["status"] == "ok")
    failure = len(results) - success
    return {
        "total": len(results),
        "success": success,
        "failure": failure,
        "results": results,
    }
