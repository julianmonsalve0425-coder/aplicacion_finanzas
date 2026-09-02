# ============================================================
# analitica.py — Módulo de Inteligencia Financiera y Machine Learning
# Modelos: Regresión Lineal (Scikit-learn), Z-Score Anomalies, Persistencia (joblib)
# ============================================================

from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any

import pandas as pd
import numpy as np
import joblib
from sklearn.linear_model import LinearRegression
from sqlalchemy.orm import Session

from config import settings
from models import IngresoGasto, Categoria


def cargar_datos_usuario(db: Session, id_usuario: int) -> pd.DataFrame:
    """
    Carga todos los movimientos financieros del usuario en un DataFrame de pandas.
    Realiza parsing de fechas y tipos numéricos.
    """
    movimientos = (
        db.query(
            IngresoGasto.id_movimiento,
            IngresoGasto.fecha,
            IngresoGasto.tipo,
            IngresoGasto.monto,
            IngresoGasto.id_categoria,
            Categoria.nombre.label("nombre_categoria"),
            IngresoGasto.descripcion,
        )
        .join(Categoria, IngresoGasto.id_categoria == Categoria.id_categoria, isouter=True)
        .filter(IngresoGasto.id_usuario == id_usuario)
        .order_by(IngresoGasto.fecha.asc())
        .all()
    )

    if not movimientos:
        return pd.DataFrame(columns=[
            "id_movimiento", "fecha", "tipo", "monto", 
            "id_categoria", "nombre_categoria", "descripcion", "mes"
        ])

    data = [
        {
            "id_movimiento": m.id_movimiento,
            "fecha": m.fecha,
            "tipo": m.tipo,
            "monto": float(m.monto),
            "id_categoria": m.id_categoria,
            "nombre_categoria": m.nombre_categoria or f"Categoría #{m.id_categoria}",
            "descripcion": m.descripcion or "",
        }
        for m in movimientos
    ]

    df = pd.DataFrame(data)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["mes"] = df["fecha"].dt.to_period("M")
    df["monto"] = df["monto"].astype(float)
    return df


def _get_model_path(id_usuario: int) -> Path:
    """Retorna la ruta del archivo .joblib del modelo del usuario."""
    return settings.ML_MODELS_DIR / f"usuario_{id_usuario}_regresion.joblib"


def entrenar_y_persistir_modelo(df: pd.DataFrame, id_usuario: int) -> Dict[str, Any]:
    """
    Entrena el modelo de Regresión Lineal con el historial mensual de gastos
    y lo serializa en disco utilizando joblib.
    """
    gastos = df[df["tipo"] == "gasto"].copy()
    if gastos.empty:
        return {
            "mensaje": "Sin historial de gastos para entrenar el modelo",
            "modelo_guardado": False,
            "total_meses": 0,
            "coeficiente": 0.0,
            "intercepto": 0.0,
        }

    resumen_mensual = (
        gastos.groupby("mes")["monto"]
        .sum()
        .reset_index()
        .sort_values("mes")
    )
    cant_meses = len(resumen_mensual)

    if cant_meses < 2:
        promedio = float(resumen_mensual["monto"].mean())
        payload = {
            "tipo": "promedio_simple",
            "cant_meses": cant_meses,
            "promedio": promedio,
            "fecha_entrenamiento": datetime.now(timezone.utc).isoformat(),
        }
        joblib.dump(payload, _get_model_path(id_usuario))
        return {
            "mensaje": "Datos insuficientes (< 2 meses). Se persistió baseline promedio.",
            "modelo_guardado": True,
            "total_meses": cant_meses,
            "coeficiente": 0.0,
            "intercepto": promedio,
        }

    resumen_mensual["n_mes"] = range(cant_meses)
    X = resumen_mensual[["n_mes"]]
    y = resumen_mensual["monto"]

    modelo = LinearRegression()
    modelo.fit(X, y)

    model_payload = {
        "tipo": "regresion_lineal",
        "modelo": modelo,
        "cant_meses": cant_meses,
        "ultimo_mes": str(resumen_mensual["mes"].iloc[-1]),
        "coeficiente": float(modelo.coef_[0]),
        "intercepto": float(modelo.intercept_),
        "fecha_entrenamiento": datetime.now(timezone.utc).isoformat(),
    }

    joblib.dump(model_payload, _get_model_path(id_usuario))

    return {
        "mensaje": f"Modelo entrenado y persistido con éxito ({cant_meses} meses procesados)",
        "modelo_guardado": True,
        "total_meses": cant_meses,
        "coeficiente": round(float(modelo.coef_[0]), 2),
        "intercepto": round(float(modelo.intercept_), 2),
    }


def predecir_gasto_proximo_mes(df: pd.DataFrame, id_usuario: int) -> Dict[str, Any]:
    """
    Calcula la estimación de gasto para el mes siguiente.
    Intenta cargar el modelo pre-entrenado desde disco con joblib;
    si no existe, lo entrena dinámicamente y lo persiste.
    """
    gastos = df[df["tipo"] == "gasto"].copy()
    if gastos.empty:
        return {
            "prediccion": 0.0,
            "confianza": "baja",
            "razon": "No existen movimientos de gasto registrados en la cuenta",
            "modelo_cargado": False,
            "mes_proyectado": None,
        }

    resumen_mensual = (
        gastos.groupby("mes")["monto"]
        .sum()
        .reset_index()
        .sort_values("mes")
    )
    cant_meses = len(resumen_mensual)
    ultimo_mes = resumen_mensual["mes"].iloc[-1]
    proximo_mes = str(ultimo_mes + 1)

    model_path = _get_model_path(id_usuario)
    modelo_cargado = False
    model_payload = None

    # Intentar cargar modelo desde disco con joblib
    if model_path.exists():
        try:
            model_payload = joblib.load(model_path)
            if model_payload.get("cant_meses") == cant_meses:
                modelo_cargado = True
        except Exception:
            model_payload = None

    # Si no había modelo o está desactualizado, reentrenar y persistir
    if not modelo_cargado:
        entrenar_y_persistir_modelo(df, id_usuario)
        if model_path.exists():
            try:
                model_payload = joblib.load(model_path)
            except Exception:
                pass

    # Caso 1: Historial corto (< 2 meses)
    if cant_meses < 2:
        promedio = float(resumen_mensual["monto"].mean())
        return {
            "prediccion": round(promedio, 2),
            "confianza": "baja",
            "razon": "Historial insuficiente (< 2 meses). Se aplicó promedio simple de gastos.",
            "modelo_cargado": modelo_cargado,
            "mes_proyectado": proximo_mes,
        }

    # Caso 2: Predicción con Regresión Lineal
    if model_payload and model_payload.get("tipo") == "regresion_lineal":
        modelo = model_payload["modelo"]
    else:
        resumen_mensual["n_mes"] = range(cant_meses)
        modelo = LinearRegression()
        modelo.fit(resumen_mensual[["n_mes"]], resumen_mensual["monto"])

    siguiente_mes_idx = np.array([[cant_meses]])
    prediccion_raw = float(modelo.predict(siguiente_mes_idx)[0])
    prediccion_final = max(0.0, prediccion_raw)

    confianza = "alta" if cant_meses >= 6 else "media"
    tendencia = "ascendente ↗️" if modelo.coef_[0] > 0 else "descendente ↘️"

    return {
        "prediccion": round(prediccion_final, 2),
        "confianza": confianza,
        "razon": f"Modelo de Regresión Lineal ({cant_meses} meses analizados, tendencia {tendencia})",
        "modelo_cargado": modelo_cargado,
        "mes_proyectado": proximo_mes,
    }


def detectar_anomalias(df: pd.DataFrame, umbral_z: float = 1.5) -> List[Dict[str, Any]]:
    """
    Detecta gastos anormalmente altos o desviados estadísticamente
    mediante el cálculo del Z-Score agrupado por categoría.
    """
    gastos = df[df["tipo"] == "gasto"].copy()
    if gastos.empty:
        return []

    # Calcular media y desviación estándar por categoría
    stats = gastos.groupby("id_categoria")["monto"].agg(["mean", "std"]).reset_index()
    stats["std"] = stats["std"].fillna(0.0)

    gastos = gastos.merge(stats, on="id_categoria", how="left")

    # Z-Score = (monto - media) / desviacion_estandar
    gastos["z_score"] = np.where(
        gastos["std"] > 0,
        (gastos["monto"] - gastos["mean"]) / gastos["std"],
        0.0
    )

    # Filtrar anomalías que superen el umbral positivo
    anomalias = gastos[gastos["z_score"] > umbral_z].sort_values("z_score", ascending=False)

    resultado = []
    for _, row in anomalias.iterrows():
        resultado.append({
            "id_movimiento": int(row["id_movimiento"]) if "id_movimiento" in row and pd.notna(row["id_movimiento"]) else None,
            "fecha": row["fecha"].strftime("%Y-%m-%d"),
            "id_categoria": int(row["id_categoria"]),
            "nombre_categoria": str(row.get("nombre_categoria", f"Categoría #{row['id_categoria']}")),
            "monto": float(row["monto"]),
            "promedio_categoria": round(float(row["mean"]), 2),
            "z_score": round(float(row["z_score"]), 2),
        })

    return resultado