# ============================================================
# routers/analitica.py — Endpoints del Módulo Analítico (Machine Learning)
# Rutas: /api/analitica/prediccion, /api/analitica/anomalias, /api/analitica/entrenar
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import Usuario
from schemas import (
    PrediccionResponse,
    AnomaliasResponse,
    AnomaliaItem,
    EntrenamientoResponse,
)
from core.security import get_current_user
from analitica import (
    cargar_datos_usuario,
    predecir_gasto_proximo_mes,
    detectar_anomalias,
    entrenar_y_persistir_modelo,
)

router = APIRouter(prefix="/api/analitica", tags=["Analítica / ML"])


@router.get(
    "/prediccion",
    response_model=PrediccionResponse,
    summary="Predecir gasto del próximo mes (Regresión Lineal Scikit-learn)",
)
def prediccion_gasto(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Estima el gasto del próximo mes para el usuario autenticado:
    - Analiza la serie temporal de gastos mensuales con Regresión Lineal.
    - Carga o persiste automáticamente el modelo entrenado con `joblib`.
    - Retorna el monto proyectado, nivel de confianza y justificación analítica.
    """
    try:
        df = cargar_datos_usuario(db, current_user.id_usuario)
        resultado = predecir_gasto_proximo_mes(df, current_user.id_usuario)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en el motor analítico de predicción: {str(exc)}",
        )

    return PrediccionResponse(
        id_usuario=current_user.id_usuario,
        prediccion=resultado["prediccion"],
        confianza=resultado["confianza"],
        razon=resultado["razon"],
        metodo="regresion_lineal",
        mes_proyectado=resultado.get("mes_proyectado"),
        modelo_cargado=resultado.get("modelo_cargado", False),
    )


@router.get(
    "/anomalias",
    response_model=AnomaliasResponse,
    summary="Detectar gastos atípicos o anomalías estadísticas (Z-Score)",
)
def anomalias_gasto(
    umbral_z: float = Query(1.5, ge=0.5, le=5.0, description="Umbral Z-Score para considerar anomalía"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Detecta transacciones de gasto con montos anormalmente altos respecto
    a la media histórica de su respectiva categoría usando la métrica Z-Score.
    """
    try:
        df = cargar_datos_usuario(db, current_user.id_usuario)
        lista_anomalias = detectar_anomalias(df, umbral_z=umbral_z)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al analizar anomalías estadísticas: {str(exc)}",
        )

    items = [AnomaliaItem(**a) for a in lista_anomalias]
    return AnomaliasResponse(
        id_usuario=current_user.id_usuario,
        anomalias=items,
        total=len(items),
    )


@router.post(
    "/entrenar",
    response_model=EntrenamientoResponse,
    summary="Forzar reentrenamiento y guardado del modelo en disco (joblib)",
)
def reentrenar_modelo(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Fuerza el reentrenamiento de la regresión lineal del usuario
    y serializa el nuevo artefacto binario `.joblib` en el directorio de modelos.
    """
    try:
        df = cargar_datos_usuario(db, current_user.id_usuario)
        resultado = entrenar_y_persistir_modelo(df, current_user.id_usuario)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error durante el reentrenamiento del modelo: {str(exc)}",
        )

    return EntrenamientoResponse(**resultado)
