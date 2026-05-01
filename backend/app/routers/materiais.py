from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    ROLE_ORCAMENTISTA,
    get_db,
    require_roles,
)
from app.models.material import Material
from app.schemas.material import MaterialCreate, MaterialResponse, MaterialUpdate

router = APIRouter(
    dependencies=[Depends(require_roles(ROLE_ORCAMENTISTA, ROLE_ADMIN))]
)


@router.get("/", response_model=list[MaterialResponse])
def listar_materiais(db: Session = Depends(get_db)):
    stmt = select(Material).order_by(Material.id_material.desc())
    return db.scalars(stmt).all()


@router.get("/{id_material}", response_model=MaterialResponse)
def obter_material(id_material: int, db: Session = Depends(get_db)):
    material = db.get(Material, id_material)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material não encontrado")
    return material


@router.post("/", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def criar_material(payload: MaterialCreate, db: Session = Depends(get_db)):
    material = Material(**payload.model_dump())
    db.add(material)

    try:
        db.commit()
        db.refresh(material)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código de material duplicado ou dados inválidos",
        )

    return material


@router.put("/{id_material}", response_model=MaterialResponse)
def atualizar_material(id_material: int, payload: MaterialUpdate, db: Session = Depends(get_db)):
    material = db.get(Material, id_material)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material não encontrado")

    for campo, valor in payload.model_dump(exclude_unset=True).items():
        setattr(material, campo, valor)

    try:
        db.commit()
        db.refresh(material)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível atualizar o material",
        )

    return material


@router.delete("/{id_material}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_material(id_material: int, db: Session = Depends(get_db)):
    material = db.get(Material, id_material)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material não encontrado")

    db.delete(material)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nao e possivel eliminar: material associado a orcamentos",
        )
    return None
