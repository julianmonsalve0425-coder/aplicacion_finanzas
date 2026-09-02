# ============================================================
# database.py — Configuración de Base de Datos y Sesiones ORM
# Soporte dinámico para SQLite local y motores de producción (PostgreSQL, MySQL)
# ============================================================

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Configuración de URL dinámica: variable de entorno DATABASE_URL o SQLite local por defecto
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./finanzas.db")

# Normalización para servicios cloud (ej. Render/Heroku usa postgres:// que SQLAlchemy requiere como postgresql://)
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configurar motor SQLAlchemy según el tipo de base de datos
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=3600
    )

# Fábrica de sesiones ORM
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)

# Clase base declarativa para los modelos ORM
class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos SQLAlchemy."""
    pass

# Dependencia inyectable para FastAPI
def get_db():
    """Generador de contexto que entrega una sesión de base de datos por petición."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
