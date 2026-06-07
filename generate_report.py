import anthropic, os, json, re
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak

REPORTS_DIR = Path("/tmp")
GREEN = colors.HexColor("#00d68f")
RED = colors.HexColor("#ff4d6d")
GOLD = colors.HexColor("#f0b429")
BLUE = colors.HexColor("#4da6ff")
PANEL = colors.HexColor("#0d1520")
MUTED = colors.HexColor("#4a5568")
LIGHT = colors.HexColor("#c9d1d9")
WHITE = colors.white

def st(name, **kw):
    base = getSampleStyleSheet()["Normal"]
    return ParagraphStyle(name, parent=base, **kw)

def fetch(api_key):
    today = datetime.now().strftime("%A %d %B %Y")
    hour = datetime.now().strftime("%H:%M")
    print(f"Analyse complete du {today} a {hour}...")
    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Tu es analyste financier senior pour Capital.com avec acces aux donnees en temps reel.
Aujourd hui: {today} a {hour} CET.

Fais une recherche web COMPLETE et FIABLE sur:
1. Toutes les actualites macro-economiques importantes du jour
2. Les prix ACTUELS de tous ces instruments
3. Les evenements qui peuvent creer des opportunites intraday

INSTRUMENTS FAVORIS a analyser en priorite:
- US 500 (S&P500)
- USD/JPY
- Brent Oil Spot
- Gold (XAU/USD)
- Germany 40 (DAX)

AUTRES MARCHES a surveiller pour opportunites:
- EUR/USD, GBP/USD, EUR/GBP
- Nasdaq 100, Dow Jones
- Silver (XAG/USD), Natural Gas
- USD/CHF, AUD/USD
- France 40 (CAC40), Japan 225

Pour chaque opportunite identifiee (favoris ET autres marches), fournis:
- Prix exact actuel
- Signal clair (ACHETER/VENDRE/ATTENDRE)
- Score de fiabilite de 1 a 10
- Entree precise, Stop Loss, Take Profit
- Taille de position pour 100 CHF avec risque de 1 CHF
- Horizon temporel (intraday/court terme/moyen terme)
- Catalyseur principal

Reponds UNIQUEMENT en JSON valide sans markdown:
{{
  "date": "{today}",
  "heure": "{hour}",
  "sentiment_global": "HAUSSIER ou NEUTRE ou BAISSIER",
  "resume_executif": "analyse complete et fiable en 4-5 phrases avec chiffres reels",
  "actualites_cles": ["news importante 1 avec impact", "news 2", "news 3", "news 4"],
  "calendrier_economique": "evenements du jour et de la semaine avec heures CET",
  "instruments_favoris": [
    {{
      "nom": "US 500",
      "prix": 7383.74,
      "variation_jour": "-2.64%",
      "variation_semaine": "-3.1%",
      "tendance": "BAISSIER",
      "signal": "VENDRE",
      "score_fiabilite": 8,
      "conviction": "FORTE",
      "entree": 7383.74,
      "sl": 7450.00,
      "tp": 7250.00,
      "rr": "1:2",
      "taille_100chf": "0.015 CFD = risque 1 CHF",
      "horizon": "Court terme 2-3 jours",
      "catalyseur": "raison principale du signal",
      "support": 7200.0,
      "resistance": 7500.0,
      "analyse": "analyse technique et fondamentale detaillee en 3-4 phrases"
    }}
  ],
  "opportunites_autres_marches": [
    {{
      "nom": "EUR/USD",
      "prix": 1.0850,
      "variation_jour": "+0.15%",
      "signal": "ACHETER",
      "score_fiabilite": 7,
      "conviction": "MOYENNE",
      "entree": 1.0850,
      "sl": 1.0800,
      "tp": 1.0950,
      "rr": "1:2",
      "taille_100chf": "0.02 lot micro = risque 1 CHF",
      "horizon": "Intraday",
      "catalyseur": "raison du signal",
      "analyse": "pourquoi cette opportunite maintenant"
    }}
  ],
  "top3_opportunites_du_jour": [
    {{
      "rang": 1,
      "instrument": "nom",
      "direction": "LONG ou SHORT",
      "score": 9,
      "raison": "pourquoi cest la meilleure opportunite"
    }}
  ],
  "opportunites_intraday": [
    {{
      "heure_cible": "14:30 CET",
      "instrument": "US 500",
      "evenement": "ouverture Wall Street",
      "strategie": "ce quil faut faire et pourquoi",
      "direction": "LONG ou SHORT"
    }}
  ],
  "risques_majeurs": ["risque 1 avec detail", "risque 2", "risque 3"],
  "conseil_100chf": "plan detaille pour trader aujourd hui avec 100 CHF, quoi faire exactement",
  "marches_eviter": ["instrument a eviter avec raison"]
}}"""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in response.content if hasattr(b, "text"))
    text = text.replace("```json","").replace("```","").strip()
    data = json.loads(text[text.find("{"):text.rfind("}")+1])
    print(f"Sentiment: {data.get('sentiment_global')} | {len(data.get('instruments_favoris',[]))} favoris | {len(data.get('opportunites_autres_marches',[]))} autres opportunites")
    return data

def score_color(score):
    if score >= 8: return GREEN
    if score >= 6: return GOLD
    return RED

def score_text(score):
    if score >= 8: return "EXCELLENT"
    if score >= 6: return "BON"
    return "FAIBLE"

def build(data):
    date_str = datetime.now().strftime("%Y-%m-%d")
    sent = data.get("sentiment_global","NEUTRE")
    sc = GREEN if sent=="HAUSSIER" else (RED if sent=="BAISSIER" else GOLD)
    out = REPORTS_DIR / f"rapport-{date_str}.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=12*mm, bottomMargin=12*mm)
    story = []
    W = 180*mm

    # ── HEADER ──────────────────────────────────────────────────────────────
    header = Table([[
        Paragraph("SOZO TRADE", st("logo", fontSize=18, textColor=GREEN, fontName="Helvetica-Bold")),
        Paragraph(f"Rapport du {data.get('date','')} a {data.get('heure','')}", st("date", fontSize=9, textColor=MUTED, alignment=2)),
    ]], colWidths=["60%","40%"])
    header.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),PANEL),
        ("ROWPADDING",(0,0),(-1,-1),12),
        ("LINEBELOW",(0,0),(-1,-1),2,GREEN),
    ]))
    story.append(header)
    story.append(Spacer(1,4*mm))

    # ── SENTIMENT + RESUME ───────────────────────────────────────────────────
    sent_table = Table([[
        [Paragraph("SENTIMENT GLOBAL", st("sl1", fontSize=8, textColor=MUTED)),
         Paragraph(sent, st("sv1", fontSize=16, textColor=sc, fontName="Helvetica-Bold"))],
        [Paragraph("CAPITAL", st("sl2", fontSize=8, textColor=MUTED)),
         Paragraph("100 CHF", st("sv2", fontSize=16, textColor=WHITE, fontName="Helvetica-Bold"))],
        [Paragraph("RISQUE/TRADE", st("sl3", fontSize=8, textColor=MUTED)),
         Paragraph("1 CHF (1%)", st("sv3", fontSize=16, textColor=GOLD, fontName="Helvetica-Bold"))],
    ]], colWidths=["33%","33%","34%"])
    sent_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),PANEL),
        ("ROWPADDING",(0,0),(-1,-1),10),
        ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#1a2535")),
    ]))
    story.append(sent_table)
    story.append(Spacer(1,4*mm))

    story.append(Paragraph("RESUME EXECUTIF", st("rl", fontSize=8, textColor=MUTED)))
    story.append(Paragraph(data.get("resume_executif",""), st("rb", fontSize=10, textColor=LIGHT, leading=16)))
    story.append(Spacer(1,3*mm))

    # ── ACTUALITES CLES ──────────────────────────────────────────────────────
    if data.get("actualites_cles"):
        story.append(Paragraph("ACTUALITES CLES DU JOUR", st("al", fontSize=8, textColor=MUTED)))
        for news in data["actualites_cles"]:
            story.append(Paragraph(f"► {news}", st(f"ni{hash(news)%9999}", fontSize=9, textColor=LIGHT, leading=14, leftIndent=5)))
        story.append(Spacer(1,3*mm))

    # ── CALENDRIER ───────────────────────────────────────────────────────────
    if data.get("calendrier_economique"):
        cal_box = Table([[Paragraph(f"CALENDRIER: {data['calendrier_economique']}", st("cal", fontSize=9, textColor=GOLD, leading=14))]])
        cal_box.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#1a1400")),("ROWPADDING",(0,0),(-1,-1),8),("LINELEFT",(0,0),(0,-1),3,GOLD)]))
        story.append(cal_box)
        story.append(Spacer(1,4*mm))

    # ── TOP 3 OPPORTUNITES ───────────────────────────────────────────────────
    if data.get("top3_opportunites_du_jour"):
        story.append(PageBreak())
        story.append(Paragraph("TOP 3 MEILLEURES OPPORTUNITES DU JOUR", st("top_h", fontSize=12, textColor=GREEN, fontName="Helvetica-Bold")))
        story.append(Spacer(1,3*mm))
        for op in data["top3_opportunites_du_jour"]:
            dc = GREEN if op.get("direction")=="LONG" else RED
            score = op.get("score",0)
            top_row = Table([[
                Paragraph(f"#{op.get('rang','')} {op.get('instrument','')}", st(f"tr{op.get('rang',0)}", fontSize=14, textColor=WHITE, fontName="Helvetica-Bold")),
                Paragraph(op.get("direction",""), st(f"td{op.get('rang',0)}", fontSize=14, textColor=dc, fontName="Helvetica-Bold")),
                Paragraph(f"Score: {score}/10 — {score_text(score)}", st(f"ts{op.get('rang',0)}", fontSize=11, textColor=score_color(score), fontName="Helvetica-Bold")),
            ],[
                Paragraph(op.get("raison",""), st(f"tra{op.get('rang',0)}", fontSize=10, textColor=LIGHT, leading=14)),
                Paragraph("","e1"),
                Paragraph("","e2"),
            ]], colWidths=["40%","20%","40%"])
            top_row.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,-1),PANEL),
                ("ROWPADDING",(0,0),(-1,-1),10),
                ("LINELEFT",(0,0),(0,-1),4,dc),
                ("SPAN",(0,1),(2,1)),
            ]))
            story.append(top_row)
            story.append(Spacer(1,4*mm))

    # ── INSTRUMENTS FAVORIS ──────────────────────────────────────────────────
    story.append(Paragraph("VOS 5 INSTRUMENTS FAVORIS", st("fav_h", fontSize=12, textColor=GREEN, fontName="Helvetica-Bold")))
    story.append(Spacer(1,3*mm))

    for i, inst in enumerate(data.get("instruments_favoris",[])):
        signal = str(inst.get("signal","ATTENDRE"))
        conviction = str(inst.get("conviction","MOYENNE"))
        score = inst.get("score_fiabilite", 5)
        sc2 = GREEN if signal=="ACHETER" else (RED if signal=="VENDRE" else GOLD)
        cc = GREEN if conviction=="FORTE" else (GOLD if conviction=="MOYENNE" else MUTED)
        vc = GREEN if "+" in str(inst.get("variation_jour","")) else RED

        story.append(Spacer(1,4*mm))

        # Ligne 1 — Nom + Prix + Signal
        t1 = Table([[
            Paragraph(str(inst.get("nom","")), st(f"fn{i}", fontSize=14, textColor=WHITE, fontName="Helvetica-Bold")),
            [Paragraph(str(inst.get("prix","")), st(f"fp{i}", fontSize=14, textColor=WHITE, fontName="Helvetica-Bold")),
             Paragraph(str(inst.get("variation_jour","")), st(f"fv{i}", fontSize=10, textColor=vc))],
            Paragraph(f"SIGNAL: {signal}", st(f"fs{i}", fontSize=13, textColor=sc2, fontName="Helvetica-Bold")),
            Paragraph(f"Score: {score}/10", st(f"fsc{i}", fontSize=11, textColor=score_color(score), fontName="Helvetica-Bold")),
        ]], colWidths=["28%","22%","28%","22%"])
        t1.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),("ROWPADDING",(0,0),(-1,-1),10),("LINELEFT",(0,0),(0,-1),4,sc2),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
        story.append(t1)

        # Ligne 2 — Niveaux
        t2 = Table([[
            Paragraph(f"ENTREE\n{inst.get('entree','')}", st(f"fe{i}", fontSize=11, textColor=WHITE, fontName="Helvetica-Bold", leading=15)),
            Paragraph(f"STOP LOSS\n{inst.get('sl','')}", st(f"fsl{i}", fontSize=11, textColor=RED, fontName="Helvetica-Bold", leading=15)),
            Paragraph(f"TAKE PROFIT\n{inst.get('tp','')}", st(f"ftp{i}", fontSize=11, textColor=GREEN, fontName="Helvetica-Bold", leading=15)),
            Paragraph(f"R/R\n{inst.get('rr','')}", st(f"frr{i}", fontSize=11, textColor=GOLD, fontName="Helvetica-Bold", leading=15)),
            Paragraph(f"HORIZON\n{inst.get('horizon','')}", st(f"fh{i}", fontSize=9, textColor=BLUE, leading=13)),
        ]], colWidths=["18%","18%","20%","12%","32%"])
        t2.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#070b10")),("ROWPADDING",(0,0),(-1,-1),9),("GRID",(0,0),(-1,-1),0.3,PANEL)]))
        story.append(t2)

        # Ligne 3 — Analyse + Taille + Support/Resistance
        t3 = Table([[
            [Paragraph(str(inst.get("analyse","")), st(f"fa{i}", fontSize=9, textColor=LIGHT, leading=14)),
             Paragraph(f"Catalyseur: {inst.get('catalyseur','')}", st(f"fcat{i}", fontSize=9, textColor=GOLD, leading=13))],
            [Paragraph(f"Position: {inst.get('taille_100chf','')}", st(f"fsz{i}", fontSize=9, textColor=GOLD)),
             Spacer(1,2*mm),
             Paragraph(f"Support: {inst.get('support','')} | Resistance: {inst.get('resistance','')}", st(f"fsr{i}", fontSize=9, textColor=MUTED)),
             Spacer(1,2*mm),
             Paragraph(f"Conviction: {conviction}", st(f"fcv{i}", fontSize=9, textColor=cc, fontName="Helvetica-Bold"))],
        ]], colWidths=["65%","35%"])
        t3.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),("ROWPADDING",(0,0),(-1,-1),10),("VALIGN",(0,0),(-1,-1),"TOP")]))
        story.append(t3)

    # ── AUTRES MARCHES ───────────────────────────────────────────────────────
    if data.get("opportunites_autres_marches"):
        story.append(PageBreak())
        story.append(Paragraph("AUTRES OPPORTUNITES DE MARCHE", st("autres_h", fontSize=12, textColor=BLUE, fontName="Helvetica-Bold")))
        story.append(Paragraph("Instruments hors favoris avec potentiel aujourd'hui", st("autres_sub", fontSize=9, textColor=MUTED)))
        story.append(Spacer(1,4*mm))

        for i, inst in enumerate(data.get("opportunites_autres_marches",[])):
            signal = str(inst.get("signal","ATTENDRE"))
            score = inst.get("score_fiabilite", 5)
            sc2 = GREEN if signal=="ACHETER" else (RED if signal=="VENDRE" else GOLD)
            vc = GREEN if "+" in str(inst.get("variation_jour","")) else RED

            story.append(Spacer(1,3*mm))
            t1 = Table([[
                Paragraph(str(inst.get("nom","")), st(f"an{i}", fontSize=13, textColor=WHITE, fontName="Helvetica-Bold")),
                Paragraph(str(inst.get("prix","")), st(f"ap{i}", fontSize=13, textColor=WHITE, fontName="Helvetica-Bold")),
                Paragraph(f"{signal}", st(f"as{i}", fontSize=12, textColor=sc2, fontName="Helvetica-Bold")),
                Paragraph(f"Score: {score}/10", st(f"asc{i}", fontSize=10, textColor=score_color(score), fontName="Helvetica-Bold")),
            ]], colWidths=["28%","20%","26%","26%"])
            t1.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),("ROWPADDING",(0,0),(-1,-1),9),("LINELEFT",(0,0),(0,-1),3,sc2)]))
            story.append(t1)

            t2 = Table([[
                Paragraph(f"Entree: {inst.get('entree','')} | SL: {inst.get('sl','')} | TP: {inst.get('tp','')} | R/R: {inst.get('rr','')}", st(f"al{i}", fontSize=10, textColor=LIGHT)),
                Paragraph(inst.get("taille_100chf",""), st(f"asz{i}", fontSize=9, textColor=GOLD)),
            ]], colWidths=["65%","35%"])
            t2.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#070b10")),("ROWPADDING",(0,0),(-1,-1),8)]))
            story.append(t2)

            story.append(Table([[
                Paragraph(f"{inst.get('catalyseur','')} — {inst.get('analyse','')}", st(f"acat{i}", fontSize=9, textColor=LIGHT, leading=14)),
                Paragraph(f"Horizon: {inst.get('horizon','')}", st(f"ah{i}", fontSize=9, textColor=BLUE)),
            ]], colWidths=["75%","25%"]))

    # ── OPPORTUNITES INTRADAY ────────────────────────────────────────────────
    if data.get("opportunites_intraday"):
        story.append(Spacer(1,6*mm))
        story.append(Paragraph("OPPORTUNITES INTRADAY — A SURVEILLER AUJOURD'HUI", st("intra_h", fontSize=12, textColor=GOLD, fontName="Helvetica-Bold")))
        story.append(Spacer(1,3*mm))
        for op in data.get("opportunites_intraday",[]):
            dc = GREEN if op.get("direction")=="LONG" else (RED if op.get("direction")=="SHORT" else GOLD)
            intra = Table([[
                Paragraph(op.get("heure_cible",""), st(f"ih{hash(str(op))%9999}", fontSize=12, textColor=GOLD, fontName="Helvetica-Bold")),
                Paragraph(op.get("instrument",""), st(f"ii{hash(str(op))%9999}", fontSize=12, textColor=WHITE, fontName="Helvetica-Bold")),
                Paragraph(op.get("direction",""), st(f"id{hash(str(op))%9999}", fontSize=11, textColor=dc, fontName="Helvetica-Bold")),
            ],[
                Paragraph(op.get("evenement",""), st(f"ie{hash(str(op))%9999}", fontSize=9, textColor=MUTED)),
                Paragraph(op.get("strategie",""), st(f"is{hash(str(op))%9999}", fontSize=9, textColor=LIGHT, leading=13)),
                Paragraph("","ie2"),
            ]], colWidths=["20%","25%","55%"])
            intra.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,-1),PANEL),
                ("ROWPADDING",(0,0),(-1,-1),9),
                ("LINELEFT",(0,0),(0,-1),3,GOLD),
                ("SPAN",(1,1),(2,1)),
            ]))
            story.append(intra)
            story.append(Spacer(1,3*mm))

    # ── PAGE FINALE ──────────────────────────────────────────────────────────
    story.append(PageBreak())

    # Risques
    story.append(Paragraph("RISQUES MAJEURS A SURVEILLER", st("rh", fontSize=11, textColor=RED, fontName="Helvetica-Bold")))
    story.append(Spacer(1,3*mm))
    for r in data.get("risques_majeurs",[]):
        story.append(Paragraph(f"⚠ {r}", st(f"ri{abs(hash(r))%99999}", fontSize=10, textColor=LIGHT, leading=16)))

    # Marches a eviter
    if data.get("marches_eviter"):
        story.append(Spacer(1,4*mm))
        story.append(Paragraph("MARCHES A EVITER AUJOURD'HUI", st("ev_h", fontSize=11, textColor=RED, fontName="Helvetica-Bold")))
        story.append(Spacer(1,2*mm))
        for m in data["marches_eviter"]:
            story.append(Paragraph(f"✗ {m}", st(f"ev{abs(hash(m))%99999}", fontSize=10, textColor=RED, leading=16)))

    # Conseil 100 CHF
    story.append(Spacer(1,5*mm))
    conseil_box = Table([[
        [Paragraph("PLAN DE TRADING — 100 CHF", st("ch_label", fontSize=9, textColor=GOLD, fontName="Helvetica-Bold", spaceAfter=4)),
         Paragraph(data.get("conseil_100chf",""), st("ch_val", fontSize=10, textColor=LIGHT, leading=16))]
    ]])
    conseil_box.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#1a1400")),
        ("ROWPADDING",(0,0),(-1,-1),14),
        ("LINELEFT",(0,0),(0,-1),4,GOLD),
    ]))
    story.append(conseil_box)

    # Footer
    story.append(Spacer(1,5*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN))
    story.append(Spacer(1,2*mm))
    story.append(Paragraph(
        f"SOZO TRADE — Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')} par Claude AI (Anthropic) | "
        f"Sources: Investing.com, Bloomberg, Reuters, FXStreet | "
        f"A titre informatif uniquement — Pas un conseil financier — Le trading comporte des risques de perte en capital",
        st("ft", fontSize=7, textColor=MUTED, alignment=1)
    ))

    doc.build(story)
    print(f"PDF genere: {out}")
    return str(out)

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY","")
    if not api_key:
        api_key = input("Cle API: ").strip()
    data = fetch(api_key)
    pdf_path = build(data)
    print(f"Rapport OK: {pdf_path}")

if __name__ == "__main__":
    main()
