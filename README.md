# FranceClimate — Climat mensuel par département

Application web affichant les données climatologiques mensuelles d'un département
français (température, précipitations, ensoleillement, vent) par rapport à la
normale climatique 1991-2020.

Les données proviennent des **données climatologiques de base mensuelles** de
Météo-France (Licence Ouverte 2.0). Elles sont agrégées par département à partir
des observations des stations météorologiques.

## Stack

| Composant | Technologie |
|-----------|-------------|
| Frontend | HTML / CSS / JS (vanilla) |
| Graphiques | Chart.js (via CDN) |
| Backend | Python + Flask |
| Données | CSV Météo-France / JSON pré-calculés |
| Environnement | `uv` (gestion des dépendances Python) |

## Structure

```
FranceClimate/
├── data/
│   ├── raw/                        # Cache des CSV gz Météo-France (gitignoré)
│   ├── normales_climat.csv         # Normales 1991-2020 par département (4 métriques)
│   ├── observations_mensuelles.csv # Observations 2018-2024 par département
│   ├── anomalies.json              # Anomalies pré-calculées (4 métriques)
│   └── departements.json            # Liste des départements
├── backend/
│   ├── app.py                       # API Flask
│   ├── data_processing.py          # Pipeline de téléchargement + traitement
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
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
python backend/data_processing.py
```

Le script télécharge les fichiers mensuels Météo-France (~146 MB, mis en cache
dans `data/raw/`), agrège les stations par département, calcule les normales
1991-2020 et les observations 2018-2024, puis produit `anomalies.json`. Le
téléchargement n'a lieu qu'une seule fois ; les exécutions suivantes réutilisent
le cache.

Source : [données climatologiques de base mensuelles](https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-mensuelles)
de Météo-France, Licence Ouverte 2.0.

### 3. Lancer l'API

```bash
python backend/app.py
```

L'API démarre sur `http://localhost:5000`.

### 4. Lancer le frontend

Ouvrir `frontend/index.html` dans un navigateur, ou servir le dossier :

```bash
python -m http.server 8000 --directory frontend
```

Puis ouvrir `http://localhost:8000`.

## Métriques

| Métrique | Champ | Unité | Source Météo-France |
|----------|-------|-------|---------------------|
| Température moyenne | `temperature` | °C | TM |
| Précipitations (cumul) | `precipitation` | mm | RR |
| Ensoleillement (durée) | `ensoleillement` | h | INST (converti de minutes) |
| Vent moyen à 10 m | `vent` | m/s | FFM |

## API

| Endpoint | Paramètres | Description |
|----------|------------|-------------|
| `GET /api/departements` | — | Liste des départements |
| `GET /api/annees` | — | Années disponibles |
| `GET /api/metrics` | — | Liste des métriques (libellés, unités, champs) |
| `GET /api/anomalie` | `departement`, `mois`, `annee` | Données pour un point |
| `GET /api/anomalies` | `departement` | Série complète d'un département |

Exemple :

```
GET /api/anomalies?departement=Gironde
```

```json
{
  "departement": "Gironde",
  "mois": 7,
  "annee": 2023,
  "temperature": 21.7,
  "normale_temperature": 21.2,
  "anomalie_temperature": 0.5,
  "precipitation": 28.0,
  "normale_precipitation": 46.3,
  "anomalie_precipitation": -18.3,
  "ensoleillement": 242.8,
  "normale_ensoleillement": 262.8,
  "anomalie_ensoleillement": -20.0,
  "vent": 2.8,
  "normale_vent": 2.8,
  "anomalie_vent": 0.0
}
```

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

## Déploiement

- **Backend** : Render ou PythonAnywhere (web service Python).
- **Frontend** : GitHub Pages ou Netlify (site statique).
- Mettre à jour `API_BASE` dans `frontend/script.js` avec l'URL de l'API
  déployée.

## Notes

- Les données sont agrégées par département (moyenne des stations).
- La Corse (fichier unifié 20) est séparée en Corse-du-Sud (2A) et Haute-Corse
  (2B) par latitude.
- Mayotte (976) n'a pas de données mensuelles disponibles.
- Les normales sont calculées sur la période 1991-2020, les observations sur
  2018-2024.
