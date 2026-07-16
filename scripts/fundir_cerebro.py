#!/usr/bin/env python3
"""
fundir_cerebro.py — Constrói o grafo cognitivo vivo DEFINITIVO do LIBERTUS,
fundindo as duas fontes:
  1. bootstrap das 989 memórias do Supabase (dá cobertura ampla)
  2. import da extração semântica do graphify (dá conexões por SIGNIFICADO)

O resultado é o cérebro que raciocina sobre a rede boa, não sobre tags.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, "/home/libertus/LIBERTUS")
from core.grafo_cognitivo import GrafoCognitivo, BASE_DIR  # noqa: E402

GRAPHIFY_JSON = BASE_DIR / "corpus_graphify" / "graphify-out" / "graph.json"


def load_env():
    for line in (BASE_DIR / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def puxar_memorias():
    load_env()
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    todas, passo, off = [], 1000, 0
    while True:
        q = (f"{url}/rest/v1/libertus_memoria?select=id,tipo,titulo,tags"
             f"&order=created_at.desc&limit={passo}&offset={off}")
        req = urllib.request.Request(
            q, headers={"apikey": key, "Authorization": f"Bearer {key}"})
        lote = json.loads(urllib.request.urlopen(req, timeout=30).read())
        if not lote:
            break
        todas.extend(lote)
        if len(lote) < passo:
            break
        off += passo
    return todas


def main():
    print("=== FUSÃO DO CÉREBRO LIBERTUS ===\n")
    gc = GrafoCognitivo(autoload=False)

    print("1) bootstrap das memórias (cobertura ampla, ligações por tag)...")
    mems = puxar_memorias()
    rb = gc.bootstrap_de_memorias(mems)
    print(f"   {rb}\n")

    print("2) import do graphify (conexões por SIGNIFICADO)...")
    if not GRAPHIFY_JSON.exists():
        print(f"   ERRO: {GRAPHIFY_JSON} não existe. Rode a extração primeiro.")
        sys.exit(1)
    ri = gc.importar_graphify(GRAPHIFY_JSON)
    print(f"   {ri}\n")

    print("3) consolidação inicial...")
    print(f"   {gc.consolidar()}\n")

    gc.salvar()
    print(f"✅ cérebro salvo: {gc.path}")

    st = gc.stats()
    print(f"\n-- STATS FINAIS --")
    print(f"   nós: {st['nos']}  arestas: {st['arestas']}")
    print("   GOD NODES (semânticos):")
    for nome, grau in gc.god_nodes(12):
        print(f"     {grau:4d}  {nome}")

    print("\n-- TESTE: ativação semântica (compare com o por-tag de antes) --")
    for semente in ["pentest", "reconhecimento", "supabase", "identidade"]:
        ativ = gc.ativar([semente], profundidade=2)[:6]
        if ativ:
            nomes = [gc.g.nodes[k].get("rotulo", k) for k, _ in ativ[1:6]]
            print(f"   '{semente}' → {', '.join(nomes)}")
        else:
            print(f"   '{semente}' → (não encontrado)")

    print("\n4) snapshot Supabase...")
    print(f"   {'✅' if gc.snapshot_supabase() else '⚠️ falhou'}")


if __name__ == "__main__":
    main()
