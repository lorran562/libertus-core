#!/usr/bin/env python3
"""
bootstrap_grafo.py — Semeia o grafo cognitivo do LIBERTUS a partir das
memórias reais já existentes no Supabase (libertus_memoria).

Uso:
    python3 scripts/bootstrap_grafo.py

Puxa TODAS as memórias (paginado), constrói a rede viva, roda uma consolidação
inicial, salva local e envia snapshot pro Supabase.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.grafo_cognitivo import GrafoCognitivo, BASE_DIR  # noqa: E402


def load_env():
    env = BASE_DIR / ".env"
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def puxar_todas_memorias():
    load_env()
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    todas = []
    passo = 1000
    offset = 0
    while True:
        q = (f"{url}/rest/v1/libertus_memoria"
             f"?select=id,tipo,titulo,tags,relevancia&order=created_at.desc"
             f"&limit={passo}&offset={offset}")
        req = urllib.request.Request(
            q, headers={"apikey": key, "Authorization": f"Bearer {key}"})
        lote = json.loads(urllib.request.urlopen(req, timeout=30).read())
        if not lote:
            break
        todas.extend(lote)
        if len(lote) < passo:
            break
        offset += passo
    return todas


def main():
    print("=== BOOTSTRAP GRAFO COGNITIVO LIBERTUS ===")
    print("Puxando memórias do Supabase...")
    mems = puxar_todas_memorias()
    print(f"  {len(mems)} memórias carregadas")

    gc = GrafoCognitivo(autoload=False)  # grafo de produção
    res = gc.bootstrap_de_memorias(mems)
    print(f"  bootstrap: {res}")

    print("Consolidação inicial (decai + poda órfãos)...")
    print(f"  {gc.consolidar()}")

    gc.salvar()
    print(f"  salvo local: {gc.path}")

    print("\n-- STATS FINAIS --")
    st = gc.stats()
    print(f"  nós:     {st['nos']}")
    print(f"  arestas: {st['arestas']}")
    print("  GOD NODES (por onde tudo se conecta):")
    for nome, grau in gc.god_nodes(15):
        print(f"    {grau:4d}  {nome}")

    print("\nEnviando snapshot pro Supabase...")
    ok = gc.snapshot_supabase()
    print(f"  {'✅ enviado' if ok else '⚠️ falhou'}")


if __name__ == "__main__":
    main()
