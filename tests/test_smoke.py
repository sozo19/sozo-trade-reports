"""Tests hors-ligne (aucun reseau, aucune cle API requise).

Lancer depuis la racine du repo :  python -m pytest tests/ -v
"""
import asyncio
import json

from pytoniq_core import Address, begin_cell


def test_imports():
    import bot  # noqa: F401
    import generate_report  # noqa: F401
    from sozo_bot import config, signals, swap, wallet  # noqa: F401


def test_parse_chat_ids():
    from sozo_bot.config import _parse_chat_ids
    assert _parse_chat_ids("123, 456;-789") == {123, 456, -789}
    assert _parse_chat_ids("") == set()
    assert _parse_chat_ids("abc, 12x") == set()


def test_file_storage(tmp_path, monkeypatch):
    from sozo_bot import config, wallet
    monkeypatch.setattr(config, "SESSIONS_DIR", tmp_path)

    async def scenario():
        storage = wallet.FileStorage(chat_id=42)
        assert await storage.get_item("connection") is None
        assert await storage.get_item("connection", "def") == "def"
        await storage.set_item("connection", "abc")
        assert await storage.get_item("connection") == "abc"
        await storage.remove_item("connection")
        assert await storage.get_item("connection") is None

    asyncio.run(scenario())
    assert (tmp_path / "42.json").exists()


def test_make_tonconnect_tx():
    from sozo_bot import swap
    to = Address("EQCxE6mUtQJKFnGfaROTKOt1lZbDiiX1kCixRv7Nw2Id_sDs")
    body = begin_cell().store_uint(0, 32).end_cell()
    tx = swap.make_tonconnect_tx(to, 150_000_000, body)
    assert set(tx.keys()) == {"valid_until", "messages"}
    assert isinstance(tx["valid_until"], int)
    msg = tx["messages"][0]
    assert msg["address"] == to.to_str()
    assert msg["amount"] == "150000000"
    assert isinstance(msg["payload"], str) and len(msg["payload"]) > 0


def test_units_roundtrip():
    from sozo_bot import config, swap
    assert swap.to_units(1.5, config.TON_DECIMALS) == 1_500_000_000
    assert swap.to_units(10, config.USDT_DECIMALS) == 10_000_000
    assert swap.from_units(2_500_000, config.USDT_DECIMALS) == 2.5


def test_format_signal_escapes_html():
    from sozo_bot import signals
    data = {
        "signal": "ACHETER",
        "conviction": "FORTE",
        "score_fiabilite": 8,
        "prix_ton_usdt": 5.43,
        "variation_24h": "+2.1%",
        "support": 5.2,
        "resistance": 5.8,
        "horizon": "Court terme",
        "montant_suggere": "10 USDT",
        "analyse": "Cassure <b>test</b> & volume",
        "risques": ["Fed <hawkish>"],
    }
    text = signals.format_signal(data)
    assert "ACHETER" in text
    assert "<b>test</b>" not in text  # le HTML injecte doit etre echappe
    assert "&lt;b&gt;test&lt;/b&gt; &amp; volume" in text
    assert "&lt;hawkish&gt;" in text


def test_build_pdf_from_fixture(tmp_path, monkeypatch):
    import generate_report
    monkeypatch.setattr(generate_report, "REPORTS_DIR", tmp_path)
    data = {
        "date": "Lundi 1 Janvier 2026",
        "heure": "07:00",
        "sentiment_global": "HAUSSIER",
        "resume_executif": "Marche calme.",
        "actualites_cles": ["News 1"],
        "calendrier_economique": "Rien aujourd'hui",
        "instruments_favoris": [{
            "nom": "Gold", "prix": 4331.0, "variation_jour": "+1.0%", "signal": "ACHETER",
            "score_fiabilite": 8, "conviction": "FORTE", "entree": 4331.0, "sl": 4300.0,
            "tp": 4400.0, "rr": "1:2", "taille_100chf": "micro", "horizon": "Court terme",
            "catalyseur": "test", "support": 4300.0, "resistance": 4400.0, "analyse": "ok",
        }],
        "opportunites_autres_marches": [],
        "top3_opportunites_du_jour": [
            {"rang": 1, "instrument": "Gold", "direction": "LONG", "score": 9, "raison": "test"},
        ],
        "opportunites_intraday": [],
        "risques_majeurs": ["Risque test"],
        "conseil_100chf": "Prudence.",
        "marches_eviter": [],
    }
    pdf_path = generate_report.build(data)
    from pathlib import Path
    out = Path(pdf_path)
    assert out.exists() and out.stat().st_size > 1000
    assert out.suffix == ".pdf"
