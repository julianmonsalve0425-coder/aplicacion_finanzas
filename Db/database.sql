-- ============================================================
-- database.sql — Esquema DDL para MySQL / MariaDB
-- Base de Datos: finanzas_personales
-- ============================================================

CREATE DATABASE IF NOT EXISTS finanzas_personales
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE finanzas_personales;

-- ─────────────────────────────────────────
-- 1. TABLA: usuarios
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario           INT AUTO_INCREMENT PRIMARY KEY,
    nombre               VARCHAR(100) NOT NULL,
    correo               VARCHAR(150) NOT NULL UNIQUE,
    contrasena_hash      VARCHAR(255) NOT NULL,
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro       DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_nombre_usuario CHECK (nombre <> ''),
    CONSTRAINT chk_correo_usuario CHECK (correo REGEXP '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'),
    CONSTRAINT chk_contrasena_hash CHECK (CHAR_LENGTH(contrasena_hash) >= 8)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────
-- 2. TABLA: categorias
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categorias (
    id_categoria    INT AUTO_INCREMENT PRIMARY KEY,
    nombre          VARCHAR(50) NOT NULL,
    tipo            ENUM('ingreso', 'gasto') NOT NULL,
    id_usuario      INT NOT NULL,
    fecha_creacion  DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_nombre_categoria CHECK (nombre <> ''),
    CONSTRAINT fk_categoria_usuario FOREIGN KEY (id_usuario) 
        REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    UNIQUE KEY uq_usuario_categoria_tipo (id_usuario, nombre, tipo)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────
-- 3. TABLA: ingresos_gastos (Movimientos)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS ingresos_gastos (
    id_movimiento   INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario      INT NOT NULL,
    id_categoria    INT NOT NULL,
    tipo            ENUM('ingreso', 'gasto') NOT NULL,
    monto           DECIMAL(12,2) NOT NULL,
    fecha           DATE NOT NULL,
    descripcion     VARCHAR(255),
    fecha_creacion  DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_monto_positivo CHECK (monto > 0),
    CONSTRAINT fk_movimiento_usuario FOREIGN KEY (id_usuario) 
        REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_movimiento_categoria FOREIGN KEY (id_categoria) 
        REFERENCES categorias(id_categoria) ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ─────────────────────────────────────────
-- 4. TABLA: presupuestos
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS presupuestos (
    id_presupuesto  INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario      INT NOT NULL,
    id_categoria    INT NOT NULL,
    monto_limite    DECIMAL(12,2) NOT NULL,
    mes             TINYINT UNSIGNED NOT NULL,
    anio            SMALLINT UNSIGNED NOT NULL,
    fecha_creacion  DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_monto_limite_positivo CHECK (monto_limite > 0),
    CONSTRAINT chk_mes_valido CHECK (mes BETWEEN 1 AND 12),
    CONSTRAINT chk_anio_valido CHECK (anio >= 2020),
    CONSTRAINT fk_presupuesto_usuario FOREIGN KEY (id_usuario) 
        REFERENCES usuarios(id_usuario) ON DELETE CASCADE,
    CONSTRAINT fk_presupuesto_categoria FOREIGN KEY (id_categoria) 
        REFERENCES categorias(id_categoria) ON DELETE CASCADE,
    UNIQUE KEY uq_usuario_categoria_periodo (id_usuario, id_categoria, mes, anio)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────
-- 5. TABLA: metas_ahorro
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS metas_ahorro (
    id_meta          INT AUTO_INCREMENT PRIMARY KEY,
    id_usuario       INT NOT NULL,
    nombre           VARCHAR(100) NOT NULL,
    monto_objetivo   DECIMAL(12,2) NOT NULL,
    monto_actual     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    fecha_limite     DATE NULL,
    completada       BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_creacion   DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_monto_objetivo_positivo CHECK (monto_objetivo > 0),
    CONSTRAINT chk_monto_actual_no_negativo CHECK (monto_actual >= 0),
    CONSTRAINT fk_meta_usuario FOREIGN KEY (id_usuario) 
        REFERENCES usuarios(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ─────────────────────────────────────────
-- ÍNDICES DE RENDIMIENTO
-- ─────────────────────────────────────────
CREATE INDEX idx_mov_usuario_fecha ON ingresos_gastos (id_usuario, fecha);
CREATE INDEX idx_mov_categoria ON ingresos_gastos (id_categoria);
CREATE INDEX idx_mov_tipo ON ingresos_gastos (tipo);
CREATE INDEX idx_presupuesto_usuario_periodo ON presupuestos (id_usuario, anio, mes);
CREATE INDEX idx_metas_usuario ON metas_ahorro (id_usuario);