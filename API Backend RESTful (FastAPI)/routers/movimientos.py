# ============================================================
# routers/movimientos.py — CRUD completo de movimientos con filtros y paginación
# Ruta base: /api/movimientos
# ============================================================

from typing import List, Optional, Literal, Union
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from models import IngresoGasto, Categoria, Usuario
from schemas import (
    MovimientoCreate,
    MovimientoUpdate,
    MovimientoResponse,
    MovimientosPaginadosResponse,
    MensajeResponse,
)
from core.security import get_current_user

router = APIRouter(prefix="/api/movimientos", tags=["Movimientos"])


def _enriquecer_movimiento(mov: IngresoGasto) -> MovimientoResponse:
    """
    Convierte un modelo ORM en un MovimientoResponse agregando
    el nombre de la categoría para legibilidad en el cliente.
    """
    resp = MovimientoResponse.model_validate(mov)
    resp.nombre_categoria = mov.categoria.nombre if mov.categoria else f"Cat #{mov.id_categoria}"
    return resp


@router.get(
    "",
    response_model=Union[List[MovimientoResponse], MovimientosPaginadosResponse],
    summary="Listar movimientos del usuario con filtros avanzados y paginación",
)
def listar_movimientos(
    desde:        Optional[date] = Query(None, description="Fecha inicial (YYYY-MM-DD)"),
    hasta:        Optional[date] = Query(None, description="Fecha final (YYYY-MM-DD)"),
    id_categoria: Optional[int]  = Query(None, description="Filtrar por categoría específica"),
    tipo:         Optional[Literal["ingreso", "gasto"]] = Query(None, description="'ingreso' o 'gasto'"),
    monto_min:    Optional[Decimal] = Query(None, ge=0, description="Monto mínimo"),
    monto_max:    Optional[Decimal] = Query(None, ge=0, description="Monto máximo"),
    limit:        int = Query(50, ge=1, le=500, description="Cantidad máxima de resultados por página"),
    offset:       int = Query(0, ge=0, description="Desplazamiento para paginación"),
    paginado:     bool = Query(False, description="Si es True devuelve metadata de paginación (total, limit, offset)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Retorna los movimientos financieros del usuario autenticado con filtros opcionales:
    - Rango de fechas (`desde` y `hasta`)
    - Categoría específica (`id_categoria`)
    - Tipo (`ingreso` / `gasto`)
    - Rango de montos (`monto_min` y `monto_max`)
    - Paginación (`limit` y `offset`)
    """
    query = (
        db.query(IngresoGasto)
        .filter(IngresoGasto.id_usuario == current_user.id_usuario)
    )

    if desde:
        query = query.filter(IngresoGasto.fecha >= desde)
    if hasta:
        query = query.filter(IngresoGasto.fecha <= hasta)
    if id_categoria:
        query = query.filter(IngresoGasto.id_categoria == id_categoria)
    if tipo:
        query = query.filter(IngresoGasto.tipo == tipo)
    if monto_min is not None:
        query = query.filter(IngresoGasto.monto >= monto_min)
    if monto_max is not None:
        query = query.filter(IngresoGasto.monto <= monto_max)

    total_count = query.count()

    movimientos = (
        query.order_by(IngresoGasto.fecha.desc(), IngresoGasto.id_movimiento.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    items = [_enriquecer_movimiento(m) for m in movimientos]

    if paginado:
        return MovimientosPaginadosResponse(
            total=total_count,
            limit=limit,
            offset=offset,
            items=items,
        )

    return items


@router.post(
    "",
    response_model=MovimientoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo movimiento financiero",
)
def crear_movimiento(
    payload: MovimientoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Registra un ingreso o gasto para el usuario autenticado:
    - Valida que la categoría exista y pertenezca al usuario.
    - Valida que el tipo de movimiento coincida con el tipo de la categoría.
    """
    categoria = (
        db.query(Categoria)
        .filter(
            Categoria.id_categoria == payload.id_categoria,
            Categoria.id_usuario == current_user.id_usuario,
        )
        .first()
    )
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La categoría con ID {payload.id_categoria} no existe o no pertenece a tu cuenta.",
        )

    if categoria.tipo != payload.tipo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Inconsistencia: La categoría '{categoria.nombre}' es de tipo '{categoria.tipo}', pero el movimiento es de tipo '{payload.tipo}'.",
        )

    nuevo = IngresoGasto(
        id_usuario=current_user.id_usuario,
        id_categoria=payload.id_categoria,
        tipo=payload.tipo,
        monto=payload.monto,
        fecha=payload.fecha,
        descripcion=payload.descripcion.strip() if payload.descripcion else None,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return _enriquecer_movimiento(nuevo)


@router.get(
    "/{id_movimiento}",
    response_model=MovimientoResponse,
    summary="Obtener un movimiento por su ID",
)
def obtener_movimiento(
    id_movimiento: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Retorna los datos de un movimiento específico del usuario."""
    mov = (
        db.query(IngresoGasto)
        .filter(
            IngresoGasto.id_movimiento == id_movimiento,
            IngresoGasto.id_usuario == current_user.id_usuario,
        )
        .first()
    )
    if not mov:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movimiento {id_movimiento} no encontrado",
        )
    return _enriquecer_movimiento(mov)


@router.put(
    "/{id_movimiento}",
    response_model=MovimientoResponse,
    summary="Actualizar un movimiento existente",
)
def actualizar_movimiento(
    id_movimiento: int,
    payload: MovimientoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Actualiza parcialmente los campos de un movimiento del usuario autenticado.
    """
    mov = (
        db.query(IngresoGasto)
        .filter(
            IngresoGasto.id_movimiento == id_movimiento,
            IngresoGasto.id_usuario == current_user.id_usuario,
        )
        .first()
    )
    if not mov:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movimiento {id_movimiento} no encontrado",
        )

    # Validar cambio de categoría si se suministra
    if payload.id_categoria is not None and payload.id_categoria != mov.id_categoria:
        categoria = (
            db.query(Categoria)
            .filter(
                Categoria.id_categoria == payload.id_categoria,
                Categoria.id_usuario == current_user.id_usuario,
            )
            .first()
        )
        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"La categoría {payload.id_categoria} no pertenece a tu cuenta.",
            )
        tipo_final = payload.tipo or mov.tipo
        if categoria.tipo != tipo_final:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"La categoría '{categoria.nombre}' ({categoria.tipo}) no coincide con el tipo '{tipo_final}'.",
            )
        mov.id_categoria = payload.id_categoria

    if payload.tipo is not None:
        mov.tipo = payload.tipo
    if payload.monto is not None:
        mov.monto = payload.monto
    if payload.fecha is not None:
        mov.fecha = payload.fecha
    if payload.descripcion is not None:
        mov.descripcion = payload.descripcion.strip() if payload.descripcion else None

    db.commit()
    db.refresh(mov)
    return _enriquecer_movimiento(mov)


@router.delete(
    "/{id_movimiento}",
    response_model=MensajeResponse,
    summary="Eliminar un movimiento",
)
def eliminar_movimiento(
    id_movimiento: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Elimina un movimiento financiero perteneciente al usuario."""
    mov = (
        db.query(IngresoGasto)
        .filter(
            IngresoGasto.id_movimiento == id_movimiento,
            IngresoGasto.id_usuario == current_user.id_usuario,
        )
        .first()
    )
    if not mov:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movimiento {id_movimiento} no encontrado",
        )

    db.delete(mov)
    db.commit()
    return MensajeResponse(mensaje=f"Movimiento #{id_movimiento} eliminado correctamente")
