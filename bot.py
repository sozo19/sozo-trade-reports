"""Sozo Trade Bot — bot Telegram qui trade TON/USDT depuis ton wallet Telegram.

Fonctionnement :
  1. /connecter lie ton wallet Telegram (TON Space) au bot via TON Connect.
  2. /acheter, /vendre ou les boutons de /signal preparent un swap sur STON.fi.
  3. Chaque transaction doit etre confirmee PAR TOI dans le wallet Telegram —
     le bot ne detient jamais tes cles privees.

Lancement : python bot.py  (variables d'environnement : voir .env.example)
"""
import asyncio
import html
import logging

from pytonconnect.exceptions import TonConnectError, UserRejectsError
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

import generate_report
from sozo_bot import config, signals, swap, wallet

logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("sozo_bot")

CONNECT_TIMEOUT = 240  # secondes pour approuver la connexion dans le wallet
TX_TIMEOUT = 300       # secondes pour approuver une transaction dans le wallet


def _authorized(update: Update) -> bool:
    chat = update.effective_chat
    return chat is not None and chat.id in config.AUTHORIZED_CHAT_IDS


async def _deny(update: Update) -> None:
    chat_id = update.effective_chat.id if update.effective_chat else "?"
    if not config.AUTHORIZED_CHAT_IDS:
        await update.effective_message.reply_text(
            "⛔ Aucun utilisateur autorisé n'est configuré.\n\n"
            f"Ton chat_id est : {chat_id}\n"
            "Ajoute la variable d'environnement AUTHORIZED_CHAT_IDS avec cette valeur "
            "puis relance le bot."
        )
    else:
        await update.effective_message.reply_text("⛔ Tu n'es pas autorisé à utiliser ce bot.")


# ---------------------------------------------------------------- commandes

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    await update.effective_message.reply_text(
        "👋 Salut ! Je suis <b>Sozo Trade Bot</b>.\n\n"
        "Je peux trader TON/USDT directement depuis ton wallet Telegram (TON Space), "
        "via STON.fi. Chaque trade doit être confirmé par toi dans le wallet : "
        "je ne détiens jamais tes clés.\n\n"
        "<b>Commandes</b>\n"
        "/connecter — lier ton wallet Telegram\n"
        "/wallet — adresse et soldes (TON, USDT)\n"
        "/prix — prix actuel TON/USDT\n"
        "/signal — signal de trading généré par Claude\n"
        "/acheter 10 — acheter du TON avec 10 USDT\n"
        "/vendre 2 — vendre 2 TON contre des USDT\n"
        "/rapport — rapport de marché quotidien (PDF)\n"
        "/deconnecter — délier le wallet\n\n"
        f"Ton chat_id : <code>{chat_id}</code>\n\n"
        "<i>À titre informatif — pas un conseil financier.</i>",
        parse_mode=ParseMode.HTML,
    )


async def cmd_aide(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await cmd_start(update, context)


async def cmd_connecter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    chat_id = update.effective_chat.id
    connector = await wallet.restore(chat_id)
    address = wallet.wallet_address(connector)
    if address:
        return await update.effective_message.reply_text(
            f"✅ Wallet déjà connecté :\n{address}\n\nUtilise /deconnecter pour le délier."
        )

    tg_wallet = wallet.find_telegram_wallet()
    if tg_wallet is None:
        return await update.effective_message.reply_text(
            "❌ Impossible de récupérer la configuration du wallet Telegram. Réessaie plus tard."
        )

    url = await connector.connect(tg_wallet)
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔗 Ouvrir mon wallet Telegram", url=url)]]
    )
    msg = await update.effective_message.reply_text(
        "Appuie sur le bouton puis <b>confirme la connexion</b> dans ton wallet Telegram.\n"
        f"J'attends ta confirmation ({CONNECT_TIMEOUT // 60} min max)…",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )

    async def wait_connection():
        try:
            await asyncio.wait_for(connector.wait_for_connection(), timeout=CONNECT_TIMEOUT)
        except asyncio.TimeoutError:
            return await msg.reply_text("⏱ Temps écoulé — relance /connecter pour réessayer.")
        address = wallet.wallet_address(connector)
        if address:
            await msg.reply_text(f"✅ Wallet connecté !\n{address}\n\nEssaie /wallet ou /signal.")
        else:
            await msg.reply_text("❌ Connexion refusée ou échouée. Relance /connecter.")

    context.application.create_task(wait_connection())


async def cmd_deconnecter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    connector = await wallet.restore(update.effective_chat.id)
    if connector.connected:
        try:
            await connector.disconnect()
        except Exception:
            logger.exception("Erreur lors de la deconnexion")
    await update.effective_message.reply_text("🔌 Wallet déconnecté.")


async def cmd_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    connector = await wallet.restore(update.effective_chat.id)
    address = wallet.wallet_address(connector)
    if not address:
        return await update.effective_message.reply_text(
            "Aucun wallet connecté. Utilise /connecter d'abord."
        )
    try:
        balances = await wallet.get_balances(address)
    except Exception:
        logger.exception("Lecture des soldes impossible")
        return await update.effective_message.reply_text(
            f"Adresse : {address}\n⚠️ Impossible de lire les soldes pour le moment."
        )
    await update.effective_message.reply_text(
        "👛 <b>Ton wallet Telegram</b>\n"
        f"<code>{address}</code>\n\n"
        f"💎 TON : {balances['ton']:.4f}\n"
        f"💵 USDT : {balances['usdt']:.2f}\n\n"
        f"<a href=\"https://tonviewer.com/{address}\">Voir sur Tonviewer</a>",
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def cmd_prix(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    try:
        quote = await swap.get_quote(swap.TON_TO_USDT, 1.0)
    except Exception:
        logger.exception("Devis prix impossible")
        return await update.effective_message.reply_text(
            "⚠️ Impossible de récupérer le prix sur STON.fi pour le moment."
        )
    await update.effective_message.reply_text(
        f"💎 1 TON ≈ {quote['ask_amount']:.4f} USDT (STON.fi)\n"
        f"Impact prix pour 1 TON : {quote.get('price_impact', '?')}"
    )


def _parse_amount(args: list[str]) -> float | None:
    if not args:
        return None
    try:
        amount = float(args[0].replace(",", "."))
    except ValueError:
        return None
    return amount if amount > 0 else None


async def _propose_trade(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         direction: str, amount: float) -> None:
    """Affiche le devis et demande confirmation avant d'envoyer au wallet."""
    chat_id = update.effective_chat.id
    connector = await wallet.restore(chat_id)
    address = wallet.wallet_address(connector)
    if not address:
        return await update.effective_message.reply_text(
            "Aucun wallet connecté. Utilise /connecter d'abord."
        )

    if direction == swap.USDT_TO_TON and amount > config.MAX_SWAP_USDT:
        return await update.effective_message.reply_text(
            f"⛔ Plafond de sécurité : {config.MAX_SWAP_USDT:g} USDT max par swap "
            "(modifiable via MAX_SWAP_USDT)."
        )
    if direction == swap.TON_TO_USDT and amount > config.MAX_SWAP_TON:
        return await update.effective_message.reply_text(
            f"⛔ Plafond de sécurité : {config.MAX_SWAP_TON:g} TON max par swap "
            "(modifiable via MAX_SWAP_TON)."
        )

    try:
        quote = await swap.get_quote(direction, amount)
    except Exception:
        logger.exception("Devis STON.fi impossible")
        return await update.effective_message.reply_text(
            "⚠️ Impossible d'obtenir un devis STON.fi. Réessaie dans un instant."
        )

    if direction == swap.USDT_TO_TON:
        desc = (f"🟢 <b>Achat</b> : {amount:g} USDT → ≈ {quote['ask_amount']:.4f} TON\n"
                f"Minimum garanti : {quote['min_ask_amount']:.4f} TON")
    else:
        desc = (f"🔴 <b>Vente</b> : {amount:g} TON → ≈ {quote['ask_amount']:.2f} USDT\n"
                f"Minimum garanti : {quote['min_ask_amount']:.2f} USDT")

    context.chat_data["pending_trade"] = {"direction": direction, "amount": amount}
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Confirmer", callback_data="trade_confirm"),
        InlineKeyboardButton("❌ Annuler", callback_data="trade_cancel"),
    ]])
    await update.effective_message.reply_text(
        f"{desc}\n"
        f"Slippage toléré : {config.SLIPPAGE_BPS / 100:.2f} % | "
        f"Impact prix : {quote.get('price_impact', '?')}\n\n"
        "Confirmer ? La transaction sera ensuite à valider dans ton wallet Telegram.",
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )


async def cmd_acheter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    amount = _parse_amount(context.args)
    if amount is None:
        return await update.effective_message.reply_text(
            "Utilisation : /acheter <montant en USDT>\nExemple : /acheter 10"
        )
    await _propose_trade(update, context, swap.USDT_TO_TON, amount)


async def cmd_vendre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    amount = _parse_amount(context.args)
    if amount is None:
        return await update.effective_message.reply_text(
            "Utilisation : /vendre <montant en TON>\nExemple : /vendre 2"
        )
    await _propose_trade(update, context, swap.TON_TO_USDT, amount)


async def _execute_trade(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    pending = context.chat_data.pop("pending_trade", None)
    if not pending:
        return await query.edit_message_text("Ce trade a expiré. Relance /acheter ou /vendre.")

    chat_id = update.effective_chat.id
    connector = await wallet.restore(chat_id)
    address = wallet.wallet_address(connector)
    if not address:
        return await query.edit_message_text("Wallet déconnecté. Utilise /connecter puis réessaie.")

    await query.edit_message_text("🛠 Préparation de la transaction…")
    try:
        tx, quote = await swap.build_swap_tx(pending["direction"], pending["amount"], address)
    except Exception:
        logger.exception("Construction du swap impossible")
        return await query.edit_message_text(
            "❌ Impossible de préparer le swap (STON.fi ou réseau TON indisponible). Réessaie."
        )

    await query.edit_message_text(
        "📲 <b>Confirme la transaction dans ton wallet Telegram</b> "
        f"(tu as {TX_TIMEOUT // 60} minutes).",
        parse_mode=ParseMode.HTML,
    )

    async def wait_tx():
        try:
            await asyncio.wait_for(connector.send_transaction(tx), timeout=TX_TIMEOUT)
        except asyncio.TimeoutError:
            return await query.message.reply_text("⏱ Transaction non confirmée à temps — rien n'a été envoyé.")
        except UserRejectsError:
            return await query.message.reply_text("🚫 Transaction refusée dans le wallet — rien n'a été envoyé.")
        except TonConnectError:
            logger.exception("Erreur TON Connect pendant le swap")
            return await query.message.reply_text("❌ Erreur TON Connect pendant l'envoi. Réessaie.")
        except Exception:
            logger.exception("Erreur inattendue pendant le swap")
            return await query.message.reply_text("❌ Erreur inattendue pendant l'envoi. Réessaie.")
        await query.message.reply_text(
            "✅ <b>Swap envoyé sur la blockchain !</b>\n"
            "Il sera visible d'ici ~1 minute :\n"
            f"<a href=\"https://tonviewer.com/{address}\">Suivre sur Tonviewer</a>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        )

    context.application.create_task(wait_tx())


async def cmd_signal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    if not config.ANTHROPIC_API_KEY:
        return await update.effective_message.reply_text(
            "⚠️ ANTHROPIC_API_KEY manquante — impossible de générer un signal."
        )
    waiting = await update.effective_message.reply_text("🧠 Analyse du marché TON en cours…")
    try:
        data = await asyncio.to_thread(signals.fetch_signal)
    except Exception:
        logger.exception("Generation du signal impossible")
        return await waiting.edit_text("❌ Impossible de générer le signal. Réessaie plus tard.")

    buttons = []
    sig = data.get("signal")
    if sig == "ACHETER":
        amount = min(10.0, config.MAX_SWAP_USDT)
        buttons = [[InlineKeyboardButton(
            f"🟢 Acheter du TON ({amount:g} USDT)", callback_data=f"sig_buy:{amount:g}")]]
    elif sig == "VENDRE":
        amount = min(2.0, config.MAX_SWAP_TON)
        buttons = [[InlineKeyboardButton(
            f"🔴 Vendre {amount:g} TON", callback_data=f"sig_sell:{amount:g}")]]

    await waiting.edit_text(
        signals.format_signal(data),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
    )


async def cmd_rapport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _authorized(update):
        return await _deny(update)
    if not config.ANTHROPIC_API_KEY:
        return await update.effective_message.reply_text(
            "⚠️ ANTHROPIC_API_KEY manquante — impossible de générer le rapport."
        )
    waiting = await update.effective_message.reply_text(
        "📊 Génération du rapport en cours (1 à 2 minutes)…"
    )
    try:
        data = await asyncio.to_thread(generate_report.fetch, config.ANTHROPIC_API_KEY)
        pdf_path = await asyncio.to_thread(generate_report.build, data)
    except Exception:
        logger.exception("Generation du rapport impossible")
        return await waiting.edit_text("❌ Impossible de générer le rapport. Réessaie plus tard.")
    with open(pdf_path, "rb") as fh:
        await update.effective_message.reply_document(
            fh, caption="📊 Sozo Trade — rapport du jour"
        )
    await waiting.delete()


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    if not _authorized(update):
        return await query.edit_message_text("⛔ Non autorisé.")

    data = query.data or ""
    if data == "trade_confirm":
        await _execute_trade(update, context)
    elif data == "trade_cancel":
        context.chat_data.pop("pending_trade", None)
        await query.edit_message_text("Trade annulé. 👍")
    elif data.startswith("sig_buy:") or data.startswith("sig_sell:"):
        try:
            amount = float(data.split(":", 1)[1])
        except ValueError:
            return await query.message.reply_text("Montant invalide.")
        direction = swap.USDT_TO_TON if data.startswith("sig_buy:") else swap.TON_TO_USDT
        await _propose_trade(update, context, direction, amount)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Erreur non geree", exc_info=context.error)


def main() -> None:
    if not config.BOT_TOKEN:
        raise SystemExit(
            "TELEGRAM_BOT_TOKEN manquant. Cree un bot via @BotFather puis exporte le token "
            "(voir .env.example)."
        )
    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .concurrent_updates(True)
        .build()
    )
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler(["aide", "help"], cmd_aide))
    app.add_handler(CommandHandler("connecter", cmd_connecter))
    app.add_handler(CommandHandler("deconnecter", cmd_deconnecter))
    app.add_handler(CommandHandler("wallet", cmd_wallet))
    app.add_handler(CommandHandler("prix", cmd_prix))
    app.add_handler(CommandHandler("signal", cmd_signal))
    app.add_handler(CommandHandler("acheter", cmd_acheter))
    app.add_handler(CommandHandler("vendre", cmd_vendre))
    app.add_handler(CommandHandler("rapport", cmd_rapport))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_error_handler(on_error)

    logger.info("Sozo Trade Bot démarré (testnet=%s)", config.IS_TESTNET)
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
