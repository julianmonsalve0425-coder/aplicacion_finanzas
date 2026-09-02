# ============================================================
# config.py — Configuración centralizada de la aplicación
# Lee variables desde el archivo .env usando pydantic-settings
# ============================================================

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):
    """
    Clase de configuración global.
    Carga variables desde el entorno o archivo .env.
    """

    # --- Servidor FastAPI ---
    DEBUG: bool = True
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

    # --- Base de Datos (SQLite por defecto o URL personalizada vía DATABASE_URL) ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./finanzas.db")
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "finanzas_personales"

    # --- Seguridad y Tokens JWT ---
    SECRET_KEY: str = "9f8e7d6c5b4a39281726354859607182a1b2c3d4e5f60718293a4b5c6d7e8f90"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # --- Orígenes CORS permitidos ---
    CORS_ORIGINS: str = "*"

    # Directorio para almacenar modelos de Machine Learning (.joblib)
    @property
    def ML_MODELS_DIR(self) -> Path:
        models_dir = BASE_DIR / "ml_models"
        models_dir.mkdir(parents=True, exist_ok=True)
        return models_dir

    # Busca .env en directorio backend o en la raíz del proyecto
    model_config = SettingsConfigDict(
        env_file=[
            str(BASE_DIR / ".env"),
            str(PROJECT_ROOT / ".env"),
            ".env"
        ],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Instancia singleton accesible globalmente
settings = Settings()
