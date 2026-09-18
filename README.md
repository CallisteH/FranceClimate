# FranceClimate — Climat et démographie par département

Application web statique affichant les données climatologiques mensuelles
d'un département français (température, précipitations, ensoleillement, vent)
par rapport à la normale climatique 1991-2020, ainsi que l'évolution
démographique (population INSEE).

Les données climatiques proviennent des **données climatologiques de base
mensuelles** de Météo-France (Licence Ouverte 2.0). Elles sont agrégées par
département à partir des observations des stations météorologiques. Les
données de population proviennent de l'INSEE (estimations de population,
Licence Ouverte 2.0).

Le site est déployé via GitHub Pages : aucune API, les données sont
pré-calculées en JSON et servies en statique.

## Stack

| Composant | Technologie |
|-----------|-------------|
| Frontend | HTML / CSS / JS (vanilla) |
| Graphiques | Chart.js (via CDN) |
| Build | Python 3.10+ (pipelines de données) |
| Données | CSV Météo-France/INSEE → JSON pré-calculés |
| Déploiement | GitHub Pages (site statique) |
| Environnement | `uv` (gestion des dépendances Python) |

## Structure

```
FranceClimate/
├── data/
│   ├── raw/                        # Cache CSV gz Météo-France + xlsx INSEE (gitignoré)
│   ├── normales_climat.csv         # Normales 1991-2020 par département (4 métriques)
│   ├── observations_mensuelles.csv # Observations 2018-2026 par département
│   ├── anomalies.json              # Anomalies pré-calculées (4 métriques)
│   ├── population.json             # Population par département (INSEE, 1975-2026)
│   └── departements.json           # Liste des départements
├── backend/
│   ├── data_processing.py          # Pipeline : téléchargement + traitement Météo-France
│   ├── population.py              # Pipeline : population INSEE par département
│   ├── refresh.py                  # Rafraîchit les données récentes (latest)
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js                   # Fetch des JSON statiques + rendu Chart.js
│   ├── carte-france.svg
│   └── data/                       # Données servies en statique (GitHub Pages)
│       ├── departements.json
│       ├── population.json
│       └── departements/           # Un fichier <code>.json par département
├── .github/workflows/pages.yml     # Déploiement GitHub Pages
├── pyproject.toml
└── .gitignore
```

## Démarrage rapide

### 1. Environnement Python

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r backend/requirements.txt
```

### 2. Générer les données

```bash
python backend/data_processing.py   # climat Météo-France
python backend/population.py         # population INSEE
```

Le script `data_processing.py` télécharge les fichiers mensuels Météo-France
(~146 MB, mis en cache dans `data/raw/`), agrège les stations par département,
calcule les normales 1991-2020 et les observations 2018-2026, puis produit
`anomalies.json` et les fichiers statiques dans `frontend/data/`.

Source : [données climatologiques de base mensuelles](https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-mensuelles)
de Météo-France, Licence Ouverte 2.0.

### 3. Servir le frontend en local

```bash
python -m http.server 8000 --directory frontend
```

Puis ouvrir `http://localhost:8000`.

## Déploiement GitHub Pages

Le workflow `.github/workflows/pages.yml` publie le dossier `frontend/` sur
GitHub Pages à chaque push sur `main`. Configurer dans Settings → Pages →
Source : **GitHub Actions**.

## Métriques

| Métrique | Champ | Unité | Source Météo-France |
|----------|-------|-------|---------------------|
| Température moyenne | `temperature` | °C | TM |
| Précipitations (cumul) | `precipitation` | mm | RR |
| Ensoleillement (durée) | `ensoleillement` | h | INST (converti de minutes) |
| Vent moyen à 10 m | `vent` | m/s | FFM |

## Format des données

### `normales_climat.csv`

```csv
departement,mois,normale_temperature,normale_precipitation,normale_vent,normale_ensoleillement
Gironde,1,6.7,85.8,3.2,91.0
Gironde,7,21.2,46.3,2.8,262.8
```

### `observations_mensuelles.csv`

```csv
departement,annee,mois,temperature,precipitation,vent,ensoleillement
Gironde,2023,7,21.7,28.0,2.8,242.8
```

## Notes

- Les données sont agrégées par département (moyenne des stations).
- La Corse (fichier unifié 20) est séparée en Corse-du-Sud (2A) et Haute-Corse
  (2B) par latitude.
- Mayotte (976) n'a pas de données mensuelles disponibles.
- Les normales sont calculées sur la période 1991-2020, les observations sur
  2018-2026.
