# AGENTS.md — FranceClimate

## À propos du projet

FranceClimate est une application web statique affichant les données
climatologiques mensuelles de chaque département français (température,
précipitations, ensoleillement, vent) par rapport à la normale climatique
1991-2020, ainsi que l'évolution démographique (population INSEE). Les données
climatiques proviennent des **données climatologiques de base mensuelles** de
Météo-France (Licence Ouverte 2.0), agrégées par département à partir des
stations météorologiques. Le site est déployé via GitHub Pages, sans backend
runtime : les données sont pré-calculées en JSON et servies en statique.

## Stack

| Composant    | Technologie                   |
|--------------|-------------------------------|
| Frontend     | HTML / CSS / JS (vanilla)      |
| Graphiques   | Chart.js (via CDN)            |
| Build        | Python 3.10+ (pipelines données) |
| Données      | CSV sources + JSON pré-calculés |
| Déploiement  | GitHub Pages (site statique)  |
| Environnement| `uv` (gestion des dépendances) |

## Structure

```
FranceClimate/
├── data/
│   ├── raw/                    # Cache des CSV gz Météo-France + xlsx INSEE (gitignoré)
│   ├── normales_climat.csv     # Normales 1991-2020 (4 métriques)
│   ├── observations_mensuelles.csv
│   ├── anomalies.json          # Anomalies pré-calculées
│   ├── population.json         # Population par département (INSEE, 1975-2026)
│   ├── immobilier.json         # Indice Notaires-INSEE par région (1996→)
│   └── departements.json       # Liste des départements
├── backend/
│   ├── data_processing.py      # Pipeline : téléchargement + traitement Météo-France
│   ├── population.py           # Pipeline : population INSEE par département
│   ├── immobilier.py           # Pipeline : indice Notaires-INSEE par région
│   ├── refresh.py              # Rafraîchit les données récentes (latest)
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js              # Fetch des JSON statiques + rendu Chart.js
│   ├── carte-france.svg
│   ├── carte-france-regions.svg
│   └── data/                   # Données servies en statique (GitHub Pages)
│       ├── departements.json
│       ├── population.json
│       ├── immobilier.json
│       └── departements/       # Un fichier <code>.json par département
├── .github/workflows/pages.yml # Déploiement GitHub Pages
├── pyproject.toml
└── .gitignore
```

## Commandes utiles

```bash
# Environnement Python
uv venv .venv
source .venv/bin/activate
uv pip install -r backend/requirements.txt

# Télécharger + traiter les données Météo-France (cache dans data/raw/)
python backend/data_processing.py

# Télécharger + traiter les données de population INSEE
python backend/population.py

# Rafraîchir uniquement les données récentes (latest, mise à jour quotidienne)
python backend/refresh.py

# Servir le frontend en local (http://localhost:8000)
python -m http.server 8000 --directory frontend
```

## Données statiques (frontend/data/)

Les fichiers dans `frontend/data/` sont générés par les pipelines Python et
servis en statique par le frontend via `fetch()`. Ils sont régénérés à chaque
exécution de `backend/data_processing.py` (climat) et
`backend/population.py` (population).

| Fichier                       | Source                        | Description                          |
|-------------------------------|-------------------------------|--------------------------------------|
| `departements.json`           | `data_processing.py`         | Liste des départements (nom, code)  |
| `departements/<code>.json`    | `data_processing.py`         | Anomalies d'un département (série)  |
| `population.json`              | `population.py`              | Population par département (INSEE)  |
| `immobilier.json`             | `immobilier.py`              | Indice Notaires-INSEE par région     |

## Règles de travail

### Confidentialité

- **Ne jamais** intégrer d'informations confidentielles dans le dépôt :
  clés API, tokens, mots de passe, identifiants, données personnelles,
  URLs internes privées.
- Les secrets appartiennent au fichier `.env` (déjà ignoré par `.gitignore`)
  ou aux variables d'environnement du système de déploiement.
- Ne jamais lire, afficher, ou copier le contenu d'un fichier `.env`.
- Si une clé ou un secret est découvert dans le code, le retirer
  immédiatement et alerter l'utilisateur.

### Style et conventions

- Frontend : JavaScript vanilla, pas de framework ni de build step.
- Backend : Python, type hints sur les fonctions publiques, docstrings
  concis en français.
- Noms de fichiers et de variables en français, cohérents avec l'existant.
- Indentation : 4 espaces côté Python, 4 espaces côté JS/CSS.
- Les messages d'erreur et le texte affiché à l'utilisateur sont en français.

### Données

- `data/anomalies.json`, `data/departements.json`, `data/normales_climat.csv`
  et `data/observations_mensuelles.csv` sont régénérés par
  `backend/data_processing.py` ; ne pas les éditer à la main.
- `data/population.json` est régénéré par `backend/population.py` ; ne pas
  l'éditer à la main. La source (fichier xlsx INSEE) est mise en cache dans
  `data/raw/` (gitignoré). L'URL INSEE est codée en dur dans
  `backend/population.py` et doit être mise à jour annuellement.
- `data/immobilier.json` est régénéré par `backend/immobilier.py` ; ne pas
  l'éditer à la main. Les données proviennent de l'API SDMX de l'INSEE
  (indice Notaires-INSEE des prix des logements anciens, base 100 = 2015),
  sans clé ni cache fichier (une requête batch à chaque exécution). Les
  données sont structurées par région (13 régions métropolitaines) : 5
  séries régionales distinctes (Province, Île-de-France, AURA, PACA,
  Hauts-de-France) couvrent l'ensemble du territoire. La carte de l'onglet
  immobilier utilise `frontend/carte-france-regions.svg` (généré par
  fusion des paths départements du SVG existant). Les DOM ne sont pas
  couverts.
- Les CSV bruts Météo-France sont mis en cache dans `data/raw/` (gitignoré).
- Les données sont des vraies observations Météo-France agrégées par
  département (moyenne des stations), pas des échantillons synthétiques.

### Dépendances

- Ajouter toute nouvelle dépendance Python dans `backend/requirements.txt`
  **et** `pyproject.toml`.
- Le frontend charge Chart.js via CDN : ne pas introduire de bundler.

### Git

- Messages de commit en français, préfixés par `feat:`, `fix:`, `docs:`,
  `refactor:`, `chore:` selon la nature du changement.
- Ne pas committer `.venv/`, `__pycache__/`, `.env`, `.vibe/`, `node_modules/`.
- Travailler sur une branche dédiée, pas directement sur `main`.
