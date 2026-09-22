# Proyecto de Virtualización - El Quetzal

Aplicación web para gestionar inventario y pedidos de Distribuidora El Quetzal sobre una infraestructura virtualizada.

Esta rama (`datos/jeam256`) integra el Backend de dominio de Héctor con la capa de Datos de PostgreSQL. La rama `main` original se mantiene sin modificaciones.

## Arquitectura actual

```text
Cliente / navegador
        |
        v
  Gateway Nginx + Vue       (integración de frontend y gateway)
        |
        v
  Microservicios Flask
  ├── inventario  ──> inventario_db
  ├── clientes    ──> clientes_db
  ├── pedidos     ──> pedidos_db
  ├── reportes    ──> consulta inventario y pedidos por HTTP
  └── catalogo    ──> consulta inventario por HTTP
        |
        v
  Un motor PostgreSQL con bases independientes por servicio
```

El Backend de esta rama se ejecuta con `docker-compose.dev.yml`. El gateway y el frontend tienen ramas separadas en el repositorio y se integran posteriormente.

## Qué se integró

### Backend existente

Se conserva el trabajo de Héctor:

- Microservicios Flask de inventario, clientes, pedidos, reportes y catálogo.
- CRUD de productos y clientes.
- Creación y consulta de pedidos.
- Validación de stock.
- Descuento atómico mediante `SELECT ... FOR UPDATE`.
- Dashboard agregado mediante llamadas HTTP.

El contrato completo de rutas y JSON está en [DocumentacionBackend.md](DocumentacionBackend.md).

### Capa de Datos añadida

Se reemplazó el script inicial de PostgreSQL por una inicialización completa en `postgres-init/`:

```text
postgres-init/
├── init-databases.sh
├── schema/
│   ├── inventario.sql
│   ├── clientes.sql
│   └── pedidos.sql
└── seeds/
    ├── inventario.sql
    └── clientes.sql
```

El bootstrap crea:

| Servicio | Base | Usuario | Tablas |
|---|---|---|---|
| Inventario | `inventario_db` | `inventario_user` | `productos` |
| Clientes | `clientes_db` | `clientes_user` | `clientes` |
| Pedidos | `pedidos_db` | `pedidos_user` | `pedidos`, `pedido_items` |

`catalogo` y `reportes` no tienen base propia porque consumen los endpoints de otros servicios.

## Cómo ejecutar localmente

### Requisitos

- Docker Engine.
- Docker Compose.
- Git.

### 1. Crear las variables locales

En PowerShell:

```powershell
Copy-Item .env.example .env
```

Editar `.env` y cambiar las contraseñas de ejemplo. El archivo `.env` está ignorado por Git y no debe subirse.

Las variables más importantes son:

```text
POSTGRES_ADMIN_USER
POSTGRES_ADMIN_PASSWORD
INVENTARIO_DB_NAME
INVENTARIO_DB_USER
INVENTARIO_DB_PASSWORD
CLIENTES_DB_NAME
CLIENTES_DB_USER
CLIENTES_DB_PASSWORD
PEDIDOS_DB_NAME
PEDIDOS_DB_USER
PEDIDOS_DB_PASSWORD
UMBRAL_STOCK_BAJO
```

El valor actual de `UMBRAL_STOCK_BAJO` es `10`, porque es el valor que utiliza el Backend de inventario.

### 2. Levantar el Backend

```powershell
docker compose --env-file .env -f docker-compose.dev.yml up --build -d
```

Servicios publicados localmente:

| Servicio | URL base |
|---|---|
| PostgreSQL | `localhost:5432` |
| Inventario | `http://localhost:5001` |
| Clientes | `http://localhost:5002` |
| Pedidos | `http://localhost:5003` |
| Reportes | `http://localhost:5004` |
| Catálogo | `http://localhost:5005` |

Para revisar el estado:

```powershell
docker compose --env-file .env -f docker-compose.dev.yml ps
docker compose --env-file .env -f docker-compose.dev.yml logs -f postgres
```

El script de PostgreSQL se ejecuta automáticamente únicamente cuando el volumen `postgres_data` está vacío. Si se modifican las tablas y se necesita recrear la base desde cero, se puede usar:

```powershell
docker compose --env-file .env -f docker-compose.dev.yml down -v
docker compose --env-file .env -f docker-compose.dev.yml up --build -d
```

`down -v` elimina los datos locales de PostgreSQL; usarlo solo cuando se quiera reiniciar la base.

## Pruebas rápidas

### Salud de los servicios

```powershell
Invoke-RestMethod http://localhost:5001/api/inventario/health
Invoke-RestMethod http://localhost:5002/api/clientes/health
Invoke-RestMethod http://localhost:5003/api/pedidos/health
Invoke-RestMethod http://localhost:5004/api/reportes/health
Invoke-RestMethod http://localhost:5005/api/catalogo/health
```

### Inventario

```powershell
Invoke-RestMethod http://localhost:5001/api/inventario/productos
Invoke-RestMethod http://localhost:5001/api/inventario/resumen
```

### Pedido válido

```powershell
$body = @{
  carne = "1234567"
  items = @(
    @{ sku = "A1"; cantidad = 2 }
  )
} | ConvertTo-Json -Depth 4

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:5003/api/pedidos `
  -ContentType "application/json" `
  -Body $body
```

El pedido debe quedar `confirmado` y el stock del producto `A1` debe disminuir.

### Pedido rechazado

Probar con una cantidad mayor al stock disponible, por ejemplo:

```powershell
$body = @{
  carne = "1234567"
  items = @(
    @{ sku = "D4"; cantidad = 1 }
  )
} | ConvertTo-Json -Depth 4

Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:5003/api/pedidos `
  -ContentType "application/json" `
  -Body $body
```

Debe responder con estado HTTP `409` y no modificar el stock.

### Persistencia

```powershell
docker compose --env-file .env -f docker-compose.dev.yml down
docker compose --env-file .env -f docker-compose.dev.yml up -d
Invoke-RestMethod http://localhost:5001/api/inventario/productos
```

Los productos y pedidos deben conservarse porque PostgreSQL utiliza el volumen nombrado `postgres_data`.

## Decisiones de datos

- Inventario es dueño de la tabla `productos` y de la transacción de reserva de stock.
- Pedidos no accede directamente a `inventario_db`; llama a `/api/inventario/reservar`.
- `pedido_items` guarda una copia del SKU, nombre y precio del producto en el momento del pedido.
- No existe una llave foránea entre `pedidos.carne` y `clientes.carne` porque pertenecen a bases distintas.
- Los carnés incluidos en `postgres-init/seeds/clientes.sql` son de demostración y deben reemplazarse por los reales del grupo.
- El endpoint `/api/inventario/liberar` existe para compensar una reserva si un pedido se cancela posteriormente.

## Pendientes antes de la entrega final

1. Reemplazar los carnés de prueba por los carnés reales.
2. Confirmar con el equipo si `pedidos` debe validar el carné mediante el servicio `clientes`.
3. Definir con Orquestación el Compose final que incluya gateway, frontend, red interna y VM.
4. Verificar la compensación de `/api/inventario/liberar` si falla la persistencia posterior a una reserva.
5. Probar el flujo completo y capturar las evidencias exigidas: hostname de la VM, reloj, carnés y URL de Docker Hub.

## Rama de trabajo

Los cambios de esta integración están en:

```text
datos/jeam256
```

La rama `main` de Héctor no se modifica directamente. La integración debe revisarse mediante Pull Request.
