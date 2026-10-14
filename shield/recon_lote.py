#!/usr/bin/env python3
"""Recon passivo em LOTE para os leads da SHIELD (somente dado publico).

Para cada dominio: DNS, HTTP/HTTPS, TLS, cabecalhos de seguranca, robots/sitemap
e status de caminhos sensiveis. Saida: JSON por dominio + tabela resumo no stdout.

NENHUMA requisicao intrusiva. Caminho sensivel que responder 200 e registrado como
EXISTENTE, com valores REDIGIDOS (nunca imprime segredo).
"""
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")

LEADS = [
    ("CEDDI Centro de Diagnóstico", "ceddi.com.br"),
    ("Bruni Imóveis", "bruniimoveis.com.br"),
    ("Imobiliária Aislan Santos", "aislansantosimoveis.com.br"),
    ("Oikos Assessoria", "oikosassessoria.com.br"),
    ("AD Imóveis", "adimoveisro.com.br"),
    ("Marques Imóveis", "marquesimoveisro.com.br"),
    ("Laboratório São José", "saojoselaboratorio.com.br"),
]

PATHS = ["/.env", "/.git/HEAD", "/.git/config", "/config", "/backup.sql",
         "/wp-config.php.bak", "/.DS_Store", "/admin/", "/wp-login.php",
         "/server-status", "/phpinfo.php"]

SENS = re.compile(r"(password|senha|secret|token|api[_-]?key|db_|aws_|chave)", re.I)
HDRS = ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options",
        "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"]


def req(url, method="GET", timeout=20, cap=6000):
    r = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        resp = urllib.request.urlopen(r, timeout=timeout)
        body = resp.read(cap) if method != "HEAD" else b""
        return {"status": resp.status, "headers": dict(resp.headers),
                "body": body.decode("utf-8", "replace"), "final": resp.url}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "headers": dict(e.headers or {}), "body": "", "final": url}
    except Exception as e:
        return {"status": None, "error": f"{type(e).__name__}", "headers": {}, "body": "", "final": url}


def redige(txt):
    out = []
    for line in txt.splitlines()[:20]:
        out.append(f"{line.split('=')[0].split(':')[0].strip()[:40]}= <REDIGIDO>" if SENS.search(line) else line[:110])
    return out


def analisa(nome, dom, outdir):
    d = {"empresa": nome, "dominio": dom, "coletado_em": datetime.now(timezone.utc).isoformat()}
    # 1. resolve / www
    base = None
    for cand in (f"https://{dom}/", f"https://www.{dom}/"):
        r = req(cand, "HEAD")
        if r["status"] and r["status"] < 500:
            base = cand
            break
    d["responde"] = bool(base)
    d["base"] = base
    if not base:
        return d

    # 2. headers
    r = req(base)
    h = r["headers"]
    d["http"] = {"status": r["status"], "final": r["final"], "server": h.get("Server"),
                 "powered_by": h.get("X-Powered-By"), "generator": None}
    html = r["body"] or ""
    g = re.search(r'name="generator"\s+content="([^"]+)"', html, re.I)
    d["http"]["generator"] = g.group(1) if g else None
    tit = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    d["http"]["title"] = (tit.group(1).strip()[:90] if tit else None)
    d["headers_faltando"] = [k for k in HDRS if not h.get(k)]
    csp = h.get("Content-Security-Policy") or ""
    d["csp"] = {"presente": bool(csp),
                "permite_unsafe_inline": "'unsafe-inline'" in csp,
                "permite_unsafe_eval": "'unsafe-eval'" in csp,
                "origens_internas_vazadas": sorted(set(re.findall(r"https?://[a-z0-9.\-]*localhost[a-z0-9.:\-]*", csp)))}
    if h.get("Set-Cookie"):
        d["cookies_sem_flag"] = [c.split("=")[0] for c in str(h["Set-Cookie"]).split(",")
                                 if any(f not in c for f in ("HttpOnly", "Secure", "SameSite"))]
    # 3. TLS + redirect http->https
    try:
        host = base.split("//")[1].rstrip("/")
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=15) as s:
            with ctx.wrap_socket(s, server_hostname=host) as ss:
                c = ss.getpeercert()
                d["tls"] = {"protocolo": ss.version(),
                            "emissor": dict(x[0] for x in c.get("issuer", [])).get("organizationName"),
                            "ate": c.get("notAfter")}
    except Exception as e:
        d["tls"] = {"erro": type(e).__name__}
    rh = req(f"http://{dom}/", "HEAD")
    d["redireciona_https"] = (rh.get("final") or "").startswith("https://")

    # 4. robots + sitemap
    rb = req(base + "robots.txt")
    d["robots"] = {"status": rb["status"], "disallows": re.findall(r"Disallow:\s*(\S+)", rb["body"] or "")[:20]}
    # 5. caminhos sensiveis (SO status; conteudo redigido)
    d["caminhos"] = []
    for p in PATHS:
        rr = req(base.rstrip("/") + p, cap=2500)
        e = {"p": p, "status": rr["status"]}
        if rr["status"] == 200:
            e["EXPOSTO"] = True
            e["amostra"] = redige(rr["body"] or "")
        d["caminhos"].append(e)
    return d


def resumo(d):
    if not d.get("responde"):
        return f"{d['empresa'][:26]:26} | NAO RESPONDE"
    expostos = [c["p"] for c in d.get("caminhos", []) if c.get("EXPOSTO")]
    falt = d.get("headers_faltando") or []
    tls = (d.get("tls") or {}).get("protocolo") or "?"
    flags = []
    if expostos:
        flags.append("EXPOSTO:" + ",".join(expostos))
    if not d.get("redireciona_https"):
        flags.append("SEM-REDIRECT-HTTPS")
    if tls != "TLSv1.3":
        flags.append(f"TLS={tls}")
    if len(falt) >= 4:
        flags.append(f"faltam {len(falt)} headers")
    if d.get("csp", {}).get("permite_unsafe_eval"):
        flags.append("CSP-fraca")
    if d.get("csp", {}).get("origens_internas_vazadas"):
        flags.append("vaza-origem-interna")
    if d.get("http", {}).get("generator"):
        flags.append("generator=" + str(d["http"]["generator"])[:22])
    return f"{d['empresa'][:26]:26} | {d['base'][:34]:34} | " + ("; ".join(flags) if flags else "sem achado obvio")


def main():
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recon")
    os.makedirs(outdir, exist_ok=True)
    resultados = []
    for nome, dom in LEADS:
        print(f"... analisando {dom}", file=sys.stderr)
        d = analisa(nome, dom, outdir)
        resultados.append(d)
        slug = dom.replace(".", "_")
        json.dump(d, open(os.path.join(outdir, f"lote_{slug}.json"), "w"), indent=1, ensure_ascii=False)
    print("=" * 110)
    print(f"{'EMPRESA':26} | {'ALVO':34} | ACHADOS")
    print("=" * 110)
    for d in resultados:
        print(resumo(d))
    print("=" * 110)
    json.dump(resultados, open(os.path.join(outdir, "lote_resumo.json"), "w"), indent=1, ensure_ascii=False)
    print(f"JSONs salvos em {outdir}/lote_*.json", file=sys.stderr)


if __name__ == "__main__":
    main()
