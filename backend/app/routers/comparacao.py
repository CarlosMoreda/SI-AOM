from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    ROLE_GESTOR,
    ROLE_ORCAMENTISTA,
    ROLE_PRODUCAO,
    get_db,
    require_roles,
)
from app.schemas.comparacao import ComparacaoOrcamentoResponse
from app.services.comparacao_service import obter_comparacao_orcamento

router = APIRouter(
    dependencies=[
        Depends(
            require_roles(
                ROLE_ORCAMENTISTA,
                ROLE_GESTOR,
                ROLE_PRODUCAO,
                ROLE_ADMIN,
            )
        )
    ]
)


@router.get("/orcamento/{id_orcamento}", response_model=ComparacaoOrcamentoResponse)
def comparar_orcamento_vs_real(id_orcamento: int, db: Session = Depends(get_db)):
    resultado = obter_comparacao_orcamento(db, id_orcamento)

    if not resultado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Orçamento não encontrado",
        )

    return resultado
