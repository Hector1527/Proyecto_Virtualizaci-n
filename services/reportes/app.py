import os

import requests
from flask import Flask, jsonify

INVENTARIO_URL = os.environ.get("INVENTARIO_URL", "http://inventario:5000")
PEDIDOS_URL = os.environ.get("PEDIDOS_URL", "http://pedidos:5000")

app = Flask(__name__)


@app.get("/api/reportes/health")
def health():
    return jsonify({"status": "ok", "service": "reportes"})


@app.get("/api/reportes/dashboard")
def dashboard():
    """
    No tiene base de datos propia: agrega en tiempo real lo que ya
    exponen inventario y pedidos. Si más adelante el volumen de datos
    lo justifica, se puede migrar a un modelo de agregación con caché.
    """
    try:
        resumen_inv = requests.get(
            f"{INVENTARIO_URL}/api/inventario/resumen", timeout=5
        ).json()
    except requests.RequestException as exc:
        return jsonify({"error": f"inventario no disponible: {exc}"}), 502

    try:
        resumen_ped = requests.get(
            f"{PEDIDOS_URL}/api/pedidos/resumen-hoy", timeout=5
        ).json()
    except requests.RequestException as exc:
        return jsonify({"error": f"pedidos no disponible: {exc}"}), 502

    return jsonify(
        {
            "total_productos": resumen_inv["total_productos"],
            "valor_total_inventario_q": resumen_inv["valor_total_inventario_q"],
            "pedidos_hoy": resumen_ped["pedidos_hoy"],
            "confirmados_hoy": resumen_ped["confirmados_hoy"],
            "rechazados_hoy": resumen_ped["rechazados_hoy"],
            "alerta_stock_bajo": resumen_inv["productos_stock_bajo"],
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
