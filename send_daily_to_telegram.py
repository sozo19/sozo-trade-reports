"""Envoie le rapport PDF du jour sur Telegram (utilise par le workflow GitHub Actions).

Variables d'environnement : TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID.
Le PDF est cherche dans /tmp (la ou generate_report.py l'ecrit).
"""
import glob
import os
import sys

import httpx


def main() -> int:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID manquant — envoi Telegram ignore.")
        return 0

    pdfs = sorted(glob.glob("/tmp/rapport-*.pdf"))
    if not pdfs:
        print("Aucun PDF /tmp/rapport-*.pdf trouve.")
        return 1
    pdf_path = pdfs[-1]

    with open(pdf_path, "rb") as fh:
        r = httpx.post(
            f"https://api.telegram.org/bot{token}/sendDocument",
            data={
                "chat_id": chat_id,
                "caption": "📊 Sozo Trade — ton rapport quotidien est prêt !",
            },
            files={"document": (os.path.basename(pdf_path), fh, "application/pdf")},
            timeout=120,
        )
    if r.status_code != 200:
        print(f"Echec de l'envoi Telegram ({r.status_code}) : {r.text[:300]}")
        return 1
    print(f"Rapport envoye sur Telegram : {pdf_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
