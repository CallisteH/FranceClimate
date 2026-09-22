#!/usr/bin/env bash
# start.sh — Lance un serveur local pour visualiser le site statique.
set -euo pipefail

cd "$(dirname "$0")"

PORT="${1:-8000}"

echo "→ FranceClimate sur http://localhost:$PORT"
echo "  Ctrl-C pour arrêter."
echo ""

python3 -m http.server "$PORT" --directory frontend
