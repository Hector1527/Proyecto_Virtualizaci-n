import os

from flask import Flask, jsonify, request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import Producto, build_database_uri, db

UMBRAL_STOCK_BAJO = int(os.environ.get("UMBRAL_STOCK_BAJO", "10"))


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = build_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


def register_routes(app: Flask):
    @app.get("/api/inventario/health")
    def health():
        return jsonify({"status": "ok", "service": "inventario"})

    # ---------- CRUD de productos ----------

    @app.get("/api/inventario/productos")
    def listar_productos():
        productos = Producto.query.order_by(Producto.nombre).all()
        return jsonify([p.to_dict() for p in productos])

    @app.get("/api/inventario/productos/<int:producto_id>")
    def obtener_producto(producto_id):
        producto = db.session.get(Producto, producto_id)
        if producto is None:
            return jsonify({"error": "producto no encontrado"}), 404
        return jsonify(producto.to_dict())

    @app.post("/api/inventario/productos")
    def crear_producto():
        data = request.get_json(force=True) or {}
        campos_requeridos = {"sku", "nombre", "categoria", "precio_q", "stock"}
        faltantes = campos_requeridos - data.keys()
        if faltantes:
            return jsonify({"error": f"faltan campos: {sorted(faltantes)}"}), 400

        producto = Producto(
            sku=data["sku"],
            nombre=data["nombre"],
            categoria=data["categoria"],
            precio_q=data["precio_q"],
            stock=data["stock"],
        )
        db.session.add(producto)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "el SKU ya existe"}), 409

        return jsonify(producto.to_dict()), 201

    @app.put("/api/inventario/productos/<int:producto_id>")
    def editar_producto(producto_id):
        producto = db.session.get(Producto, producto_id)
        if producto is None:
            return jsonify({"error": "producto no encontrado"}), 404

        data = request.get_json(force=True) or {}
        for campo in ("nombre", "categoria", "precio_q", "stock"):
            if campo in data:
                setattr(producto, campo, data[campo])

        db.session.commit()
        return jsonify(producto.to_dict())

    @app.delete("/api/inventario/productos/<int:producto_id>")
    def eliminar_producto(producto_id):
        producto = db.session.get(Producto, producto_id)
        if producto is None:
            return jsonify({"error": "producto no encontrado"}), 404

        db.session.delete(producto)
        db.session.commit()
        return "", 204

    # ---------- Regla de negocio: reserva atómica de stock ----------
    # Este es el endpoint que consume el servicio "pedidos".
    # Garantiza todo-o-nada usando una sola transacción de Postgres,
    # porque todas las filas involucradas viven en esta misma base.

    @app.post("/api/inventario/reservar")
    def reservar_stock():
        """
        Body esperado:
        {"items": [{"sku": "ABC123", "cantidad": 2}, ...]}

        Respuesta 200 (éxito): stock descontado, detalle con precio
        unitario de cada producto para que "pedidos" arme su registro.

        Respuesta 409 (rechazo): NO se modifica nada, se listan los
        SKUs con stock insuficiente.
        """
        data = request.get_json(force=True) or {}
        items = data.get("items", [])
        if not items:
            return jsonify({"error": "items vacío"}), 400

        skus = [item["sku"] for item in items]

        # SELECT ... FOR UPDATE: bloquea las filas involucradas hasta el
        # commit/rollback, para que dos pedidos concurrentes sobre el
        # mismo SKU no lean el mismo stock "antes" de que el otro decida.
        stmt = (
            select(Producto)
            .where(Producto.sku.in_(skus))
            .with_for_update()
        )
        productos_por_sku = {p.sku: p for p in db.session.execute(stmt).scalars()}

        insuficientes = []
        for item in items:
            producto = productos_por_sku.get(item["sku"])
            if producto is None:
                insuficientes.append({"sku": item["sku"], "motivo": "no existe"})
            elif producto.stock < item["cantidad"]:
                insuficientes.append(
                    {
                        "sku": item["sku"],
                        "motivo": "stock insuficiente",
                        "disponible": producto.stock,
                        "solicitado": item["cantidad"],
                    }
                )

        if insuficientes:
            db.session.rollback()  # libera los locks, no se toca nada
            return jsonify({"confirmado": False, "insuficientes": insuficientes}), 409

        detalle = []
        for item in items:
            producto = productos_por_sku[item["sku"]]
            producto.stock -= item["cantidad"]
            detalle.append(
                {
                    "sku": producto.sku,
                    "nombre": producto.nombre,
                    "cantidad": item["cantidad"],
                    "precio_unitario_q": float(producto.precio_q),
                }
            )

        db.session.commit()
        return jsonify({"confirmado": True, "items": detalle}), 200

    @app.post("/api/inventario/liberar")
    def liberar_stock():
        """Compensación: repone stock si un pedido confirmado se cancela
        después. Útil para no dejar el inventario inconsistente."""
        data = request.get_json(force=True) or {}
        items = data.get("items", [])

        skus = [item["sku"] for item in items]
        stmt = select(Producto).where(Producto.sku.in_(skus)).with_for_update()
        productos_por_sku = {p.sku: p for p in db.session.execute(stmt).scalars()}

        for item in items:
            producto = productos_por_sku.get(item["sku"])
            if producto is not None:
                producto.stock += item["cantidad"]

        db.session.commit()
        return jsonify({"liberado": True})

    # ---------- Datos de solo lectura que usa reportes/dashboard ----------

    @app.get("/api/inventario/resumen")
    def resumen_inventario():
        productos = Producto.query.all()
        total_productos = len(productos)
        valor_total_q = sum(float(p.precio_q) * p.stock for p in productos)
        stock_bajo = [
            p.to_dict() for p in productos if p.stock < UMBRAL_STOCK_BAJO
        ]
        return jsonify(
            {
                "total_productos": total_productos,
                "valor_total_inventario_q": round(valor_total_q, 2),
                "umbral_stock_bajo": UMBRAL_STOCK_BAJO,
                "productos_stock_bajo": stock_bajo,
            }
        )


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
