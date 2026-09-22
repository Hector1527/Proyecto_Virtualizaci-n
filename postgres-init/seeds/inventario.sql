INSERT INTO productos (sku, nombre, categoria, precio_q, stock)
VALUES
    ('A1', 'Mouse', 'Perifericos', 50.00, 10),
    ('B2', 'Teclado', 'Perifericos', 100.00, 3),
    ('C3', 'Monitor', 'Pantallas', 1200.00, 8),
    ('D4', 'Cable HDMI', 'Cables', 75.00, 0)
ON CONFLICT (sku) DO NOTHING;
