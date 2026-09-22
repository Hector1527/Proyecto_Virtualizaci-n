CREATE TABLE IF NOT EXISTS pedidos (
    id BIGSERIAL PRIMARY KEY,
    carne VARCHAR(20) NOT NULL,
    estado TEXT NOT NULL CHECK (estado IN ('confirmado', 'rechazado')),
    total_q NUMERIC(10, 2) NOT NULL DEFAULT 0 CHECK (total_q >= 0),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pedidos_carne_no_vacio CHECK (BTRIM(carne) <> '')
);

CREATE TABLE IF NOT EXISTS pedido_items (
    id BIGSERIAL PRIMARY KEY,
    pedido_id BIGINT NOT NULL REFERENCES pedidos (id) ON DELETE CASCADE,
    sku TEXT NOT NULL,
    nombre_producto TEXT,
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario_q NUMERIC(10, 2) NOT NULL CHECK (precio_unitario_q >= 0)
);

CREATE INDEX IF NOT EXISTS idx_pedidos_creado_en ON pedidos (creado_en);
CREATE INDEX IF NOT EXISTS idx_pedidos_carne ON pedidos (carne);
CREATE INDEX IF NOT EXISTS idx_pedido_items_pedido_id ON pedido_items (pedido_id);
