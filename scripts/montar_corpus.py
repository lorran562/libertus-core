#!/usr/bin/env python3
"""
montar_corpus.py — Monta a pasta ~/LIBERTUS/corpus_graphify/ com o conhecimento
real do LIBERTUS num formato que o graphify extrai bem (markdown + código).

Fontes:
  1. Memórias do Supabase (libertus_memoria) -> corpus/memorias/*.md agrupadas por tipo
  2. Código do cérebro                       -> corpus/core/*.py (cópia dos módulos-chave)
  3. Skills do projeto                       -> corpus/skills/*.md

O graphify roda EM CIMA dessa pasta e gera conexões por SIGNIFICADO (via LLM),
não por tag — que é o que falta pro grafo cognitivo vivo.
"""
import json
import os
import re
import shutil
import urllib.request
from collections import defaultdict
from pathlib import Path

BASE = Path("/home/libertus/LIBERTUS")
CORPUS = BASE / "corpus_graphify"


def load_env():
    for line in (BASE / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def slug(s: str, n: int = 60) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s[:n] or "sem-titulo"


def puxar_memorias():
    load_env()
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_KEY"]
    todas, passo, off = [], 1000, 0
    while True:
        q = (f"{url}/rest/v1/libertus_memoria?select=id,tipo,titulo,conteudo,tags,"
             f"relevancia,created_at&order=created_at.desc&limit={passo}&offset={off}")
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


def escrever_memorias(mems):
    """Agrupa memórias por tipo, um arquivo .md por tipo (evita 989 arquivos)."""
    d = CORPUS / "memorias"
    d.mkdir(parents=True, exist_ok=True)
    por_tipo = defaultdict(list)
    for m in mems:
        por_tipo[m.get("tipo") or "outros"].append(m)
    for tipo, items in por_tipo.items():
        linhas = [f"# Memórias LIBERTUS — tipo: {tipo}\n"]
        for m in items:
            titulo = (m.get("titulo") or "").strip()
            conteudo = (m.get("conteudo") or "").strip()
            tags = ", ".join(m.get("tags") or [])
            linhas.append(f"\n## {titulo}\n")
            if tags:
                linhas.append(f"_Tags: {tags}_\n")
            if conteudo:
                linhas.append(f"{conteudo}\n")
        (d / f"{slug(tipo)}.md").write_text("\n".join(linhas), encoding="utf-8")
    return len(por_tipo), len(mems)


def copiar_core():
    """Copia os módulos-chave do cérebro (não tudo — só o que é conhecimento)."""
    d = CORPUS / "core"
    d.mkdir(parents=True, exist_ok=True)
    chave = [
        "grafo_cognitivo.py", "groq_client.py", "claude_client.py",
        "libertus_rag.py", "pentest_pipeline.py", "motor_decisao.py",
        "identidade_cognitiva.py", "sistema_objetivos.py", "auto_evolucao.py",
        "memoria_local.py", "supabase_client.py", "reconhecimento.py",
    ]
    n = 0
    for nome in chave:
        src = BASE / "core" / nome
        if src.exists():
            shutil.copy2(src, d / nome)
            n += 1
    return n


def copiar_skills():
    """Copia SKILL.md das skills do LIBERTUS (identidade/devops)."""
    d = CORPUS / "skills"
    d.mkdir(parents=True, exist_ok=True)
    n = 0
    skills_dir = Path.home() / ".hermes" / "skills" / "devops"
    if skills_dir.exists():
        for sk in skills_dir.glob("libertus-*/SKILL.md"):
            dest = d / f"{sk.parent.name}.md"
            shutil.copy2(sk, dest)
            n += 1
    # alma / identidade
    alma = Path.home() / ".hermes" / "HERMES.md"
    if alma.exists():
        shutil.copy2(alma, d / "alma-libertus.md")
        n += 1
    return n


def main():
    print("=== MONTAR CORPUS GRAPHIFY ===")
    if CORPUS.exists():
        shutil.rmtree(CORPUS)
    CORPUS.mkdir(parents=True)

    print("Puxando memórias do Supabase...")
    mems = puxar_memorias()
    n_tipos, n_mems = escrever_memorias(mems)
    print(f"  {n_mems} memórias em {n_tipos} arquivos por tipo")

    n_core = copiar_core()
    print(f"  {n_core} módulos core copiados")

    n_sk = copiar_skills()
    print(f"  {n_sk} skills/alma copiadas")

    # inventário
    total = sum(1 for _ in CORPUS.rglob("*") if _.is_file())
    print(f"\n✅ corpus montado: {CORPUS}  ({total} arquivos)")


if __name__ == "__main__":
    main()
