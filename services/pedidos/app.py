import os

import requests
from flask import Flask, jsonify, request

from models import Pedido, PedidoItem, build_database_uri, db

INVENTARIO_URL = os.environ.get("INVENTARIO_URL", "http://inventario:5000")


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
    @app.get("/api/pedidos/health")
    def health():
        return jsonify({"status": "ok", "service": "pedidos"})

    @app.get("/api/pedidos")
    def listar_pedidos():
        pedidos = Pedido.query.order_by(Pedido.creado_en.desc()).all()
        return jsonify([p.to_dict(incluir_items=False) for p in pedidos])

    @app.get("/api/pedidos/<int:pedido_id>")
    def obtener_pedido(pedido_id):
        pedido = db.session.get(Pedido, pedido_id)
        if pedido is None:
            return jsonify({"error": "pedido no encontrado"}), 404
        return jsonify(pedido.to_dict())

    @app.post("/api/pedidos")
    def crear_pedido():
        """
        Body esperado:
        {"carne": "1234567", "items": [{"sku": "ABC123", "cantidad": 2}]}

        Regla de negocio: se delega a inventario la validación y el
        descuento atómico de stock (todo o nada). Este servicio solo
        interpreta la respuesta y persiste el resultado.
        """
        data = request.get_json(force=True) or {}
        carne = data.get("carne")
        items = data.get("items", [])

        if not carne or not items:
            return jsonify({"error": "faltan campos: carne, items"}), 400

        try:
            respuesta = requests.post(
                f"{INVENTARIO_URL}/api/inventario/reservar",
                json={"items": items},
                timeout=5,
            )
        except requests.RequestException as exc:
            return jsonify({"error": f"inventario no disponible: {exc}"}), 502

        if respuesta.status_code == 409:
            # Rechazado: no se movió stock. Se guarda para trazabilidad,
            # pero sin precios (no fueron confirmados).
            cuerpo = respuesta.json()
            pedido = Pedido(carne=carne, estado="rechazado", total_q=0)
            for item in items:
                pedido.items.append(
                    PedidoItem(
                        sku=item["sku"],
                        cantidad=item["cantidad"],
                        precio_unitario_q=0,
                    )
                )
            db.session.add(pedido)
            db.session.commit()
            return (
                jsonify(
                    {
                        "pedido": pedido.to_dict(),
                        "motivo": cuerpo.get("insuficientes"),
                    }
                ),
                409,
            )

        if respuesta.status_code != 200:
            return jsonify({"error": "fallo al reservar stock"}), 502

        cuerpo = respuesta.json()
        detalle = cuerpo["items"]

        pedido = Pedido(carne=carne, estado="confirmado", total_q=0)
        total = 0
        for item in detalle:
            subtotal = item["precio_unitario_q"] * item["cantidad"]
            total += subtotal
            pedido.items.append(
                PedidoItem(
                    sku=item["sku"],
                    nombre_producto=item["nombre"],
                    cantidad=item["cantidad"],
                    precio_unitario_q=item["precio_unitario_q"],
                )
            )
        pedido.total_q = total

        db.session.add(pedido)
        db.session.commit()
        return jsonify(pedido.to_dict()), 201

    # ---------- Datos de solo lectura que usa reportes/dashboard ----------

    @app.get("/api/pedidos/resumen-hoy")
    def resumen_pedidos_hoy():
        from datetime import datetime, timedelta

        inicio_dia = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        pedidos_hoy = Pedido.query.filter(Pedido.creado_en >= inicio_dia).all()
        confirmados = [p for p in pedidos_hoy if p.estado == "confirmado"]

        return jsonify(
            {
                "pedidos_hoy": len(pedidos_hoy),
                "confirmados_hoy": len(confirmados),
                "rechazados_hoy": len(pedidos_hoy) - len(confirmados),
            }
        )


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
