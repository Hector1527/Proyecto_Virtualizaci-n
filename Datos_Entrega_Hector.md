# Entrega de Datos para Backend

Esta entrega implementa el contrato definido en `DocumentacionBackend.md`.

## Bases y usuarios

| Servicio | Base | Usuario | Tablas |
|---|---|---|---|
| inventario | `inventario_db` | `inventario_user` | `productos` |
| clientes | `clientes_db` | `clientes_user` | `clientes` |
| pedidos | `pedidos_db` | `pedidos_user` | `pedidos`, `pedido_items` |

`catalogo` y `reportes` no tienen base propia; consumen los endpoints de inventario y pedidos por HTTP.

## Archivos entregados

- `postgres-init/init-databases.sh`: crea roles, bases, esquemas y seeds.
- `postgres-init/schema/inventario.sql`: tabla `productos`.
- `postgres-init/schema/clientes.sql`: tabla `clientes`.
- `postgres-init/schema/pedidos.sql`: tablas `pedidos` y `pedido_items`.
- `postgres-init/seeds/inventario.sql`: productos de prueba.
- `postgres-init/seeds/clientes.sql`: carnés de demostración; deben sustituirse por los reales.
- `.env.example`: nombres de bases, usuarios, contraseñas de ejemplo y configuración común.

## Integración con Backend

Cada servicio Flask debe recibir las variables genéricas siguientes con valores propios:

```text
DB_HOST=postgres
DB_PORT=5432
DB_NAME=...
DB_USER=...
DB_PASSWORD=...
```

El servicio `inventario` es dueño de `productos` y realiza la reserva con `SELECT ... FOR UPDATE` dentro de una transacción. El servicio `pedidos` no debe conectarse directamente a `inventario_db`; debe usar `/api/inventario/reservar` y persistir el resultado en `pedidos_db`.

No existe una llave foránea entre `pedidos.carne` y `clientes.carne` porque están en bases separadas. Deben confirmar si Backend validará el carné llamando al servicio `clientes` antes de crear un pedido.

`pedido_items` conserva `sku`, `nombre_producto`, `cantidad` y `precio_unitario_q` como una fotografía del pedido. El subtotal puede calcularse en la respuesta y no se almacena como columna independiente.

## Decisiones pendientes

1. Sustituir los carnés de demostración por los carnés reales del grupo.
2. Confirmar que `UMBRAL_STOCK_BAJO=10` coincide con el Backend.
3. Confirmar la compensación con `/api/inventario/liberar` si la reserva fue exitosa pero falla la persistencia del pedido.
4. Confirmar con Orquestación que el volumen de PostgreSQL se monte junto con `postgres-init/` y que el script se ejecute únicamente con un volumen nuevo.

Compose debe montar la carpeta de inicialización en el contenedor de PostgreSQL:

```yaml
volumes:
  - ./postgres-init:/docker-entrypoint-initdb.d:ro
```

El volumen nombrado de datos de PostgreSQL debe conservarse aparte. Los scripts de inicialización solo se ejecutan automáticamente cuando ese volumen está vacío.

## Pruebas de aceptación

- PostgreSQL crea las tres bases y sus usuarios sin errores.
- El Backend puede listar, crear, editar y eliminar productos.
- Un pedido válido reduce stock.
- Un pedido con stock insuficiente devuelve `409` y no cambia el stock.
- Los carnés aparecen en clientes y pedidos.
- `docker compose down` seguido de `docker compose up -d` conserva los datos.
