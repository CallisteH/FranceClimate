#!/usr/bin/env bash
# start.sh — Prépare l'environnement, génère les données si besoin,
# puis lance l'API Flask et le serveur frontend.
set -euo pipefail

cd "$(dirname "$0")"

API_PORT=5000
FRONTEND_PORT=8000
VENV_DIR=".venv"

# ---- 1. Environnement Python (uv) -------------------------------------------
if [ ! -d "$VENV_DIR" ]; then
    echo "→ Création de l'environnement virtuel…"
    uv venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

echo "→ Installation des dépendances…"
uv pip install -r backend/requirements.txt

# ---- 2. Génération des données (si absentes) --------------------------------
if [ ! -f "data/anomalies.json" ]; then
    echo "→ Données manquantes : génération via data_processing.py…"
    python backend/data_processing.py
else
    echo "→ Données déjà présentes (data/anomalies.json). Étape ignorée."
fi

# ---- 3. Démarrage de l'API Flask ---------------------------------------------
echo "→ Démarrage de l'API sur http://localhost:$API_PORT …"
python backend/app.py &
API_PID=$!

# ---- 4. Démarrage du serveur frontend ---------------------------------------
echo "→ Démarrage du frontend sur http://localhost:$FRONTEND_PORT …"
python -m http.server "$FRONTEND_PORT" --directory frontend &
FRONTEND_PID=$!

# ---- Arrêt propre sur Ctrl-C ------------------------------------------------
cleanup() {
    echo
    echo "→ Arrêt des serveurs…"
    kill "$API_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo ""
echo "FranceClimate est démarré :"
echo "  Frontend : http://localhost:$FRONTEND_PORT"
echo "  API      : http://localhost:$API_PORT"
echo "  Ctrl-C pour arrêter."
echo ""

wait
