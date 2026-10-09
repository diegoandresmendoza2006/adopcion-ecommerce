--
-- PostgreSQL database dump
--

\restrict XNN4bkMgoivfHdD9t3XICiFxF36zN12c6QbKoNgdFhgZ8SQfcIPprss1W4Q8syg

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: adopcion; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA adopcion;


--
-- Name: fn_auditar_cambios(); Type: FUNCTION; Schema: adopcion; Owner: -
--

CREATE FUNCTION adopcion.fn_auditar_cambios() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    usuario_actual TEXT;
    datos_anteriores JSON;
    datos_nuevos JSON;
BEGIN

    -- Obtiene el usuario de PostgreSQL que ejecuta la operación
    usuario_actual := CURRENT_USER;

    -- INSERT
    IF TG_OP = 'INSERT' THEN

        datos_nuevos := row_to_json(NEW);

        INSERT INTO adopcion.auditoria (
            nombre_usuario,
            accion,
            tabla_afectada,
            detalle_cambios
        )
        VALUES (
            usuario_actual,
            'INSERT',
            TG_TABLE_NAME,
            json_build_object(
                'nuevo', datos_nuevos
            )
        );

        RETURN NEW;

    -- UPDATE
    ELSIF TG_OP = 'UPDATE' THEN

        datos_anteriores := row_to_json(OLD);
        datos_nuevos := row_to_json(NEW);

        INSERT INTO adopcion.auditoria (
            nombre_usuario,
            accion,
            tabla_afectada,
            detalle_cambios
        )
        VALUES (
            usuario_actual,
            'UPDATE',
            TG_TABLE_NAME,
            json_build_object(
                'anterior', datos_anteriores,
                'nuevo', datos_nuevos
            )
        );

        RETURN NEW;

    -- DELETE
    ELSIF TG_OP = 'DELETE' THEN

        datos_anteriores := row_to_json(OLD);

        INSERT INTO adopcion.auditoria (
            nombre_usuario,
            accion,
            tabla_afectada,
            detalle_cambios
        )
        VALUES (
            usuario_actual,
            'DELETE',
            TG_TABLE_NAME,
            json_build_object(
                'anterior', datos_anteriores
            )
        );

        RETURN OLD;

    END IF;

    RETURN NULL;
END;
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: auditoria; Type: TABLE; Schema: adopcion; Owner: -
--

CREATE TABLE adopcion.auditoria (
    id integer NOT NULL,
    nombre_usuario character varying(100) NOT NULL,
    accion character varying(20) NOT NULL,
    tabla_afectada character varying(50) NOT NULL,
    detalle_cambios json,
    fecha_accion timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_auditoria_accion CHECK (((accion)::text = ANY ((ARRAY['INSERT'::character varying, 'UPDATE'::character varying, 'DELETE'::character varying])::text[])))
);


--
-- Name: auditoria_id_seq; Type: SEQUENCE; Schema: adopcion; Owner: -
--

CREATE SEQUENCE adopcion.auditoria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: auditoria_id_seq; Type: SEQUENCE OWNED BY; Schema: adopcion; Owner: -
--

ALTER SEQUENCE adopcion.auditoria_id_seq OWNED BY adopcion.auditoria.id;


--
-- Name: categorias_productos; Type: TABLE; Schema: adopcion; Owner: -
--

CREATE TABLE adopcion.categorias_productos (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text
);


--
-- Name: categorias_productos_id_seq; Type: SEQUENCE; Schema: adopcion; Owner: -
--

CREATE SEQUENCE adopcion.categorias_productos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: categorias_productos_id_seq; Type: SEQUENCE OWNED BY; Schema: adopcion; Owner: -
--

ALTER SEQUENCE adopcion.categorias_productos_id_seq OWNED BY adopcion.categorias_productos.id;


--
-- Name: detalles_orden; Type: TABLE; Schema: adopcion; Owner: -
--

CREATE TABLE adopcion.detalles_orden (
    id integer NOT NULL,
    orden_id integer NOT NULL,
    producto_id integer NOT NULL,
    cantidad integer NOT NULL,
    precio_unitario numeric(10,2) NOT NULL,
    CONSTRAINT chk_detalle_cantidad CHECK ((cantidad > 0)),
    CONSTRAINT chk_detalle_precio CHECK ((precio_unitario >= (0)::numeric))
);


--
-- Name: detalles_orden_id_seq; Type: SEQUENCE; Schema: adopcion; Owner: -
--

CREATE SEQUENCE adopcion.detalles_orden_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: detalles_orden_id_seq; Type: SEQUENCE OWNED BY; Schema: adopcion; Owner: -
--

ALTER SEQUENCE adopcion.detalles_orden_id_seq OWNED BY adopcion.detalles_orden.id;


--
-- Name: mascotas; Type: TABLE; Schema: adopcion; Owner: -
--

CREATE TABLE adopcion.mascotas (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    especie character varying(50) NOT NULL,
    raza character varying(50),
    edad_meses integer,
    descripcion text,
    estado_adopcion character varying(50) DEFAULT 'Disponible'::character varying NOT NULL,
    refugio_id integer NOT NULL,
    imagen_url text,
    CONSTRAINT chk_mascotas_edad CHECK (((edad_meses IS NULL) OR (edad_meses >= 0))),
    CONSTRAINT chk_mascotas_estado CHECK (((estado_adopcion)::text = ANY ((ARRAY['Disponible'::character varying, 'En Proceso'::character varying, 'Adoptada'::character varying])::text[])))
);


--
-- Name: mascotas_id_seq; Type: SEQUENCE; Schema: adopcion; Owner: -
--

CREATE SEQUENCE adopcion.mascotas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: mascotas_id_seq; Type: SEQUENCE OWNED BY; Schema: adopcion; Owner: -
--

ALTER SEQUENCE adopcion.mascotas_id_seq OWNED BY adopcion.mascotas.id;


--
-- Name: ordenes_compra; Type: TABLE; Schema: adopcion; Owner: -
--

CREATE TABLE adopcion.ordenes_compra (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    total numeric(10,2) NOT NULL,
    estado_pedido character varying(50) DEFAULT 'Pendiente'::character varying NOT NULL,
    fecha_compra timestamp without time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_orden_estado CHECK (((estado_pedido)::text = ANY ((ARRAY['Pendiente'::character varying, 'Pagada'::character varying, 'Enviada'::character varying, 'Entregada'::character varying])::text[]))),
    CONSTRAINT chk_orden_total CHECK ((total >= (0)::numeric))
);


--
-- Name: ordenes_compra_id_seq; Type: SEQUENCE; Schema: adopcion; Owner: -
--

CREATE SEQUENCE adopcion.ordenes_compra_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: ordenes_compra_id_seq; Type: SEQUENCE OWNED BY; Schema: adopcion; Owner: -
--

ALTER SEQUENCE adopcion.ordenes_compra_id_seq OWNED BY adopcion.ordenes_compra.id;


--
-- Name: productos; Type: TABLE; Schema: adopcion; Owner: -
--

CREATE TABLE adopcion.productos (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    descripcion text,
    precio numeric(10,2) NOT NULL,
    stock integer DEFAULT 0 NOT NULL,
    categoria_id integer NOT NULL,
    imagen_url text,
    CONSTRAINT chk_productos_precio CHECK ((precio >= (0)::numeric)),
    CONSTRAINT chk_productos_stock CHECK ((stock >= 0))
);


--
-- Name: productos_id_seq; Type: SEQUENCE; Schema: adopcion; Owner: -
--

CREATE SEQUENCE adopcion.productos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: productos_id_seq; Type: SEQUENCE OWNED BY; Schema: adopcion; Owner: -
--

ALTER SEQUENCE adopcion.productos_id_seq OWNED BY adopcion.productos.id;


--
-- Name: refugios; Type: TABLE; Schema: adopcion; Owner: -
--

CREATE TABLE adopcion.refugios (
    id integer NOT NULL,
    nombre character varying(100) NOT NULL,
    direccion character varying(255),
    telefono character varying(20)
);


--
-- Name: refugios_id_seq; Type: SEQUENCE; Schema: adopcion; Owner: -
--

CREATE SEQUENCE adopcion.refugios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: refugios_id_seq; Type: SEQUENCE OWNED BY; Schema: adopcion; Owner: -
--

ALTER SEQUENCE adopcion.refugios_id_seq OWNED BY adopcion.refugios.id;


--
-- Name: roles; Type: TABLE; Schema: adopcion; Owner: -
--

CREATE TABLE adopcion.roles (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL,
    CONSTRAINT chk_roles_nombre CHECK (((nombre)::text = ANY ((ARRAY['Administrador'::character varying, 'Encargado'::character varying, 'Usuario'::character varying, 'Invitado'::character varying])::text[])))
);


--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: adopcion; Owner: -
--

CREATE SEQUENCE adopcion.roles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: adopcion; Owner: -
--

ALTER SEQUENCE adopcion.roles_id_seq OWNED BY adopcion.roles.id;


--
-- Name: seguimiento_adopciones; Type: TABLE; Schema: adopcion; Owner: -
--

CREATE TABLE adopcion.seguimiento_adopciones (
    id integer NOT NULL,
    solicitud_id integer NOT NULL,
    fecha_reporte timestamp without time zone DEFAULT now() NOT NULL,
    estado_salud character varying(50) NOT NULL,
    observaciones_texto text,
    CONSTRAINT chk_seguimiento_salud CHECK (((estado_salud)::text = ANY ((ARRAY['Excelente'::character varying, 'Bueno'::character varying, 'Regular'::character varying, 'Malo'::character varying])::text[])))
);


--
-- Name: seguimiento_adopciones_id_seq; Type: SEQUENCE; Schema: adopcion; Owner: -
--

CREATE SEQUENCE adopcion.seguimiento_adopciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: seguimiento_adopciones_id_seq; Type: SEQUENCE OWNED BY; Schema: adopcion; Owner: -
--

ALTER SEQUENCE adopcion.seguimiento_adopciones_id_seq OWNED BY adopcion.seguimiento_adopciones.id;


--
-- Name: seleccion_productos; Type: TABLE; Schema: adopcion; Owner: -
--

CREATE TABLE adopcion.seleccion_productos (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    producto_id integer NOT NULL,
    tipo_lista character varying(20) NOT NULL,
    cantidad integer DEFAULT 1 NOT NULL,
    CONSTRAINT chk_seleccion_cantidad CHECK ((cantidad > 0)),
    CONSTRAINT chk_seleccion_tipo CHECK (((tipo_lista)::text = ANY ((ARRAY['CARRITO'::character varying, 'FAVORITO'::character varying])::text[])))
);


--
-- Name: seleccion_productos_id_seq; Type: SEQUENCE; Schema: adopcion; Owner: -
--

CREATE SEQUENCE adopcion.seleccion_productos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: seleccion_productos_id_seq; Type: SEQUENCE OWNED BY; Schema: adopcion; Owner: -
--

ALTER SEQUENCE adopcion.seleccion_productos_id_seq OWNED BY adopcion.seleccion_productos.id;


--
-- Name: solicitudes_adopcion; Type: TABLE; Schema: adopcion; Owner: -
--

CREATE TABLE adopcion.solicitudes_adopcion (
    id integer NOT NULL,
    usuario_id integer NOT NULL,
    mascota_id integer NOT NULL,
    estado character varying(50) DEFAULT 'En Revisión'::character varying NOT NULL,
    fecha_solicitud timestamp without time zone DEFAULT now() NOT NULL,
    nombre_contacto character varying(150),
    telefono character varying(30),
    tipo_vivienda character varying(50),
    motivo text,
    fecha_nacimiento date,
    email_contacto character varying(100),
    direccion character varying(255),
    vivienda_permite_mascotas boolean,
    tiene_patio boolean,
    tiene_cercas boolean,
    personas_hogar integer,
    tuvo_mascotas boolean,
    mascotas_vacunadas boolean,
    mascotas_esterilizadas boolean,
    horas_solo integer,
    responsable_viajes text,
    comentario_encargado text,
    fecha_respuesta timestamp without time zone,
    CONSTRAINT chk_solicitud_horas_solo CHECK (((horas_solo IS NULL) OR ((horas_solo >= 0) AND (horas_solo <= 24)))),
    CONSTRAINT chk_solicitud_personas_hogar CHECK (((personas_hogar IS NULL) OR ((personas_hogar >= 1) AND (personas_hogar <= 30)))),
    CONSTRAINT chk_solicitudes_estado CHECK (((estado)::text = ANY ((ARRAY['En Revisión'::character varying, 'Aprobada'::character varying, 'Rechazada'::character varying, 'Entregada'::character varying, 'En Seguimiento'::character varying, 'Cerrada'::character varying])::text[])))
);


--
-- Name: solicitudes_adopcion_id_seq; Type: SEQUENCE; Schema: adopcion; Owner: -
--

CREATE SEQUENCE adopcion.solicitudes_adopcion_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: solicitudes_adopcion_id_seq; Type: SEQUENCE OWNED BY; Schema: adopcion; Owner: -
--

ALTER SEQUENCE adopcion.solicitudes_adopcion_id_seq OWNED BY adopcion.solicitudes_adopcion.id;


--
-- Name: usuarios; Type: TABLE; Schema: adopcion; Owner: -
--

CREATE TABLE adopcion.usuarios (
    id integer NOT NULL,
    nombre_completo character varying(100) NOT NULL,
    email character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    rol_id integer NOT NULL,
    refugio_id integer,
    fecha_registro timestamp without time zone DEFAULT now() NOT NULL
);


--
-- Name: usuarios_id_seq; Type: SEQUENCE; Schema: adopcion; Owner: -
--

CREATE SEQUENCE adopcion.usuarios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: usuarios_id_seq; Type: SEQUENCE OWNED BY; Schema: adopcion; Owner: -
--

ALTER SEQUENCE adopcion.usuarios_id_seq OWNED BY adopcion.usuarios.id;


--
-- Name: auditoria id; Type: DEFAULT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.auditoria ALTER COLUMN id SET DEFAULT nextval('adopcion.auditoria_id_seq'::regclass);


--
-- Name: categorias_productos id; Type: DEFAULT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.categorias_productos ALTER COLUMN id SET DEFAULT nextval('adopcion.categorias_productos_id_seq'::regclass);


--
-- Name: detalles_orden id; Type: DEFAULT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.detalles_orden ALTER COLUMN id SET DEFAULT nextval('adopcion.detalles_orden_id_seq'::regclass);


--
-- Name: mascotas id; Type: DEFAULT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.mascotas ALTER COLUMN id SET DEFAULT nextval('adopcion.mascotas_id_seq'::regclass);


--
-- Name: ordenes_compra id; Type: DEFAULT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.ordenes_compra ALTER COLUMN id SET DEFAULT nextval('adopcion.ordenes_compra_id_seq'::regclass);


--
-- Name: productos id; Type: DEFAULT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.productos ALTER COLUMN id SET DEFAULT nextval('adopcion.productos_id_seq'::regclass);


--
-- Name: refugios id; Type: DEFAULT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.refugios ALTER COLUMN id SET DEFAULT nextval('adopcion.refugios_id_seq'::regclass);


--
-- Name: roles id; Type: DEFAULT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.roles ALTER COLUMN id SET DEFAULT nextval('adopcion.roles_id_seq'::regclass);


--
-- Name: seguimiento_adopciones id; Type: DEFAULT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.seguimiento_adopciones ALTER COLUMN id SET DEFAULT nextval('adopcion.seguimiento_adopciones_id_seq'::regclass);


--
-- Name: seleccion_productos id; Type: DEFAULT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.seleccion_productos ALTER COLUMN id SET DEFAULT nextval('adopcion.seleccion_productos_id_seq'::regclass);


--
-- Name: solicitudes_adopcion id; Type: DEFAULT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.solicitudes_adopcion ALTER COLUMN id SET DEFAULT nextval('adopcion.solicitudes_adopcion_id_seq'::regclass);


--
-- Name: usuarios id; Type: DEFAULT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.usuarios ALTER COLUMN id SET DEFAULT nextval('adopcion.usuarios_id_seq'::regclass);


--
-- Name: auditoria auditoria_pkey; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.auditoria
    ADD CONSTRAINT auditoria_pkey PRIMARY KEY (id);


--
-- Name: categorias_productos categorias_productos_nombre_key; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.categorias_productos
    ADD CONSTRAINT categorias_productos_nombre_key UNIQUE (nombre);


--
-- Name: categorias_productos categorias_productos_pkey; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.categorias_productos
    ADD CONSTRAINT categorias_productos_pkey PRIMARY KEY (id);


--
-- Name: detalles_orden detalles_orden_pkey; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.detalles_orden
    ADD CONSTRAINT detalles_orden_pkey PRIMARY KEY (id);


--
-- Name: mascotas mascotas_pkey; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.mascotas
    ADD CONSTRAINT mascotas_pkey PRIMARY KEY (id);


--
-- Name: ordenes_compra ordenes_compra_pkey; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.ordenes_compra
    ADD CONSTRAINT ordenes_compra_pkey PRIMARY KEY (id);


--
-- Name: productos productos_pkey; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.productos
    ADD CONSTRAINT productos_pkey PRIMARY KEY (id);


--
-- Name: refugios refugios_pkey; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.refugios
    ADD CONSTRAINT refugios_pkey PRIMARY KEY (id);


--
-- Name: roles roles_nombre_key; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.roles
    ADD CONSTRAINT roles_nombre_key UNIQUE (nombre);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: seguimiento_adopciones seguimiento_adopciones_pkey; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.seguimiento_adopciones
    ADD CONSTRAINT seguimiento_adopciones_pkey PRIMARY KEY (id);


--
-- Name: seleccion_productos seleccion_productos_pkey; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.seleccion_productos
    ADD CONSTRAINT seleccion_productos_pkey PRIMARY KEY (id);


--
-- Name: solicitudes_adopcion solicitudes_adopcion_pkey; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.solicitudes_adopcion
    ADD CONSTRAINT solicitudes_adopcion_pkey PRIMARY KEY (id);


--
-- Name: solicitudes_adopcion uq_solicitud_usuario_mascota; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.solicitudes_adopcion
    ADD CONSTRAINT uq_solicitud_usuario_mascota UNIQUE (usuario_id, mascota_id);


--
-- Name: usuarios usuarios_email_key; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.usuarios
    ADD CONSTRAINT usuarios_email_key UNIQUE (email);


--
-- Name: usuarios usuarios_pkey; Type: CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.usuarios
    ADD CONSTRAINT usuarios_pkey PRIMARY KEY (id);


--
-- Name: idx_auditoria_fecha; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_auditoria_fecha ON adopcion.auditoria USING btree (fecha_accion DESC);


--
-- Name: idx_auditoria_tabla; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_auditoria_tabla ON adopcion.auditoria USING btree (tabla_afectada);


--
-- Name: idx_detalles_orden; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_detalles_orden ON adopcion.detalles_orden USING btree (orden_id);


--
-- Name: idx_detalles_producto; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_detalles_producto ON adopcion.detalles_orden USING btree (producto_id);


--
-- Name: idx_mascotas_edad; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_mascotas_edad ON adopcion.mascotas USING btree (edad_meses);


--
-- Name: idx_mascotas_estado; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_mascotas_estado ON adopcion.mascotas USING btree (estado_adopcion);


--
-- Name: idx_mascotas_refugio; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_mascotas_refugio ON adopcion.mascotas USING btree (refugio_id);


--
-- Name: idx_ordenes_estado; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_ordenes_estado ON adopcion.ordenes_compra USING btree (estado_pedido);


--
-- Name: idx_ordenes_usuario; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_ordenes_usuario ON adopcion.ordenes_compra USING btree (usuario_id);


--
-- Name: idx_productos_categoria; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_productos_categoria ON adopcion.productos USING btree (categoria_id);


--
-- Name: idx_productos_nombre; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_productos_nombre ON adopcion.productos USING btree (nombre);


--
-- Name: idx_productos_precio; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_productos_precio ON adopcion.productos USING btree (precio);


--
-- Name: idx_seguimiento_solicitud; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_seguimiento_solicitud ON adopcion.seguimiento_adopciones USING btree (solicitud_id);


--
-- Name: idx_seleccion_producto; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_seleccion_producto ON adopcion.seleccion_productos USING btree (producto_id);


--
-- Name: idx_seleccion_usuario; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_seleccion_usuario ON adopcion.seleccion_productos USING btree (usuario_id);


--
-- Name: idx_solicitudes_estado; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_solicitudes_estado ON adopcion.solicitudes_adopcion USING btree (estado);


--
-- Name: idx_solicitudes_mascota; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_solicitudes_mascota ON adopcion.solicitudes_adopcion USING btree (mascota_id);


--
-- Name: idx_solicitudes_usuario; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_solicitudes_usuario ON adopcion.solicitudes_adopcion USING btree (usuario_id);


--
-- Name: idx_usuarios_refugio; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_usuarios_refugio ON adopcion.usuarios USING btree (refugio_id);


--
-- Name: idx_usuarios_rol; Type: INDEX; Schema: adopcion; Owner: -
--

CREATE INDEX idx_usuarios_rol ON adopcion.usuarios USING btree (rol_id);


--
-- Name: categorias_productos trg_auditoria_categorias; Type: TRIGGER; Schema: adopcion; Owner: -
--

CREATE TRIGGER trg_auditoria_categorias AFTER INSERT OR DELETE OR UPDATE ON adopcion.categorias_productos FOR EACH ROW EXECUTE FUNCTION adopcion.fn_auditar_cambios();


--
-- Name: detalles_orden trg_auditoria_detalles; Type: TRIGGER; Schema: adopcion; Owner: -
--

CREATE TRIGGER trg_auditoria_detalles AFTER INSERT OR DELETE OR UPDATE ON adopcion.detalles_orden FOR EACH ROW EXECUTE FUNCTION adopcion.fn_auditar_cambios();


--
-- Name: mascotas trg_auditoria_mascotas; Type: TRIGGER; Schema: adopcion; Owner: -
--

CREATE TRIGGER trg_auditoria_mascotas AFTER INSERT OR DELETE OR UPDATE ON adopcion.mascotas FOR EACH ROW EXECUTE FUNCTION adopcion.fn_auditar_cambios();


--
-- Name: ordenes_compra trg_auditoria_ordenes; Type: TRIGGER; Schema: adopcion; Owner: -
--

CREATE TRIGGER trg_auditoria_ordenes AFTER INSERT OR DELETE OR UPDATE ON adopcion.ordenes_compra FOR EACH ROW EXECUTE FUNCTION adopcion.fn_auditar_cambios();


--
-- Name: productos trg_auditoria_productos; Type: TRIGGER; Schema: adopcion; Owner: -
--

CREATE TRIGGER trg_auditoria_productos AFTER INSERT OR DELETE OR UPDATE ON adopcion.productos FOR EACH ROW EXECUTE FUNCTION adopcion.fn_auditar_cambios();


--
-- Name: refugios trg_auditoria_refugios; Type: TRIGGER; Schema: adopcion; Owner: -
--

CREATE TRIGGER trg_auditoria_refugios AFTER INSERT OR DELETE OR UPDATE ON adopcion.refugios FOR EACH ROW EXECUTE FUNCTION adopcion.fn_auditar_cambios();


--
-- Name: roles trg_auditoria_roles; Type: TRIGGER; Schema: adopcion; Owner: -
--

CREATE TRIGGER trg_auditoria_roles AFTER INSERT OR DELETE OR UPDATE ON adopcion.roles FOR EACH ROW EXECUTE FUNCTION adopcion.fn_auditar_cambios();


--
-- Name: seguimiento_adopciones trg_auditoria_seguimientos; Type: TRIGGER; Schema: adopcion; Owner: -
--

CREATE TRIGGER trg_auditoria_seguimientos AFTER INSERT OR DELETE OR UPDATE ON adopcion.seguimiento_adopciones FOR EACH ROW EXECUTE FUNCTION adopcion.fn_auditar_cambios();


--
-- Name: seleccion_productos trg_auditoria_seleccion; Type: TRIGGER; Schema: adopcion; Owner: -
--

CREATE TRIGGER trg_auditoria_seleccion AFTER INSERT OR DELETE OR UPDATE ON adopcion.seleccion_productos FOR EACH ROW EXECUTE FUNCTION adopcion.fn_auditar_cambios();


--
-- Name: solicitudes_adopcion trg_auditoria_solicitudes; Type: TRIGGER; Schema: adopcion; Owner: -
--

CREATE TRIGGER trg_auditoria_solicitudes AFTER INSERT OR DELETE OR UPDATE ON adopcion.solicitudes_adopcion FOR EACH ROW EXECUTE FUNCTION adopcion.fn_auditar_cambios();


--
-- Name: usuarios trg_auditoria_usuarios; Type: TRIGGER; Schema: adopcion; Owner: -
--

CREATE TRIGGER trg_auditoria_usuarios AFTER INSERT OR DELETE OR UPDATE ON adopcion.usuarios FOR EACH ROW EXECUTE FUNCTION adopcion.fn_auditar_cambios();


--
-- Name: detalles_orden fk_detalle_orden; Type: FK CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.detalles_orden
    ADD CONSTRAINT fk_detalle_orden FOREIGN KEY (orden_id) REFERENCES adopcion.ordenes_compra(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: detalles_orden fk_detalle_producto; Type: FK CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.detalles_orden
    ADD CONSTRAINT fk_detalle_producto FOREIGN KEY (producto_id) REFERENCES adopcion.productos(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: mascotas fk_mascotas_refugio; Type: FK CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.mascotas
    ADD CONSTRAINT fk_mascotas_refugio FOREIGN KEY (refugio_id) REFERENCES adopcion.refugios(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: ordenes_compra fk_orden_usuario; Type: FK CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.ordenes_compra
    ADD CONSTRAINT fk_orden_usuario FOREIGN KEY (usuario_id) REFERENCES adopcion.usuarios(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: productos fk_productos_categoria; Type: FK CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.productos
    ADD CONSTRAINT fk_productos_categoria FOREIGN KEY (categoria_id) REFERENCES adopcion.categorias_productos(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: seguimiento_adopciones fk_seguimiento_solicitud; Type: FK CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.seguimiento_adopciones
    ADD CONSTRAINT fk_seguimiento_solicitud FOREIGN KEY (solicitud_id) REFERENCES adopcion.solicitudes_adopcion(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: seleccion_productos fk_seleccion_producto; Type: FK CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.seleccion_productos
    ADD CONSTRAINT fk_seleccion_producto FOREIGN KEY (producto_id) REFERENCES adopcion.productos(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: seleccion_productos fk_seleccion_usuario; Type: FK CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.seleccion_productos
    ADD CONSTRAINT fk_seleccion_usuario FOREIGN KEY (usuario_id) REFERENCES adopcion.usuarios(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: solicitudes_adopcion fk_solicitudes_mascota; Type: FK CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.solicitudes_adopcion
    ADD CONSTRAINT fk_solicitudes_mascota FOREIGN KEY (mascota_id) REFERENCES adopcion.mascotas(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: solicitudes_adopcion fk_solicitudes_usuario; Type: FK CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.solicitudes_adopcion
    ADD CONSTRAINT fk_solicitudes_usuario FOREIGN KEY (usuario_id) REFERENCES adopcion.usuarios(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: usuarios fk_usuarios_refugio; Type: FK CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.usuarios
    ADD CONSTRAINT fk_usuarios_refugio FOREIGN KEY (refugio_id) REFERENCES adopcion.refugios(id) ON UPDATE CASCADE ON DELETE SET NULL;


--
-- Name: usuarios fk_usuarios_rol; Type: FK CONSTRAINT; Schema: adopcion; Owner: -
--

ALTER TABLE ONLY adopcion.usuarios
    ADD CONSTRAINT fk_usuarios_rol FOREIGN KEY (rol_id) REFERENCES adopcion.roles(id) ON UPDATE CASCADE ON DELETE RESTRICT;


--
-- Name: SCHEMA adopcion; Type: ACL; Schema: -; Owner: -
--

GRANT ALL ON SCHEMA adopcion TO usuario_adopcion;


--
-- Name: TABLE auditoria; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON TABLE adopcion.auditoria TO usuario_adopcion;


--
-- Name: SEQUENCE auditoria_id_seq; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON SEQUENCE adopcion.auditoria_id_seq TO usuario_adopcion;


--
-- Name: TABLE categorias_productos; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON TABLE adopcion.categorias_productos TO usuario_adopcion;


--
-- Name: SEQUENCE categorias_productos_id_seq; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON SEQUENCE adopcion.categorias_productos_id_seq TO usuario_adopcion;


--
-- Name: TABLE detalles_orden; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON TABLE adopcion.detalles_orden TO usuario_adopcion;


--
-- Name: SEQUENCE detalles_orden_id_seq; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON SEQUENCE adopcion.detalles_orden_id_seq TO usuario_adopcion;


--
-- Name: TABLE mascotas; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON TABLE adopcion.mascotas TO usuario_adopcion;


--
-- Name: SEQUENCE mascotas_id_seq; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON SEQUENCE adopcion.mascotas_id_seq TO usuario_adopcion;


--
-- Name: TABLE ordenes_compra; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON TABLE adopcion.ordenes_compra TO usuario_adopcion;


--
-- Name: SEQUENCE ordenes_compra_id_seq; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON SEQUENCE adopcion.ordenes_compra_id_seq TO usuario_adopcion;


--
-- Name: TABLE productos; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON TABLE adopcion.productos TO usuario_adopcion;


--
-- Name: SEQUENCE productos_id_seq; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON SEQUENCE adopcion.productos_id_seq TO usuario_adopcion;


--
-- Name: TABLE refugios; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON TABLE adopcion.refugios TO usuario_adopcion;


--
-- Name: SEQUENCE refugios_id_seq; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON SEQUENCE adopcion.refugios_id_seq TO usuario_adopcion;


--
-- Name: TABLE roles; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON TABLE adopcion.roles TO usuario_adopcion;


--
-- Name: SEQUENCE roles_id_seq; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON SEQUENCE adopcion.roles_id_seq TO usuario_adopcion;


--
-- Name: TABLE seguimiento_adopciones; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON TABLE adopcion.seguimiento_adopciones TO usuario_adopcion;


--
-- Name: SEQUENCE seguimiento_adopciones_id_seq; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON SEQUENCE adopcion.seguimiento_adopciones_id_seq TO usuario_adopcion;


--
-- Name: TABLE seleccion_productos; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON TABLE adopcion.seleccion_productos TO usuario_adopcion;


--
-- Name: SEQUENCE seleccion_productos_id_seq; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON SEQUENCE adopcion.seleccion_productos_id_seq TO usuario_adopcion;


--
-- Name: TABLE solicitudes_adopcion; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON TABLE adopcion.solicitudes_adopcion TO usuario_adopcion;


--
-- Name: SEQUENCE solicitudes_adopcion_id_seq; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON SEQUENCE adopcion.solicitudes_adopcion_id_seq TO usuario_adopcion;


--
-- Name: TABLE usuarios; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON TABLE adopcion.usuarios TO usuario_adopcion;


--
-- Name: SEQUENCE usuarios_id_seq; Type: ACL; Schema: adopcion; Owner: -
--

GRANT ALL ON SEQUENCE adopcion.usuarios_id_seq TO usuario_adopcion;


--
-- PostgreSQL database dump complete
--

\unrestrict XNN4bkMgoivfHdD9t3XICiFxF36zN12c6QbKoNgdFhgZ8SQfcIPprss1W4Q8syg

