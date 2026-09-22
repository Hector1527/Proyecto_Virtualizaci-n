CREATE TABLE IF NOT EXISTS productos (
    id BIGSERIAL PRIMARY KEY,
    sku TEXT NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    categoria TEXT NOT NULL,
    precio_q NUMERIC(10, 2) NOT NULL CHECK (precio_q >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_productos_stock ON productos (stock);
CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos (categoria);

CREATE OR REPLACE FUNCTION actualizar_productos_actualizado_en()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.actualizado_en = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_productos_actualizado_en ON productos;

CREATE TRIGGER trg_productos_actualizado_en
BEFORE UPDATE ON productos
FOR EACH ROW
EXECUTE FUNCTION actualizar_productos_actualizado_en();
