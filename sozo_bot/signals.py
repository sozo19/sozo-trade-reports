"""Signal de trading TON/USDT genere par Claude (recherche web incluse).

Appels synchrones (SDK Anthropic) : a lancer via asyncio.to_thread depuis le bot.
"""
import html
import json

import anthropic

from . import config

SIGNAL_PROMPT = """Tu es analyste crypto senior. Analyse le marche du TON (Toncoin) MAINTENANT
avec une recherche web complete (prix actuel TON/USDT, tendance, actualites TON/Telegram,
sentiment global crypto, niveaux techniques).

Contexte : je trade uniquement la paire TON/USDT depuis mon wallet Telegram (TON Space),
avec de petits montants. ACHETER = echanger des USDT contre du TON.
VENDRE = echanger du TON contre des USDT. ATTENDRE = ne rien faire.

Reponds UNIQUEMENT en JSON valide, sans texte autour :
{
  "signal": "ACHETER" | "VENDRE" | "ATTENDRE",
  "conviction": "FORTE" | "MOYENNE" | "FAIBLE",
  "score_fiabilite": 7,
  "prix_ton_usdt": 5.43,
  "variation_24h": "+2.1%",
  "support": 5.20,
  "resistance": 5.80,
  "horizon": "Court terme",
  "montant_suggere": "10 USDT",
  "raison": "resume en 1 phrase",
  "analyse": "analyse detaillee en francais, 3-4 phrases, avec les vrais chiffres du jour",
  "risques": ["risque 1", "risque 2"]
}
Remplace toutes les valeurs par les vraies donnees actuelles issues de ta recherche web."""


def fetch_signal() -> dict:
    """Interroge Claude pour un signal TON/USDT. Leve une exception si le JSON est invalide."""
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=2000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": SIGNAL_PROMPT}],
    )
    text = "".join(b.text for b in response.content if hasattr(b, "text"))
    text = text.replace("```json", "").replace("```", "").strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"Reponse sans JSON exploitable : {text[:200]}")
    return json.loads(text[start:end + 1])


def format_signal(data: dict) -> str:
    """Met en forme le signal pour un message Telegram (HTML)."""

    def esc(key, default="?"):
        return html.escape(str(data.get(key, default) or default))

    emoji = {"ACHETER": "🟢", "VENDRE": "🔴", "ATTENDRE": "🟡"}.get(data.get("signal", ""), "⚪")
    lines = [
        f"{emoji} <b>Signal TON/USDT : {esc('signal')}</b>",
        f"Conviction : {esc('conviction')} — fiabilité {esc('score_fiabilite')}/10",
        "",
        f"💰 Prix TON : {esc('prix_ton_usdt')} USDT ({esc('variation_24h')} sur 24h)",
        f"📉 Support : {esc('support')} | 📈 Résistance : {esc('resistance')}",
        f"⏱ Horizon : {esc('horizon')} | Montant suggéré : {esc('montant_suggere')}",
        "",
        f"<i>{esc('analyse', '')}</i>",
    ]
    risques = data.get("risques") or []
    if risques:
        lines.append("")
        lines.append("⚠️ Risques : " + " • ".join(html.escape(str(r)) for r in risques))
    lines.append("")
    lines.append("<i>À titre informatif — pas un conseil financier.</i>")
    return "\n".join(lines)
