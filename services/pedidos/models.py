import os
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def build_database_uri() -> str:
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ.get("DB_NAME", "pedidos_db")
    return f"postgresql://{user}:{password}@{host}:{port}/{name}"


class Pedido(db.Model):
    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key=True)
    # Carné del integrante que creó el pedido: evidencia personalizada
    # obligatoria, debe verse en el panel/UI.
    carne = db.Column(db.String(20), nullable=False, index=True)
    estado = db.Column(db.String(20), nullable=False)  # confirmado | rechazado
    total_q = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    items = db.relationship(
        "PedidoItem", backref="pedido", cascade="all, delete-orphan"
    )

    def to_dict(self, incluir_items=True):
        data = {
            "id": self.id,
            "carne": self.carne,
            "estado": self.estado,
            "total_q": float(self.total_q),
            "creado_en": self.creado_en.isoformat(),
        }
        if incluir_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data


class PedidoItem(db.Model):
    __tablename__ = "pedido_items"

    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey("pedidos.id"), nullable=False)
    sku = db.Column(db.String(40), nullable=False)
    nombre_producto = db.Column(db.String(120))
    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario_q = db.Column(db.Numeric(10, 2), nullable=False)

    def to_dict(self):
        return {
            "sku": self.sku,
            "nombre_producto": self.nombre_producto,
            "cantidad": self.cantidad,
            "precio_unitario_q": float(self.precio_unitario_q),
            "subtotal_q": float(self.precio_unitario_q) * self.cantidad,
        }
