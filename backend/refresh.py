#!/usr/bin/env python3
"""
Rafraîchit les données récentes de FranceClimate.

Télécharge (ou met à jour) uniquement les fichiers « latest » de Météo-France
(séries 2025-2026, stations actives), puis relance le pipeline complet pour
régénérer les fichiers de données dans /data.

L'archive « previous » (1950-2024) n'est pas retéléchargée : elle est figée
et déjà présente dans le cache data/raw/.

Usage :
    python backend/refresh.py              # rafraîchit les latest, puis régénère
    python backend/refresh.py --skip-build # retélécharge les latest uniquement
"""

import argparse
import sys
from pathlib import Path

# Permet d'importer data_processing depuis le même dossier.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import data_processing as dp


def rafraichir_latest() -> int:
    """Retélécharge les fichiers latest pour tous les départements.

    Retourne le nombre de fichiers téléchargés avec succès.
    """
    print("=== FranceClimate — Rafraîchissement des données récentes ===\n")
    print(f"Téléchargement des fichiers latest (cache : {dp.RAW_DIR})")

    compteur = 0
    for code in dp.CODES_FICHIER:
        nom = dp.DEPARTEMENTS_NOMS.get(code, ("?", code))[0]
        chemin = dp.telecharger_fichier(code, fenetre="latest", force=True)
        if chemin is not None:
            compteur += 1
            print(f"  OK {code} ({nom})")
        else:
            print(f"  ECHEC {code} ({nom})")

    print(f"\n  {compteur}/{len(dp.CODES_FICHIER)} fichiers latest téléchargés\n")
    return compteur


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rafraîchit les données récentes Météo-France et régénère le pipeline."
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Retélécharge les fichiers latest sans relancer le pipeline complet.",
    )
    args = parser.parse_args()

    rafraichir_latest()

    if args.skip_build:
        print("Option --skip-build : pipeline non relancé.")
        print("Lancez « python backend/data_processing.py » pour régénérer les données.")
        return

    print("Régénération du pipeline complet…\n")
    dp.main()


if __name__ == "__main__":
    main()
