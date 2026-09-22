-- Valores de demostración. Reemplazar por los carnés reales del grupo antes de la entrega.
INSERT INTO clientes (carne, nombre, contacto)
VALUES
    ('1234567', 'Integrante de prueba 1', 'prueba1@elquetzal.local'),
    ('7654321', 'Integrante de prueba 2', 'prueba2@elquetzal.local')
ON CONFLICT (carne) DO NOTHING;
