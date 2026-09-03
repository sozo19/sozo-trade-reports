"""Configuration du bot Sozo Trade — tout vient des variables d'environnement."""
import os
from pathlib import Path


def _parse_chat_ids(raw: str) -> set[int]:
    ids = set()
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if part.lstrip("-").isdigit():
            ids.add(int(part))
    return ids


BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Seuls ces chat_ids peuvent utiliser les commandes sensibles (wallet, trades, rapports).
AUTHORIZED_CHAT_IDS = _parse_chat_ids(os.environ.get("AUTHORIZED_CHAT_IDS", ""))

# Manifest TON Connect : doit etre une URL publique (le wallet la lit pour afficher
# le nom de l'application au moment de la connexion).
MANIFEST_URL = os.environ.get(
    "TONCONNECT_MANIFEST_URL",
    "https://raw.githubusercontent.com/sozo19/sozo-trade-reports/main/tonconnect-manifest.json",
)

TONCENTER_API_KEY = os.environ.get("TONCENTER_API_KEY", "")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

# Garde-fous : montant maximum par swap.
MAX_SWAP_TON = float(os.environ.get("MAX_SWAP_TON", "25"))
MAX_SWAP_USDT = float(os.environ.get("MAX_SWAP_USDT", "50"))

# Slippage tolere, en points de base (100 = 1 %).
SLIPPAGE_BPS = int(os.environ.get("SLIPPAGE_BPS", "100"))

# Repertoire ou sont conservees les sessions TON Connect (une par chat).
SESSIONS_DIR = Path(os.environ.get("TC_SESSIONS_DIR", ".tc_sessions"))

IS_TESTNET = os.environ.get("TON_TESTNET", "").strip().lower() in ("1", "true", "oui", "yes")

# Jetton master USDT (Tether USD) sur TON mainnet — https://tonscan.com/EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs
USDT_MASTER = "EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs"

TON_DECIMALS = 9
USDT_DECIMALS = 6
