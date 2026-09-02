# Proyecto de Aula: Aplicación Web de Finanzas Personales con Dashboard Analítico

**Nivel:** Intermedio–Avanzado
**Duración sugerida:** 4 semanas (16-20 horas de trabajo autónomo + acompañamiento en clase)
**Modalidad:** Individual o en parejas

---

## 1. Presentación del proyecto

Vas a construir una aplicación web full-stack que le permita a una persona registrar sus ingresos y gastos, y que le devuelva **información útil** sobre su comportamiento financiero: cuánto ahorra, en qué categoría gasta más, cómo ha sido su tendencia mes a mes, y una estimación de cuánto gastará el próximo mes.

Este proyecto integra tres competencias que todo desarrollador de software debe demostrar:

1. **Desarrollo Frontend** (HTML5, CSS3, JavaScript, Chart.js)
2. **Desarrollo Backend / API REST** (Python con Flask o FastAPI)
3. **Persistencia de datos y análisis** (MySQL, Pandas, Scikit-learn)

No es un ejercicio decorativo: al finalizar tendrás un proyecto real para tu portafolio, capaz de sustentar una entrevista técnica.

---

## 2. Objetivos de aprendizaje

Al finalizar el proyecto, el aprendiz estará en capacidad de:

- Diseñar un modelo relacional normalizado (mínimo 3FN) para un dominio de negocio real.
- Construir una API REST en Python que exponga operaciones CRUD sobre una base de datos MySQL.
- Consumir esa API desde JavaScript usando `fetch` y manejar peticiones asíncronas.
- Visualizar datos dinámicos en el navegador con Chart.js.
- Procesar y limpiar datos con Pandas.
- Aplicar un modelo simple de Scikit-learn (regresión) para generar una predicción y detectar anomalías.
- Documentar y sustentar un proyecto de software de principio a fin.

---

## 3. Arquitectura general

```
[ Frontend: HTML/CSS/JS + Chart.js ]
              |  fetch() / JSON
              v
[ Backend/API: Python (Flask o FastAPI) ]
              |  mysql-connector-python / SQLAlchemy
              v
[ Base de Datos: MySQL ]
              |
              v
[ Módulo Analítico: Pandas + Scikit-learn ]
              |  (resultados en JSON)
              v
[ Frontend: Dashboard con gráficos ]
```

> El módulo analítico puede vivir dentro del mismo backend (como un endpoint `/api/analitica`) o como un script independiente que se ejecuta bajo demanda. Se recomienda integrarlo como endpoint para que el dashboard lo consuma en tiempo real.

---

## 4. Historia de usuario (punto de partida)

> "Como usuario de la aplicación, quiero registrar mis ingresos y gastos clasificados por categoría, para poder ver en un panel visual cuánto he ahorrado, en qué gasto más, y recibir una alerta cuando un gasto sea inusualmente alto o una proyección de cuánto gastaré el próximo mes."

---

## 5. Requerimientos funcionales (RF)

| # | Requerimiento |
|---|----------------|
| RF01 | El sistema debe permitir crear un usuario (registro simple, puede ser sin autenticación robusta para esta fase). |
| RF02 | El sistema debe permitir crear, listar, editar y eliminar categorías (ej: Alimentación, Transporte, Salario, Entretenimiento). |
| RF03 | El sistema debe permitir registrar un movimiento (ingreso o gasto) con: monto, fecha, categoría, descripción y tipo (ingreso/gasto). |
| RF04 | El sistema debe permitir listar los movimientos de un usuario, con filtros por rango de fechas y categoría. |
| RF05 | El sistema debe calcular y mostrar: total de ingresos, total de gastos y balance (ahorro) de un periodo. |
| RF06 | El sistema debe mostrar en un gráfico de pastel/dona la distribución del gasto por categoría. |
| RF07 | El sistema debe mostrar en un gráfico de líneas o barras la tendencia de ingresos vs. gastos por mes. |
| RF08 | El sistema debe generar una **predicción del gasto del próximo mes** usando un modelo de regresión sobre el histórico. |
| RF09 | El sistema debe **detectar y señalar anomalías**: movimientos cuyo monto se desvíe significativamente del comportamiento habitual del usuario en esa categoría. |
| RF10 | El sistema debe presentar los resultados del análisis (RF08 y RF09) en el dashboard, de forma visual y legible. |

## 6. Requerimientos no funcionales (RNF)

- La API debe responder en formato JSON y seguir convenciones REST (verbos HTTP correctos, códigos de estado adecuados).
- El código backend debe estar organizado por capas (rutas, lógica de negocio, acceso a datos).
- Las contraseñas (si se implementa login) deben almacenarse con hash (ej: `bcrypt`), nunca en texto plano.
- El frontend debe ser responsivo (usable en escritorio y tablet como mínimo).
- El proyecto debe incluir un archivo `README.md` con instrucciones de instalación y ejecución.
- El código debe estar versionado en Git con commits descriptivos.

---

## 7. Modelo de datos (MySQL)

### 7.1 Diagrama entidad-relación (descripción)

- Un **usuario** puede tener muchos **movimientos** (ingresos_gastos).
- Una **categoría** puede estar asociada a muchos **movimientos**.
- Cada **movimiento** pertenece a un único usuario y a una única categoría.

```
usuarios (1) ----< (N) ingresos_gastos (N) >---- (1) categorias
```

### 7.2 Script de creación (punto de partida)

```sql
CREATE DATABASE IF NOT EXISTS finanzas_personales
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE finanzas_personales;

CREATE TABLE usuarios (
    id_usuario      INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    correo          VARCHAR(150) NOT NULL UNIQUE,
    contrasena_hash VARCHAR(255) NOT NULL,
    fecha_registro  DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categorias (
    id_categoria    INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50) NOT NULL,
    tipo            ENUM('ingreso', 'gasto') NOT NULL,
    id_usuario      INT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
        ON DELETE CASCADE
);

CREATE TABLE ingresos_gastos (
    id_movimiento   INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario      INT NOT NULL,
    id_categoria    INT NOT NULL,
    tipo            ENUM('ingreso', 'gasto') NOT NULL,
    monto           DECIMAL(12,2) NOT NULL,
    fecha           DATE NOT NULL,
    descripcion     VARCHAR(255),
    fecha_creacion  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_usuario) REFERENCES usuarios(id_usuario)
        ON DELETE CASCADE,
    FOREIGN KEY (id_categoria) REFERENCES categorias(id_categoria)
        ON DELETE RESTRICT
);

-- Índices recomendados para consultas analíticas
CREATE INDEX idx_mov_usuario_fecha ON ingresos_gastos (id_usuario, fecha);
CREATE INDEX idx_mov_categoria ON ingresos_gastos (id_categoria);
```

### 7.3 Datos ficticios de prueba (seed)

```sql
INSERT INTO usuarios (nombre, correo, contrasena_hash)
VALUES ('Ana Torres', 'ana@example.com', 'hash_generado_con_bcrypt');

INSERT INTO categorias (nombre, tipo, id_usuario) VALUES
('Salario', 'ingreso', 1),
('Freelance', 'ingreso', 1),
('Alimentación', 'gasto', 1),
('Transporte', 'gasto', 1),
('Entretenimiento', 'gasto', 1),
('Salud', 'gasto', 1);

INSERT INTO ingresos_gastos (id_usuario, id_categoria, tipo, monto, fecha, descripcion) VALUES
(1, 1, 'ingreso', 2500000, '2026-06-01', 'Pago mensual'),
(1, 3, 'gasto', 320000, '2026-06-05', 'Mercado del mes'),
(1, 4, 'gasto', 90000,  '2026-06-07', 'Transporte semanal'),
(1, 5, 'gasto', 150000, '2026-06-10', 'Cine y salidas'),
(1, 1, 'ingreso', 2500000, '2026-07-01', 'Pago mensual'),
(1, 3, 'gasto', 300000, '2026-07-04', 'Mercado del mes'),
(1, 6, 'gasto', 800000, '2026-07-15', 'Consulta médica de urgencia'); -- Posible anomalía
```

> **Tarea del aprendiz:** amplía este seed con al menos 6 meses de datos históricos y varios usuarios, para que el módulo analítico tenga suficiente información con la que trabajar.

---

## 8. Especificación de la API (backend)

Diseña como mínimo estas rutas. Puedes usar Flask o FastAPI; la tabla es agnóstica al framework.

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/usuarios` | Crear un usuario nuevo. |
| POST | `/api/categorias` | Crear una categoría. |
| GET | `/api/categorias?id_usuario=` | Listar categorías de un usuario. |
| POST | `/api/movimientos` | Registrar un ingreso o gasto. |
| GET | `/api/movimientos?id_usuario=&desde=&hasta=&categoria=` | Listar movimientos con filtros opcionales. |
| PUT | `/api/movimientos/{id}` | Editar un movimiento. |
| DELETE | `/api/movimientos/{id}` | Eliminar un movimiento. |
| GET | `/api/resumen?id_usuario=&mes=` | Totales de ingresos, gastos y balance del periodo. |
| GET | `/api/analitica/prediccion?id_usuario=` | Predicción del gasto del próximo mes. |
| GET | `/api/analitica/anomalias?id_usuario=` | Lista de movimientos marcados como anómalos. |

### Ejemplo de contrato JSON (POST `/api/movimientos`)

```json
{
  "id_usuario": 1,
  "id_categoria": 3,
  "tipo": "gasto",
  "monto": 85000,
  "fecha": "2026-08-20",
  "descripcion": "Mercado quincenal"
}
```

### Ejemplo de respuesta (GET `/api/analitica/prediccion`)

```json
{
  "id_usuario": 1,
  "prediccion_proximo_mes": 1180000,
  "metodo": "regresion_lineal",
  "confianza": "media",
  "detalle_por_categoria": {
    "Alimentación": 320000,
    "Transporte": 95000,
    "Entretenimiento": 140000
  }
}
```

---

## 9. Módulo analítico (el corazón del proyecto)

Este es el componente que diferencia tu proyecto de un simple CRUD. Debe:

1. **Extraer** los datos históricos del usuario desde MySQL con una consulta SQL o con `pandas.read_sql`.
2. **Limpiar** los datos: verificar tipos, manejar valores nulos, convertir la columna `fecha` a `datetime`.
3. **Calcular métricas clave**:
   - Porcentaje de ahorro mensual: `(ingresos - gastos) / ingresos * 100`
   - Categoría más costosa del mes y del histórico.
   - Tendencia mensual de gasto (agrupando con `groupby` por mes).
4. **Predecir el gasto del próximo mes** con un modelo simple, por ejemplo `LinearRegression` de Scikit-learn usando el número de mes como variable independiente y el gasto total como variable dependiente.
5. **Detectar anomalías**, por ejemplo con una regla estadística simple (z-score) o con `IsolationForest` de Scikit-learn: un gasto es "anómalo" si se aleja más de 2 desviaciones estándar del promedio de su categoría.

### Esqueleto de referencia (Pandas + Scikit-learn)

```python
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np

def cargar_datos(conexion, id_usuario):
    query = """
        SELECT fecha, tipo, monto, id_categoria
        FROM ingresos_gastos
        WHERE id_usuario = %s
    """
    df = pd.read_sql(query, conexion, params=(id_usuario,))
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['mes'] = df['fecha'].dt.to_period('M')
    return df

def predecir_gasto_proximo_mes(df):
    gastos = df[df['tipo'] == 'gasto']
    resumen_mensual = gastos.groupby('mes')['monto'].sum().reset_index()
    resumen_mensual['n_mes'] = range(len(resumen_mensual))

    X = resumen_mensual[['n_mes']]
    y = resumen_mensual['monto']

    modelo = LinearRegression()
    modelo.fit(X, y)

    siguiente = [[len(resumen_mensual)]]
    prediccion = modelo.predict(siguiente)[0]
    return round(prediccion, 2)

def detectar_anomalias(df, umbral_z=2):
    gastos = df[df['tipo'] == 'gasto'].copy()
    stats = gastos.groupby('id_categoria')['monto'].agg(['mean', 'std']).reset_index()
    gastos = gastos.merge(stats, on='id_categoria')
    gastos['z_score'] = (gastos['monto'] - gastos['mean']) / gastos['std']
    anomalias = gastos[gastos['z_score'].abs() > umbral_z]
    return anomalias
```

> Este código es un **punto de partida**, no la solución final. El aprendiz debe adaptarlo, manejar casos con pocos datos (menos de 3 meses), y justificar sus decisiones en el informe final.

---

## 10. Frontend

- Formulario de registro de movimiento (monto, fecha, categoría, tipo, descripción) con validación básica en JS (montos positivos, fecha no futura para gastos, campos obligatorios).
- Tabla o lista de movimientos recientes, con opción de editar/eliminar.
- Dashboard con al menos:
  - Gráfico de dona: distribución de gastos por categoría (Chart.js `doughnut`).
  - Gráfico de líneas: ingresos vs. gastos por mes (Chart.js `line`).
  - Tarjetas (cards) con: total ingresos, total gastos, balance/ahorro, predicción próximo mes.
  - Listado o alerta visual de anomalías detectadas.
- Uso de `fetch()` con `async/await`, manejo de errores (try/catch) y estados de carga (spinners o mensajes "cargando...").

---

## 11. Hoja de ruta / Cronograma sugerido (4 semanas)

| Semana | Entregable | Detalle |
|--------|-----------|---------|
| 1 | Base de datos + Backend inicial | Esquema MySQL creado, datos de prueba cargados, servidor Flask/FastAPI con conexión a MySQL y rutas GET/POST básicas de usuarios, categorías y movimientos funcionando (probadas con Postman/Insomnia). |
| 2 | Frontend conectado | Formularios funcionales, tabla de movimientos, consumo de la API con `fetch`, CRUD completo desde la interfaz. |
| 3 | Módulo analítico | Endpoint de resumen financiero, predicción con regresión lineal y detección de anomalías, probados con datos reales del seed ampliado. |
| 4 | Dashboard final + entrega | Gráficos con Chart.js integrados, README completo, código versionado en Git, sustentación oral del proyecto (10-15 min). |

---

## 12. Rúbrica de evaluación (100 puntos)

| Criterio | Puntos | Descripción |
|----------|--------|-------------|
| Modelo de base de datos | 15 | Normalización correcta, claves foráneas, índices, datos de prueba coherentes. |
| API REST (backend) | 20 | Endpoints completos, códigos de estado correctos, manejo de errores, organización del código. |
| Frontend e integración | 20 | Formularios funcionales, UX clara, consumo correcto de la API, manejo de estados de carga/error. |
| Módulo analítico | 25 | Cálculo correcto de métricas, predicción razonable, detección de anomalías justificada, uso adecuado de Pandas/Scikit-learn. |
| Visualización (Chart.js) | 10 | Gráficos claros, correctamente alimentados con datos reales, buena elección de tipo de gráfico. |
| Documentación y sustentación | 10 | README claro, código comentado, capacidad de explicar decisiones técnicas. |

---

## 13. Retos opcionales (para subir de nivel)

- Autenticación con JWT y sesiones por usuario.
- Exportar el reporte analítico a PDF (puede usarse `reportlab` o similar).
- Comparar varios modelos de predicción (regresión lineal vs. `RandomForestRegressor`) y justificar cuál funciona mejor.
- Desplegar el proyecto (backend en Render/Railway, base de datos en un servicio gestionado, frontend en Netlify/Vercel).
- Agregar metas de ahorro por categoría con alertas cuando el usuario se acerque al límite.

---

## 14. Entregables finales

1. Repositorio Git con la siguiente estructura sugerida:
   ```
   /backend
     /rutas
     /modelos
     /analitica
     app.py
     requirements.txt
   /frontend
     index.html
     /css
     /js
   /database
     schema.sql
     seed.sql
   README.md
   ```
2. Video o sustentación en vivo (10-15 min) mostrando el flujo completo: registrar un movimiento, ver el dashboard actualizarse, y explicar cómo se calculó la predicción.
3. Informe corto (1-2 páginas) explicando las decisiones de diseño de base de datos y del modelo analítico.

---

### Nota para el aprendiz

No busques la solución "perfecta" desde el inicio. Construye primero el CRUD funcionando de punta a punta con datos simples, y solo después añade la capa analítica. Es más valioso un proyecto simple que funciona completo, que uno ambicioso a medio terminar.
