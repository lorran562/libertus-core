#!/usr/bin/env python3
"""Gera laudo SHIELD em PDF a partir de um JSON descritivo.

Uso:
    python3 gerar_laudo_pdf.py laudo.json [saida.pdf]

O JSON deve ter as chaves: empresa, dominio, segmento, data, resumo,
achados[{titulo, severidade, evidencia, impacto}], lgpd[], plano[{passo, prazo}],
oferta[{item, preco}].

Regra do projeto: nada de achado inventado. O texto do JSON tem que ser fato
reverificado no dia da emissão — o PDF é a versão formal do que foi conferido.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

from xml.sax.saxutils import escape as esc

AZUL = colors.HexColor("#1e40af")
CINZA = colors.HexColor("#475569")
SEV = {
    "CRÍTICO": colors.HexColor("#dc2626"),
    "ALTO": colors.HexColor("#ea580c"),
    "MÉDIO": colors.HexColor("#ca8a04"),
    "BAIXO": colors.HexColor("#16a34a"),
}


def estilos():
    s = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("t", parent=s["Title"], fontName="Helvetica-Bold",
                                 fontSize=22, leading=27, textColor=AZUL, alignment=TA_LEFT),
        "sub": ParagraphStyle("s", parent=s["Normal"], fontName="Helvetica",
                              fontSize=11.5, leading=16, textColor=CINZA),
        "h1": ParagraphStyle("h1", parent=s["Heading1"], fontName="Helvetica-Bold",
                             fontSize=14, leading=18, textColor=AZUL, spaceBefore=14, spaceAfter=6),
        "h2": ParagraphStyle("h2", parent=s["Heading2"], fontName="Helvetica-Bold",
                             fontSize=11.5, leading=15, textColor=colors.black, spaceBefore=10, spaceAfter=4),
        "corpo": ParagraphStyle("c", parent=s["BodyText"], fontName="Helvetica",
                                fontSize=9.8, leading=14, alignment=TA_JUSTIFY, spaceAfter=6),
        "mono": ParagraphStyle("m", parent=s["BodyText"], fontName="Courier",
                               fontSize=8.3, leading=11.5, textColor=colors.HexColor("#0f172a"),
                               backColor=colors.HexColor("#f1f5f9"), borderPadding=5, spaceAfter=6),
        "cap": ParagraphStyle("cp", parent=s["Normal"], fontName="Helvetica",
                              fontSize=8.5, leading=11, textColor=CINZA),
    }


def rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(CINZA)
    canvas.drawString(2 * cm, 1.15 * cm, "SHIELD Ciberseguranca - Ariquemes/RO | Documento confidencial")
    canvas.drawRightString(A4[0] - 2 * cm, 1.15 * cm, f"pagina {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#cbd5e1"))
    canvas.line(2 * cm, 1.5 * cm, A4[0] - 2 * cm, 1.5 * cm)
    canvas.restoreState()


def tabela_achado(a, E):
    sev = a.get("severidade", "MÉDIO").upper()
    cor = SEV.get(sev, SEV["MÉDIO"])
    linhas = [
        [Paragraph(f"<b>{esc(a['titulo'])}</b>", E["h2"]),
         Paragraph(f"<font color='#ffffff'><b>{sev}</b></font>", E["cap"])],
        [Paragraph(esc(a["evidencia"]), E["corpo"]), ""],
        [Paragraph(f"<b>Impacto:</b> {esc(a['impacto'])}", E["corpo"]), ""],
    ]
    t = Table(linhas, colWidths=[13.6 * cm, 3.4 * cm])
    t.setStyle(TableStyle([
        ("SPAN", (0, 1), (1, 1)), ("SPAN", (0, 2), (1, 2)),
        ("BACKGROUND", (1, 0), (1, 0), cor),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#cbd5e1")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return KeepTogether([t, Spacer(1, 10)])


def gerar(dados, saida):
    E = estilos()
    doc = SimpleDocTemplate(str(saida), pagesize=A4,
                            leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2 * cm, bottomMargin=2 * cm,
                            title=f"Laudo SHIELD - {dados['empresa']}",
                            author="SHIELD Ciberseguranca - Lorran Gustavo")
    f = []
    # capa
    f.append(Spacer(1, 2.2 * cm))
    f.append(Paragraph("SHIELD", ParagraphStyle("sh", parent=E["titulo"], fontSize=30, leading=34)))
    f.append(Paragraph("Seu escudo digital", E["sub"]))
    f.append(Spacer(1, 1.4 * cm))
    f.append(Paragraph("LAUDO DE ANÁLISE DE SEGURANÇA<br/>PASSIVA (DADOS PÚBLICOS)", E["titulo"]))
    f.append(Spacer(1, 0.8 * cm))
    cap = [
        ["Empresa", dados["empresa"]],
        ["Segmento", dados["segmento"]],
        ["Endereço analisado", dados["dominio"]],
        ["Data da análise", dados["data"]],
        ["Escopo", "Somente informação pública (HTTP/HTTPS, DNS, certificado)\nNenhum acesso autenticado ou tentativa de intrusão"],
        ["Emitido por", "Lorran Gustavo — SHIELD Cibersegurança, Ariquemes/RO"],
    ]
    t = Table([[Paragraph(f"<b>{k}</b>", E["corpo"]), Paragraph(esc(str(v)).replace("\n", "<br/>"), E["corpo"])]
               for k, v in cap], colWidths=[4.6 * cm, 12.4 * cm])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#94a3b8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8fafc")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    f.append(t)
    f.append(PageBreak())

    f.append(Paragraph("1. Resumo executivo", E["h1"]))
    for p in dados["resumo"].split("\n\n"):
        f.append(Paragraph(esc(p.strip()), E["corpo"]))

    f.append(Paragraph("2. Achados", E["h1"]))
    for a in dados["achados"]:
        f.append(tabela_achado(a, E))

    if dados.get("lgpd"):
        f.append(Paragraph("3. Exposição legal (LGPD)", E["h1"]))
        for l in dados["lgpd"]:
            f.append(Paragraph(f"• {esc(l)}", E["corpo"]))

    if dados.get("plano"):
        f.append(Paragraph("4. Plano de correção", E["h1"]))
        t = Table([[Paragraph("<b>#</b>", E["corpo"]), Paragraph("<b>Ação</b>", E["corpo"]),
                    Paragraph("<b>Prazo</b>", E["corpo"])]] +
                  [[Paragraph(str(i + 1), E["corpo"]), Paragraph(esc(p["passo"]), E["corpo"]),
                    Paragraph(esc(p["prazo"]), E["corpo"])] for i, p in enumerate(dados["plano"])],
                  colWidths=[1.2 * cm, 12.3 * cm, 3.5 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#94a3b8")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        f.append(t)

    if dados.get("oferta"):
        f.append(Paragraph("5. O que a SHIELD entrega", E["h1"]))
        for o in dados["oferta"]:
            f.append(Paragraph(f"<b>{esc(o['item'])}</b> — {esc(o['preco'])}", E["corpo"]))

    f.append(Spacer(1, 0.4 * cm))
    f.append(Paragraph(
        "Este documento foi produzido exclusivamente a partir de informação "
        "pública, sem acesso a sistemas internos e sem tentativa de exploração. "
        "Testes ativos, correções e monitoramento exigem contrato e autorização "
        "por escrito do responsável.", E["cap"]))
    f.append(Spacer(1, 0.3 * cm))
    f.append(Paragraph(
        f"Contato: Lorran Gustavo — SHIELD Cibersegurança — Ariquemes/RO — "
        f"emitido em {datetime.now().strftime('%d/%m/%Y %H:%M')}", E["cap"]))

    doc.build(f, onFirstPage=rodape, onLaterPages=rodape)
    return Path(saida)


if __name__ == "__main__":
    src = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".pdf")
    p = gerar(json.loads(src.read_text(encoding="utf-8")), out)
    print(f"PDF gerado: {p} ({p.stat().st_size} bytes)")
