# FranceClimate — Anomalies de Température par Département

Application web affichant l'anomalie de température mensuelle d'un département
français par rapport à la normale climatique 1991-2020.

## Stack

| Composant | Technologie |
|-----------|-------------|
| Frontend | HTML / CSS / JS (vanilla) |
| Backend | Python + Flask |
| Données | CSV / JSON pré-calculés |
| Environnement | `uv` (gestion des dépendances Python) |

## Structure

```
FranceClimate/
├── data/
│   ├── normales_1991_2020.csv       # Normales mensuelles par département
│   ├── temperatures_mensuelles.csv  # Températures observées (2018-2024)
│   ├── anomalies.json               # Anomalies pré-calculées
│   └── departements.json            # Liste des départements
├── backend/
│   ├── app.py                       # API Flask
│   ├── data_processing.py           # Génération des données
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

Les fichiers sont écrits dans `/data`. Les données actuelles sont des
**échantillons synthétiques** réalistes. Pour les remplacer par les vraies
données Météo France :

1. Télécharger les normales 1991-2020 et les températures mensuelles depuis
   [data.gouv.fr](https://www.data.gouv.fr/datasets/donnees-climatologiques-de-base-mensuelles).
2. Nettoyer les CSV pour respecter le format attendu (voir ci-dessous).
3. Relancer `data_processing.py` (adapté) pour régénérer `anomalies.json`.

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

## API

| Endpoint | Paramètres | Description |
|----------|------------|-------------|
| `GET /api/departements` | — | Liste des départements |
| `GET /api/annees` | — | Années disponibles |
| `GET /api/anomalie` | `departement`, `mois`, `annee` | Anomalie pour un point |
| `GET /api/anomalies` | `departement` | Série complète d'un département |

Exemple :

```
GET /api/anomalie?departement=Gironde&mois=7&annee=2023
```

```json
{
  "departement": "Gironde",
  "mois": 7,
  "annee": 2023,
  "temperature_moyenne": 26.7,
  "normale_1991_2020": 25.0,
  "anomalie": 1.7
}
```

## Format des données attendu

### `normales_1991_2020.csv`

```csv
departement,mois,normale_1991_2020
Gironde,1,6.2
Gironde,2,7.1
```

### `temperatures_mensuelles.csv`

```csv
departement,mois,annee,temperature_moyenne
Gironde,7,2023,22.5
```

## Déploiement

- **Backend** : Render ou PythonAnywhere (web service Python).
- **Frontend** : GitHub Pages ou Netlify (site statique).
- Mettre à jour `API_BASE` dans `frontend/script.js` avec l'URL de l'API
  déployée.
