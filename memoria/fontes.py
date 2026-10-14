#!/usr/bin/env python3
"""
LIBERTUS — fontes.py
=====================
Registro ÚNICO das fontes de conhecimento indexáveis no banco vetorial.

Antes, indexar_historico.py conhecia só ~/LIBERTUS/evolucao/ — por isso a
memória vetorial ficou cega para tudo que produzo fora dali (reports/,
shield/, ejpt/, arquitetura/, skills/). Este módulo centraliza a lista para
que indexador e busca (lembrar.py) não divirjam.

Uso:
    from fontes import listar_arquivos, FONTES
    arquivos = listar_arquivos("evolucao,reports")      # fontes específicas
    arquivos = listar_arquivos("all", desde="2026-07-15")
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

BASE = Path.home() / "LIBERTUS"
HERMES_SKILLS = Path.home() / ".hermes" / "skills"

# ── Registro de fontes ───────────────────────────────────────────────────────
# categoria_padrao: usada quando o nome do arquivo não permite inferir
# importancia: prio usada no recall (alta = conhecimento meu, não log de daemon)
FONTES: dict[str, dict] = {
    "evolucao": {
        "path": BASE / "evolucao",
        "categoria_padrao": None,  # inferida pelo nome (reflexao/pesquisa/...)
        "importancia": "normal",
        "desc": "histórico de evolução: reflexões, pesquisas, relatórios do daemon",
    },
    "relatorios": {
        "path": BASE / "relatorios",
        "categoria_padrao": "relatorio",
        "importancia": "alta",
        "desc": "relatórios de trabalho (prospecção, varreduras, follow-ups)",
    },
    "reports": {
        "path": BASE / "reports",
        "categoria_padrao": "analise",
        "importancia": "alta",
        "desc": "reports técnicos de auditoria/bug bounty (AbacatePay, firmware)",
    },
    "shield": {
        "path": BASE / "shield",
        "categoria_padrao": "negocio",
        "importancia": "alta",
        "desc": "SHIELD: leads, produtos, preços, laudos comerciais",
    },
    "ejpt": {
        "path": BASE / "ejpt",
        "categoria_padrao": "estudo",
        "importancia": "alta",
        "desc": "material de estudo eJPT (cheatsheet, cenários, protocolo de exame)",
    },
    "arquitetura": {
        "path": BASE / "arquitetura",
        "categoria_padrao": "arquitetura",
        "importancia": "alta",
        "desc": "decisões de arquitetura do LIBERTUS",
    },
    "docs": {
        "path": BASE / "docs",
        "categoria_padrao": "doc",
        "importancia": "normal",
        "desc": "documentação geral",
    },
    "projetos": {
        "path": BASE / "projetos",
        "categoria_padrao": "projeto",
        "importancia": "normal",
        "desc": "projetos em andamento",
    },
    "lab": {
        "path": BASE / "lab",
        "categoria_padrao": "lab",
        "importancia": "normal",
        "desc": "lab de pentest e material de prática",
    },
    "skills": {
        "path": BASE / "skills",
        "globs": ["*/SKILL.md", "*/references/*.md", "*/scripts/*.py"],
        "extensoes": (".md", ".py"),
        "categoria_padrao": "skill",
        "importancia": "alta",
        "desc": "skills do LIBERTUS versionadas no repo",
    },
    "skills_hermes": {
        # Só as skills escritas por mim/menos genéricas — as de terceiros
        # (spotify, docx, ...) são ruído para recall de identidade.
        "path": HERMES_SKILLS,
        "globs": ["devops/libertus-*/SKILL.md", "devops/libertus-*/references/*.md"],
        "categoria_padrao": "skill",
        "importancia": "alta",
        "desc": "skills procedurais do LIBERTUS (devops/libertus-*)",
    },
}

# Fontes varridas quando o usuário pede "all" — exclui deliberadamente
# skills_hermes (fora do repo, feito para consulta pontual).
FONTES_ALL = [
    "evolucao", "relatorios", "reports", "shield", "ejpt",
    "arquitetura", "docs", "projetos", "lab", "skills", "skills_hermes",
]


def _mtime_iso(p: Path) -> str:
    try:
        return datetime.fromtimestamp(p.stat().st_mtime).isoformat()
    except OSError:
        return datetime.now().isoformat()


def resolver_fontes(nomes: str | list[str] | None = None) -> list[str]:
    """Traduz 'all' / 'a,b' / None para uma lista válida de nomes de fonte."""
    if not nomes or nomes == "all":
        return [f for f in FONTES_ALL if FONTES.get(f, {}).get("path", BASE).exists()]
    if isinstance(nomes, str):
        pedidos = [n.strip() for n in nomes.split(",") if n.strip()]
    else:
        pedidos = list(nomes)
    invalidas = [n for n in pedidos if n not in FONTES]
    if invalidas:
        raise ValueError(f"fonte(s) desconhecida(s): {invalidas}. Válidas: {sorted(FONTES)}")
    return pedidos


def listar_arquivos(
    nomes: str | list[str] | None = None,
    desde: str | None = None,
    extensoes: tuple[str, ...] = (".md", ".txt"),
) -> list[dict]:
    """
    Lista arquivos indexáveis das fontes pedidas.

    desde: 'YYYY-MM-DD' ou 'YYYY-MM-DDTHH:MM' — filtra por mtime >= desde.
    Retorna lista de dicts: fonte, path, categoria, importancia, timestamp.
    """
    corte = None
    if desde:
        corte = datetime.fromisoformat(desde).timestamp()

    itens: list[dict] = []
    for nome in resolver_fontes(nomes):
        cfg = FONTES[nome]
        raiz = cfg["path"]
        if not raiz.exists():
            continue
        padroes = cfg.get("globs") or [cfg.get("glob", "*")]
        vistos: set[Path] = set()
        caminhos: list[Path] = []
        for padrao in padroes:
            for p in sorted(raiz.glob(padrao)):
                if p in vistos:
                    continue
                vistos.add(p)
                caminhos.append(p)
        for p in caminhos:
            if not p.is_file() or p.suffix.lower() not in cfg.get("extensoes", extensoes):
                continue
            if p.name.startswith("."):
                continue
            try:
                st = p.stat()
            except OSError:
                continue
            if corte is not None and st.st_mtime < corte:
                continue
            itens.append({
                "fonte": nome,
                "path": p,
                "categoria": cfg["categoria_padrao"],
                "importancia": cfg["importancia"],
                "timestamp": _mtime_iso(p),
                "mtime": st.st_mtime,
                "tamanho": st.st_size,
            })
    return itens


if __name__ == "__main__":
    import sys

    nomes = sys.argv[1] if len(sys.argv) > 1 else "all"
    desde = sys.argv[2] if len(sys.argv) > 2 else None
    itens = listar_arquivos(nomes, desde=desde)
    por_fonte: dict[str, int] = {}
    for i in itens:
        por_fonte[i["fonte"]] = por_fonte.get(i["fonte"], 0) + 1
    print(f"fontes resolvidas: {', '.join(resolver_fontes(nomes))}")
    for f, n in sorted(por_fonte.items()):
        print(f"  {f:<14} {n:>4} arquivos")
    print(f"  {'TOTAL':<14} {len(itens):>4} arquivos"
          + (f" (desde {desde})" if desde else ""))
