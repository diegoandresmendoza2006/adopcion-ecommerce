-- =============================================================================
-- Migración 002: formulario de adopción completo + comentario del encargado
-- Tabla: adopcion.solicitudes_adopcion
--
-- Cómo ejecutarla (una sola vez, con el usuario dueño de las tablas, p. ej. postgres):
--   psql -U postgres -h localhost -d adopcion_ecommerce -f backend/migrations/002_formulario_adopcion.sql
--
-- Es segura de repetir: usa IF NOT EXISTS y las filas antiguas se conservan
-- (las columnas nuevas quedan en NULL para las solicitudes enviadas antes).
-- =============================================================================

BEGIN;

ALTER TABLE adopcion.solicitudes_adopcion
    -- (ya existían desde la migración anterior; se repiten por si la base es nueva)
    ADD COLUMN IF NOT EXISTS nombre_contacto           VARCHAR(150),
    ADD COLUMN IF NOT EXISTS telefono                  VARCHAR(30),
    ADD COLUMN IF NOT EXISTS tipo_vivienda             VARCHAR(50),
    ADD COLUMN IF NOT EXISTS motivo                    TEXT,
    -- datos personales
    ADD COLUMN IF NOT EXISTS fecha_nacimiento          DATE,
    ADD COLUMN IF NOT EXISTS email_contacto            VARCHAR(100),
    ADD COLUMN IF NOT EXISTS direccion                 VARCHAR(255),
    -- vivienda, entorno y espacio
    ADD COLUMN IF NOT EXISTS vivienda_permite_mascotas BOOLEAN,
    ADD COLUMN IF NOT EXISTS tiene_patio               BOOLEAN,
    ADD COLUMN IF NOT EXISTS tiene_cercas              BOOLEAN,
    ADD COLUMN IF NOT EXISTS personas_hogar            INTEGER,
    -- experiencia previa
    ADD COLUMN IF NOT EXISTS tuvo_mascotas             BOOLEAN,
    ADD COLUMN IF NOT EXISTS mascotas_vacunadas        BOOLEAN,
    ADD COLUMN IF NOT EXISTS mascotas_esterilizadas    BOOLEAN,
    -- disponibilidad y estilo de vida
    ADD COLUMN IF NOT EXISTS horas_solo                INTEGER,
    ADD COLUMN IF NOT EXISTS responsable_viajes        TEXT,
    -- respuesta del encargado (la ve el adoptante en "Mis trámites")
    ADD COLUMN IF NOT EXISTS comentario_encargado      TEXT,
    ADD COLUMN IF NOT EXISTS fecha_respuesta           TIMESTAMP;

-- Reglas de integridad (los NULL de solicitudes antiguas siguen siendo válidos)
ALTER TABLE adopcion.solicitudes_adopcion DROP CONSTRAINT IF EXISTS chk_solicitud_horas_solo;
ALTER TABLE adopcion.solicitudes_adopcion
    ADD CONSTRAINT chk_solicitud_horas_solo CHECK (horas_solo IS NULL OR horas_solo BETWEEN 0 AND 24);

ALTER TABLE adopcion.solicitudes_adopcion DROP CONSTRAINT IF EXISTS chk_solicitud_personas_hogar;
ALTER TABLE adopcion.solicitudes_adopcion
    ADD CONSTRAINT chk_solicitud_personas_hogar CHECK (personas_hogar IS NULL OR personas_hogar BETWEEN 1 AND 30);

COMMIT;
