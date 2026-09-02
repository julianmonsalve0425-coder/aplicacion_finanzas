# ============================================================
# routers/categorias.py — Endpoints para gestión de categorías
# Ruta base: /api/categorias
# ============================================================

from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Categoria, Usuario
from schemas import CategoriaCreate, CategoriaResponse, MensajeResponse
from core.security import get_current_user

router = APIRouter(prefix="/api/categorias", tags=["Categorías"])


@router.get(
    "",
    response_model=List[CategoriaResponse],
    summary="Listar categorías del usuario autenticado",
)
def listar_categorias(
    tipo: Optional[Literal["ingreso", "gasto"]] = Query(None, description="Filtrar por 'ingreso' o 'gasto'"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna todas las categorías asociadas al usuario autenticado mediante JWT.
    Permite filtrar opcionalmente por tipo.
    """
    query = (
        db.query(Categoria)
        .filter(Categoria.id_usuario == current_user.id_usuario)
        .order_by(Categoria.tipo, Categoria.nombre)
    )

    if tipo:
        query = query.filter(Categoria.tipo == tipo)

    return query.all()


@router.post(
    "",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva categoría",
)
def crear_categoria(
    payload: CategoriaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Crea una categoría asociada al usuario autenticado.
    - Valida que no exista duplicado (mismo nombre y tipo para el usuario).
    """
    nombre_limpio = payload.nombre.strip()

    existente = (
        db.query(Categoria)
        .filter(
            Categoria.id_usuario == current_user.id_usuario,
            Categoria.nombre.ilike(nombre_limpio),
            Categoria.tipo == payload.tipo,
        )
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya tienes una categoría llamada '{nombre_limpio}' de tipo '{payload.tipo}'",
        )

    nueva = Categoria(
        nombre=nombre_limpio,
        tipo=payload.tipo,
        id_usuario=current_user.id_usuario,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva


@router.delete(
    "/{id_categoria}",
    response_model=MensajeResponse,
    summary="Eliminar una categoría",
)
def eliminar_categoria(
    id_categoria: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Elimina una categoría del usuario.
    - Retorna 404 si la categoría no existe o no pertenece al usuario.
    - Retorna 409 si la categoría tiene movimientos o presupuestos asociados.
    """
    categoria = (
        db.query(Categoria)
        .filter(
            Categoria.id_categoria == id_categoria,
            Categoria.id_usuario == current_user.id_usuario,
        )
        .first()
    )
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Categoría con ID {id_categoria} no encontrada",
        )

    try:
        db.delete(categoria)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No se puede eliminar la categoría porque tiene movimientos financieros o presupuestos asociados",
        )

    return MensajeResponse(mensaje=f"Categoría '{categoria.nombre}' eliminada con éxito")
