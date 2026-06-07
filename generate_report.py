#!/usr/bin/env python3
"""
📊 Générateur de Rapport Quotidien des Marchés — Capital.com
Développé avec Claude AI (Anthropic)

Ce script génère chaque matin un rapport PDF complet avec :
- Analyse macro-économique et géopolitique
- Marchés actions (Nasdaq, S&P500, CAC40, DAX, Nikkei)
- Devises majeures (EUR/USD, GBP/USD, USD/JPY, USD/CHF)
- Matières premières (Or, Pétrole, Gaz)
- Stratégie de trading pour Capital.com
- Recommandations d'investissement du jour
"""

import anthropic
import os
import json
import re
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ─── CONFIGURATION ─────────────────────────────────────────────────────────
# 🔑 Mets ta clé API Anthropic ici (ou dans la variable d'environnement ANTHROPIC_API_KEY)
API_KEY = os.environ.get("ANTHROPIC_API_KEY", "METS_TA_CLE_ICI")

# 📁 Dossier où les rapports seront sauvegardés
REPORTS_DIR = Path.home() / "Documents" / "Rapports_Marches"

# 📈 Marchés à analyser
MARKETS = [
    "Macro-économie et géopolitique mondiale",
    "Nasdaq 100, S&P 500 (actions US)",
    "CAC 40, DAX, FTSE 100 (actions européennes)",
    "Nikkei, Hang Seng (actions asiatiques)",
    "EUR/USD, GBP/USD, USD/JPY, USD/CHF (devises)",
    "Or (XAU/USD), Pétrole (WTI/Brent), Gaz naturel",
]

# ─── COULEURS ───────────────────────────────────────────────────────────────
DARK = colors.HexColor("#070b10")
GREEN = colors.HexColor("#00d68f")
RED = colors.HexColor("#ff4d6d")
GOLD = colors.HexColor("#f0b429")
BLUE = colors.HexColor("#4da6ff")
LIGHT = colors.HexColor("#c9d1d9")
MUTED = colors.HexColor("#4a5568")
PANEL = colors.HexColor("#0d1520")
WHITE = colors.white


# ─── PROMPT ─────────────────────────────────────────────────────────────────
def build_prompt():
    today = datetime.now().strftime("%A %d %B %Y")
    markets_list = "\n".join(f"- {m}" for m in MARKETS)
    return f"""Tu es un analyste financier senior spécialisé dans le trading sur Capital.com.
Aujourd'hui nous sommes le {today}.

Utilise ta recherche web pour obtenir les données les plus récentes et génère un rapport d'analyse complet.

MARCHÉS À ANALYSER:
{markets_list}

Pour chaque marché, fournis:
- Les niveaux clés actuels (prix, variations du jour/semaine)
- Les catalyseurs importants (news, événements économiques)
- La tendance court terme (haussière/baissière/neutre)
- Les niveaux de support et résistance clés

STRATÉGIE CAPITAL.COM:
Propose 3 opportunités de trading concrètes pour aujourd'hui sur Capital.com avec:
- L'instrument exact (ex: EUR/USD, Gold, Nasdaq100)
- La direction (Long/Short)
- Le prix d'entrée suggéré
- Le Stop Loss
- Le Take Profit
- Le ratio risque/rendement
- La conviction (Forte/Moyenne/Faible)

VERDICT GLOBAL:
- Sentiment général du marché
- Les 3 secteurs/instruments les plus attractifs du jour
- Les 3 risques majeurs à surveiller

RÉPONDS UNIQUEMENT EN JSON VALIDE (pas de markdown, pas de backticks):
{{
  "date": "{today}",
  "sentiment_global": "HAUSSIER | NEUTRE | BAISSIER",
  "resume_executif": "3-4 phrases résumant l'essentiel",
  "sections": [
    {{
      "titre": "Macro & Géopolitique",
      "emoji": "🌍",
      "contenu": "analyse détaillée avec faits et chiffres",
      "tendance": "HAUSSIER | NEUTRE | BAISSIER"
    }}
  ],
  "opportunites_trading": [
    {{
      "instrument": "EUR/USD",
      "direction": "LONG | SHORT",
      "entree": 1.0850,
      "stop_loss": 1.0800,
      "take_profit": 1.0950,
      "ratio_rr": "1:2",
      "conviction": "FORTE | MOYENNE | FAIBLE",
      "justification": "raison courte"
    }}
  ],
  "top_instruments": ["instrument1", "instrument2", "instrument3"],
  "risques_majeurs": ["risque1", "risque2", "risque3"],
  "calendrier_economique": "événements importants du jour/semaine"
}}"""


# ─── API CALL ───────────────────────────────────────────────────────────────
def fetch_analysis():
    print("🔍 Connexion à Claude AI avec recherche web...")
    client = anthropic.Anthropic(api_key=API_KEY)

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": build_prompt()}],
    )

    full_text = "".join(
        block.text for block in response.content if hasattr(block, "text")
    )

    # Nettoyage robuste du JSON
    cleaned = re.sub(r"```json|```", "", full_text).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Format JSON invalide dans la réponse")

    return json.loads(cleaned[start:end + 1])


# ─── PDF BUILDER ────────────────────────────────────────────────────────────
def build_pdf(data: dict, output_path: Path):
    print(f"📄 Génération du PDF : {output_path.name}")

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    story = []

    # ── Styles ──────────────────────────────────────────────────────────────
    def style(name, **kw):
        base = getSampleStyleSheet()["Normal"]
        s = ParagraphStyle(name, parent=base, **kw)
        return s

    S_LABEL = style("label", fontSize=8, textColor=MUTED, spaceAfter=4, leading=10)
    S_TITLE = style("title", fontSize=28, textColor=WHITE, fontName="Helvetica-Bold", spaceAfter=4, leading=32)
    S_SUBTITLE = style("subtitle", fontSize=13, textColor=GREEN, fontName="Helvetica-Bold", spaceAfter=8)
    S_BODY = style("body", fontSize=10, textColor=LIGHT, leading=16, spaceAfter=6)
    S_SECTION = style("section", fontSize=13, textColor=WHITE, fontName="Helvetica-Bold", spaceAfter=6, spaceBefore=14)
    S_SMALL = style("small", fontSize=8, textColor=MUTED, leading=12)
    S_CENTER = style("center", fontSize=9, textColor=MUTED, alignment=TA_CENTER)

    date_str = data.get("date", datetime.now().strftime("%A %d %B %Y"))
    sentiment = data.get("sentiment_global", "NEUTRE")
    sent_color = GREEN if sentiment == "HAUSSIER" else (RED if sentiment == "BAISSIER" else GOLD)

    # ── Header ──────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("RAPPORT QUOTIDIEN DES MARCHÉS", style("hl", fontSize=8, textColor=MUTED, fontName="Helvetica")),
        Paragraph(f'<font color="#{sent_color.hexval()[2:]}">● {sentiment}</font>',
                  style("hr", fontSize=11, textColor=sent_color, alignment=TA_RIGHT, fontName="Helvetica-Bold")),
    ]]
    header_table = Table(header_data, colWidths=["60%", "40%"])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("ROWPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -1), 1, GREEN),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8 * mm))

    # ── Title ───────────────────────────────────────────────────────────────
    story.append(Paragraph("Analyse des Marchés", S_TITLE))
    story.append(Paragraph(f'Capital.com — {date_str}', S_SUBTITLE))
    story.append(HRFlowable(width="100%", thickness=1, color=PANEL))
    story.append(Spacer(1, 4 * mm))

    # ── Résumé exécutif ─────────────────────────────────────────────────────
    story.append(Paragraph("RÉSUMÉ EXÉCUTIF", S_LABEL))
    story.append(Paragraph(data.get("resume_executif", ""), S_BODY))
    story.append(Spacer(1, 4 * mm))

    # ── Calendrier économique ────────────────────────────────────────────────
    if data.get("calendrier_economique"):
        story.append(Paragraph("📅 CALENDRIER ÉCONOMIQUE", S_LABEL))
        story.append(Paragraph(data["calendrier_economique"], S_BODY))
        story.append(Spacer(1, 4 * mm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=MUTED))
    story.append(Spacer(1, 4 * mm))

    # ── Sections marchés ────────────────────────────────────────────────────
    story.append(Paragraph("ANALYSE DES MARCHÉS", S_LABEL))
    for section in data.get("sections", []):
        tendance = section.get("tendance", "NEUTRE")
        t_color = GREEN if tendance == "HAUSSIER" else (RED if tendance == "BAISSIER" else GOLD)
        header = f'{section.get("emoji", "📊")} {section.get("titre", "")}   <font color="#{t_color.hexval()[2:]}">[{tendance}]</font>'
        story.append(Paragraph(header, S_SECTION))
        story.append(Paragraph(section.get("contenu", ""), S_BODY))

    story.append(PageBreak())

    # ── Opportunités de trading ──────────────────────────────────────────────
    story.append(Paragraph("🎯 OPPORTUNITÉS DE TRADING — CAPITAL.COM", S_LABEL))
    story.append(Spacer(1, 3 * mm))

    for op in data.get("opportunites_trading", []):
        direction = op.get("direction", "LONG")
        dir_color = GREEN if direction == "LONG" else RED
        conv = op.get("conviction", "MOYENNE")
        conv_color = GREEN if conv == "FORTE" else (GOLD if conv == "MOYENNE" else MUTED)

        op_data = [
            [
                Paragraph(f'<b>{op.get("instrument", "")}</b>',
                          style("i", fontSize=14, textColor=WHITE, fontName="Helvetica-Bold")),
                Paragraph(f'<font color="#{dir_color.hexval()[2:]}"><b>{direction}</b></font>',
                          style("d", fontSize=14, textColor=dir_color, fontName="Helvetica-Bold", alignment=TA_RIGHT)),
            ],
            [
                Paragraph(op.get("justification", ""), style("j", fontSize=9, textColor=LIGHT, leading=13)),
                Paragraph(f'Conviction: <font color="#{conv_color.hexval()[2:]}">{conv}</font>',
                          style("c", fontSize=9, textColor=MUTED, alignment=TA_RIGHT)),
            ],
            [
                Table([[
                    Paragraph(f"Entrée\n<b>{op.get('entree', '')}</b>",
                              style("e", fontSize=9, textColor=LIGHT, leading=13, fontName="Helvetica")),
                    Paragraph(f"Stop Loss\n<font color='#ff4d6d'><b>{op.get('stop_loss', '')}</b></font>",
                              style("sl", fontSize=9, textColor=LIGHT, leading=13)),
                    Paragraph(f"Take Profit\n<font color='#00d68f'><b>{op.get('take_profit', '')}</b></font>",
                              style("tp", fontSize=9, textColor=LIGHT, leading=13)),
                    Paragraph(f"Ratio R/R\n<b>{op.get('ratio_rr', '')}</b>",
                              style("rr", fontSize=9, textColor=GOLD, leading=13, fontName="Helvetica-Bold")),
                ]], colWidths=["25%", "25%", "25%", "25%"]),
                "",
            ],
        ]

        op_table = Table(op_data, colWidths=["70%", "30%"])
        op_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), PANEL),
            ("ROWPADDING", (0, 0), (-1, -1), 10),
            ("SPAN", (0, 2), (1, 2)),
            ("LINELEFT", (0, 0), (0, -1), 3, dir_color),
            ("BOTTOMPADDING", (0, 2), (-1, 2), 12),
        ]))
        story.append(op_table)
        story.append(Spacer(1, 4 * mm))

    story.append(Spacer(1, 4 * mm))

    # ── Top instruments & risques ────────────────────────────────────────────
    bottom_data = [[
        # Top instruments
        [
            Paragraph("✅ TOP INSTRUMENTS DU JOUR", style("th", fontSize=9, textColor=GREEN, fontName="Helvetica-Bold")),
            Spacer(1, 2 * mm),
        ] + [
            Paragraph(f"▸ {inst}", style("ti", fontSize=10, textColor=LIGHT, leading=16))
            for inst in data.get("top_instruments", [])
        ],
        # Risques
        [
            Paragraph("⚠ RISQUES À SURVEILLER", style("rh", fontSize=9, textColor=RED, fontName="Helvetica-Bold")),
            Spacer(1, 2 * mm),
        ] + [
            Paragraph(f"▸ {r}", style("ri", fontSize=10, textColor=LIGHT, leading=16))
            for r in data.get("risques_majeurs", [])
        ],
    ]]

    # Flatten nested lists for table cells
    top_cell = [Paragraph("✅ TOP INSTRUMENTS DU JOUR", style("th2", fontSize=9, textColor=GREEN, fontName="Helvetica-Bold"))]
    top_cell += [Paragraph(f"▸ {inst}", style("ti2", fontSize=10, textColor=LIGHT, leading=16)) for inst in data.get("top_instruments", [])]

    risk_cell = [Paragraph("⚠ RISQUES À SURVEILLER", style("rh2", fontSize=9, textColor=RED, fontName="Helvetica-Bold"))]
    risk_cell += [Paragraph(f"▸ {r}", style("ri2", fontSize=10, textColor=LIGHT, leading=16)) for r in data.get("risques_majeurs", [])]

    summary_table = Table([[top_cell, risk_cell]], colWidths=["50%", "50%"])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PANEL),
        ("ROWPADDING", (0, 0), (-1, -1), 14),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBETWEEN", (0, 0), (1, 0), 1, MUTED),
    ]))
    story.append(summary_table)

    # ── Footer ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "⚠ À TITRE INFORMATIF UNIQUEMENT — PAS UN CONSEIL FINANCIER — "
        "Le trading comporte des risques, vous pouvez perdre tout votre capital. "
        f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} par Claude AI (Anthropic)",
        S_CENTER,
    ))

    doc.build(story)
    print(f"✅ PDF sauvegardé : {output_path}")


# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  📊 Générateur de Rapport Marchés — Capital.com")
    print("=" * 55)

    # Créer le dossier de rapports
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Dossier : {REPORTS_DIR}")

    # Nom du fichier avec la date
    date_str = datetime.now().strftime("%Y-%m-%d")
    output_path = REPORTS_DIR / f"rapport-marches-{date_str}.pdf"

    # Vérifier si le rapport du jour existe déjà
    if output_path.exists():
        print(f"ℹ️  Le rapport du {date_str} existe déjà.")
        resp = input("Regénérer ? (o/n) : ").strip().lower()
        if resp != "o":
            print("✅ Rapport existant conservé.")
            return

    try:
        # 1. Récupérer l'analyse
        data = fetch_analysis()
        print(f"✅ Analyse reçue — Sentiment : {data.get('sentiment_global', 'N/A')}")
        print(f"   {len(data.get('opportunites_trading', []))} opportunités de trading identifiées")

        # 2. Générer le PDF
        build_pdf(data, output_path)

        # 3. Ouvrir automatiquement le PDF
        os.system(f'open "{output_path}"')
        print("\n🎉 Rapport ouvert dans Aperçu !")

    except Exception as e:
        print(f"\n❌ Erreur : {e}")
        raise


if __name__ == "__main__":
    main()
