#!/usr/bin/env bash
# Demarre Sozo Trade Bot avec la configuration du fichier .env.
# Usage :  bash start.sh
set -e
cd "$(dirname "$0")"

if [ ! -f .env ]; then
    echo "❌ Pas de fichier .env — lance d'abord :  bash install.sh"
    exit 1
fi
if [ ! -x venv/bin/python ]; then
    echo "❌ Environnement non installé — lance d'abord :  bash install.sh"
    exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

if [ -z "${AUTHORIZED_CHAT_IDS:-}" ]; then
    echo "ℹ️  AUTHORIZED_CHAT_IDS est vide : envoie /start au bot pour connaître ton chat_id,"
    echo "   puis mets-le dans .env et relance. En attendant, les commandes sensibles sont bloquées."
fi

echo "🚀 Démarrage de Sozo Trade Bot (Ctrl+C pour arrêter)…"
exec ./venv/bin/python bot.py
