"""
Génère des données d'échantillon réalistes pour le développement de l'application.

Produit trois fichiers dans /data :
  - normales_1991_2020.csv  : normale mensuelle par département (moyenne 1991-2020)
  - temperatures_mensuelles.csv : température moyenne mensuelle observée (2018-2024)
  - anomalies.json          : anomalies pré-calculées (température - normale)

Les valeurs sont synthétiques mais plausibles ( climat tempéré français ).
Remplacer ensuite par les vraies données Météo France / data.gouv.fr.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Échantillon de départements couvrant plusieurs climats français.
DEPARTEMENTS = [
    # (nom, numéro, température annuelle moyenne de base en °C)
    ("Paris", 75, 12.3),
    ("Seine-Maritime", 76, 11.2),
    ("Nord", 59, 10.8),
    ("Gironde", 33, 14.0),
    ("Haute-Garonne", 31, 13.9),
    ("Loire-Atlantique", 44, 12.8),
    ("Bouches-du-Rhône", 13, 15.6),
    ("Var", 83, 15.9),
    ("Rhône", 69, 12.4),
    ("Isère", 38, 11.8),
    ("Bas-Rhin", 67, 10.9),
    ("Calvados", 14, 11.5),
    ("Finistère", 29, 11.8),
    ("Hérault", 34, 15.1),
    ("Puy-de-Dôme", 63, 11.0),
]

MOIS_NOMS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]

# Amplitude saisonnière approximative ( France métropolitaine ).
AMPLITUDE = 11.0  # écart de température autour de la moyenne annuelle

# Tendance de réchauffement par année ( °C / an ) - tendances récentes.
TENDANCE = 0.04

ANNEES = list(range(2018, 2025))  # 2018 -> 2024 inclus


def normale_mensuelle(t_base: float, mois: int) -> float:
    """Normale 1991-2020 : sinusoïde centrée sur juillet (mois le plus chaud)."""
    return round(t_base + AMPLITUDE * np.cos(2 * np.pi * (mois - 7) / 12), 1)


def temperature_observee(t_base: float, mois: int, annee: int, rng: np.random.Generator) -> float:
    """Température observée : normale + tendance de réchauffement + bruit aléatoire."""
    base = normale_mensuelle(t_base, mois)
    tendance = TENDANCE * (annee - 2005)  # référence 2005
    bruit = rng.normal(0, 1.0)
    return round(base + tendance + bruit, 1)


def main() -> None:
    rng = np.random.default_rng(42)

    # --- Normales 1991-2020 ---
    normales_rows = []
    for nom, _, t_base in DEPARTEMENTS:
        for mois in range(1, 13):
            normales_rows.append({
                "departement": nom,
                "mois": mois,
                "normale_1991_2020": normale_mensuelle(t_base, mois),
            })
    normales = pd.DataFrame(normales_rows)
    normales.to_csv(DATA_DIR / "normales_1991_2020.csv", index=False)

    # --- Températures mensuelles observées ---
    temp_rows = []
    for nom, _, t_base in DEPARTEMENTS:
        for annee in ANNEES:
            for mois in range(1, 13):
                temp_rows.append({
                    "departement": nom,
                    "mois": mois,
                    "annee": annee,
                    "temperature_moyenne": temperature_observee(t_base, mois, annee, rng),
                })
    temperatures = pd.DataFrame(temp_rows)
    temperatures.to_csv(DATA_DIR / "temperatures_mensuelles.csv", index=False)

    # --- Anomalies pré-calculées ---
    merged = pd.merge(
        temperatures,
        normales,
        on=["departement", "mois"],
        how="left",
    )
    merged["anomalie"] = (merged["temperature_moyenne"] - merged["normale_1991_2020"]).round(1)
    anomalies = merged[[
        "departement", "mois", "annee",
        "temperature_moyenne", "normale_1991_2020", "anomalie",
    ]]
    anomalies.to_json(DATA_DIR / "anomalies.json", orient="records", force_ascii=False, indent=2)

    # --- Liste des départements pour le frontend ---
    depts = [{"nom": nom, "code": code} for nom, code, _ in DEPARTEMENTS]
    (DATA_DIR / "departements.json").write_text(
        json.dumps(depts, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Départements : {len(DEPARTEMENTS)}")
    print(f"Normales     : {len(normales)} lignes")
    print(f"Températures : {len(temperatures)} lignes")
    print(f"Anomalies    : {len(anomalies)} entrées")
    print(f"Période      : {ANNEES[0]}-{ANNEES[-1]}")
    print("Fichiers générés dans /data")


if __name__ == "__main__":
    main()
