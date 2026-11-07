-- =============================================================================
-- Migración 005: quién aprobó cada adopción (firma del certificado)
-- Tabla: adopcion.solicitudes_adopcion
--
-- Agrega la columna resuelto_por_id. El certificado de adopción muestra el nombre de la
-- persona que aprobó la solicitud. Las adopciones aprobadas ANTES de esta migración quedan sin
-- nombre y el certificado sale con la línea de firma en blanco.
--
-- Cómo ejecutarla (una sola vez; en Neon: SQL Editor). Es segura de repetir y no borra datos.
-- =============================================================================

BEGIN;

ALTER TABLE adopcion.solicitudes_adopcion
    ADD COLUMN IF NOT EXISTS resuelto_por_id INTEGER
    REFERENCES adopcion.usuarios(id) ON DELETE SET NULL;

COMMIT;
