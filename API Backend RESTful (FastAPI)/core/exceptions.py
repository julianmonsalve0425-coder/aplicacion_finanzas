# ============================================================
# core/exceptions.py — Manejadores Centralizados de Excepciones
# Estandariza las respuestas de error en formato JSON
# ============================================================

import sys
from pathlib import Path
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Captura HTTPExceptions y devuelve JSON estructurado."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status_code": exc.status_code,
            "error": "HTTP_ERROR",
            "detalle": exc.detail,
        },
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Captura errores de validación de esquemas Pydantic / FastAPI."""
    detalles = []
    for error in exc.errors():
        campo = " -> ".join([str(loc) for loc in error.get("loc", [])])
        mensaje = error.get("msg", "Dato inválido")
        detalles.append(f"{campo}: {mensaje}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "error": "VALIDATION_ERROR",
            "detalle": detalles if len(detalles) > 1 else (detalles[0] if detalles else "Error de validación"),
            "raw_errors": exc.errors() if settings.DEBUG else None
        },
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Captura errores de base de datos SQLAlchemy / MySQL."""
    status_code = status.HTTP_409_CONFLICT if isinstance(exc, IntegrityError) else status.HTTP_500_INTERNAL_SERVER_ERROR
    detalle = "Conflicto de integridad de datos en la BD" if isinstance(exc, IntegrityError) else "Error en la capa de base de datos"
    
    if settings.DEBUG:
        detalle = f"{detalle}: {str(exc)}"

    return JSONResponse(
        status_code=status_code,
        content={
            "status_code": status_code,
            "error": "DATABASE_ERROR",
            "detalle": detalle,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Captura cualquier excepción no controlada."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error": "INTERNAL_SERVER_ERROR",
            "detalle": str(exc) if settings.DEBUG else "Ocurrió un error interno en el servidor",
        },
    )
