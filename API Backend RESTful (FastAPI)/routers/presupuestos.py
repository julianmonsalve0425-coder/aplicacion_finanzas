# ============================================================
# routers/presupuestos.py — Endpoints para presupuestos mensuales
# Ruta base: /api/presupuestos
# ============================================================

from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from database import get_db
from models import Presupuesto, Categoria, IngresoGasto, Usuario
from schemas import (
    PresupuestoCreate,
    PresupuestoUpdate,
    PresupuestoResponse,
    PresupuestoResumenItem,
    PresupuestosResumenResponse,
    MensajeResponse,
)
from core.security import get_current_user

router = APIRouter(prefix="/api/presupuestos", tags=["Presupuestos"])


def _enriquecer_presupuesto(p: Presupuesto) -> PresupuestoResponse:
    resp = PresupuestoResponse.model_validate(p)
    resp.nombre_categoria = p.categoria.nombre if p.categoria else f"Cat #{p.id_categoria}"
    return resp


@router.get(
    "",
    response_model=List[PresupuestoResponse],
    summary="Listar presupuestos del usuario",
)
def listar_presupuestos(
    mes:  Optional[int] = Query(None, ge=1, le=12, description="Mes del presupuesto (1-12)"),
    anio: Optional[int] = Query(None, ge=2020, description="Año del presupuesto"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Retorna los presupuestos fijados por el usuario autenticado."""
    query = (
        db.query(Presupuesto)
        .filter(Presupuesto.id_usuario == current_user.id_usuario)
        .order_by(Presupuesto.anio.desc(), Presupuesto.mes.desc())
    )
    if mes:
        query = query.filter(Presupuesto.mes == mes)
    if anio:
        query = query.filter(Presupuesto.anio == anio)

    presupuestos = query.all()
    return [_enriquecer_presupuesto(p) for p in presupuestos]


@router.post(
    "",
    response_model=PresupuestoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear o actualizar presupuesto mensual por categoría",
)
def crear_presupuesto(
    payload: PresupuestoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Establece un límite de gasto mensual para una categoría.
    - La categoría debe pertenecer al usuario y ser de tipo 'gasto'.
    - Si ya existe un presupuesto para el mismo período y categoría, se actualiza el monto.
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
            detail=f"La categoría {payload.id_categoria} no pertenece a tu cuenta.",
        )

    if categoria.tipo != "gasto":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Solo se pueden asignar presupuestos a categorías de gasto ('{categoria.nombre}' es de ingreso).",
        )

    existente = (
        db.query(Presupuesto)
        .filter(
            Presupuesto.id_usuario == current_user.id_usuario,
            Presupuesto.id_categoria == payload.id_categoria,
            Presupuesto.mes == payload.mes,
            Presupuesto.anio == payload.anio,
        )
        .first()
    )

    if existente:
        existente.monto_limite = payload.monto_limite
        db.commit()
        db.refresh(existente)
        return _enriquecer_presupuesto(existente)

    nuevo = Presupuesto(
        id_usuario=current_user.id_usuario,
        id_categoria=payload.id_categoria,
        monto_limite=payload.monto_limite,
        mes=payload.mes,
        anio=payload.anio,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return _enriquecer_presupuesto(nuevo)


@router.get(
    "/resumen",
    response_model=PresupuestosResumenResponse,
    summary="Resumen de ejecución presupuestal vs gastos reales",
)
def resumen_presupuestos(
    mes:  Optional[int] = Query(None, ge=1, le=12, description="Mes a consultar (por defecto mes actual)"),
    anio: Optional[int] = Query(None, ge=2020, description="Año a consultar (por defecto año actual)"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Compara el límite presupuestado contra el gasto real ejecutado
    en cada categoría para el mes especificado.
    """
    hoy = date.today()
    mes_target = mes or hoy.month
    anio_target = anio or hoy.year

    presupuestos = (
        db.query(Presupuesto)
        .filter(
            Presupuesto.id_usuario == current_user.id_usuario,
            Presupuesto.mes == mes_target,
            Presupuesto.anio == anio_target,
        )
        .all()
    )

    items = []
    total_presupuestado = 0.0
    total_gastado = 0.0

    for p in presupuestos:
        limite = float(p.monto_limite)
        total_presupuestado += limite

        # Calcular suma de gastos en este mes y categoría
        gasto_query = (
            db.query(func.coalesce(func.sum(IngresoGasto.monto), 0))
            .filter(
                IngresoGasto.id_usuario == current_user.id_usuario,
                IngresoGasto.id_categoria == p.id_categoria,
                IngresoGasto.tipo == "gasto",
                extract("year", IngresoGasto.fecha) == anio_target,
                extract("month", IngresoGasto.fecha) == mes_target,
            )
            .scalar()
        )
        gastado = float(gasto_query or 0.0)
        total_gastado += gastado

        porcentaje = round((gastado / limite * 100), 2) if limite > 0 else 0.0
        restante = round(limite - gastado, 2)
        sobregirado = gastado > limite

        nombre_cat = p.categoria.nombre if p.categoria else f"Cat #{p.id_categoria}"

        items.append(PresupuestoResumenItem(
            id_presupuesto=p.id_presupuesto,
            id_categoria=p.id_categoria,
            nombre_categoria=nombre_cat,
            monto_limite=limite,
            monto_gastado=round(gastado, 2),
            porcentaje_usado=porcentaje,
            restante=restante,
            sobregirado=sobregirado,
            mes=mes_target,
            anio=anio_target,
        ))

    return PresupuestosResumenResponse(
        mes=mes_target,
        anio=anio_target,
        total_presupuestado=round(total_presupuestado, 2),
        total_gastado=round(total_gastado, 2),
        items=items,
    )


@router.delete(
    "/{id_presupuesto}",
    response_model=MensajeResponse,
    summary="Eliminar un presupuesto",
)
def eliminar_presupuesto(
    id_presupuesto: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Elimina una regla de presupuesto."""
    presupuesto = (
        db.query(Presupuesto)
        .filter(
            Presupuesto.id_presupuesto == id_presupuesto,
            Presupuesto.id_usuario == current_user.id_usuario,
        )
        .first()
    )
    if not presupuesto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Presupuesto {id_presupuesto} no encontrado",
        )

    db.delete(presupuesto)
    db.commit()
    return MensajeResponse(mensaje=f"Presupuesto #{id_presupuesto} eliminado con éxito")
