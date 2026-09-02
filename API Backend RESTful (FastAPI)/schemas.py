# ============================================================
# schemas.py — Schemas Pydantic v2 (Validación Request / Response)
# ============================================================

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Literal, Union, Any
from pydantic import BaseModel, EmailStr, field_validator, ConfigDict, Field


# ─────────────────────────────────────────
# AUTENTICACIÓN Y TOKENS JWT
# ─────────────────────────────────────────

class Token(BaseModel):
    """Respuesta tras login o registro exitoso."""
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    usuario: Optional["UsuarioResponse"] = None


class TokenData(BaseModel):
    """Payload decodificado del JWT."""
    correo: Optional[str] = None
    id_usuario: Optional[int] = None


class TokenRefreshRequest(BaseModel):
    """Body para POST /api/auth/refresh."""
    refresh_token: str


class LoginRequest(BaseModel):
    """Body JSON alternativo para login directo."""
    correo: EmailStr
    contrasena: str


# ─────────────────────────────────────────
# USUARIOS
# ─────────────────────────────────────────

class UsuarioCreate(BaseModel):
    """Body para registrar un nuevo usuario."""
    nombre:     str = Field(..., min_length=2, max_length=100)
    correo:     EmailStr
    contrasena: str = Field(..., min_length=8, max_length=100)

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("El nombre no puede estar compuesto únicamente de espacios")
        return clean


class UsuarioResponse(BaseModel):
    """Datos públicos del usuario (sin exponer password hash)."""
    id_usuario:          int
    nombre:              str
    correo:              str
    is_active:           bool
    fecha_registro:      Optional[Union[datetime, str]] = None

    model_config = ConfigDict(from_attributes=True)


class UsuarioUpdate(BaseModel):
    """Body para actualizar perfil o contraseña."""
    nombre:             Optional[str] = None
    contrasena_actual:  Optional[str] = None
    contrasena_nueva:   Optional[str] = None


# ─────────────────────────────────────────
# CATEGORÍAS
# ─────────────────────────────────────────

class CategoriaCreate(BaseModel):
    """Body para crear categoría asociada al usuario autenticado."""
    nombre: str = Field(..., min_length=1, max_length=50)
    tipo:   Literal["ingreso", "gasto"]

    @field_validator("nombre")
    @classmethod
    def nombre_no_vacio(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("El nombre de la categoría no puede estar vacío")
        return clean


class CategoriaResponse(BaseModel):
    """Respuesta al consultar categorías."""
    id_categoria:   int
    nombre:         str
    tipo:           str
    id_usuario:     int
    fecha_creacion: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────
# MOVIMIENTOS (Ingresos y Gastos)
# ─────────────────────────────────────────

class MovimientoCreate(BaseModel):
    """Body para registrar un nuevo movimiento financiero."""
    id_categoria: int
    tipo:         Literal["ingreso", "gasto"]
    monto:        Decimal = Field(..., gt=0)
    fecha:        date
    descripcion:  Optional[str] = Field(None, max_length=255)

    @field_validator("monto")
    @classmethod
    def monto_positivo(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("El monto debe ser estrictamente mayor a 0")
        return v


class MovimientoUpdate(BaseModel):
    """Body para actualizar parcialmente un movimiento."""
    id_categoria: Optional[int] = None
    tipo:         Optional[Literal["ingreso", "gasto"]] = None
    monto:        Optional[Decimal] = Field(None, gt=0)
    fecha:        Optional[date] = None
    descripcion:  Optional[str] = Field(None, max_length=255)


class MovimientoResponse(BaseModel):
    """Respuesta de un movimiento individual."""
    id_movimiento:    int
    id_usuario:       int
    id_categoria:     int
    tipo:             str
    monto:            Decimal
    fecha:            date
    descripcion:      Optional[str] = None
    fecha_creacion:   datetime
    nombre_categoria: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MovimientosPaginadosResponse(BaseModel):
    """Respuesta paginada para listas grandes de movimientos."""
    total:  int
    limit:  int
    offset: int
    items:  List[MovimientoResponse]


# ─────────────────────────────────────────
# PRESUPUESTOS POR CATEGORÍA
# ─────────────────────────────────────────

class PresupuestoCreate(BaseModel):
    """Body para fijar presupuesto mensual en una categoría."""
    id_categoria: int
    monto_limite: Decimal = Field(..., gt=0)
    mes:          int = Field(..., ge=1, le=12)
    anio:         int = Field(..., ge=2020, le=2100)


class PresupuestoUpdate(BaseModel):
    """Body para editar monto o período de un presupuesto."""
    monto_limite: Optional[Decimal] = Field(None, gt=0)
    mes:          Optional[int] = Field(None, ge=1, le=12)
    anio:         Optional[int] = Field(None, ge=2020, le=2100)


class PresupuestoResponse(BaseModel):
    """Respuesta con datos de presupuesto."""
    id_presupuesto:   int
    id_usuario:       int
    id_categoria:     int
    monto_limite:     Decimal
    mes:              int
    anio:             int
    fecha_creacion:   datetime
    nombre_categoria: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PresupuestoResumenItem(BaseModel):
    """Detalle de ejecución de un presupuesto comparado contra gastos reales."""
    id_presupuesto:   int
    id_categoria:     int
    nombre_categoria: str
    monto_limite:     float
    monto_gastado:    float
    porcentaje_usado: float
    restante:         float
    sobregirado:      bool
    mes:              int
    anio:             int


class PresupuestosResumenResponse(BaseModel):
    """Resumen consolidado de presupuestos del mes consultado."""
    mes:                  int
    anio:                 int
    total_presupuestado:  float
    total_gastado:        float
    items:                List[PresupuestoResumenItem]


# ─────────────────────────────────────────
# METAS DE AHORRO
# ─────────────────────────────────────────

class MetaAhorroCreate(BaseModel):
    """Body para crear una meta de ahorro."""
    nombre:         str = Field(..., min_length=2, max_length=100)
    monto_objetivo: Decimal = Field(..., gt=0)
    monto_actual:   Optional[Decimal] = Field(default=Decimal(0), ge=0)
    fecha_limite:   Optional[date] = None


class MetaAhorroUpdate(BaseModel):
    """Body para editar atributos de una meta."""
    nombre:         Optional[str] = None
    monto_objetivo: Optional[Decimal] = Field(None, gt=0)
    monto_actual:   Optional[Decimal] = Field(None, ge=0)
    fecha_limite:   Optional[date] = None
    completada:     Optional[bool] = None


class MetaAhorroAbono(BaseModel):
    """Body para ingresar un aporte económico a la meta."""
    monto: Decimal = Field(..., gt=0)


class MetaAhorroResponse(BaseModel):
    """Respuesta con cálculo dinámico de avance porcentual."""
    id_meta:              int
    id_usuario:           int
    nombre:               str
    monto_objetivo:       Decimal
    monto_actual:         Decimal
    porcentaje_progreso:  float = 0.0
    fecha_limite:         Optional[date] = None
    completada:           bool
    fecha_creacion:       datetime

    model_config = ConfigDict(from_attributes=True)


# ─────────────────────────────────────────
# RESUMEN FINANCIERO (KPIs)
# ─────────────────────────────────────────

class ResumenResponse(BaseModel):
    """Respuesta para GET /api/resumen."""
    id_usuario:        int
    total_ingresos:    float
    total_gastos:      float
    balance:           float
    porcentaje_ahorro: float = 0.0


# ─────────────────────────────────────────
# ANALÍTICA Y MACHINE LEARNING
# ─────────────────────────────────────────

class PrediccionResponse(BaseModel):
    """Respuesta de proyección con regresión lineal persistida."""
    id_usuario:      int
    prediccion:      float
    confianza:       str  # "alta", "media", "baja"
    razon:           str
    metodo:          str = "regresion_lineal"
    mes_proyectado:  Optional[str] = None
    modelo_cargado:  bool = False


class AnomaliaItem(BaseModel):
    """Detalle de un movimiento marcado como atípico."""
    id_movimiento:       Optional[int] = None
    fecha:               str
    id_categoria:        int
    nombre_categoria:    Optional[str] = None
    monto:               float
    promedio_categoria:  float
    z_score:             float


class AnomaliasResponse(BaseModel):
    """Respuesta con anomalías estadísticas detectadas."""
    id_usuario: int
    anomalias:  List[AnomaliaItem]
    total:      int


class EntrenamientoResponse(BaseModel):
    """Respuesta tras forzar reentrenamiento y guardado con joblib."""
    mensaje:          str
    modelo_guardado:  bool
    total_meses:      int
    coeficiente:      float
    intercepto:       float


# ─────────────────────────────────────────
# RESPUESTAS GENÉRICAS Y ERRORES
# ─────────────────────────────────────────

class MensajeResponse(BaseModel):
    """Confirmaciones simples."""
    mensaje: str
    detalle: Optional[str] = None


class ErrorResponse(BaseModel):
    """Esquema estándar para respuestas de error JSON."""
    status_code: int
    error:       str
    detalle:     Any
