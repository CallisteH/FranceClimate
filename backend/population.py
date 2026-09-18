#!/usr/bin/env python3
"""
Télécharge et traite les estimations de population par département (INSEE).

Produit dans /data :
  - population.json : série annuelle de population totale par département
    (structure : { "Ain": [{"annee": 1975, "population": 123456}, ...], ... })

Source : INSEE — Estimations de population au 1er janvier par département,
sexe et grande classe d'âge (1975-2026).
Licence Ouverte 2.0.
Le fichier brut est mis en cache dans data/raw/ (cf. .gitignore).

Usage :
    python backend/population.py
"""

import json
import sys
from pathlib import Path

import pandas as pd
import requests

# Permet d'importer data_processing depuis le même dossier.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import data_processing as dp

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Fichier INSEE — estimations de population par département.
# L'identifiant de page et l'année dans le nom de fichier changent à chaque
# mise à jour annuelle : vérifier https://www.insee.fr/fr/statistiques/8721456
# et adapter l'URL ci-dessous si besoin.
INSEE_URL = (
    "https://www.insee.fr/fr/statistiques/fichier/8721456"
    "/estim-pop-dep-sexe-gca-1975-2026.xlsx"
)
RAW_FILENAME = "estim-pop-dep-sexe-gca.xlsx"

# Ligne de début des données dans chaque onglet annuel (après l'en-tête).
LIGNE_DEBUT = 5
# Colonnes : 0 = code département, 1 = nom, 7 = population totale (Ensemble).
COL_CODE = 0
COL_NOM = 1
COL_POPULATION = 7

# Codes à exclure (lignes de totaux nationaux présentes dans le fichier).
CODES_A_EXCLURE = {"DOM", "FR", "975"}  # 975 = Saint-Pierre-et-Miquelon (pas de données météo)


def telecharger_population(force: bool = False) -> Path:
    """Télécharge le fichier Excel de l'INSEE si absent du cache.

    Args:
        force: si True, retélécharge même si déjà en cache.
    """
    chemin = RAW_DIR / RAW_FILENAME
    if chemin.exists() and not force:
        return chemin
    resp = requests.get(INSEE_URL, timeout=120)
    resp.raise_for_status()
    chemin.write_bytes(resp.content)
    print(f"  Fichier téléchargé : {chemin.name}")
    return chemin


def code_vers_nom() -> dict[str, str]:
    """Construit une correspondance code INSEE → nom de département du projet.

    Utilise DEPARTEMENTS_NOMS (code → (nom, code)) et CODES_CORSE (nom → code)
    pour gérer le cas spécifique de la Corse (2A/2B).
    """
    mapping: dict[str, str] = {}
    for code, (nom, _) in dp.DEPARTEMENTS_NOMS.items():
        mapping[code] = nom
    # Ajouter les codes corses officiels (2A, 2B)
    for nom, code in dp.CODES_CORSE.items():
        mapping[code] = nom
    return mapping


def extraire_population(chemin: Path) -> list[dict]:
    """Lit le fichier Excel et retourne une liste d'enregistrements
    {departement, annee, population}.

    Un onglet par année (1975-2026). On ignore l'onglet « À savoir ».
    """
    mapping = code_vers_nom()
    xls = pd.ExcelFile(chemin)
    records: list[dict] = []

    for sheet in xls.sheet_names:
        if not sheet.isdigit():
            continue
        annee = int(sheet)
        df = pd.read_excel(xls, sheet_name=sheet, header=None, skiprows=LIGNE_DEBUT)
        # Garder uniquement les 3 colonnes d'intérêt
        df = df.iloc[:, [COL_CODE, COL_NOM, COL_POPULATION]].copy()
        df.columns = ["code", "nom", "population"]
        df["code"] = df["code"].astype(str).str.strip()

        for _, row in df.iterrows():
            code = row["code"]
            # Ignorer les lignes de totaux nationaux / hors champ
            if code in CODES_A_EXCLURE or pd.isna(row["population"]):
                continue
            # Ne garder que les départements présents dans le projet
            if code not in mapping:
                continue
            pop = pd.to_numeric(row["population"], errors="coerce")
            if pd.isna(pop):
                continue
            records.append({
                "departement": mapping[code],
                "annee": annee,
                "population": int(pop),
            })

    return records


def main() -> None:
    print("=== FranceClimate — Population par département (INSEE) ===\n")

    print(f"Téléchargement du fichier INSEE (cache : {RAW_DIR})")
    chemin = telecharger_population()
    print()

    print("Extraction des données de population…")
    records = extraire_population(chemin)

    # Restructurer en dict {departement: [{annee, population}, ...]} trié par année
    par_dept: dict[str, list[dict]] = {}
    for r in records:
        par_dept.setdefault(r["departement"], []).append(
            {"annee": r["annee"], "population": r["population"]}
        )
    for dept in par_dept:
        par_dept[dept].sort(key=lambda x: x["annee"])

    output = DATA_DIR / "population.json"
    output.write_text(
        json.dumps(par_dept, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  {len(par_dept)} départements écrits dans population.json")
    for dept, serie in sorted(par_dept.items()):
        if serie:
            print(f"    {dept} : {serie[0]['annee']}-{serie[-1]['annee']} "
                  f"({len(serie)} années)")

    print("\n=== Résumé ===")
    print(f"Départements : {len(par_dept)}")
    if records:
        annees = sorted({r["annee"] for r in records})
        print(f"Période      : {annees[0]}-{annees[-1]}")
    print(f"Fichier      : {output}")


if __name__ == "__main__":
    main()
