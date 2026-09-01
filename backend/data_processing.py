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

# Tous les départements français (96 métropolitains + 5 DOM).
# (nom, numéro, température annuelle moyenne de base en °C, amplitude saisonnière en °C)
# Métropole : amplitude ~11°C ; DOM : amplitude ~2-3°C (climat tropical).
DEPARTEMENTS = [
    ("Ain", 1, 11.5, 11.0),
    ("Aisne", 2, 11.0, 11.0),
    ("Allier", 3, 12.0, 11.0),
    ("Alpes-de-Haute-Provence", 4, 11.0, 11.5),
    ("Hautes-Alpes", 5, 9.0, 12.0),
    ("Alpes-Maritimes", 6, 16.0, 9.0),
    ("Ardèche", 7, 13.5, 11.0),
    ("Ardennes", 8, 10.5, 11.0),
    ("Ariège", 9, 12.5, 10.5),
    ("Aube", 10, 11.0, 11.5),
    ("Aude", 11, 14.5, 10.0),
    ("Aveyron", 12, 11.0, 11.0),
    ("Bouches-du-Rhône", 13, 15.6, 10.0),
    ("Calvados", 14, 11.5, 10.5),
    ("Cantal", 15, 9.5, 11.0),
    ("Charente", 16, 13.0, 10.5),
    ("Charente-Maritime", 17, 13.0, 9.5),
    ("Cher", 18, 12.0, 11.5),
    ("Corrèze", 19, 11.5, 11.0),
    ("Corse-du-Sud", "2A", 16.0, 8.0),
    ("Haute-Corse", "2B", 15.5, 8.5),
    ("Côte-d'Or", 21, 11.0, 11.5),
    ("Côtes-d'Armor", 22, 11.5, 8.5),
    ("Creuse", 23, 10.5, 11.5),
    ("Dordogne", 24, 13.0, 10.5),
    ("Doubs", 25, 10.5, 11.5),
    ("Drôme", 26, 13.5, 11.0),
    ("Eure", 27, 11.0, 10.5),
    ("Eure-et-Loir", 28, 11.0, 11.5),
    ("Finistère", 29, 11.8, 7.5),
    ("Gard", 30, 15.0, 10.0),
    ("Haute-Garonne", 31, 13.9, 10.5),
    ("Gers", 32, 13.5, 10.0),
    ("Gironde", 33, 14.0, 9.5),
    ("Hérault", 34, 15.1, 9.5),
    ("Ille-et-Vilaine", 35, 11.5, 8.5),
    ("Indre", 36, 12.0, 11.5),
    ("Indre-et-Loire", 37, 12.0, 11.0),
    ("Isère", 38, 11.8, 11.5),
    ("Jura", 39, 10.5, 11.5),
    ("Landes", 40, 14.0, 9.0),
    ("Loir-et-Cher", 41, 11.5, 11.5),
    ("Loire", 42, 11.5, 11.0),
    ("Haute-Loire", 43, 10.0, 11.5),
    ("Loire-Atlantique", 44, 12.8, 9.0),
    ("Loiret", 45, 11.5, 11.5),
    ("Lot", 46, 12.5, 10.5),
    ("Lot-et-Garonne", 47, 13.5, 10.5),
    ("Lozère", 48, 10.0, 11.5),
    ("Maine-et-Loire", 49, 12.0, 10.5),
    ("Manche", 50, 11.0, 7.5),
    ("Marne", 51, 10.5, 11.5),
    ("Haute-Marne", 52, 10.0, 12.0),
    ("Mayenne", 53, 11.5, 10.5),
    ("Meurthe-et-Moselle", 54, 10.5, 11.5),
    ("Meuse", 55, 10.0, 12.0),
    ("Morbihan", 56, 12.0, 8.0),
    ("Moselle", 57, 10.0, 11.5),
    ("Nièvre", 58, 11.5, 11.5),
    ("Nord", 59, 10.8, 10.0),
    ("Oise", 60, 11.0, 11.0),
    ("Orne", 61, 11.0, 10.5),
    ("Pas-de-Calais", 62, 10.5, 9.5),
    ("Puy-de-Dôme", 63, 11.0, 11.0),
    ("Pyrénées-Atlantiques", 64, 13.5, 9.0),
    ("Hautes-Pyrénées", 65, 11.0, 10.0),
    ("Pyrénées-Orientales", 66, 15.5, 9.5),
    ("Bas-Rhin", 67, 10.9, 11.5),
    ("Haut-Rhin", 68, 10.5, 11.5),
    ("Rhône", 69, 12.4, 11.0),
    ("Haute-Saône", 70, 10.0, 11.5),
    ("Saône-et-Loire", 71, 11.5, 11.5),
    ("Sarthe", 72, 11.5, 11.0),
    ("Savoie", 73, 10.0, 11.5),
    ("Haute-Savoie", 74, 9.5, 11.5),
    ("Paris", 75, 12.3, 11.0),
    ("Seine-Maritime", 76, 11.2, 10.0),
    ("Seine-et-Marne", 77, 11.5, 11.0),
    ("Yvelines", 78, 11.5, 11.0),
    ("Deux-Sèvres", 79, 12.5, 10.5),
    ("Somme", 80, 10.5, 10.5),
    ("Tarn", 81, 13.0, 10.5),
    ("Tarn-et-Garonne", 82, 13.5, 10.5),
    ("Var", 83, 15.9, 9.0),
    ("Vaucluse", 84, 14.5, 10.0),
    ("Vendée", 85, 12.5, 9.0),
    ("Vienne", 86, 12.5, 10.5),
    ("Haute-Vienne", 87, 11.5, 11.0),
    ("Vosges", 88, 10.0, 11.5),
    ("Yonne", 89, 11.5, 11.5),
    ("Territoire de Belfort", 90, 10.0, 11.5),
    ("Essonne", 91, 11.5, 11.0),
    ("Hauts-de-Seine", 92, 12.0, 11.0),
    ("Seine-Saint-Denis", 93, 12.0, 11.0),
    ("Val-de-Marne", 94, 12.0, 11.0),
    ("Val-d'Oise", 95, 11.5, 11.0),
    # DOM (climat tropical, amplitude faible)
    ("Guadeloupe", 971, 26.0, 2.0),
    ("Martinique", 972, 26.5, 2.0),
    ("Guyane", 973, 26.5, 1.5),
    ("La Réunion", 974, 23.0, 3.0),
    ("Mayotte", 976, 26.0, 2.0),
]

MOIS_NOMS = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]

# Tendance de réchauffement par année ( °C / an ) - tendances récentes.
TENDANCE = 0.04

ANNEES = list(range(2018, 2025))  # 2018 -> 2024 inclus


def normale_mensuelle(t_base: float, amplitude: float, mois: int) -> float:
    """Normale 1991-2020 : sinusoïde centrée sur juillet (mois le plus chaud)."""
    return round(t_base + amplitude * np.cos(2 * np.pi * (mois - 7) / 12), 1)


def temperature_observee(t_base: float, amplitude: float, mois: int, annee: int, rng: np.random.Generator) -> float:
    """Température observée : normale + tendance de réchauffement + bruit aléatoire."""
    base = normale_mensuelle(t_base, amplitude, mois)
    tendance = TENDANCE * (annee - 2005)  # référence 2005
    bruit = rng.normal(0, 1.0)
    return round(base + tendance + bruit, 1)


def main() -> None:
    rng = np.random.default_rng(42)

    # --- Normales 1991-2020 ---
    normales_rows = []
    for nom, _, t_base, amplitude in DEPARTEMENTS:
        for mois in range(1, 13):
            normales_rows.append({
                "departement": nom,
                "mois": mois,
                "normale_1991_2020": normale_mensuelle(t_base, amplitude, mois),
            })
    normales = pd.DataFrame(normales_rows)
    normales.to_csv(DATA_DIR / "normales_1991_2020.csv", index=False)

    # --- Températures mensuelles observées ---
    temp_rows = []
    for nom, _, t_base, amplitude in DEPARTEMENTS:
        for annee in ANNEES:
            for mois in range(1, 13):
                temp_rows.append({
                    "departement": nom,
                    "mois": mois,
                    "annee": annee,
                    "temperature_moyenne": temperature_observee(t_base, amplitude, mois, annee, rng),
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
    depts = [{"nom": nom, "code": code} for nom, code, _, _ in DEPARTEMENTS]
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
