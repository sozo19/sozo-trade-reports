#!/usr/bin/env bash
# Installation guidee de Sozo Trade Bot (Linux / macOS).
# Usage :  bash install.sh
set -e
cd "$(dirname "$0")"

echo "════════════════════════════════════════"
echo "   Installation de Sozo Trade Bot 🤖💎"
echo "════════════════════════════════════════"
echo

# --- Python ---
if command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    echo "❌ Python 3 est requis. Installe-le depuis https://www.python.org/downloads/ puis relance ce script."
    exit 1
fi
echo "✔ Python trouvé : $($PY --version)"

# --- Environnement virtuel + dépendances ---
if [ ! -d venv ]; then
    echo "→ Création de l'environnement virtuel…"
    $PY -m venv venv
fi
echo "→ Installation des dépendances (1-2 minutes)…"
./venv/bin/pip install --quiet --upgrade pip
./venv/bin/pip install --quiet -r requirements.txt
echo "✔ Dépendances installées"
echo

# --- Configuration (.env) ---
if [ -f .env ]; then
    echo "✔ Un fichier .env existe déjà — il est conservé."
    echo "  (supprime-le et relance ce script pour recommencer la configuration)"
else
    echo "Configuration — les valeurs sont enregistrées dans le fichier .env, qui reste sur cette machine."
    echo
    read -r -p "1/3 Token du bot Telegram (donné par @BotFather) : " BOT_TOKEN
    read -r -p "2/3 Clé API Anthropic (sk-ant-…) : " ANTHROPIC_KEY
    read -r -p "3/3 URL publique du manifest TON Connect (voir README, étape 2) : " MANIFEST_URL
    umask 077
    cat > .env <<EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
ANTHROPIC_API_KEY=$ANTHROPIC_KEY
TONCONNECT_MANIFEST_URL=$MANIFEST_URL
AUTHORIZED_CHAT_IDS=
EOF
    chmod 600 .env
    echo
    echo "✔ Fichier .env créé (permissions 600 : lisible par toi uniquement)"
fi

echo
echo "════════════════════════════════════════"
echo "Installation terminée ! Prochaines étapes :"
echo
echo "  1. Démarre le bot :        bash start.sh"
echo "  2. Dans Telegram, envoie /start à ton bot : il t'affiche ton chat_id."
echo "  3. Arrête le bot (Ctrl+C), ouvre .env et mets ce nombre dans"
echo "     AUTHORIZED_CHAT_IDS=…  puis relance :  bash start.sh"
echo "  4. Envoie /connecter au bot pour lier ton wallet Telegram."
echo "════════════════════════════════════════"
