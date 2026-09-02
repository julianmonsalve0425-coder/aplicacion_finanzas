# ============================================================
# models.py — Modelos SQLAlchemy (Mapeo ORM para MySQL)
# Tablas: usuarios, categorias, ingresos_gastos, presupuestos, metas_ahorro
# ============================================================

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Enum, DECIMAL, Date,
    DateTime, Boolean, ForeignKey, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from database import Base


class Usuario(Base):
    """
    Tabla: usuarios
    Representa las cuentas de usuario y credenciales de acceso.
    """
    __tablename__ = "usuarios"

    id_usuario          = Column(Integer, primary_key=True, autoincrement=True)
    nombre              = Column(String(100), nullable=False)
    correo              = Column(String(150), nullable=False, unique=True, index=True)
    contrasena_hash     = Column(String(255), nullable=False)
    is_active           = Column(Boolean, default=True, nullable=False)
    fecha_registro      = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones ORM
    categorias   = relationship("Categoria", back_populates="usuario", cascade="all, delete-orphan")
    movimientos  = relationship("IngresoGasto", back_populates="usuario", cascade="all, delete-orphan")
    presupuestos = relationship("Presupuesto", back_populates="usuario", cascade="all, delete-orphan")
    metas        = relationship("MetaAhorro", back_populates="usuario", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Usuario id={self.id_usuario} correo='{self.correo}'>"


class Categoria(Base):
    """
    Tabla: categorias
    Clasifica los movimientos del usuario (ej. Salario, Alimentación).
    """
    __tablename__ = "categorias"

    id_categoria   = Column(Integer, primary_key=True, autoincrement=True)
    nombre         = Column(String(50), nullable=False)
    tipo           = Column(Enum("ingreso", "gasto", name="tipo_categoria_enum"), nullable=False)
    id_usuario     = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    usuario      = relationship("Usuario", back_populates="categorias")
    movimientos  = relationship("IngresoGasto", back_populates="categoria")
    presupuestos = relationship("Presupuesto", back_populates="categoria", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("nombre <> ''", name="chk_nombre_categoria"),
        UniqueConstraint("id_usuario", "nombre", "tipo", name="uq_usuario_categoria_tipo"),
    )

    def __repr__(self):
        return f"<Categoria id={self.id_categoria} nombre='{self.nombre}' tipo='{self.tipo}'>"


class IngresoGasto(Base):
    """
    Tabla: ingresos_gastos
    Registra cada transacción financiera (ingreso o gasto) realizada por el usuario.
    """
    __tablename__ = "ingresos_gastos"

    id_movimiento  = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario     = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    id_categoria   = Column(Integer, ForeignKey("categorias.id_categoria", ondelete="RESTRICT"), nullable=False)
    tipo           = Column(Enum("ingreso", "gasto", name="tipo_movimiento_enum"), nullable=False)
    monto          = Column(DECIMAL(12, 2), nullable=False)
    fecha          = Column(Date, nullable=False)
    descripcion    = Column(String(255), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    usuario   = relationship("Usuario", back_populates="movimientos")
    categoria = relationship("Categoria", back_populates="movimientos")

    __table_args__ = (
        CheckConstraint("monto > 0", name="chk_monto_positivo"),
        Index("idx_mov_usuario_fecha", "id_usuario", "fecha"),
        Index("idx_mov_categoria", "id_categoria"),
        Index("idx_mov_tipo", "tipo"),
    )

    def __repr__(self):
        return f"<IngresoGasto id={self.id_movimiento} tipo='{self.tipo}' monto={self.monto}>"


class Presupuesto(Base):
    """
    Tabla: presupuestos
    Define límites de gasto mensuales por categoría fijados por el usuario.
    """
    __tablename__ = "presupuestos"

    id_presupuesto = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario     = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    id_categoria   = Column(Integer, ForeignKey("categorias.id_categoria", ondelete="CASCADE"), nullable=False)
    monto_limite   = Column(DECIMAL(12, 2), nullable=False)
    mes            = Column(Integer, nullable=False)  # 1 a 12
    anio           = Column(Integer, nullable=False)  # ej: 2026
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    usuario   = relationship("Usuario", back_populates="presupuestos")
    categoria = relationship("Categoria", back_populates="presupuestos")

    __table_args__ = (
        CheckConstraint("monto_limite > 0", name="chk_monto_limite_positivo"),
        CheckConstraint("mes BETWEEN 1 AND 12", name="chk_mes_valido"),
        CheckConstraint("anio >= 2020", name="chk_anio_valido"),
        UniqueConstraint("id_usuario", "id_categoria", "mes", "anio", name="uq_usuario_categoria_periodo"),
        Index("idx_presupuesto_usuario_periodo", "id_usuario", "anio", "mes"),
    )

    def __repr__(self):
        return f"<Presupuesto id={self.id_presupuesto} cat={self.id_categoria} periodo={self.mes}/{self.anio}>"


class MetaAhorro(Base):
    """
    Tabla: metas_ahorro
    Metas de ahorro financiero con seguimiento de progreso y fecha objetivo.
    """
    __tablename__ = "metas_ahorro"

    id_meta        = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario     = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    nombre         = Column(String(100), nullable=False)
    monto_objetivo = Column(DECIMAL(12, 2), nullable=False)
    monto_actual   = Column(DECIMAL(12, 2), nullable=False, default=0.00)
    fecha_limite   = Column(Date, nullable=True)
    completada     = Column(Boolean, nullable=False, default=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    usuario = relationship("Usuario", back_populates="metas")

    __table_args__ = (
        CheckConstraint("monto_objetivo > 0", name="chk_monto_objetivo_positivo"),
        CheckConstraint("monto_actual >= 0", name="chk_monto_actual_no_negativo"),
        Index("idx_metas_usuario", "id_usuario"),
    )

    def __repr__(self):
        return f"<MetaAhorro id={self.id_meta} nombre='{self.nombre}' progreso={self.monto_actual}/{self.monto_objetivo}>"
