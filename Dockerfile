# ============================================================
# Dockerfile — Contenedor de Producción para la API FastAPI
# Multi-stage / Python 3.11-slim optimizado
# ============================================================

FROM python:3.11-slim

# Evitar escritura de archivos .pyc y forzar logs sin buffer
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema para compilación y utilidades
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar todo el código del proyecto
COPY . .

# Crear directorio para persistencia de modelos de Machine Learning
RUN mkdir -p "/app/API Backend RESTful (FastAPI)/ml_models"

# Exponer el puerto de Uvicorn
EXPOSE 8000

# Comando de arranque apuntando al directorio del backend
WORKDIR "/app/API Backend RESTful (FastAPI)"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
