import os

import requests
from flask import Flask, jsonify

INVENTARIO_URL = os.environ.get("INVENTARIO_URL", "http://inventario:5000")

app = Flask(__name__)

# SUPUESTO A CONFIRMAR CON EL EQUIPO / DOCENTE:
# El enunciado no detalla qué hace "catalogo" además de servir de
# ejemplo de ruta para el gateway. Aquí se implementa como una vista
# pública de solo lectura sobre los productos de inventario (sin base
# de datos propia, ya que no hay un requerimiento funcional que exija
# datos distintos a los de inventario). Si el profesor espera algo
# distinto (p. ej. categorías propias, promociones), hay que ajustarlo.


@app.get("/api/catalogo/health")
def health():
    return jsonify({"status": "ok", "service": "catalogo"})


@app.get("/api/catalogo/productos")
def listar_catalogo():
    try:
        productos = requests.get(
            f"{INVENTARIO_URL}/api/inventario/productos", timeout=5
        ).json()
    except requests.RequestException as exc:
        return jsonify({"error": f"inventario no disponible: {exc}"}), 502

    # Vista pública: se omite el stock exacto, solo disponibilidad.
    publico = [
        {
            "sku": p["sku"],
            "nombre": p["nombre"],
            "categoria": p["categoria"],
            "precio_q": p["precio_q"],
            "disponible": p["stock"] > 0,
        }
        for p in productos
    ]
    return jsonify(publico)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
