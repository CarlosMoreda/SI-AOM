from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import (
    ROLE_ADMIN,
    ROLE_GESTOR,
    ROLE_ORCAMENTISTA,
    ROLE_PRODUCAO,
    get_db,
    require_roles,
)
from app.models.material import Material
from app.schemas.material import MaterialCreate, MaterialResponse, MaterialUpdate

# Producao/Gestor precisam de LER o catalogo para resolver IDs em nomes.
# So orcamentista+admin podem editar o catalogo.
READ_DEPS = [Depends(require_roles(
    ROLE_ORCAMENTISTA, ROLE_GESTOR, ROLE_PRODUCAO, ROLE_ADMIN,
))]
WRITE_DEPS = [Depends(require_roles(ROLE_ORCAMENTISTA, ROLE_ADMIN))]

router = APIRouter()


@router.get("/", response_model=list[MaterialResponse], dependencies=READ_DEPS)
def listar_materiais(
    response: Response,
    q: str | None = Query(None, description="Pesquisa por codigo ou nome"),
    limit: int | None = Query(
        default=None, ge=1, le=500,
        description="Registos por pagina. Omitir devolve todos (catalogo).",
    ),
    offset: int = Query(default=0, ge=0, description="Deslocamento (pagina)"),
    db: Session = Depends(get_db),
):
    base = select(Material)
    if q:
        termo = func.unaccent(f"%{q.lower()}%")
        base = base.where(
            or_(
                func.unaccent(func.lower(Material.codigo)).like(termo),
                func.unaccent(func.lower(Material.nome)).like(termo),
            )
        )

    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    response.headers["X-Total-Count"] = str(total)

    stmt = base.order_by(Material.id_material.desc())
    if limit is not None:
        stmt = stmt.limit(limit).offset(offset)
    return db.scalars(stmt).all()


@router.get("/{id_material}", response_model=MaterialResponse, dependencies=READ_DEPS)
def obter_material(id_material: int, db: Session = Depends(get_db)):
    material = db.get(Material, id_material)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Material não encontrado")
    return material


@router.post(
    "/",
    response_model=MaterialResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=WRITE_DEPS,
)
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


@router.put("/{id_material}", response_model=MaterialResponse, dependencies=WRITE_DEPS)
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


@router.delete(
    "/{id_material}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=WRITE_DEPS,
)
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
