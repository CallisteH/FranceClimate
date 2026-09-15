"""
API Flask servant les données climatologiques par département / mois / année.

Endpoints :
  GET /api/departements          -> liste des départements disponibles
  GET /api/annees                -> liste des années disponibles
  GET /api/metrics               -> liste des métriques (libellés, unités, champs)
  GET /api/anomalie?departement=&mois=&annee=
      -> données pour un département/mois/année donné
  GET /api/anomalies?departement=
      -> toutes les données d'un département (série temporelle)
"""

import json
from functools import lru_cache
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@lru_cache(maxsize=1)
def load_anomalies() -> list[dict]:
    with open(DATA_DIR / "anomalies.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_departements() -> list[dict]:
    with open(DATA_DIR / "departements.json", encoding="utf-8") as f:
        return json.load(f)


@app.route("/api/departements", methods=["GET"])
def get_departements():
    return jsonify(load_departements())


@app.route("/api/annees", methods=["GET"])
def get_annees():
    annees = sorted({a["annee"] for a in load_anomalies()})
    return jsonify(annees)


@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Liste des métriques disponibles avec leurs libellés, unités et noms de champs."""
    return jsonify([
        {
            "key": "temperature",
            "label": "Température",
            "unit": "°C",
            "field": "temperature",
            "normal_field": "normale_temperature",
            "anomaly_field": "anomalie_temperature",
        },
        {
            "key": "precipitation",
            "label": "Précipitations",
            "unit": "mm",
            "field": "precipitation",
            "normal_field": "normale_precipitation",
            "anomaly_field": "anomalie_precipitation",
        },
        {
            "key": "ensoleillement",
            "label": "Ensoleillement",
            "unit": "h",
            "field": "ensoleillement",
            "normal_field": "normale_ensoleillement",
            "anomaly_field": "anomalie_ensoleillement",
        },
        {
            "key": "vent",
            "label": "Vent moyen",
            "unit": "m/s",
            "field": "vent",
            "normal_field": "normale_vent",
            "anomaly_field": "anomalie_vent",
        },
    ])


@app.route("/api/anomalie", methods=["GET"])
def get_anomalie():
    departement = request.args.get("departement")
    mois = request.args.get("mois")
    annee = request.args.get("annee")

    if not departement or not mois or not annee:
        return jsonify({"error": "Paramètres requis: departement, mois, annee"}), 400

    try:
        mois_int = int(mois)
        annee_int = int(annee)
    except ValueError:
        return jsonify({"error": "mois et annee doivent être des entiers"}), 400

    for a in load_anomalies():
        if (
            a["departement"] == departement
            and a["mois"] == mois_int
            and a["annee"] == annee_int
        ):
            return jsonify(a)

    return jsonify({"error": "Données non trouvées"}), 404


@app.route("/api/anomalies", methods=["GET"])
def get_anomalies_serie():
    """Retourne toutes les anomalies d'un département (série 2018-2026)."""
    departement = request.args.get("departement")
    if not departement:
        return jsonify({"error": "Paramètre requis: departement"}), 400

    serie = [a for a in load_anomalies() if a["departement"] == departement]
    if not serie:
        return jsonify({"error": "Département introuvable"}), 404

    return jsonify(serie)


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "FranceClimate API"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
