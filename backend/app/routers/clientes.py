from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    ROLE_GESTOR,
    ROLE_ORCAMENTISTA,
    get_db,
    require_roles,
)
from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate, ClienteResponse, ClienteUpdate

router = APIRouter(
    dependencies=[Depends(require_roles(ROLE_ORCAMENTISTA, ROLE_GESTOR, ROLE_ADMIN))]
)


@router.get("/", response_model=list[ClienteResponse])
def listar_clientes(db: Session = Depends(get_db)):
    stmt = select(Cliente).order_by(Cliente.ativo.desc(), Cliente.nome.asc())
    return db.scalars(stmt).all()


@router.get("/{id_cliente}", response_model=ClienteResponse)
def obter_cliente(id_cliente: int, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, id_cliente)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente nao encontrado")
    return cliente


@router.post("/", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
def criar_cliente(payload: ClienteCreate, db: Session = Depends(get_db)):
    cliente = Cliente(**payload.model_dump())
    db.add(cliente)

    try:
        db.commit()
        db.refresh(cliente)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao foi possivel criar o cliente com os dados enviados",
        )

    return cliente


@router.put("/{id_cliente}", response_model=ClienteResponse)
def atualizar_cliente(id_cliente: int, payload: ClienteUpdate, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, id_cliente)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente nao encontrado")

    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)

    try:
        db.commit()
        db.refresh(cliente)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nao foi possivel atualizar o cliente",
        )

    return cliente


@router.delete("/{id_cliente}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_cliente(id_cliente: int, db: Session = Depends(get_db)):
    cliente = db.get(Cliente, id_cliente)
    if not cliente:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente nao encontrado")

    db.delete(cliente)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao e possivel eliminar: cliente associado a projetos",
        )
    return None
