# ============================================================
# main.py — Punto de Entrada Principal de la API FastAPI
# Ejecutar con: uvicorn main:app --reload
# ============================================================

import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

# Ajustar sys.path para permitir imports absolutos
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import settings
from database import engine, Base, SessionLocal
import models
from core.security import hashear_contrasena, verificar_contrasena
from core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler,
)

# Importar routers
from routers import (
    auth,
    usuarios,
    categorias,
    movimientos,
    presupuestos,
    metas,
    resumen,
    analitica as analitica_router,
)

# Creación automática de tablas en SQLite / Base de Datos al cargar el módulo
Base.metadata.create_all(bind=engine)


def _inicializar_datos_demo(db):
    """Puebla la base de datos con un usuario demo y datos de prueba si está vacía."""
    from datetime import date
    from decimal import Decimal

    usuario_demo = db.query(models.Usuario).filter(models.Usuario.correo == "ana@example.com").first()
    if usuario_demo:
        if not usuario_demo.is_active or not verificar_contrasena("Password123!", usuario_demo.contrasena_hash):
            usuario_demo.contrasena_hash = hashear_contrasena("Password123!")
            usuario_demo.is_active = True
            db.commit()
        return

    # 1. Crear usuario demo Ana Torres
    usuario = models.Usuario(
        nombre="Ana Torres",
        correo="ana@example.com",
        contrasena_hash=hashear_contrasena("Password123!"),
        is_active=True,
    )
    db.add(usuario)
    db.flush()

    # 2. Categorías base
    cats = [
        models.Categoria(nombre="Salario", tipo="ingreso", id_usuario=usuario.id_usuario),
        models.Categoria(nombre="Freelance / Honorarios", tipo="ingreso", id_usuario=usuario.id_usuario),
        models.Categoria(nombre="Alimentación y Supermercado", tipo="gasto", id_usuario=usuario.id_usuario),
        models.Categoria(nombre="Transporte y Movilidad", tipo="gasto", id_usuario=usuario.id_usuario),
        models.Categoria(nombre="Vivienda y Servicios", tipo="gasto", id_usuario=usuario.id_usuario),
        models.Categoria(nombre="Entretenimiento y Ocio", tipo="gasto", id_usuario=usuario.id_usuario),
        models.Categoria(nombre="Salud y Bienestar", tipo="gasto", id_usuario=usuario.id_usuario),
        models.Categoria(nombre="Educación", tipo="gasto", id_usuario=usuario.id_usuario),
    ]
    db.add_all(cats)
    db.flush()

    cat_map = {c.nombre: c.id_categoria for c in cats}

    # 3. Movimientos históricos
    movs = [
        # Mayo 2026
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Salario"], tipo="ingreso", monto=Decimal("3500000.00"), fecha=date(2026, 5, 1), descripcion="Salario mensual"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Freelance / Honorarios"], tipo="ingreso", monto=Decimal("800000.00"), fecha=date(2026, 5, 15), descripcion="Proyecto Frontend freelance"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Vivienda y Servicios"], tipo="gasto", monto=Decimal("1100000.00"), fecha=date(2026, 5, 5), descripcion="Arriendo y servicios"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Alimentación y Supermercado"], tipo="gasto", monto=Decimal("450000.00"), fecha=date(2026, 5, 8), descripcion="Mercado quincenal"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Transporte y Movilidad"], tipo="gasto", monto=Decimal("140000.00"), fecha=date(2026, 5, 12), descripcion="Transporte"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Entretenimiento y Ocio"], tipo="gasto", monto=Decimal("200000.00"), fecha=date(2026, 5, 20), descripcion="Cena y cine"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Alimentación y Supermercado"], tipo="gasto", monto=Decimal("420000.00"), fecha=date(2026, 5, 24), descripcion="Mercado segunda quincena"),
        # Junio 2026
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Salario"], tipo="ingreso", monto=Decimal("3500000.00"), fecha=date(2026, 6, 1), descripcion="Salario mensual"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Vivienda y Servicios"], tipo="gasto", monto=Decimal("1100000.00"), fecha=date(2026, 6, 5), descripcion="Arriendo y servicios"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Alimentación y Supermercado"], tipo="gasto", monto=Decimal("480000.00"), fecha=date(2026, 6, 7), descripcion="Mercado quincenal"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Transporte y Movilidad"], tipo="gasto", monto=Decimal("150000.00"), fecha=date(2026, 6, 11), descripcion="Transporte"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Entretenimiento y Ocio"], tipo="gasto", monto=Decimal("250000.00"), fecha=date(2026, 6, 18), descripcion="Salida fin de semana"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Salud y Bienestar"], tipo="gasto", monto=Decimal("180000.00"), fecha=date(2026, 6, 25), descripcion="Medicamentos y cita médica"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Alimentación y Supermercado"], tipo="gasto", monto=Decimal("460000.00"), fecha=date(2026, 6, 28), descripcion="Mercado fin de mes"),
        # Julio 2026
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Salario"], tipo="ingreso", monto=Decimal("3500000.00"), fecha=date(2026, 7, 1), descripcion="Salario mensual"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Freelance / Honorarios"], tipo="ingreso", monto=Decimal("600000.00"), fecha=date(2026, 7, 10), descripcion="Asesoría técnica"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Vivienda y Servicios"], tipo="gasto", monto=Decimal("1100000.00"), fecha=date(2026, 7, 5), descripcion="Arriendo y servicios"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Alimentación y Supermercado"], tipo="gasto", monto=Decimal("510000.00"), fecha=date(2026, 7, 6), descripcion="Mercado grande"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Transporte y Movilidad"], tipo="gasto", monto=Decimal("160000.00"), fecha=date(2026, 7, 12), descripcion="Transporte y combustible"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Salud y Bienestar"], tipo="gasto", monto=Decimal("950000.00"), fecha=date(2026, 7, 16), descripcion="Urgencia médica (Anomalía)"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Entretenimiento y Ocio"], tipo="gasto", monto=Decimal("190000.00"), fecha=date(2026, 7, 22), descripcion="Suscripciones y streaming"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Alimentación y Supermercado"], tipo="gasto", monto=Decimal("490000.00"), fecha=date(2026, 7, 27), descripcion="Mercado complementario"),
        # Agosto 2026
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Salario"], tipo="ingreso", monto=Decimal("3500000.00"), fecha=date(2026, 8, 1), descripcion="Salario mensual"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Vivienda y Servicios"], tipo="gasto", monto=Decimal("1100000.00"), fecha=date(2026, 8, 5), descripcion="Arriendo y servicios"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Alimentación y Supermercado"], tipo="gasto", monto=Decimal("520000.00"), fecha=date(2026, 8, 8), descripcion="Mercado mensual"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Transporte y Movilidad"], tipo="gasto", monto=Decimal("155000.00"), fecha=date(2026, 8, 14), descripcion="Transporte"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Educación"], tipo="gasto", monto=Decimal("350000.00"), fecha=date(2026, 8, 20), descripcion="Curso de FastAPI"),
        models.IngresoGasto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Entretenimiento y Ocio"], tipo="gasto", monto=Decimal("210000.00"), fecha=date(2026, 8, 26), descripcion="Restaurantes y ocio"),
    ]
    db.add_all(movs)

    # 4. Presupuestos
    pres = [
        models.Presupuesto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Alimentación y Supermercado"], monto_limite=Decimal("1000000.00"), mes=9, anio=2026),
        models.Presupuesto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Transporte y Movilidad"], monto_limite=Decimal("350000.00"), mes=9, anio=2026),
        models.Presupuesto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Vivienda y Servicios"], monto_limite=Decimal("1200000.00"), mes=9, anio=2026),
        models.Presupuesto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Entretenimiento y Ocio"], monto_limite=Decimal("400000.00"), mes=9, anio=2026),
        models.Presupuesto(id_usuario=usuario.id_usuario, id_categoria=cat_map["Salud y Bienestar"], monto_limite=Decimal("300000.00"), mes=9, anio=2026),
    ]
    db.add_all(pres)

    # 5. Metas de ahorro
    metas_data = [
        models.MetaAhorro(id_usuario=usuario.id_usuario, nombre="Fondo de Emergencia (6 meses)", monto_objetivo=Decimal("15000000.00"), monto_actual=Decimal("6800000.00"), fecha_limite=date(2026, 12, 31), completada=False),
        models.MetaAhorro(id_usuario=usuario.id_usuario, nombre="Vacaciones a San Andrés", monto_objetivo=Decimal("4500000.00"), monto_actual=Decimal("3200000.00"), fecha_limite=date(2026, 11, 15), completada=False),
        models.MetaAhorro(id_usuario=usuario.id_usuario, nombre="Renovación Portátil Developer", monto_objetivo=Decimal("5000000.00"), monto_actual=Decimal("5000000.00"), fecha_limite=date(2026, 8, 1), completada=True),
    ]
    db.add_all(metas_data)

    db.commit()


# Inicialización asegurada en arranque de módulo
try:
    _init_db = SessionLocal()
    try:
        _inicializar_datos_demo(_init_db)
    finally:
        _init_db.close()
except Exception:
    pass


# ─────────────────────────────────────────
# Ciclo de Vida de la Aplicación (Lifespan)
# ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicialización y limpieza al arrancar el servidor."""
    settings.ML_MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Auto-creación de tablas al iniciar la aplicación y población inicial
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            _inicializar_datos_demo(db)
        finally:
            db.close()
    except Exception as e:
        print(f"⚠️ Aviso al inicializar base de datos en el arranque: {e}")

    yield


# ─────────────────────────────────────────
# Instancia Principal de FastAPI
# ─────────────────────────────────────────
app = FastAPI(
    title="API de Finanzas Personales & Inteligencia Predictiva",
    description=(
        "API RESTful para la gestión integral de finanzas personales, presupuestos mensuales, "
        "metas de ahorro y proyecciones de gasto impulsadas por Machine Learning (Scikit-learn)."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─────────────────────────────────────────
# Middleware CORS
# ─────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# Manejadores Centralizados de Excepciones
# ─────────────────────────────────────────
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# ─────────────────────────────────────────
# Registro de Routers
# ─────────────────────────────────────────
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(categorias.router)
app.include_router(movimientos.router)
app.include_router(presupuestos.router)
app.include_router(metas.router)
app.include_router(resumen.router)
app.include_router(analitica_router.router)

# ─────────────────────────────────────────
# Archivos Estáticos del Frontend
# ─────────────────────────────────────────
if PROJECT_ROOT.exists():
    app.mount("/static", StaticFiles(directory=str(PROJECT_ROOT)), name="static")


@app.get("/", include_in_schema=False)
async def servir_frontend():
    """Sirve el dashboard interactivo (index.html)."""
    index_path = PROJECT_ROOT / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse(
        content={
            "mensaje": "API de Finanzas Personales activa.",
            "documentacion": "/docs",
            "version": "2.0.0",
        }
    )


# ─────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────
@app.get("/health", tags=["Sistema"], summary="Estado del servicio y la base de datos")
async def health_check():
    """Verifica el estado del servicio y su configuración."""
    return {
        "estado": "operacional",
        "version": "2.0.0",
        "debug": settings.DEBUG,
        "jwt_algorithm": settings.ALGORITHM,
        "token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    }


# ─────────────────────────────────────────
# Arranque directo (Modo Desarrollo)
# ─────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
