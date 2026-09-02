-- ============================================================
-- seed.sql — Datos iniciales de prueba para finanzas_personales
-- Usuario Demo: ana@example.com / Password123!
-- ============================================================

USE finanzas_personales;

-- 1. Insertar Usuario Demo
-- Contraseña en texto plano: Password123!
-- Hash Bcrypt de 60 caracteres compatible con passlib / bcrypt
INSERT INTO usuarios (id_usuario, nombre, correo, contrasena_hash, is_active)
VALUES (
    1,
    'Ana Torres',
    'ana@example.com',
    '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW',
    TRUE
)
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);

-- 2. Insertar Categorías base para el usuario 1
INSERT INTO categorias (id_categoria, nombre, tipo, id_usuario) VALUES
(1, 'Salario', 'ingreso', 1),
(2, 'Freelance / Honorarios', 'ingreso', 1),
(3, 'Alimentación y Supermercado', 'gasto', 1),
(4, 'Transporte y Movilidad', 'gasto', 1),
(5, 'Vivienda y Servicios', 'gasto', 1),
(6, 'Entretenimiento y Ocio', 'gasto', 1),
(7, 'Salud y Bienestar', 'gasto', 1),
(8, 'Educación', 'gasto', 1)
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre);

-- 3. Insertar Movimientos históricos (Últimos 4 meses para alimentar el modelo ML)
INSERT INTO ingresos_gastos (id_usuario, id_categoria, tipo, monto, fecha, descripcion) VALUES
-- Mayo 2026
(1, 1, 'ingreso', 3500000.00, '2026-05-01', 'Salario mensual'),
(1, 2, 'ingreso', 800000.00,  '2026-05-15', 'Proyecto Frontend freelance'),
(1, 5, 'gasto',   1100000.00, '2026-05-05', 'Arriendo y servicios públicos'),
(1, 3, 'gasto',    450000.00, '2026-05-08', 'Mercado quincenal'),
(1, 4, 'gasto',    140000.00, '2026-05-12', 'Transporte y combustible'),
(1, 6, 'gasto',    200000.00, '2026-05-20', 'Cena y cine'),
(1, 3, 'gasto',    420000.00, '2026-05-24', 'Mercado segunda quincena'),

-- Junio 2026
(1, 1, 'ingreso', 3500000.00, '2026-06-01', 'Salario mensual'),
(1, 5, 'gasto',   1100000.00, '2026-06-05', 'Arriendo y servicios públicos'),
(1, 3, 'gasto',    480000.00, '2026-06-07', 'Mercado quincenal'),
(1, 4, 'gasto',    150000.00, '2026-06-11', 'Transporte'),
(1, 6, 'gasto',    250000.00, '2026-06-18', 'Salida de fin de semana'),
(1, 7, 'gasto',    180000.00, '2026-06-25', 'Medicamentos y cita odontológica'),
(1, 3, 'gasto',    460000.00, '2026-06-28', 'Mercado fin de mes'),

-- Julio 2026
(1, 1, 'ingreso', 3500000.00, '2026-07-01', 'Salario mensual'),
(1, 2, 'ingreso', 600000.00,  '2026-07-10', 'Asesoría técnica freelance'),
(1, 5, 'gasto',   1100000.00, '2026-07-05', 'Arriendo y servicios públicos'),
(1, 3, 'gasto',    510000.00, '2026-07-06', 'Mercado mensual grande'),
(1, 4, 'gasto',    160000.00, '2026-07-12', 'Transporte y recarga tarjeta'),
(1, 7, 'gasto',    950000.00, '2026-07-16', 'Urgencia médica y exámenes (Anomalía)'),
(1, 6, 'gasto',    190000.00, '2026-07-22', 'Suscripciones y streaming'),
(1, 3, 'gasto',    490000.00, '2026-07-27', 'Mercado complementario'),

-- Agosto 2026
(1, 1, 'ingreso', 3500000.00, '2026-08-01', 'Salario mensual'),
(1, 5, 'gasto',   1100000.00, '2026-08-05', 'Arriendo y servicios públicos'),
(1, 3, 'gasto',    520000.00, '2026-08-08', 'Mercado mensual'),
(1, 4, 'gasto',    155000.00, '2026-08-14', 'Transporte'),
(1, 8, 'gasto',    350000.00, '2026-08-20', 'Curso de FastAPI y Machine Learning'),
(1, 6, 'gasto',    210000.00, '2026-08-26', 'Restaurantes y entretenimiento');

-- 4. Insertar Presupuestos mensuales de prueba (Septiembre 2026)
INSERT INTO presupuestos (id_usuario, id_categoria, monto_limite, mes, anio) VALUES
(1, 3, 1000000.00, 9, 2026), -- Alimentación: $1,000,000
(1, 4,  350000.00, 9, 2026), -- Transporte: $350,000
(1, 5, 1200000.00, 9, 2026), -- Vivienda: $1,200,000
(1, 6,  400000.00, 9, 2026), -- Entretenimiento: $400,000
(1, 7,  300000.00, 9, 2026)  -- Salud: $300,000
ON DUPLICATE KEY UPDATE monto_limite=VALUES(monto_limite);

-- 5. Insertar Metas de Ahorro iniciales
INSERT INTO metas_ahorro (id_usuario, nombre, monto_objetivo, monto_actual, fecha_limite, completada) VALUES
(1, 'Fondo de Emergencia (6 meses)', 15000000.00, 6800000.00, '2026-12-31', FALSE),
(1, 'Vacaciones a San Andrés',        4500000.00, 3200000.00, '2026-11-15', FALSE),
(1, 'Renovación Portátil Developer',  5000000.00, 5000000.00, '2026-08-01', TRUE);