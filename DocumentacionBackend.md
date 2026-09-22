Backend de dominio — contrato de endpoints y base de datos (estado actual)

Van los 5 microservicios con sus rutas, formatos de entrada/salida, y la estructura de base de datos con la que ya está construida y probada la lógica. Esto es lo que hay corriendo ahora mismo.

Inventario (/api/inventario)
Método	Ruta	Body	Respuesta
GET	/api/inventario/health	—	{"status":"ok","service":"inventario"}
GET	/api/inventario/productos	—	[{"id":1,"sku":"A1","nombre":"Mouse","categoria":"Perifericos","precio_q":50.0,"stock":10}]
GET	/api/inventario/productos/<id>	—	producto individual, o 404
POST	/api/inventario/productos	{"sku":"A1","nombre":"Mouse","categoria":"Perifericos","precio_q":50,"stock":10}	201 con el producto creado, 400 si faltan campos, 409 si el SKU ya existe
PUT	/api/inventario/productos/<id>	cualquier subconjunto de {"nombre","categoria","precio_q","stock"}	producto actualizado, o 404
DELETE	/api/inventario/productos/<id>	—	204, o 404
POST	/api/inventario/reservar	{"items":[{"sku":"A1","cantidad":2}]}	200 con {"confirmado":true,"items":[{"sku","nombre","cantidad","precio_unitario_q"}]}; 409 con {"confirmado":false,"insuficientes":[{"sku","motivo","disponible","solicitado"}]}
POST	/api/inventario/liberar	{"items":[{"sku":"A1","cantidad":2}]}	{"liberado":true} (repone stock, para cancelaciones)
GET	/api/inventario/resumen	—	{"total_productos","valor_total_inventario_q","umbral_stock_bajo","productos_stock_bajo":[...]}
Clientes (/api/clientes)
Método	Ruta	Body	Respuesta
GET	/api/clientes/health	—	{"status":"ok","service":"clientes"}
GET	/api/clientes	—	[{"id","carne","nombre","contacto"}]
GET	/api/clientes/<id>	—	cliente individual, o 404
POST	/api/clientes	{"carne":"1234567","nombre":"...","contacto":"..."}	201, 400 si faltan carne/nombre, 409 si el carné ya existe
PUT	/api/clientes/<id>	subconjunto de {"nombre","contacto"}	cliente actualizado, o 404
DELETE	/api/clientes/<id>	—	204, o 404
Pedidos (/api/pedidos)
Método	Ruta	Body	Respuesta
GET	/api/pedidos/health	—	{"status":"ok","service":"pedidos"}
GET	/api/pedidos	—	lista de pedidos sin detalle de items: [{"id","carne","estado","total_q","creado_en"}]
GET	/api/pedidos/<id>	—	pedido completo con items:[{"sku","nombre_producto","cantidad","precio_unitario_q","subtotal_q"}]
POST	/api/pedidos	{"carne":"1234567","items":[{"sku":"A1","cantidad":2}]}	201 pedido confirmado; 409 pedido rechazado (con motivo); 502 si inventario no responde
GET	/api/pedidos/resumen-hoy	—	{"pedidos_hoy","confirmados_hoy","rechazados_hoy"}

estado solo toma dos valores: "confirmado" o "rechazado". El campo carne es el carné del integrante que generó el pedido y siempre queda persistido.

Reportes (/api/reportes)
Método	Ruta	Respuesta
GET	/api/reportes/health	{"status":"ok","service":"reportes"}
GET	/api/reportes/dashboard	{"total_productos","valor_total_inventario_q","pedidos_hoy","confirmados_hoy","rechazados_hoy","alerta_stock_bajo":[...]}
Catálogo (/api/catalogo)
Método	Ruta	Respuesta
GET	/api/catalogo/health	{"status":"ok","service":"catalogo"}
GET	/api/catalogo/productos	[{"sku","nombre","categoria","precio_q","disponible":true/false}] — vista pública de solo lectura sobre inventario, sin stock exacto
Base de datos (un solo motor Postgres, una base y un usuario por servicio)
Servicio	Base	Usuario	Tabla(s)
inventario	inventario_db	inventario_user	productos (id, sku UNIQUE, nombre, categoria, precio_q NUMERIC(10,2), stock INT, creado_en, actualizado_en)
clientes	clientes_db	clientes_user	clientes (id, carne UNIQUE, nombre, contacto, creado_en)
pedidos	pedidos_db	pedidos_user	pedidos (id, carne, estado, total_q, creado_en) + pedido_items (id, pedido_id FK, sku, nombre_producto, cantidad, precio_unitario_q)

reportes y catalogo no tienen base propia: consultan en tiempo real a inventario y pedidos vía HTTP.

Los nombres de base/usuario/contraseña se pasan por variables de entorno (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD), documentadas en .env.example. El script postgres-init/init-databases.sh crea las tres bases y usuarios automáticamente al levantar el contenedor de Postgres.

La regla de negocio de stock (validación y descuento todo-o-nada) vive dentro de inventario, con SELECT ... FOR UPDATE en una sola transacción — pedidos solo llama a POST /api/inventario/reservar una vez y persiste el resultado.