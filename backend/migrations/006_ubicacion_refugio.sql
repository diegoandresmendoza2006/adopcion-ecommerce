-- =============================================================================
-- Migración 006: ubicación del refugio en el mapa
-- Tabla: adopcion.refugios
--
-- Agrega latitud y longitud. El administrador elige el punto en el mapa al crear o editar un
-- refugio, y la app lo usa en el botón "Ver en el mapa" de la tarjeta del refugio.
-- Los refugios que ya existen quedan con estas columnas en NULL (siguen usando la dirección escrita).
--
-- Cómo ejecutarla (una sola vez; en Neon: SQL Editor). Es segura de repetir y no borra datos.
-- =============================================================================

BEGIN;

ALTER TABLE adopcion.refugios
    ADD COLUMN IF NOT EXISTS latitud  DOUBLE PRECISION,
    ADD COLUMN IF NOT EXISTS longitud DOUBLE PRECISION;

COMMIT;
