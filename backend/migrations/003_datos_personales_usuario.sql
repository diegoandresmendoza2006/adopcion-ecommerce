-- =============================================================================
-- Migración 003: datos personales del usuario (se piden al registrarse)
-- Tabla: adopcion.usuarios
--
-- Para qué: la app móvil pide fecha de nacimiento, teléfono y dirección al crear la cuenta
-- y los usa para llenar solos esos campos en el formulario de adopción.
--
-- Cómo ejecutarla (una sola vez):
--   * Local:  psql -U postgres -h localhost -d adopcion_ecommerce -f backend/migrations/003_datos_personales_usuario.sql
--   * Neon:   pegar el contenido en el "SQL Editor" de Neon (rama y base de datos de producción).
--
-- Es segura de repetir (IF NOT EXISTS) y no borra nada: los usuarios que ya existen
-- quedan con estas columnas en NULL.
-- =============================================================================

BEGIN;

ALTER TABLE adopcion.usuarios
    ADD COLUMN IF NOT EXISTS fecha_nacimiento DATE,
    ADD COLUMN IF NOT EXISTS telefono         VARCHAR(30),
    ADD COLUMN IF NOT EXISTS direccion        VARCHAR(255);

COMMIT;
