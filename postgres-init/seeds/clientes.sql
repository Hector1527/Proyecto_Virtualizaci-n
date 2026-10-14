-- Grupo Glitch Tec: integrantes reales, trazables desde GET /api/clientes.
INSERT INTO clientes (carne, nombre, contacto)
VALUES
    ('1072123', 'Mario Arévalo', NULL),
    ('1185023', 'Jonatán Chávez', NULL),
    ('1207022', 'Javier Ruano', NULL),
    ('1184523', 'Javier Aldana', NULL),
    ('1304223', 'Hector Pérez', NULL),
    ('1143323', 'José Rosales', NULL)
ON CONFLICT (carne) DO UPDATE SET nombre = EXCLUDED.nombre;
