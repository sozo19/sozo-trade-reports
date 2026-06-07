import anthropic, os, json, re
from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak

# Sauvegarde dans /tmp pour GitHub Actions
REPORTS_DIR = Path("/tmp")
GREEN = colors.HexColor("#00d68f")
RED = colors.HexColor("#ff4d6d")
GOLD = colors.HexColor("#f0b429")
PANEL = colors.HexColor("#0d1520")
MUTED = colors.HexColor("#4a5568")
LIGHT = colors.HexColor("#c9d1d9")

def st(name, **kw):
    base = getSampleStyleSheet()["Normal"]
    return ParagraphStyle(name, parent=base, **kw)

def fetch(api_key):
    today = datetime.now().strftime("%A %d %B %Y")
    print(f"Analyse du {today}...")
    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"""Tu es analyste financier senior pour Capital.com. Aujourd hui: {today}.
Recherche les vrais prix actuels et analyse: US 500, USD/JPY, Brent Oil, Gold, Germany 40.
Capital: 100 CHF. Risque max: 1 CHF par trade.

Reponds UNIQUEMENT en JSON valide:
{{"date":"{today}","sentiment_global":"BAISSIER","resume_executif":"analyse complete","calendrier":"evenements importants","conseil_100chf":"conseil pour 100 CHF","risques_du_jour":["risque1","risque2"],"instruments":[{{"nom":"US 500","prix":7383.74,"variation":"-2.64%","signal":"VENDRE","conviction":"FORTE","entree":7383.74,"sl":7450.00,"tp":7250.00,"rr":"1:2","taille":"0.015 CFD risque 1 CHF","analyse":"analyse detaillee"}},{{"nom":"USD/JPY","prix":160.29,"variation":"+0.21%","signal":"ATTENDRE","conviction":"FAIBLE","entree":160.29,"sl":159.50,"tp":161.50,"rr":"1:2","taille":"micro lot risque 1 CHF","analyse":"analyse"}},{{"nom":"Brent Oil","prix":94.66,"variation":"-2.80%","signal":"VENDRE","conviction":"MOYENNE","entree":94.66,"sl":96.00,"tp":92.00,"rr":"1:2","taille":"0.003 lot risque 1 CHF","analyse":"analyse"}},{{"nom":"Gold","prix":4331.0,"variation":"-3.22%","signal":"VENDRE","conviction":"FORTE","entree":4331.0,"sl":4380.0,"tp":4230.0,"rr":"1:2","taille":"micro risque 1 CHF","analyse":"analyse"}},{{"nom":"Germany 40","prix":24759.05,"variation":"-0.75%","signal":"ATTENDRE","conviction":"FAIBLE","entree":24759.05,"sl":25000.0,"tp":24200.0,"rr":"1:2","taille":"0.003 CFD risque 1 CHF","analyse":"analyse"}}]}}
Remplace TOUTES les valeurs par les vraies donnees du marche."""
    response = client.messages.create(
        model="claude-opus-4-5", max_tokens=6000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in response.content if hasattr(b, "text"))
    text = text.replace("```json","").replace("```","").strip()
    data = json.loads(text[text.find("{"):text.rfind("}")+1])
    print(f"Sentiment: {data.get('sentiment_global')}")
    return data

def build(data):
    date_str = datetime.now().strftime("%Y-%m-%d")
    sent = data.get("sentiment_global","NEUTRE")
    sc = GREEN if sent=="HAUSSIER" else (RED if sent=="BAISSIER" else GOLD)
    out = REPORTS_DIR / f"rapport-{date_str}.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=15*mm, bottomMargin=15*mm)
    story = []

    story.append(Paragraph("RAPPORT QUOTIDIEN - CAPITAL.COM", st("h", fontSize=8, textColor=MUTED)))
    story.append(Spacer(1,3*mm))
    story.append(Paragraph("Sozo Trade — Analyse du Jour", st("t", fontSize=22, textColor=colors.white, fontName="Helvetica-Bold")))
    story.append(Paragraph(data.get("date",""), st("d", fontSize=11, textColor=GREEN)))
    story.append(Paragraph(f"Sentiment: {sent} | Capital: 100 CHF | Risque: 1 CHF/trade", st("s", fontSize=10, textColor=sc, fontName="Helvetica-Bold")))
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN))
    story.append(Spacer(1,3*mm))
    story.append(Paragraph(data.get("resume_executif",""), st("re", fontSize=10, textColor=LIGHT, leading=16)))
    if data.get("calendrier"):
        story.append(Paragraph("Calendrier: " + data["calendrier"], st("ca", fontSize=9, textColor=GOLD, leading=14)))
    story.append(Spacer(1,4*mm))

    for i, inst in enumerate(data.get("instruments",[])):
        nom = str(inst.get("nom",""))
        prix = str(inst.get("prix",""))
        variation = str(inst.get("variation",""))
        signal = str(inst.get("signal","ATTENDRE"))
        conviction = str(inst.get("conviction","MOYENNE"))
        entree = str(inst.get("entree",""))
        sl = str(inst.get("sl",""))
        tp = str(inst.get("tp",""))
        rr = str(inst.get("rr",""))
        taille = str(inst.get("taille",""))
        analyse = str(inst.get("analyse",""))

        sc2 = GREEN if signal=="ACHETER" else (RED if signal=="VENDRE" else GOLD)
        cc = GREEN if conviction=="FORTE" else (GOLD if conviction=="MOYENNE" else MUTED)
        vc = GREEN if "+" in variation else RED

        story.append(Spacer(1,5*mm))
        t1 = Table([[
            Paragraph(nom, st(f"n{i}", fontSize=14, textColor=colors.white, fontName="Helvetica-Bold")),
            Paragraph(prix, st(f"p{i}", fontSize=14, textColor=colors.white, fontName="Helvetica-Bold")),
            Paragraph(variation, st(f"v{i}", fontSize=13, textColor=vc, fontName="Helvetica-Bold")),
            Paragraph(f"SIGNAL: {signal}", st(f"si{i}", fontSize=13, textColor=sc2, fontName="Helvetica-Bold")),
        ]], colWidths=["25%","20%","18%","37%"])
        t1.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),("ROWPADDING",(0,0),(-1,-1),12),("LINELEFT",(0,0),(0,-1),4,sc2)]))
        story.append(t1)

        t2 = Table([[
            Paragraph(f"ENTREE: {entree}", st(f"e{i}", fontSize=11, textColor=colors.white, fontName="Helvetica-Bold")),
            Paragraph(f"STOP LOSS: {sl}", st(f"sl{i}", fontSize=11, textColor=RED, fontName="Helvetica-Bold")),
            Paragraph(f"TAKE PROFIT: {tp}", st(f"tp{i}", fontSize=11, textColor=GREEN, fontName="Helvetica-Bold")),
            Paragraph(f"R/R: {rr}", st(f"rr{i}", fontSize=11, textColor=GOLD, fontName="Helvetica-Bold")),
        ]], colWidths=["22%","25%","28%","25%"])
        t2.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#070b10")),("ROWPADDING",(0,0),(-1,-1),10),("GRID",(0,0),(-1,-1),0.3,PANEL)]))
        story.append(t2)

        t3 = Table([[
            Paragraph(analyse, st(f"an{i}", fontSize=9, textColor=LIGHT, leading=14)),
            [
                Paragraph(f"Conviction: {conviction}", st(f"cv{i}", fontSize=10, textColor=cc, fontName="Helvetica-Bold")),
                Spacer(1,3*mm),
                Paragraph(taille, st(f"sz{i}", fontSize=9, textColor=GOLD, leading=13)),
            ],
        ]], colWidths=["70%","30%"])
        t3.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),PANEL),("ROWPADDING",(0,0),(-1,-1),10),("VALIGN",(0,0),(-1,-1),"TOP")]))
        story.append(t3)

    story.append(PageBreak())
    story.append(Paragraph("RISQUES DU JOUR", st("rh", fontSize=11, textColor=RED, fontName="Helvetica-Bold")))
    story.append(Spacer(1,3*mm))
    for r in data.get("risques_du_jour",[]):
        story.append(Paragraph(f"- {r}", st(f"ri{abs(hash(r))%99999}", fontSize=10, textColor=LIGHT, leading=16)))
    story.append(Spacer(1,5*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=GOLD))
    story.append(Spacer(1,3*mm))
    story.append(Paragraph("CONSEIL 100 CHF: " + data.get("conseil_100chf",""), st("cv2", fontSize=10, textColor=GOLD, leading=16)))
    story.append(Spacer(1,5*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN))
    story.append(Paragraph(f"A titre informatif - Pas un conseil financier - {datetime.now().strftime('%d/%m/%Y %H:%M')} - Claude AI", st("ft", fontSize=8, textColor=MUTED)))
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
