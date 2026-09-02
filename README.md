# 💰 Finanzas — Plataforma Inteligente de Finanzas Personales (v2.0)

> Aplicación web Full-Stack lista para producción para la gestión integral de finanzas personales, presupuestos mensuales, metas de ahorro y análisis predictivo con Inteligencia Artificial.
> 
> **Stack Tecnológico:**
> - **Backend:** Python 3.11 · FastAPI · SQLAlchemy 2.0 · PyMySQL · Pydantic v2 · Bcrypt · Python-Jose (JWT)
> - **Machine Learning:** Pandas · NumPy · Scikit-learn (Linear Regression) · Joblib
> - **Frontend:** HTML5 Semántico · CSS3 Glassmorphism Moderno · JavaScript Vanilla (SPA) · Chart.js
> - **Base de Datos:** MySQL 8.0 / MariaDB
> - **DevOps / Despliegue:** Docker · Docker Compose

---

## 📋 Tabla de Contenidos
- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Pilares Implementados](#-pilares-implementados)
- [Despliegue Rápido con Docker Compose](#-despliegue-rápido-con-docker-compose)
- [Instalación Local Manual](#-instalación-local-manual)
- [Catálogo de Endpoints RESTful](#-catálogo-de-endpoints-restful)
- [Módulo de Machine Learning y Persistencia](#-módulo-de-machine-learning-y-persistencia)
- [Credenciales Demo](#-credenciales-demo)

---

## 🏗️ Arquitectura del Sistema

```
┌────────────────────────────────────────────────────────────────────────┐
│              FRONTEND (SPA: HTML5 + CSS Glassmorphism + JS)            │
│  - Modal Auth (JWT en localStorage)  - Chart.js (Donut + Tendencia)    │
│  - Metas de Ahorro con Progreso      - Paginador y Filtros Avanzados   │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / JSON
                                    │ Authorization: Bearer <access_token>
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   BACKEND API (FastAPI + Python 3.11)                  │
│  - CORS Middleware                - Manejo Centralizado de Errores     │
│  - Inyección get_current_user     - Bcrypt Password Hashing            │
│  - Routers: Auth, Usuarios, Categorías, Movimientos, Presupuestos,     │
│             Metas, Resumen, Analítica                                  │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼                                 ▼
┌───────────────────────────────┐  ┌─────────────────────────────────────┐
│  BASE DE DATOS (MySQL 8.0)    │  │ MÓDULO ANALÍTICO (Scikit-learn)     │
│  - usuarios (hash, is_active) │  │ - Regresión Lineal (Gasto mensual)  │
│  - categorias & movimientos   │  │ - Persistencia de Modelos (joblib)  │
│  - presupuestos & metas_ahorro│  │ - Detección Z-Score de Anomalías    │
└───────────────────────────────┘  └─────────────────────────────────────┘
```

---

## 📁 Estructura del Proyecto

```text
Aplicacion finanzas- Julian Monsalve/
├── .env.example                               # Plantilla de variables de entorno
├── .env                                       # Variables locales
├── .gitignore                                 # Exclusiones Git (pycache, env, joblib)
├── requirements.txt                           # Dependencias completas del backend
├── Dockerfile                                 # Contenedor Docker para FastAPI
├── docker-compose.yml                         # Orquestador FastAPI + MySQL 8.0
├── README.md                                  # Documentación del proyecto
├── index.html                                 # Dashboard Frontend (SPA)
├── style.css                                  # Estilos Dark Mode Glassmorphism
├── app.js                                     # Lógica JS, interceptor JWT y Chart.js
│
├── Db/
│   ├── database.sql                           # DDL MySQL: tablas, FKs e índices
│   └── seed.sql                               # Datos de prueba con hash Bcrypt
│
└── API Backend RESTful (FastAPI)/
    ├── main.py                                # Servidor FastAPI, Lifespan y Routers
    ├── config.py                              # BaseSettings con pydantic-settings
    ├── database.py                            # SQLAlchemy engine y get_db
    ├── models.py                              # Modelos ORM (Usuario, Movimiento, etc.)
    ├── schemas.py                             # Schemas Pydantic v2
    ├── analitica.py                           # Regresión Lineal + Z-Score + joblib
    ├── core/
    │   ├── __init__.py
    │   ├── security.py                        # Bcrypt, JWT Tokens y get_current_user
    │   └── exceptions.py                      # Exception Handlers centralizados
    └── routers/
        ├── __init__.py
        ├── auth.py                            # /api/auth (login, register, refresh, me)
        ├── usuarios.py                        # /api/usuarios (perfil, password)
        ├── categorias.py                      # /api/categorias (CRUD protegido)
        ├── movimientos.py                     # /api/movimientos (filtros + paginación)
        ├── presupuestos.py                    # /api/presupuestos (resumen ejecución)
        ├── metas.py                           # /api/metas (metas de ahorro + abonos)
        ├── resumen.py                         # /api/resumen (KPIs + tasa de ahorro)
        └── analitica.py                       # /api/analitica (predicciones y anomalías)
```

---

## 🚀 Despliegue Rápido con Docker Compose

La forma más sencilla de ejecutar todo el stack (MySQL + Backend FastAPI + Frontend) en un entorno 100% aislado y reproducible:

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd "Aplicacion finanzas- Julian Monsalve"

# 2. Iniciar contenedores con Docker Compose
docker compose up --build -d

# 3. Verificar estado de los contenedores
docker compose ps
```

Listo. Accede a los siguientes enlaces:
- 🌐 **Dashboard:** [http://localhost:8000](http://localhost:8000)
- 📖 **Documentación Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- 🩺 **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

Para detener los servicios:
```bash
docker compose down
```

---

## 💻 Instalación Local Manual

### 1. Requisitos Previos
- Python 3.10+
- MySQL 8.0 o MariaDB 10.5+

### 2. Configurar la Base de Datos
Ejecuta los scripts SQL en tu servidor MySQL local:
```bash
mysql -u root -p < Db/database.sql
mysql -u root -p < Db/seed.sql
```

### 3. Entorno Virtual de Python
```bash
# En Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1

# Instalar dependencias
pip install -r requirements.txt
```

### 4. Variables de Entorno
Copia `.env.example` como `.env` y ajusta tus credenciales:
```bash
cp .env.example .env
```

### 5. Iniciar Servidor FastAPI
```bash
cd "API Backend RESTful (FastAPI)"
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

---

## 📡 Catálogo de Endpoints RESTful

### 🔐 Autenticación (`/api/auth`)
- `POST /api/auth/register` — Registrar nuevo usuario y devolver tokens JWT.
- `POST /api/auth/login` — Iniciar sesión con Form Data OAuth2 (`username`, `password`).
- `POST /api/auth/login-json` — Iniciar sesión con JSON (`correo`, `contrasena`).
- `POST /api/auth/refresh` — Renovar access token expirado mediante refresh token.
- `GET /api/auth/me` — Consultar perfil del usuario autenticado.

### 👥 Usuarios (`/api/usuarios`)
- `GET /api/usuarios/perfil` — Obtener datos del perfil actual.
- `PUT /api/usuarios/perfil` — Modificar nombre o actualizar contraseña segura.

### 🏷️ Categorías (`/api/categorias`)
- `GET /api/categorias` — Listar categorías del usuario (con filtro opcional `?tipo=`).
- `POST /api/categorias` — Crear nueva categoría personalizada.
- `DELETE /api/categorias/{id}` — Eliminar categoría (valida restricciones FK).

### 💳 Movimientos (`/api/movimientos`)
- `GET /api/movimientos` — Listado con filtros (`desde`, `hasta`, `tipo`, `id_categoria`, `monto_min`, `monto_max`) y soporte de paginación (`limit`, `offset`, `paginado=true`).
- `POST /api/movimientos` — Registrar un ingreso o gasto validando coherencia de categoría.
- `PUT /api/movimientos/{id}` — Actualizar movimiento existente.
- `DELETE /api/movimientos/{id}` — Eliminar movimiento financiero.

### 🎯 Presupuestos (`/api/presupuestos`)
- `GET /api/presupuestos` — Listar presupuestos configurados.
- `POST /api/presupuestos` — Fijar o actualizar límite mensual por categoría.
- `GET /api/presupuestos/resumen` — Monitoreo en tiempo real: gasto acumulado, porcentaje de uso, restante y alerta de sobregiro.
- `DELETE /api/presupuestos/{id}` — Eliminar presupuesto.

### 🏆 Metas de Ahorro (`/api/metas`)
- `GET /api/metas` — Listar metas activas con cálculo dinámico de progreso.
- `POST /api/metas` — Crear meta con monto objetivo y fecha límite.
- `POST /api/metas/{id}/abonar` — Registrar un abono económico (actualiza estado a completada automáticamente).
- `PUT /api/metas/{id}` — Editar meta de ahorro.
- `DELETE /api/metas/{id}` — Eliminar meta.

### 📊 Resumen Financiero (`/api/resumen`)
- `GET /api/resumen` — KPIs principales: total ingresos, total gastos, balance neto y tasa de ahorro.

### 🧠 Analítica & ML (`/api/analitica`)
- `GET /api/analitica/prediccion` — Proyección de gasto próximo mes usando Regresión Lineal y persistencia Joblib.
- `GET /api/analitica/anomalias` — Detección estadística de consumos extraordinarios mediante Z-Score (`?umbral_z=1.5`).
- `POST /api/analitica/entrenar` — Forzar reentrenamiento y serialización del modelo `.joblib` en disco.

---

## 🧠 Módulo de Machine Learning y Persistencia

1. **Regresión Lineal (`Scikit-learn`):**
   - Agrupa el historial mensual de gastos del usuario y entrena un modelo lineal univariado.
   - Evalúa la pendiente de la recta para indicar si la tendencia de consumo es **ascendente ↗️** o **descendente ↘️**.
   - Asigna niveles de confianza (*Alta*, *Media*, *Baja*) en función del número de meses disponibles en la base de datos.

2. **Persistencia con `Joblib`:**
   - Cada modelo entrenado se serializa en `ml_models/usuario_{id}_regresion.joblib`.
   - Permite inferencia instantánea sin necesidad de reentrenar en cada petición HTTP, mejorando la latencia del backend.

3. **Detección de Anomalías (Z-Score):**
   - Calcula la media $\mu$ y desviación estándar $\sigma$ de cada categoría de gasto.
   - Marca una transacción como anomalía si:
     $$Z = \frac{\text{monto} - \mu}{\sigma} > \text{umbral}$$

---

## 👤 Credenciales Demo

Para probar la plataforma de inmediato, se incluye una cuenta precargada en `Db/seed.sql`:

- **Correo:** `ana@example.com`
- **Contraseña:** `Password123!`
- **Datos incluidos:** 4 meses de movimientos históricos, categorías personalizadas, presupuestos para el mes en curso y metas de ahorro con abonos.
