CREATE TABLE IF NOT EXISTS clientes (
    id BIGSERIAL PRIMARY KEY,
    carne VARCHAR(20) NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    contacto TEXT,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT clientes_carne_no_vacio CHECK (BTRIM(carne) <> ''),
    CONSTRAINT clientes_nombre_no_vacio CHECK (BTRIM(nombre) <> '')
);
