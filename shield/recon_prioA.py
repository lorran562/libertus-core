#!/usr/bin/env python3
"""Recon passivo em lote nos leads de Prioridade A do CSV (somente dado publico).

Diferente do recon_lote.py (lista fixa), este le leads_ariquemes.csv, ignora
"sites" que na verdade sao rede social/agregador (instagram, facebook, wa.me,
linktr.ee, google) e, alem dos achados tecnicos, coleta os canais ESCRITOS de
contato (e-mail no HTML e link de formulario) — Lorran nao liga, entao o canal
escrito vale mais que o telefone.

Uso: python3 recon_prioA.py [--limite N] [--offset N]
Saida: recon/prioA_<slug>.json + recon/prioA_resumo.json
"""
import csv
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from recon_lote import analisa, req  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "recon")
CSV = os.path.join(BASE, "leads_ariquemes.csv")

SOCIAL = ("instagram.com", "facebook.com", "wa.me", "linktr.ee", "google.com",
          "bit.ly", "youtube.com", "tiktok.com")
# franquia nacional: dominio nao e do dono local, decisao de TI nao esta em Ariquemes
NAO_LOCAL = ("cartaodetodos.com.br",)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
FORM_RE = re.compile(r'href="([^"]*(?:contato|fale-conosco|contact)[^"]*)"', re.I)
WA_RE = re.compile(r"wa\.me/(\d{12,13})|api\.whatsapp\.com/send\?phone=(\d{12,13})")

CAND_CONTATO = ["/contato/", "/contato", "/fale-conosco/", "/contato.html", "/contact"]


def dominio_de(url):
    h = urllib.parse.urlparse(url).hostname or ""
    return h.lower().removeprefix("www.")


def coleta_canais(base, html):
    emails, form, wa = set(), None, set()
    pages = [(base, html)]
    for p in CAND_CONTATO:
        r = req(base.rstrip("/") + p, cap=20000)
        if r["status"] == 200 and r["body"]:
            pages.append((base.rstrip("/") + p, r["body"]))
    for url, body in pages:
        for m in EMAIL_RE.findall(body or ""):
            if not m.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                emails.add(m.lower())
        if form is None:
            f = FORM_RE.search(body or "")
            if f:
                form = urllib.parse.urljoin(url, f.group(1))
        for a, b in WA_RE.findall(body or ""):
            wa.add(a or b)
    return {"emails": sorted(emails)[:6], "formulario": form, "whatsapp": sorted(wa)[:2]}


def main():
    lim = None
    off = 0
    if "--limite" in sys.argv:
        lim = int(sys.argv[sys.argv.index("--limite") + 1])
    if "--offset" in sys.argv:
        off = int(sys.argv[sys.argv.index("--offset") + 1])

    rows = [r for r in csv.DictReader(open(CSV, encoding="utf-8"))
            if r["prioridade"] == "A" and r.get("site")]
    alvos, pulados = [], []
    for r in rows:
        dom = dominio_de(r["site"])
        if any(s in dom for s in SOCIAL):
            pulados.append((r["nome"], dom, "rede social/agregador"))
        elif any(s in dom for s in NAO_LOCAL):
            pulados.append((r["nome"], dom, "franquia nacional - decisao fora de Ariquemes"))
        elif not dom:
            pulados.append((r["nome"], r["site"], "sem dominio"))
        else:
            alvos.append((r["nome"], dom, r["vertical"], r["telefone"], r["status"]))
    # dedup por dominio
    vistos, uniq = set(), []
    for a in alvos:
        if a[1] not in vistos:
            vistos.add(a[1])
            uniq.append(a)
    alvos = uniq[off: (off + lim) if lim else None]

    print(f"alvos={len(alvos)} pulados={len(pulados)}", file=sys.stderr)
    saida = []
    for nome, dom, vert, tel, status in alvos:
        print(f"... {dom}", file=sys.stderr)
        d = analisa(nome, dom, OUT)
        d["vertical"] = vert
        d["telefone"] = tel
        d["canais"] = coleta_canais(d["base"], "") if d.get("responde") else {}
        saida.append(d)
        json.dump(d, open(os.path.join(OUT, f"prioA_{dom.replace('.', '_')}.json"), "w"),
                  indent=1, ensure_ascii=False)

    def forca(d):
        p = 0
        if not d.get("responde"):
            p += 100  # site fora do ar = gancho maximo, sem precisar de laudo
        exp = [c["p"] for c in d.get("caminhos", []) if c.get("EXPOSTO")]
        # /admin e /wp-login sao login padrao: NAO contam como forca
        exp_reais = [p_ for p_ in exp if p_ not in ("/admin/", "/wp-login.php")]
        p += 40 * len(exp_reais)
        if d.get("cookies_sem_flag"):
            p += 10
        if not d.get("redireciona_https"):
            p += 15
        if (d.get("tls") or {}).get("erro"):
            p += 25
        if d.get("http", {}).get("generator"):
            p += 5
        return p

    for d in saida:
        d["forca_venda"] = forca(d)
    saida.sort(key=lambda d: -d["forca_venda"])
    json.dump(saida, open(os.path.join(OUT, "prioA_resumo.json"), "w"), indent=1, ensure_ascii=False)

    print("=" * 118)
    print(f"{'FORCA':5} | {'EMPRESA':34} | {'DOMINIO':32} | CANAIS ESCRITOS")
    print("=" * 118)
    for d in saida:
        c = d.get("canais") or {}
        canais = ", ".join((c.get("emails") or [])[:2]) or ("form" if c.get("formulario") else "-")
        ex = "" if d.get("responde") else "FORA DO AR"
        print(f"{d['forca_venda']:5} | {d['empresa'][:34]:34} | {d['dominio'][:32]:32} | {ex} {canais}")
    print("=" * 118)
    print("pulados:", [p[0][:24] + f" ({p[2]})" for p in pulados])


if __name__ == "__main__":
    main()
