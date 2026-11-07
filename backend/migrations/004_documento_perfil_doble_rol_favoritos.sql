-- =============================================================================
-- Migración 004: documento de identidad, foto de perfil, doble rol y favoritos
-- Tablas: adopcion.usuarios, adopcion.favoritos_mascotas (nueva)
--
-- Qué hace:
--   1) usuarios: columnas tipo_documento, numero_documento y foto_url.
--   2) usuarios: el correo deja de ser único por sí solo. Ahora lo único es (correo, rol), así una
--      misma persona puede tener una cuenta de Encargado Y una de Usuario con el mismo correo.
--   3) favoritos_mascotas: las mascotas favoritas de cada usuario.
--
-- Cómo ejecutarla (una sola vez), con el usuario DUEÑO de las tablas (en Neon: SQL Editor):
--   * Local:  psql -U postgres -h localhost -d adopcion_ecommerce -f backend/migrations/004_documento_perfil_doble_rol_favoritos.sql
--
-- Es segura de repetir y no borra datos.
-- =============================================================================

BEGIN;

ALTER TABLE adopcion.usuarios
    ADD COLUMN IF NOT EXISTS tipo_documento   VARCHAR(5),
    ADD COLUMN IF NOT EXISTS numero_documento VARCHAR(20),
    ADD COLUMN IF NOT EXISTS foto_url         TEXT;

-- Doble rol: se quita la unicidad del correo solo y se exige (correo, rol)
ALTER TABLE adopcion.usuarios DROP CONSTRAINT IF EXISTS usuarios_email_key;
CREATE UNIQUE INDEX IF NOT EXISTS uq_usuarios_email_rol ON adopcion.usuarios (email, rol_id);
CREATE INDEX IF NOT EXISTS ix_usuarios_email ON adopcion.usuarios (email);
CREATE INDEX IF NOT EXISTS ix_usuarios_documento ON adopcion.usuarios (tipo_documento, numero_documento);

-- Favoritos de mascotas
CREATE TABLE IF NOT EXISTS adopcion.favoritos_mascotas (
    usuario_id integer NOT NULL REFERENCES adopcion.usuarios(id)  ON UPDATE CASCADE ON DELETE CASCADE,
    mascota_id integer NOT NULL REFERENCES adopcion.mascotas(id)  ON UPDATE CASCADE ON DELETE CASCADE,
    fecha      timestamp without time zone DEFAULT now(),
    PRIMARY KEY (usuario_id, mascota_id)
);
-- Solo da permisos si el rol existe (en Neon puede llamarse distinto o no existir)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'usuario_adopcion') THEN
        GRANT ALL ON TABLE adopcion.favoritos_mascotas TO usuario_adopcion;
    END IF;
END
$$;

COMMIT;
