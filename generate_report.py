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

def p(text, **kw):
    name = f"s{abs(hash(str(text)+str(kw)))%999999}"
    return Paragraph(str(text) if text else "", st(name, **kw))

def fetch(api_key):
    today = datetime.now().strftime("%A %d %B %Y")
    hour = datetime.now().strftime("%H:%M")
    print(f"Analyse du {today} a {hour}...")
    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""Tu es analyste financier senior pour Capital.com. Aujourd hui: {today} a {hour} CET.
Fais une recherche web complete et fiable. Reponds UNIQUEMENT en JSON valide:
{{
  "date": "{today}",
  "heure": "{hour}",
  "sentiment_global": "BAISSIER",
  "resume_executif": "analyse complete avec chiffres reels",
  "actualites_cles": ["news 1", "news 2", "news 3"],
  "calendrier_economique": "evenements importants avec heures CET",
  "instruments_favoris": [
    {{"nom":"US 500","prix":7383.74,"variation_jour":"-2.64%","signal":"VENDRE","score_fiabilite":8,"conviction":"FORTE","entree":7383.74,"sl":7450.00,"tp":7250.00,"rr":"1:2","taille_100chf":"0.015 CFD risque 1 CHF","horizon":"Court terme","catalyseur":"raison","support":7200.0,"resistance":7500.0,"analyse":"analyse detaillee"}},
    {{"nom":"USD/JPY","prix":160.29,"variation_jour":"+0.21%","signal":"ATTENDRE","score_fiabilite":6,"conviction":"FAIBLE","entree":160.29,"sl":159.50,"tp":161.50,"rr":"1:2","taille_100chf":"micro lot risque 1 CHF","horizon":"Intraday","catalyseur":"raison","support":159.0,"resistance":162.0,"analyse":"analyse"}},
    {{"nom":"Brent Oil","prix":94.66,"variation_jour":"-2.80%","signal":"VENDRE","score_fiabilite":7,"conviction":"MOYENNE","entree":94.66,"sl":96.00,"tp":92.00,"rr":"1:2","taille_100chf":"0.003 lot risque 1 CHF","horizon":"Court terme","catalyseur":"raison","support":90.0,"resistance":97.0,"analyse":"analyse"}},
    {{"nom":"Gold","prix":4331.0,"variation_jour":"-3.22%","signal":"VENDRE","score_fiabilite":8,"conviction":"FORTE","entree":4331.0,"sl":4380.0,"tp":4230.0,"rr":"1:2","taille_100chf":"micro oz risque 1 CHF","horizon":"Court terme","catalyseur":"raison","support":4200.0,"resistance":4450.0,"analyse":"analyse"}},
    {{"nom":"Germany 40","prix":24759.05,"variation_jour":"-0.75%","signal":"ATTENDRE","score_fiabilite":5,"conviction":"FAIBLE","entree":24759.05,"sl":25000.0,"tp":24200.0,"rr":"1:2","taille_100chf":"0.003 CFD risque 1 CHF","horizon":"Intraday","catalyseur":"raison","support":24000.0,"resistance":25200.0,"analyse":"analyse"}}
  ],
  "opportunites_autres_marches": [
    {{"nom":"EUR/USD","prix":1.0850,"variation_jour":"+0.15%","signal":"ACHETER","score_fiabilite":7,"conviction":"MOYENNE","entree":1.0850,"sl":1.0800,"tp":1.0950,"rr":"1:2","taille_100chf":"micro lot risque 1 CHF","horizon":"Intraday","catalyseur":"raison","analyse":"analyse"}},
    {{"nom":"Nasdaq 100","prix":19200.0,"variation_jour":"-1.5%","signal":"ATTENDRE","score_fiabilite":6,"conviction":"FAIBLE","entree":19200.0,"sl":19500.0,"tp":18800.0,"rr":"1:1.5","taille_100chf":"micro CFD risque 1 CHF","horizon":"Court terme","catalyseur":"raison","analyse":"analyse"}}
  ],
  "top3_opportunites_du_jour": [
    {{"rang":1,"instrument":"meilleur instrument","direction":"LONG ou SHORT","score":9,"raison":"pourquoi top 1"}},
    {{"rang":2,"instrument":"2eme","direction":"LONG","score":8,"raison":"pourquoi top 2"}},
    {{"rang":3,"instrument":"3eme","direction":"SHORT","score":7,"raison":"pourquoi top 3"}}
  ],
  "opportunites_intraday": [
    {{"heure_cible":"14:30 CET","instrument":"US 500","evenement":"ouverture Wall Street","strategie":"ce quil faut faire","direction":"LONG"}},
    {{"heure_cible":"08:00 CET","instrument":"EUR/USD","evenement":"ouverture Londres","strategie":"strategie","direction":"SHORT"}}
  ],
  "risques_majeurs": ["risque 1 avec detail", "risque 2", "risque 3"],
  "conseil_100chf": "plan detaille pour trader avec 100 CHF aujourd hui",
  "marches_eviter": ["marche a eviter avec raison"]
}}
Remplace TOUTES les valeurs par les vraies donnees du marche avec tes recherches web."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=8000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in response.content if hasattr(b, "text"))
    text = text.replace("```json","").replace("```","").strip()
    data = json.loads(text[text.find("{"):text.rfind("}")+1])
    print(f"Sentiment: {data.get('sentiment_global')}")
    return data

def score_color(score):
    if score >= 8: return GREEN
    if score >= 6: return GOLD
    return RED

def build(data):
    date_str = datetime.now().strftime("%Y-%m-%d")
    sent = data.get("sentiment_global","NEUTRE")
    sc = GREEN if sent=="HAUSSIER" else (RED if sent=="BAISSIER" else GOLD)
    out = REPORTS_DIR / f"rapport-{date_str}.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=15*mm, rightMargin=15*mm, topMargin=12*mm, bottomMargin=12*mm)
    story = []

    # HEADER
    story.append(p("SOZO TRADE — Rapport Quotidien des Marches", fontSize=16, textColor=GREEN, fontName="Helvetica-Bold"))
    story.append(p(f"{data.get('date','')} a {data.get('heure','')} CET | Capital.com", fontSize=9, textColor=MUTED))
    story.append(HRFlowable(width="100%", thickness=2, color=GREEN))
    story.append(Spacer(1,4*mm))

    # SENTIMENT
    sent_t = Table([[
        p(f"Sentiment: {sent}", fontSize=14, textColor=sc, fontName="Helvetica-Bold"),
        p("Capital: 100 CHF", fontSize=12, textColor=WHITE, fontName="Helvetica-Bold"),
        p("Risque max: 1 CHF/trade", fontSize=12, textColor=GOLD, fontName="Helvetica-Bold"),
    ]], colWidths=["34%","33%","33%"])
    sent_t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),("ROWPADDING",(0,0),(-1,-1),10),("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#1a2535"))]))
    story.append(sent_t)
    story.append(Spacer(1,4*mm))

    # RESUME
    story.append(p("RESUME EXECUTIF", fontSize=8, textColor=MUTED))
    story.append(p(data.get("resume_executif",""), fontSize=10, textColor=LIGHT, leading=16))
    story.append(Spacer(1,3*mm))

    # ACTUALITES
    if data.get("actualites_cles"):
        story.append(p("ACTUALITES CLES", fontSize=8, textColor=MUTED))
        for news in data["actualites_cles"]:
            story.append(p(f"► {news}", fontSize=9, textColor=LIGHT, leading=14, leftIndent=5))
        story.append(Spacer(1,3*mm))

    # CALENDRIER
    if data.get("calendrier_economique"):
        cal = Table([[p(f"CALENDRIER: {data['calendrier_economique']}", fontSize=9, textColor=GOLD, leading=14)]])
        cal.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#1a1400")),("ROWPADDING",(0,0),(-1,-1),8),("LINELEFT",(0,0),(0,-1),3,GOLD)]))
        story.append(cal)
        story.append(Spacer(1,4*mm))

    # TOP 3
    if data.get("top3_opportunites_du_jour"):
        story.append(PageBreak())
        story.append(p("TOP 3 MEILLEURES OPPORTUNITES DU JOUR", fontSize=12, textColor=GREEN, fontName="Helvetica-Bold"))
        story.append(Spacer(1,3*mm))
        for op in data["top3_opportunites_du_jour"]:
            dc = GREEN if op.get("direction")=="LONG" else RED
            score = op.get("score",0)
            top = Table([[
                p(f"#{op.get('rang','')} {op.get('instrument','')}", fontSize=13, textColor=WHITE, fontName="Helvetica-Bold"),
                p(str(op.get("direction","")), fontSize=13, textColor=dc, fontName="Helvetica-Bold"),
                p(f"Score: {score}/10", fontSize=11, textColor=score_color(score), fontName="Helvetica-Bold"),
            ],[
                p(op.get("raison",""), fontSize=10, textColor=LIGHT, leading=14),
                Paragraph("", st("e1x", fontSize=8, textColor=MUTED)),
                Paragraph("", st("e2x", fontSize=8, textColor=MUTED)),
            ]], colWidths=["45%","20%","35%"])
            top.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),("ROWPADDING",(0,0),(-1,-1),10),("LINELEFT",(0,0),(0,-1),4,dc),("SPAN",(0,1),(2,1))]))
            story.append(top)
            story.append(Spacer(1,4*mm))

    # INSTRUMENTS FAVORIS
    story.append(p("VOS 5 INSTRUMENTS FAVORIS", fontSize=12, textColor=GREEN, fontName="Helvetica-Bold"))
    story.append(Spacer(1,3*mm))

    for i, inst in enumerate(data.get("instruments_favoris",[])):
        signal = str(inst.get("signal","ATTENDRE"))
        conviction = str(inst.get("conviction","MOYENNE"))
        score = int(inst.get("score_fiabilite",5))
        sc2 = GREEN if signal=="ACHETER" else (RED if signal=="VENDRE" else GOLD)
        vc = GREEN if "+" in str(inst.get("variation_jour","")) else RED

        story.append(Spacer(1,4*mm))

        t1 = Table([[
            p(str(inst.get("nom","")), fontSize=13, textColor=WHITE, fontName="Helvetica-Bold"),
            p(str(inst.get("prix","")), fontSize=13, textColor=WHITE, fontName="Helvetica-Bold"),
            p(str(inst.get("variation_jour","")), fontSize=11, textColor=vc, fontName="Helvetica-Bold"),
            p(f"SIGNAL: {signal}", fontSize=12, textColor=sc2, fontName="Helvetica-Bold"),
            p(f"Score: {score}/10", fontSize=10, textColor=score_color(score), fontName="Helvetica-Bold"),
        ]], colWidths=["24%","17%","14%","28%","17%"])
        t1.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),("ROWPADDING",(0,0),(-1,-1),10),("LINELEFT",(0,0),(0,-1),4,sc2)]))
        story.append(t1)

        t2 = Table([[
            p(f"ENTREE: {inst.get('entree','')}", fontSize=11, textColor=WHITE, fontName="Helvetica-Bold"),
            p(f"STOP LOSS: {inst.get('sl','')}", fontSize=11, textColor=RED, fontName="Helvetica-Bold"),
            p(f"TAKE PROFIT: {inst.get('tp','')}", fontSize=11, textColor=GREEN, fontName="Helvetica-Bold"),
            p(f"R/R: {inst.get('rr','')}", fontSize=11, textColor=GOLD, fontName="Helvetica-Bold"),
        ]], colWidths=["22%","25%","28%","25%"])
        t2.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#070b10")),("ROWPADDING",(0,0),(-1,-1),10),("GRID",(0,0),(-1,-1),0.3,PANEL)]))
        story.append(t2)

        t3 = Table([[
            p(f"Taille: {inst.get('taille_100chf','')} | Horizon: {inst.get('horizon','')} | Conviction: {conviction}", fontSize=9, textColor=GOLD),
            p(f"Support: {inst.get('support','')} | Resistance: {inst.get('resistance','')}", fontSize=9, textColor=MUTED),
        ]], colWidths=["55%","45%"])
        t3.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#050a10")),("ROWPADDING",(0,0),(-1,-1),7)]))
        story.append(t3)

        story.append(p(f"Catalyseur: {inst.get('catalyseur','')} — {inst.get('analyse','')}", fontSize=9, textColor=LIGHT, leading=14))

    # AUTRES MARCHES
    if data.get("opportunites_autres_marches"):
        story.append(PageBreak())
        story.append(p("AUTRES OPPORTUNITES DE MARCHE", fontSize=12, textColor=BLUE, fontName="Helvetica-Bold"))
        story.append(p("Instruments supplementaires avec potentiel aujourd hui", fontSize=9, textColor=MUTED))
        story.append(Spacer(1,4*mm))

        for i, inst in enumerate(data.get("opportunites_autres_marches",[])):
            signal = str(inst.get("signal","ATTENDRE"))
            score = int(inst.get("score_fiabilite",5))
            sc2 = GREEN if signal=="ACHETER" else (RED if signal=="VENDRE" else GOLD)

            story.append(Spacer(1,3*mm))
            t1 = Table([[
                p(str(inst.get("nom","")), fontSize=13, textColor=WHITE, fontName="Helvetica-Bold"),
                p(str(inst.get("prix","")), fontSize=12, textColor=WHITE),
                p(f"SIGNAL: {signal}", fontSize=12, textColor=sc2, fontName="Helvetica-Bold"),
                p(f"Score: {score}/10", fontSize=10, textColor=score_color(score), fontName="Helvetica-Bold"),
            ]], colWidths=["28%","20%","30%","22%"])
            t1.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),("ROWPADDING",(0,0),(-1,-1),9),("LINELEFT",(0,0),(0,-1),3,sc2)]))
            story.append(t1)

            t2 = Table([[
                p(f"Entree: {inst.get('entree','')} | SL: {inst.get('sl','')} | TP: {inst.get('tp','')} | R/R: {inst.get('rr','')} | Taille: {inst.get('taille_100chf','')}", fontSize=9, textColor=LIGHT),
            ]])
            t2.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#070b10")),("ROWPADDING",(0,0),(-1,-1),8)]))
            story.append(t2)

            story.append(p(f"Catalyseur: {inst.get('catalyseur','')} | Horizon: {inst.get('horizon','')} — {inst.get('analyse','')}", fontSize=9, textColor=LIGHT, leading=14))

    # INTRADAY
    if data.get("opportunites_intraday"):
        story.append(Spacer(1,6*mm))
        story.append(p("OPPORTUNITES INTRADAY — A SURVEILLER AUJOURD HUI", fontSize=12, textColor=GOLD, fontName="Helvetica-Bold"))
        story.append(Spacer(1,3*mm))
        for op in data.get("opportunites_intraday",[]):
            dc = GREEN if op.get("direction")=="LONG" else (RED if op.get("direction")=="SHORT" else GOLD)
            intra = Table([[
                p(str(op.get("heure_cible","")), fontSize=12, textColor=GOLD, fontName="Helvetica-Bold"),
                p(str(op.get("instrument","")), fontSize=12, textColor=WHITE, fontName="Helvetica-Bold"),
                p(str(op.get("direction","")), fontSize=11, textColor=dc, fontName="Helvetica-Bold"),
                p(str(op.get("evenement","")), fontSize=9, textColor=MUTED),
            ],[
                p(str(op.get("strategie","")), fontSize=9, textColor=LIGHT, leading=13),
                Paragraph("", st("ii1x", fontSize=8, textColor=MUTED)), Paragraph("", st("ii2x", fontSize=8, textColor=MUTED)), Paragraph("", st("ii3x", fontSize=8, textColor=MUTED)),
            ]], colWidths=["18%","22%","15%","45%"])
            intra.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),("ROWPADDING",(0,0),(-1,-1),9),("LINELEFT",(0,0),(0,-1),3,GOLD),("SPAN",(0,1),(3,1))]))
            story.append(intra)
            story.append(Spacer(1,3*mm))

    # PAGE FINALE
    story.append(PageBreak())
    story.append(p("RISQUES MAJEURS A SURVEILLER", fontSize=11, textColor=RED, fontName="Helvetica-Bold"))
    story.append(Spacer(1,3*mm))
    for r in data.get("risques_majeurs",[]):
        story.append(p(f"⚠ {r}", fontSize=10, textColor=LIGHT, leading=16))

    if data.get("marches_eviter"):
        story.append(Spacer(1,4*mm))
        story.append(p("MARCHES A EVITER AUJOURD HUI", fontSize=11, textColor=RED, fontName="Helvetica-Bold"))
        for m in data["marches_eviter"]:
            story.append(p(f"✗ {m}", fontSize=10, textColor=RED, leading=16))

    story.append(Spacer(1,5*mm))
    conseil = Table([[p(f"PLAN DE TRADING 100 CHF: {data.get('conseil_100chf','')}", fontSize=10, textColor=LIGHT, leading=16)]])
    conseil.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#1a1400")),("ROWPADDING",(0,0),(-1,-1),14),("LINELEFT",(0,0),(0,-1),4,GOLD)]))
    story.append(conseil)

    story.append(Spacer(1,5*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN))
    story.append(p(f"SOZO TRADE | Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')} par Claude AI | Sources: Investing.com, Bloomberg, Reuters | A titre informatif — Pas un conseil financier", fontSize=7, textColor=MUTED, alignment=1))

    doc.build(story)
    print(f"PDF OK: {out}")
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
