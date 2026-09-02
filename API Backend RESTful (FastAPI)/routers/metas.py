# ============================================================
# routers/metas.py — Endpoints para Metas de Ahorro
# Ruta base: /api/metas
# ============================================================

from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import MetaAhorro, Usuario
from schemas import (
    MetaAhorroCreate,
    MetaAhorroUpdate,
    MetaAhorroAbono,
    MetaAhorroResponse,
    MensajeResponse,
)
from core.security import get_current_user

router = APIRouter(prefix="/api/metas", tags=["Metas de Ahorro"])


def _enriquecer_meta(m: MetaAhorro) -> MetaAhorroResponse:
    """Calcula el porcentaje de avance de la meta de ahorro."""
    resp = MetaAhorroResponse.model_validate(m)
    if m.monto_objetivo and float(m.monto_objetivo) > 0:
        progreso = (float(m.monto_actual) / float(m.monto_objetivo)) * 100.0
        resp.porcentaje_progreso = round(min(100.0, progreso), 2)
    else:
        resp.porcentaje_progreso = 0.0
    return resp


@router.get(
    "",
    response_model=List[MetaAhorroResponse],
    summary="Listar metas de ahorro del usuario",
)
def listar_metas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Retorna todas las metas de ahorro del usuario con su progreso porcentual."""
    metas = (
        db.query(MetaAhorro)
        .filter(MetaAhorro.id_usuario == current_user.id_usuario)
        .order_by(MetaAhorro.completada.asc(), MetaAhorro.fecha_creacion.desc())
        .all()
    )
    return [_enriquecer_meta(m) for m in metas]


@router.post(
    "",
    response_model=MetaAhorroResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva meta de ahorro",
)
def crear_meta(
    payload: MetaAhorroCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Crea una nueva meta con objetivo monetario y fecha límite opcional."""
    monto_actual = payload.monto_actual or Decimal(0)
    completada = monto_actual >= payload.monto_objetivo

    nueva = MetaAhorro(
        id_usuario=current_user.id_usuario,
        nombre=payload.nombre.strip(),
        monto_objetivo=payload.monto_objetivo,
        monto_actual=monto_actual,
        fecha_limite=payload.fecha_limite,
        completada=completada,
    )
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return _enriquecer_meta(nueva)


@router.post(
    "/{id_meta}/abonar",
    response_model=MetaAhorroResponse,
    summary="Abonar saldo a una meta de ahorro",
)
def abonar_a_meta(
    id_meta: int,
    payload: MetaAhorroAbono,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Suma un aporte económico a la meta seleccionada.
    Marca la meta automáticamente como completada si alcanza o supera el objetivo.
    """
    meta = (
        db.query(MetaAhorro)
        .filter(
            MetaAhorro.id_meta == id_meta,
            MetaAhorro.id_usuario == current_user.id_usuario,
        )
        .first()
    )
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meta de ahorro #{id_meta} no encontrada",
        )

    meta.monto_actual += payload.monto
    if meta.monto_actual >= meta.monto_objetivo:
        meta.completada = True

    db.commit()
    db.refresh(meta)
    return _enriquecer_meta(meta)


@router.put(
    "/{id_meta}",
    response_model=MetaAhorroResponse,
    summary="Actualizar información de una meta",
)
def actualizar_meta(
    id_meta: int,
    payload: MetaAhorroUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza los valores de una meta existente."""
    meta = (
        db.query(MetaAhorro)
        .filter(
            MetaAhorro.id_meta == id_meta,
            MetaAhorro.id_usuario == current_user.id_usuario,
        )
        .first()
    )
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meta de ahorro #{id_meta} no encontrada",
        )

    if payload.nombre is not None:
        meta.nombre = payload.nombre.strip()
    if payload.monto_objetivo is not None:
        meta.monto_objetivo = payload.monto_objetivo
    if payload.monto_actual is not None:
        meta.monto_actual = payload.monto_actual
    if payload.fecha_limite is not None:
        meta.fecha_limite = payload.fecha_limite
    if payload.completada is not None:
        meta.completada = payload.completada
    elif meta.monto_actual >= meta.monto_objetivo:
        meta.completada = True

    db.commit()
    db.refresh(meta)
    return _enriquecer_meta(meta)


@router.delete(
    "/{id_meta}",
    response_model=MensajeResponse,
    summary="Eliminar una meta de ahorro",
)
def eliminar_meta(
    id_meta: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Elimina una meta de ahorro."""
    meta = (
        db.query(MetaAhorro)
        .filter(
            MetaAhorro.id_meta == id_meta,
            MetaAhorro.id_usuario == current_user.id_usuario,
        )
        .first()
    )
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meta de ahorro #{id_meta} no encontrada",
        )

    db.delete(meta)
    db.commit()
    return MensajeResponse(mensaje=f"Meta '{meta.nombre}' eliminada con éxito")
