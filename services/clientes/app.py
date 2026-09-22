from flask import Flask, jsonify, request
from sqlalchemy.exc import IntegrityError

from models import Cliente, build_database_uri, db


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
    @app.get("/api/clientes/health")
    def health():
        return jsonify({"status": "ok", "service": "clientes"})

    @app.get("/api/clientes")
    def listar_clientes():
        clientes = Cliente.query.order_by(Cliente.nombre).all()
        return jsonify([c.to_dict() for c in clientes])

    @app.get("/api/clientes/<int:cliente_id>")
    def obtener_cliente(cliente_id):
        cliente = db.session.get(Cliente, cliente_id)
        if cliente is None:
            return jsonify({"error": "cliente no encontrado"}), 404
        return jsonify(cliente.to_dict())

    @app.post("/api/clientes")
    def crear_cliente():
        data = request.get_json(force=True) or {}
        if "carne" not in data or "nombre" not in data:
            return jsonify({"error": "faltan campos: carne, nombre"}), 400

        cliente = Cliente(
            carne=data["carne"], nombre=data["nombre"], contacto=data.get("contacto")
        )
        db.session.add(cliente)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "el carné ya existe"}), 409

        return jsonify(cliente.to_dict()), 201

    @app.put("/api/clientes/<int:cliente_id>")
    def editar_cliente(cliente_id):
        cliente = db.session.get(Cliente, cliente_id)
        if cliente is None:
            return jsonify({"error": "cliente no encontrado"}), 404

        data = request.get_json(force=True) or {}
        for campo in ("nombre", "contacto"):
            if campo in data:
                setattr(cliente, campo, data[campo])

        db.session.commit()
        return jsonify(cliente.to_dict())

    @app.delete("/api/clientes/<int:cliente_id>")
    def eliminar_cliente(cliente_id):
        cliente = db.session.get(Cliente, cliente_id)
        if cliente is None:
            return jsonify({"error": "cliente no encontrado"}), 404

        db.session.delete(cliente)
        db.session.commit()
        return "", 204


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
