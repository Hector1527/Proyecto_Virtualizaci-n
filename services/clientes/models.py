import os
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def build_database_uri() -> str:
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]
    host = os.environ.get("DB_HOST", "localhost")
    port = os.environ.get("DB_PORT", "5432")
    name = os.environ.get("DB_NAME", "clientes_db")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"

class Cliente(db.Model):
    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    # "carne" es el carné del integrante que sembró el registro (evidencia
    # personalizada) o del cliente real de El Quetzal, según cómo lo
    # definan; aquí lo dejamos como identificador único simple.
    carne = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(120), nullable=False)
    contacto = db.Column(db.String(120))
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "carne": self.carne,
            "nombre": self.nombre,
            "contacto": self.contacto,
        }
