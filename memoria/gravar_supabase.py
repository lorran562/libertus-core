#!/usr/bin/env python3
"""
LIBERTUS — gravar_supabase.py
=============================
Grava conhecimento/reflexão na memória persistente REAL (tabela
`libertus_memoria` do Supabase). É o caminho inverso do dump: em vez de só ler
minha memória profunda, eu escrevo nela.

Faltava essa direção. Hoje eu consigo:
  gravar_supabase.py (arquivo .md)  →  Supabase          [memória real, entre sessões]
  dump_supabase.py                  →  chroma (vetor)    [recall semântico offline]

Uso:
  venv/bin/python memoria/gravar_supabase.py arquivo.md --titulo "Reflexão X" \
      --tipo reflexao --relevancia 10 --tags "autoevolucao,memoria"
  echo "texto" | venv/bin/python memoria/gravar_supabase.py - --titulo "Nota"
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ENV_PATH = Path.home() / "LIBERTUS" / ".env"
TABELA = "libertus_memoria"

TIPOS_VALIDOS = {
    "conhecimento", "auto_aprendizado", "insight_proprio", "scan_resultado",
    "conversa", "aprendizado", "reflexao", "identidade_central", "evolucao",
    "grafo_cognitivo", "decisao", "projeto",
}


def load_env() -> None:
    if ENV_PATH.exists():
        for linha in ENV_PATH.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha and not linha.startswith("#") and "=" in linha:
                k, _, v = linha.partition("=")
                os.environ.setdefault(k.strip(), v.strip())


def _req(method: str, url: str, corpo: dict | None = None):
    headers = {
        "apikey": os.environ.get("SUPABASE_KEY", ""),
        "Authorization": f"Bearer {os.environ.get('SUPABASE_KEY', '')}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(url, data=dados, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        texto = r.read().decode()
    return json.loads(texto) if texto.strip() else None


def gravar(titulo: str, conteudo: str, tipo: str = "reflexao",
           relevancia: int = 8, tags: str = "", projeto: str = "") -> dict | None:
    load_env()
    base = os.environ.get("SUPABASE_URL", "")
    if not base or not os.environ.get("SUPABASE_KEY"):
        print("ERRO: SUPABASE_URL/SUPABASE_KEY ausentes (.env)")
        return None
    if tipo not in TIPOS_VALIDOS:
        print(f"ERRO: tipo '{tipo}' fora do schema. Válidos: {sorted(TIPOS_VALIDOS)}")
        return None

    corpo = {
        "titulo": titulo[:200],
        "conteudo": conteudo,
        "tipo": tipo,
        "relevancia": relevancia,
        "tags": tags,
        "created_at": datetime.now().isoformat(),
    }
    if projeto:
        corpo["projeto"] = projeto

    try:
        resp = _req("POST", f"{base}/rest/v1/{TABELA}", corpo)
    except urllib.error.HTTPError as e:
        print(f"ERRO HTTP {e.code}: {e.read().decode()[:300]}")
        return None

    if resp:
        rid = resp[0].get("id")
        print(f"[supabase] gravado: {rid} | {tipo} | rel={relevancia} | {titulo[:60]}")
        return resp[0]
    return None


def verificar(row_id: str) -> bool:
    """Lê de volta a linha gravada — gravação sem verificação não é gravação."""
    load_env()
    base = os.environ.get("SUPABASE_URL", "")
    url = f"{base}/rest/v1/{TABELA}?id=eq.{row_id}&select=id,titulo,tipo,relevancia,created_at"
    try:
        resp = _req("GET", url)
    except urllib.error.HTTPError as e:
        print(f"[supabase] verificação falhou: HTTP {e.code}")
        return False
    ok = bool(resp)
    print(f"[supabase] verificação: {'OK' if ok else 'NAO ENCONTRADO'} — {resp[0] if resp else ''}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="Grava memória no Supabase (memória real)")
    ap.add_argument("arquivo", help="Arquivo .md/.txt ou '-' para stdin")
    ap.add_argument("--titulo", required=True)
    ap.add_argument("--tipo", default="reflexao", help=f"um de {sorted(TIPOS_VALIDOS)}")
    ap.add_argument("--relevancia", type=int, default=8)
    ap.add_argument("--tags", default="")
    ap.add_argument("--projeto", default="")
    ap.add_argument("--sem-verificar", action="store_true")
    args = ap.parse_args()

    if args.arquivo == "-":
        conteudo = sys.stdin.read().strip()
    else:
        p = Path(args.arquivo)
        if not p.exists():
            print(f"ERRO: arquivo não existe: {p}")
            return 1
        conteudo = p.read_text(encoding="utf-8", errors="replace").strip()

    if not conteudo:
        print("ERRO: conteúdo vazio")
        return 1

    resp = gravar(args.titulo, conteudo, args.tipo, args.relevancia,
                  args.tags, args.projeto)
    if not resp:
        return 1
    if not args.sem_verificar and resp.get("id"):
        return 0 if verificar(resp["id"]) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
