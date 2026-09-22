#!/usr/bin/env python3
"""
Télécharge et traite l'indice Notaires-INSEE des prix des logements anciens.

L'indice trimestriel existe au niveau régional (et non départemental, hors
Île-de-France). On utilise donc une carte par région : 5 séries régionales
distinctes (Province, Île-de-France, AURA, PACA, Hauts-de-France) couvrent
les 13 régions métropolitaines.

Produit dans /data et frontend/data :
  - immobilier.json : série trimestrielle d'indice par région
    (structure : { "Auvergne-Rhône-Alpes": [{"trimestre": "1996-T1", "valeur": 40.8}, ...], ... })

Source : INSEE / Notaires de France — Indice des prix des logements anciens,
séries brutes, base 100 = moyenne annuelle 2015.
API SDMX (gratuite, sans clé) : https://bdm.insee.fr/series/sdmx/
Licence Ouverte 2.0.

Usage :
    python backend/immobilier.py
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_DATA_DIR = FRONTEND_DIR / "data"

# Base de l'API SDMX de l'INSEE (séries BDM). Les idBanks sont séparés par « + ».
INSEE_SDMX_URL = "https://bdm.insee.fr/series/sdmx/data/SERIES_BDM/{idbanks}?startPeriod=1996-Q1"

# 5 séries brutes utilisées (base 100 = moyenne annuelle 2015).
IDBANKS = {
    "010567072": "Province – Ensemble – brute",
    "010567078": "Île-de-France – Ensemble – brute",
    "010567130": "Auvergne-Rhône-Alpes – Ensemble – brute",
    "010567112": "PACA – Ensemble – brute",
    "010567124": "Hauts-de-France – Ensemble – brute",
}

# Mapping région → idBank. Les régions sans série propre utilisent Province.
SERIES_PAR_REGION = {
    "Auvergne-Rhône-Alpes": "010567130",
    "Bourgogne-Franche-Comté": "010567072",
    "Bretagne": "010567072",
    "Centre-Val de Loire": "010567072",
    "Corse": "010567072",
    "Grand Est": "010567072",
    "Hauts-de-France": "010567124",
    "Île-de-France": "010567078",
    "Normandie": "010567072",
    "Nouvelle-Aquitaine": "010567072",
    "Occitanie": "010567072",
    "Pays de la Loire": "010567072",
    "Provence-Alpes-Côte d'Azur": "010567112",
}


def telecharger_indices() -> bytes:
    """Télécharge les 5 séries en une seule requête SDMX batch.

    Retourne le contenu XML brut. Les données étant légères et mises à jour
    trimestriellement, aucun cache fichier n'est utilisé.
    """
    idbanks = "+".join(IDBANKS.keys())
    url = INSEE_SDMX_URL.format(idbanks=idbanks)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.content


def parser_sdmx(xml_bytes: bytes) -> dict[str, list[dict]]:
    """Parse la réponse SDMX 2.1 et retourne un dict {idbank: [observations]}.

    Chaque observation : {"trimestre": "1996-T1", "valeur": 40.8}.
    Les observations sont triées par ordre chronologique croissant.
    """
    root = ET.fromstring(xml_bytes)
    series_par_idbank: dict[str, list[dict]] = {}

    for series in root.iter("Series"):
        idbank = series.get("IDBANK")
        if not idbank:
            continue
        obs_list: list[dict] = []
        for obs in series.iter("Obs"):
            trimestre = obs.get("TIME_PERIOD")
            valeur_str = obs.get("OBS_VALUE")
            if not trimestre or not valeur_str:
                continue
            try:
                valeur = round(float(valeur_str), 2)
            except ValueError:
                continue
            obs_list.append({"trimestre": trimestre, "valeur": valeur})
        # L'API retourne les observations du plus récent au plus ancien.
        obs_list.sort(key=lambda o: o["trimestre"])
        series_par_idbank[idbank] = obs_list

    return series_par_idbank


def main() -> None:
    print("=== FranceClimate — Indice Notaires-INSEE des prix des logements anciens ===\n")

    print(f"Téléchargement des {len(IDBANKS)} séries (API SDMX INSEE)…")
    xml_bytes = telecharger_indices()
    print("  XML reçu.\n")

    print("Parsing SDMX…")
    series_par_idbank = parser_sdmx(xml_bytes)
    print(f"  {len(series_par_idbank)} séries extraites")
    for idbank, obs in sorted(series_par_idbank.items()):
        if obs:
            print(f"    {idbank} : {obs[0]['trimestre']}\u2192{obs[-1]['trimestre']} "
                  f"({len(obs)} trimestres)")
    print()

    # Construire le dict par région : nom → série d'observations.
    par_region: dict[str, list[dict]] = {}
    for region, idbank in SERIES_PAR_REGION.items():
        obs = series_par_idbank.get(idbank)
        if obs:
            par_region[region] = obs

    # Écriture dans /data et frontend/data (même contenu).
    contenu_json = json.dumps(par_region, ensure_ascii=False, indent=2)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "immobilier.json").write_text(contenu_json, encoding="utf-8")
    (FRONTEND_DATA_DIR / "immobilier.json").write_text(contenu_json, encoding="utf-8")

    print(f"  {len(par_region)} régions écrites dans immobilier.json")
    for region, obs in sorted(par_region.items()):
        if obs:
            print(f"    {region} : {obs[0]['trimestre']}\u2192{obs[-1]['trimestre']} "
                  f"({len(obs)} trimestres)")

    print("\n=== Résumé ===")
    print(f"Régions  : {len(par_region)}")
    if par_region:
        tous_trimestres = [o["trimestre"] for obs in par_region.values() for o in obs]
        print(f"Période  : {min(tous_trimestres)}\u2192{max(tous_trimestres)}")
    print(f"Fichiers : {DATA_DIR / 'immobilier.json'}")
    print(f"           {FRONTEND_DATA_DIR / 'immobilier.json'}")


if __name__ == "__main__":
    main()
