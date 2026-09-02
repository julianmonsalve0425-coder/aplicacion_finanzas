# ============================================================
# routers/resumen.py — Endpoint de KPIs y Resumen Financiero
# Ruta: GET /api/resumen
# ============================================================

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import IngresoGasto, Usuario
from schemas import ResumenResponse
from core.security import get_current_user

router = APIRouter(prefix="/api/resumen", tags=["Resumen"])


@router.get(
    "",
    response_model=ResumenResponse,
    summary="Obtener KPIs financieros del usuario autenticado",
)
def obtener_resumen(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Calcula y retorna los principales indicadores de rendimiento financiero:
    - **total_ingresos**: Sumatoria total de movimientos de tipo 'ingreso'
    - **total_gastos**: Sumatoria total de movimientos de tipo 'gasto'
    - **balance**: total_ingresos - total_gastos
    - **porcentaje_ahorro**: % del ingreso neto ahorrado
    """
    # Consulta agrupada de sumatoria por tipo de movimiento
    resultado = (
        db.query(
            IngresoGasto.tipo,
            func.coalesce(func.sum(IngresoGasto.monto), 0).label("total"),
        )
        .filter(IngresoGasto.id_usuario == current_user.id_usuario)
        .group_by(IngresoGasto.tipo)
        .all()
    )

    totales = {row.tipo: float(row.total) for row in resultado}

    total_ingresos = totales.get("ingreso", 0.0)
    total_gastos   = totales.get("gasto", 0.0)
    balance        = round(total_ingresos - total_gastos, 2)

    porcentaje_ahorro = 0.0
    if total_ingresos > 0 and balance > 0:
        porcentaje_ahorro = round((balance / total_ingresos) * 100.0, 2)

    return ResumenResponse(
        id_usuario=current_user.id_usuario,
        total_ingresos=round(total_ingresos, 2),
        total_gastos=round(total_gastos, 2),
        balance=balance,
        porcentaje_ahorro=porcentaje_ahorro,
    )
