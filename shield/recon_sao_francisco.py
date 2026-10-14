#!/usr/bin/env python3
"""Recon passivo do Laboratorio Sao Francisco (Ariquemes/RO) — 13/10/2026.

SOMENTE observacao de dado publico: DNS, HTTP headers, TLS, WHOIS/RDAP,
robots/sitemap e status de caminhos publicos. NENHUMA requisicao intrusiva,
nenhum payload, nenhuma tentativa de login.

Regra de seguranca deste script: se um caminho sensivel responder 200, o script
registra EXISTENCIA e tipo de conteudo, mas REDIGE valores (mostra no maximo os
NOMES das chaves). Nunca imprime segredo.
"""
import json
import re
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

DOMAIN = "saofranciscorondonia.com.br"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
OUT = {}

# caminhos que apareceram no laudo de maio + outros sensiveis comuns
PATHS = [
    "/", "/.env", "/.env.bak", "/.git/HEAD", "/.git/config", "/config",
    "/config.php.bak", "/wp-config.php.bak", "/backup.zip", "/backup.sql",
    "/.htaccess", "/robots.txt", "/sitemap.xml", "/phpinfo.php",
    "/admin/", "/wp-login.php", "/server-status", "/.DS_Store",
]

SENSITIVE_RE = re.compile(
    r"(password|passwd|senha|secret|token|api[_-]?key|private[_-]?key|"
    r"db_pass|database_password|aws_|chave)", re.I)


def redact(text, limit=400):
    """Mostra estrutura, nunca segredo."""
    text = text[:limit]
    lines = []
    for line in text.splitlines()[:25]:
        if SENSITIVE_RE.search(line):
            key = line.split("=")[0].split(":")[0].strip()[:40]
            lines.append(f"{key}= <REDIGIDO — valor omitido de proposito>")
        else:
            lines.append(line[:120])
    return "\n".join(lines)


def http(url, method="GET", timeout=20, max_bytes=200000):
    req = urllib.request.Request(url, method=method, headers={
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "pt-BR,pt;q=0.9",
    })
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read(max_bytes) if method != "HEAD" else b""
        return {"status": resp.status, "headers": dict(resp.headers),
                "body": body.decode("utf-8", "replace"), "url_final": resp.url}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "headers": dict(e.headers or {}), "body": "", "url_final": url}
    except Exception as e:
        return {"status": None, "error": f"{type(e).__name__}: {e}", "body": "", "url_final": url}


def main():
    OUT["coletado_em"] = datetime.now(timezone.utc).isoformat()
    OUT["alvo"] = DOMAIN

    # 1. DNS
    dns = {}
    for rt in ("A", "MX", "NS", "TXT"):
        try:
            out = subprocess.run(["dig", "+short", DOMAIN, rt], capture_output=True, text=True, timeout=15)
            dns[rt] = [l.strip() for l in out.stdout.splitlines() if l.strip()]
        except Exception as e:
            dns[rt] = [f"erro: {e}"]
    # IP + rDNS
    try:
        dns["IP"] = sorted({ai[4][0] for ai in socket.getaddrinfo(DOMAIN, 443, proto=socket.IPPROTO_TCP)})
    except Exception as e:
        dns["IP"] = [f"erro: {e}"]
    if dns.get("IP"):
        try:
            dns["reverse"] = socket.gethostbyaddr(dns["IP"][0])[0]
        except Exception:
            dns["reverse"] = None
    OUT["dns"] = dns

    # 2. HTTP/HTTPS + redirecionamentos
    http_info = {}
    for scheme in ("http", "https"):
        url = f"{scheme}://{DOMAIN}/"
        r = http(url, method="HEAD")
        http_info[scheme] = {
            "status": r["status"],
            "url_final": r.get("url_final"),
            "server": (r.get("headers") or {}).get("Server"),
            "powered_by": (r.get("headers") or {}).get("X-Powered-By"),
            "location": (r.get("headers") or {}).get("Location"),
            "error": r.get("error"),
        }
    OUT["http"] = http_info

    # 3. Headers de seguranca (o que interessa pro laudo)
    r = http(f"https://{DOMAIN}/")
    h = r.get("headers") or {}
    sec = {
        "status": r["status"],
        "Strict-Transport-Security": h.get("Strict-Transport-Security"),
        "Content-Security-Policy": h.get("Content-Security-Policy"),
        "X-Frame-Options": h.get("X-Frame-Options"),
        "X-Content-Type-Options": h.get("X-Content-Type-Options"),
        "Referrer-Policy": h.get("Referrer-Policy"),
        "Permissions-Policy": h.get("Permissions-Policy"),
        "Server": h.get("Server"),
        "X-Powered-By": h.get("X-Powered-By"),
        "Set-Cookie": ("(presente)" if h.get("Set-Cookie") else None),
        "cookies_sem_flag_seguro": [],
    }
    raw_setcookie = h.get("Set-Cookie") or ""
    for c in [x.strip() for x in raw_setcookie.split(",") if "=" in x]:
        name = c.split("=")[0]
        faltando = [f for f in ("HttpOnly", "Secure", "SameSite") if f.lower() not in c.lower()]
        if faltando:
            sec["cookies_sem_flag_seguro"].append({"cookie": name, "faltando": faltando})
    OUT["headers_seguranca"] = sec

    # 4. TLS
    tls = {}
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((DOMAIN, 443), timeout=15) as sock:
            with ctx.wrap_socket(sock, server_hostname=DOMAIN) as ss:
                cert = ss.getpeercert()
                tls = {
                    "protocolo": ss.version(),
                    "emissor": dict(x[0] for x in cert.get("issuer", [])).get("organizationName"),
                    "assunto": dict(x[0] for x in cert.get("subject", [])).get("commonName"),
                    "valido_de": cert.get("notBefore"),
                    "valido_ate": cert.get("notAfter"),
                    "SAN": [v for k, v in cert.get("subjectAltName", []) if k == "DNS"][:10],
                }
    except Exception as e:
        tls = {"erro": f"{type(e).__name__}: {e}"}
    OUT["tls"] = tls

    # 5. robots / sitemap
    rb = http(f"https://{DOMAIN}/robots.txt")
    OUT["robots_txt"] = {"status": rb["status"], "conteudo": (rb["body"] or "")[:800] if rb["status"] == 200 else None}
    sm = http(f"https://{DOMAIN}/sitemap.xml")
    OUT["sitemap_xml"] = {"status": sm["status"], "primeiras_urls": re.findall(r"<loc>(.*?)</loc>", sm["body"] or "")[:15]}

    # 6. status dos caminhos sensiveis (SOMENTE status — nao baixa conteudo sensivel)
    caminhos = []
    for p in PATHS:
        rr = http(f"https://{DOMAIN}{p}", method="GET", max_bytes=4000)
        entry = {"caminho": p, "status": rr["status"],
                 "content_type": (rr.get("headers") or {}).get("Content-Type"),
                 "tamanho_base": (rr.get("headers") or {}).get("Content-Length")}
        if rr["status"] == 200 and p not in ("/", "/robots.txt", "/sitemap.xml"):
            entry["ATENCAO"] = "respondendo 200 — conteudo exposto publicamente"
            entry["amostra_redigida"] = redact(rr["body"] or "")
        caminhos.append(entry)
    OUT["caminhos_publicos"] = caminhos

    # 7. HTML: tecnologias e formularios (sem interpretar dados de usuario)
    home = http(f"https://{DOMAIN}/")
    html = home["body"] or ""
    _title = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    OUT["homepage"] = {
        "status": home["status"],
        "title": (_title.group(1).strip()[:120] if _title else ""),
        "generator": re.findall(r'name="generator"\s+content="([^"]+)"', html, re.I),
        "scripts_externos": sorted(set(re.findall(r'<script[^>]+src="([^"]+)"', html, re.I)))[:20],
        "formularios": len(re.findall(r"<form", html, re.I)),
        "input_types": sorted(set(re.findall(r'<input[^>]+type="([^"]+)"', html, re.I))),
        "tem_https_misto": bool(re.search(r'(src|href)="http://', html, re.I)),
    }

    print(json.dumps(OUT, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
