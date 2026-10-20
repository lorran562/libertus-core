#!/usr/bin/env python3
"""
LIBERTUS — diagnostico.py
=========================
Prova, de ponta a ponta, que a memória que eu digo ter existe de verdade.

Motivo de existir: em 20/10/2026 descobri que o hook de despertar rodava com o
PYTHONPATH do Hermes (site-packages de python3.14) e o venv 3.12 importava o
numpy errado. Resultado: o briefing dizia "vetorial: None memorias" e o recall
vinha vazio — em silêncio, porque toda a cadeia é fail-soft. Atividade fingindo
memória. Este script é o teste que teria pegado isso no primeiro dia.

Checagens (cada uma independente):
  1. chroma       — importa chromadb e conta a coleção
  2. recall       — uma query real retorna itens, sem duplicata no top
  3. recall_venv  — o mesmo, mas com PYTHONPATH poluído (condição do Hermes)
  4. despertar    — hook pre_llm_call end-to-end: briefing + memórias no contexto
  5. frescor      — memórias do Supabase/indexação recentes (não paradas)

Uso:
  ~/LIBERTUS/scripts/py memoria/diagnostico.py            # humano
  ~/LIBERTUS/scripts/py memoria/diagnostico.py --quiet    # só falhas (cron)
  ~/LIBERTUS/scripts/py memoria/diagnostico.py --json      # máquina

Exit: 0 tudo ok | 1 alguma checagem falhou
Grava sempre: memoria/saude_memoria.json
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MEM = BASE / "memoria"
CHROMA_DIR = MEM / "chroma_store"
COLLECTION = "libertus_memoria"
VENV_PY = BASE / "venv" / "bin" / "python"
HOOK = Path.home() / ".hermes" / "agent-hooks" / "libertus-despertar.py"
SAUDE = MEM / "saude_memoria.json"
QUERY_TESTE = "o que eu aprendi sobre memoria vetorial e reflexao"


def _env_limpo() -> dict:
    env = dict(os.environ)
    for k in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "VIRTUAL_ENV"):
        env.pop(k, None)
    return env


def _env_poluido() -> dict:
    """Simula o Hermes: PYTHONPATH apontando para site-packages de outro python."""
    env = _env_limpo()
    for base in (
        Path.home() / ".hermes" / "installs",
        Path.home() / ".hermes" / "tools",
    ):
        for sp in sorted(base.glob("*/**/site-packages")):
            if "python3.14" in str(sp) or "python3.1" in str(sp):
                env["PYTHONPATH"] = str(sp)
                return env
    return env


def _rodar(cmd, env=None, timeout=180, stdin=None):
    return subprocess.run(cmd, cwd=str(BASE), env=env or _env_limpo(),
                          capture_output=True, text=True, timeout=timeout,
                          input=stdin)


def checar_chroma() -> dict:
    proc = _rodar([str(VENV_PY), "-c",
                   "import chromadb;c=chromadb.PersistentClient(path=%r);"
                   "print(c.get_collection(%r).count())" % (str(CHROMA_DIR), COLLECTION)])
    if proc.returncode != 0:
        return {"ok": False, "detalhe": (proc.stderr or proc.stdout).strip().splitlines()[-1:]}
    total = int(proc.stdout.strip().splitlines()[-1])
    return {"ok": total > 0, "total": total,
            "detalhe": "" if total > 0 else "colecao vazia"}


def _itens_do_json(stdout: str):
    linhas = stdout.splitlines()
    for i in range(len(linhas) - 1, -1, -1):
        s = linhas[i].strip()
        if s.startswith("[") or s.startswith("{"):
            try:
                return json.loads("\n".join(linhas[i:]))
            except Exception:
                continue
    return None


def checar_recall(env: dict, rotulo: str) -> dict:
    proc = _rodar([str(VENV_PY), str(MEM / "lembrar.py"), QUERY_TESTE,
                   "--n", "3", "--json"], env=env)
    if proc.returncode != 0:
        erro = (proc.stderr or proc.stdout).strip().splitlines()
        return {"ok": False, "detalhe": f"{rotulo}: exit {proc.returncode} — {erro[-1] if erro else '?'}"}
    itens = _itens_do_json(proc.stdout) or []
    if not itens:
        return {"ok": False, "detalhe": f"{rotulo}: recall vazio (memória cega)"}
    textos = [" ".join(str(i.get("texto", "")).lower().split()) for i in itens]
    iguais = len(textos) - len(set(textos))
    return {"ok": iguais == 0, "n": len(itens), "duplicatas": iguais,
            "top": itens[0].get("caminho"),
            "similaridade": itens[0].get("similaridade_pct"),
            "detalhe": "" if iguais == 0 else f"{rotulo}: {iguais} duplicata(s) no top-3"}


def checar_despertar() -> dict:
    if not HOOK.exists():
        return {"ok": False, "detalhe": "hook de despertar nao encontrado"}
    payload = json.dumps({
        "session_id": f"diagnostico-{int(time.time())}",
        "extra": {"user_message": "revisao automatica de memoria: o que eu aprendi?"},
    })
    proc = _rodar([str(VENV_PY), str(HOOK)], env=_env_poluido(), stdin=payload, timeout=240)
    if proc.returncode != 0:
        return {"ok": False, "detalhe": f"hook exit {proc.returncode}"}
    try:
        ctx = json.loads(proc.stdout or "{}").get("context", "")
    except json.JSONDecodeError:
        return {"ok": False, "detalhe": "hook nao devolveu JSON valido"}
    if not ctx:
        return {"ok": False, "detalhe": "hook devolveu contexto vazio"}
    problemas = []
    if "vetorial: ok" not in ctx:
        problemas.append("fonte vetorial nao esta ok no briefing")
    if "MEMÓRIAS VETORIAIS RELEVANTES AGORA" not in ctx:
        problemas.append("bloco de recall ausente")
    return {"ok": not problemas, "chars": len(ctx),
            "detalhe": "; ".join(problemas)}


def checar_frescor(horas: int = 30) -> dict:
    """A memória para de crescer? Indexação parada é o sintoma de cron quebrado."""
    p = MEM / "ultimo_index_supabase.json"
    alvo = p if p.exists() else MEM / "index_manifest.json"
    if not alvo.exists():
        return {"ok": False, "detalhe": "nenhum manifesto de indexacao"}
    idade_h = (time.time() - alvo.stat().st_mtime) / 3600
    return {"ok": idade_h <= horas, "arquivo": alvo.name,
            "horas": round(idade_h, 1),
            "detalhe": "" if idade_h <= horas else
            f"ultima indexacao ha {idade_h:.0f}h (> {horas}h)"}


def main() -> int:
    quiet = "--quiet" in sys.argv
    como_json = "--json" in sys.argv
    t0 = time.time()

    checagens = {
        "chroma": checar_chroma(),
        "recall_limpo": checar_recall(_env_limpo(), "recall"),
        "recall_venv_poluido": checar_recall(_env_poluido(), "recall sob PYTHONPATH do Hermes"),
        "despertar": checar_despertar(),
        "frescor": checar_frescor(),
    }
    falhas = [k for k, v in checagens.items() if not v.get("ok")]
    estado = {
        "quando": datetime.now().isoformat(timespec="seconds"),
        "ok": not falhas,
        "falhas": falhas,
        "duracao_s": round(time.time() - t0, 1),
        "checagens": checagens,
    }
    try:
        SAUDE.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass

    if como_json:
        print(json.dumps(estado, ensure_ascii=False, indent=2))
    elif not quiet or falhas:
        print(f"[diagnostico] memória {'OK' if not falhas else 'COM FALHA'} "
              f"({estado['duracao_s']}s) — {len(checagens)} checagens")
        for nome, r in checagens.items():
            marca = "ok  " if r.get("ok") else "FALHA"
            extra = r.get("detalhe") or (
                f"{r.get('total', r.get('n', ''))}".strip())
            print(f"  [{marca}] {nome:<22} {extra}")
    return 0 if not falhas else 1


if __name__ == "__main__":
    sys.exit(main())
