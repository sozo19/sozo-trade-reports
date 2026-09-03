"""Connexion au wallet Telegram (TON Space) via TON Connect + lecture des soldes.

Le bot ne detient JAMAIS de cle privee : il prepare les transactions et c'est
toi qui les confirmes dans ton wallet Telegram.
"""
import json
import logging
import os

import httpx
from pytoniq_core import Address
from pytonconnect import TonConnect
from pytonconnect.storage import IStorage

from . import config

logger = logging.getLogger(__name__)

TELEGRAM_WALLET_APP_NAME = "telegram-wallet"


class FileStorage(IStorage):
    """Persistance des sessions TON Connect sur disque, une par chat Telegram."""

    def __init__(self, chat_id: int):
        self._path = config.SESSIONS_DIR / f"{chat_id}.json"
        # La session contient la cle privee du canal TON Connect : lecture pour
        # le proprietaire uniquement (0700 sur le repertoire, 0600 sur le fichier).
        self._path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self._path.parent, 0o700)

    def _read(self) -> dict:
        try:
            return json.loads(self._path.read_text())
        except (OSError, ValueError):
            return {}

    def _write(self, data: dict) -> None:
        fd = os.open(self._path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write(json.dumps(data))

    async def set_item(self, key: str, value: str):
        data = self._read()
        data[key] = value
        self._write(data)

    async def get_item(self, key: str, default_value: str = None):
        return self._read().get(key, default_value)

    async def remove_item(self, key: str):
        data = self._read()
        data.pop(key, None)
        self._write(data)


_connectors: dict[int, TonConnect] = {}


def get_connector(chat_id: int) -> TonConnect:
    if chat_id not in _connectors:
        _connectors[chat_id] = TonConnect(
            manifest_url=config.MANIFEST_URL,
            storage=FileStorage(chat_id),
        )
    return _connectors[chat_id]


async def restore(chat_id: int) -> TonConnect:
    """Recupere le connecteur du chat et tente de restaurer une session existante."""
    connector = get_connector(chat_id)
    if not connector.connected:
        try:
            await connector.restore_connection()
        except Exception:
            logger.exception("Restauration de la session TON Connect impossible")
    return connector


def find_telegram_wallet() -> dict | None:
    """Retourne la config TON Connect du wallet Telegram (TON Space)."""
    try:
        wallets = TonConnect.get_wallets()
    except Exception:
        logger.exception("Liste des wallets TON Connect indisponible")
        return None
    for w in wallets:
        if w.get("app_name") == TELEGRAM_WALLET_APP_NAME:
            return w
    return None


def wallet_address(connector: TonConnect) -> str | None:
    """Adresse (format convivial, non-bounceable) du wallet connecte, ou None."""
    account = getattr(connector, "account", None)
    if connector.connected and account and account.address:
        return Address(account.address).to_str(is_bounceable=False)
    return None


def _toncenter_base() -> str:
    return (
        "https://testnet.toncenter.com/api/v3"
        if config.IS_TESTNET
        else "https://toncenter.com/api/v3"
    )


async def get_balances(address: str) -> dict:
    """Soldes TON natif + USDT du wallet, via l'API publique toncenter v3."""
    headers = {"X-API-Key": config.TONCENTER_API_KEY} if config.TONCENTER_API_KEY else {}
    base = _toncenter_base()
    ton_balance = 0.0
    usdt_balance = 0.0
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(
            f"{base}/accountStates",
            params={"address": address, "include_boc": "false"},
            headers=headers,
        )
        r.raise_for_status()
        accounts = r.json().get("accounts") or []
        if accounts:
            ton_balance = int(accounts[0].get("balance") or 0) / 10**config.TON_DECIMALS

        r2 = await client.get(
            f"{base}/jetton/wallets",
            params={
                "owner_address": address,
                "jetton_address": config.USDT_MASTER,
                "limit": 1,
            },
            headers=headers,
        )
        r2.raise_for_status()
        jw = r2.json().get("jetton_wallets") or []
        if jw:
            usdt_balance = int(jw[0].get("balance") or 0) / 10**config.USDT_DECIMALS

    return {"ton": ton_balance, "usdt": usdt_balance}
