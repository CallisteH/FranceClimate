# AGENTS.md — FranceClimate

## À propos du projet

FranceClimate est une application web affichant les données climatologiques
mensuelles de chaque département français (température, précipitations,
ensoleillement, vent) par rapport à la normale climatique 1991-2020. Les
données proviennent des **données climatologiques de base mensuelles** de
Météo-France (Licence Ouverte 2.0), agrégées par département à partir des
stations météorologiques.

## Stack

| Composant    | Technologie                   |
|--------------|-------------------------------|
| Frontend     | HTML / CSS / JS (vanilla)      |
| Graphiques   | Chart.js (via CDN)            |
| Backend      | Python 3.10+ / Flask          |
| Données      | CSV sources + JSON pré-calculés |
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
│   └── departements.json       # Liste des départements
├── backend/
│   ├── app.py                  # API Flask
│   ├── data_processing.py      # Pipeline : téléchargement + traitement
│   ├── population.py           # Pipeline : population INSEE par département
│   ├── refresh.py              # Rafraîchit les données récentes (latest)
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js              # Appel API + rendu Chart.js (4 graphiques)
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

# Lancer l'API (http://localhost:5000)
python backend/app.py

# Servir le frontend (http://localhost:8000)
python -m http.server 8000 --directory frontend
```

## API Flask

| Endpoint                  | Paramètres                        | Description                          |
|---------------------------|-----------------------------------|--------------------------------------|
| `GET /api/departements`   | —                                 | Liste des départements               |
| `GET /api/annees`         | —                                 | Années disponibles                   |
| `GET /api/metrics`        | —                                 | Liste des métriques (libellés, unités) |
| `GET /api/anomalie`       | `departement`, `mois`, `annee`    | Données pour un point (4 métriques)   |
| `GET /api/anomalies`      | `departement`                     | Série complète d'un département      |
| `GET /api/population`     | `departement`                     | Série de population (INSEE, 1975-2026) |
| `GET /api/population/evolution` | —                           | Évolution sur 5 ans, tous départements |

Le endpoint `/api/anomalie` fait une recherche linéaire dans la liste
complète chargée en mémoire ; pour des recherches fréquentes, envisager un
index par `(departement, mois, annee)`.

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
