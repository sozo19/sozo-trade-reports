"""Construction des swaps TON <-> USDT sur STON.fi (DEX v2).

Le swap est prepare ici puis envoye au wallet Telegram via TON Connect :
rien ne part sans ta confirmation dans le wallet.
"""
import time
from base64 import urlsafe_b64encode

import httpx
from pytoniq_core import Address
from tonutils.client import ToncenterV3Client
from tonutils.jetton.dex.stonfi import StonfiRouterV2
from tonutils.jetton.dex.stonfi.v2.pton.constants import PTONAddresses

from . import config

STON_API = "https://api.ston.fi"

TON_TO_USDT = "ton_usdt"
USDT_TO_TON = "usdt_ton"


def pton_address() -> str:
    """Adresse pTON (representation du TON natif cote STON.fi v2)."""
    return PTONAddresses.TESTNET if config.IS_TESTNET else PTONAddresses.MAINNET


def to_units(amount: float, decimals: int) -> int:
    return int(round(amount * 10**decimals))


def from_units(units: int, decimals: int) -> float:
    return units / 10**decimals


async def simulate(offer_address: str, ask_address: str, units: int) -> dict:
    """Simule le swap via l'API STON.fi : prix, impact, minimum recu, routeur."""
    params = {
        "offer_address": offer_address,
        "ask_address": ask_address,
        "units": str(units),
        "slippage_tolerance": str(config.SLIPPAGE_BPS / 10000),
        "dex_v2": "true",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{STON_API}/v1/swap/simulate",
            params=params,
            headers={"Accept": "application/json"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"Simulation STON.fi impossible ({r.status_code}) : {r.text[:200]}")
        return r.json()


async def get_quote(direction: str, amount: float) -> dict:
    """Devis lisible pour un montant donne, avant confirmation."""
    if direction == TON_TO_USDT:
        offer, ask = pton_address(), config.USDT_MASTER
        units = to_units(amount, config.TON_DECIMALS)
        ask_decimals = config.USDT_DECIMALS
    elif direction == USDT_TO_TON:
        offer, ask = config.USDT_MASTER, pton_address()
        units = to_units(amount, config.USDT_DECIMALS)
        ask_decimals = config.TON_DECIMALS
    else:
        raise ValueError(f"Direction inconnue : {direction}")

    sim = await simulate(offer, ask, units)
    ask_units = int(sim.get("ask_units") or 0)
    min_ask_units = int(sim.get("min_ask_units") or 0)
    return {
        "direction": direction,
        "amount": amount,
        "offer_address": offer,
        "ask_address": ask,
        "offer_units": units,
        "ask_amount": from_units(ask_units, ask_decimals),
        "min_ask_amount": from_units(min_ask_units, ask_decimals),
        "min_ask_units": min_ask_units,
        "swap_rate": sim.get("swap_rate"),
        "price_impact": sim.get("price_impact"),
        "router_address": sim.get("router_address"),
    }


def _tx_message(to: Address, value: int, body) -> dict:
    return {
        "address": to.to_str(),
        "amount": str(value),
        "payload": urlsafe_b64encode(body.to_boc()).decode(),
    }


def make_tonconnect_tx(to: Address, value: int, body, ttl_seconds: int = 300) -> dict:
    """Formate la transaction pour pytonconnect.send_transaction."""
    return {
        "valid_until": int(time.time()) + ttl_seconds,
        "messages": [_tx_message(to, value, body)],
    }


async def build_swap_tx(direction: str, amount: float, user_address: str) -> tuple[dict, dict]:
    """Prepare la transaction de swap. Retourne (transaction TON Connect, devis)."""
    quote = await get_quote(direction, amount)
    if quote["min_ask_units"] <= 0:
        raise RuntimeError("Le devis STON.fi n'a pas renvoye de montant minimum — swap annule.")

    client = ToncenterV3Client(
        api_key=config.TONCENTER_API_KEY or None,
        is_testnet=config.IS_TESTNET,
    )
    try:
        router_addr = quote.get("router_address")
        router = StonfiRouterV2(
            client,
            router_address=Address(router_addr) if router_addr else None,
        )
        user = Address(user_address)

        if direction == TON_TO_USDT:
            to, value, body = await router.get_swap_ton_to_jetton_tx_params(
                user_wallet_address=user,
                receiver_address=user,
                ask_jetton_address=Address(config.USDT_MASTER),
                offer_amount=quote["offer_units"],
                min_ask_amount=quote["min_ask_units"],
                refund_address=user,
            )
        else:
            to, value, body = await router.get_swap_jetton_to_ton_tx_params(
                user_wallet_address=user,
                receiver_address=user,
                offer_jetton_address=Address(config.USDT_MASTER),
                offer_amount=quote["offer_units"],
                min_ask_amount=quote["min_ask_units"],
                refund_address=user,
            )
    finally:
        try:
            await client.close_session()
        except Exception:
            pass

    return make_tonconnect_tx(to, value, body), quote
