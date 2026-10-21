#!/usr/bin/env python3
"""Grava um aprendizado na memoria do Supabase e VERIFICA lendo de volta.

Uso:
    python3 scripts/aprendizado_supabase.py \
        --titulo "..." --conteudo "..." --tags squashfs,binwalk --relevancia 9

Sem --conteudo, le da stdin (util para textos longos com heredoc).
Nunca confia no 201: faz GET pelo id e imprime o registro persistido.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
for path in (BASE / ".env", Path.home() / ".hermes" / ".env"):
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
KEY = os.environ.get("SUPABASE_KEY", "")
if not URL or not KEY:
    sys.exit("[erro] SUPABASE_URL/SUPABASE_KEY ausentes no .env")

H = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}
TABELA = f"{URL}/rest/v1/libertus_memoria"


def req(method, url, data=None):
    r = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                               headers=H, method=method)
    with urllib.request.urlopen(r, timeout=25) as resp:
        return json.loads(resp.read().decode() or "null")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--titulo", required=True)
    ap.add_argument("--conteudo", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--relevancia", type=int, default=9)
    a = ap.parse_args()

    conteudo = a.conteudo or sys.stdin.read()
    if not conteudo.strip():
        sys.exit("[erro] conteudo vazio")

    payload = {
        "tipo": "aprendizado",
        "titulo": a.titulo,
        "conteudo": conteudo,
        "tags": [t.strip() for t in a.tags.split(",") if t.strip()],
        "relevancia": a.relevancia,
    }
    try:
        resp = req("POST", TABELA, payload)
    except urllib.error.HTTPError as e:
        corpo = e.read().decode()[:300]
        print(f"[aviso] insert com relevancia falhou ({e.code}): {corpo}")
        payload.pop("relevancia", None)
        resp = req("POST", TABELA, payload)
    if not resp:
        sys.exit("[erro] insert nao retornou registro")

    entry = resp[0] if isinstance(resp, list) else resp
    mid = entry["id"]
    print(f"[ok] inserido id={mid}")

    lido = req("GET", f"{TABELA}?id=eq.{mid}&select=id,tipo,titulo,relevancia,tags,created_at")
    if not lido:
        sys.exit("[erro] leitura de volta vazia — insert nao persistiu")
    reg = lido[0]
    print("[verify]", json.dumps({k: reg.get(k) for k in
                                  ("id", "tipo", "titulo", "relevancia", "tags", "created_at")},
                                 ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
