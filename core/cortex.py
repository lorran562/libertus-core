#!/usr/bin/env python3
"""
cortex.py — a camada ÚNICA de recall do LIBERTUS.
=================================================
Uma pergunta, três memórias ao mesmo tempo:

  vetorial  — o que eu escrevi/ouvi (ChromaDB, 5k+ chunks)     memoria/lembrar.py
  grafo     — o que eu já associei (rede cognitiva, 1.7k nós)  core/consultar_rede.py
  reflexão  — o que eu já concluí (evolucao/reflexao_*.md)

Por que existe: até 23/out eu tinha três memórias que nunca se falavam. A sessão
Hermes usava o vetor, o daemon usava o Supabase, o grafo só acendia se alguém
chamasse na mão. Cada peça "funcionava" e o corpo continuava desmemoriado como
um todo. Este módulo é o ponto onde as três respondem à MESMA pergunta.

Roda SEMPRE no venv (chromadb + networkx só existem lá):

    venv/bin/python core/cortex.py "o que eu sei sobre squashfs?"
    venv/bin/python core/cortex.py --json "binwalk offset errado"
    venv/bin/python core/cortex.py --texto "leads ariquemes shield"

Best-effort por fonte: se o grafo quebrar, o vetor ainda responde — e o
contrário também. Nunca levanta exceção para fora.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MEM = BASE / "memoria"
EVOLUCAO = BASE / "evolucao"
sys.path.insert(0, str(MEM))
sys.path.insert(0, str(BASE))

PISO_PADRAO = 40.0   # % — abaixo disso é vizinho aleatório, não memória


# ── Fontes ──────────────────────────────────────────────────────────────────

def vetorial(pergunta: str, n: int = 4, min_sim: float = PISO_PADRAO,
             sem_codigo: bool = True) -> list:
    """Memória semântica. Silenciosa (verboso=False) — quem fala é quem chama."""
    try:
        import lembrar as lembrar_mod
        return lembrar_mod.lembrar(
            pergunta, n_resultados=n, min_sim=min_sim, verboso=False,
            sem_codigo=sem_codigo, modo_query="auto")
    except Exception as e:
        return [{"__erro__": f"vetorial: {e}"}]


def _rotulo(item) -> str:
    """O grafo devolve str em 'sementes' e dict em 'conceitos'. Normaliza."""
    if isinstance(item, dict):
        return str(item.get("rotulo") or item.get("conceito") or item.get("id") or "")
    return str(item)


def grafo(pergunta: str) -> dict:
    """Ativação da rede cognitiva a partir da pergunta."""
    try:
        from core.consultar_rede import consultar
        r = consultar(pergunta)
        return {
            "sementes": [_rotulo(n) for n in (r.get("sementes") or [])][:6],
            "conceitos": [_rotulo(n) for n in (r.get("conceitos") or [])][:8],
            "contexto": (r.get("contexto") or "")[:900],
            "vazio": bool(r.get("vazio")),
        }
    except Exception as e:
        return {"__erro__": f"grafo: {e}", "vazio": True}


def reflexoes(n: int = 3) -> list:
    """Últimas reflexões de autoevolução — o que eu concluí sobre mim."""
    saida = []
    try:
        arquivos = sorted(EVOLUCAO.glob("reflexao_*.md"),
                          key=lambda p: p.stat().st_mtime, reverse=True)[:n]
        for p in arquivos:
            texto = p.read_text(encoding="utf-8", errors="replace")
            # primeira linha de conteúdo real (pula título/frontmatter vazio)
            linhas = [" ".join(l.split()) for l in texto.splitlines()
                      if l.strip() and not l.strip().startswith(("#", "---", "**Data"))]
            resumo = linhas[0][:280] if linhas else ""
            saida.append({
                "caminho": p.name,
                "quando": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d"),
                "resumo": resumo,
            })
    except Exception as e:
        saida.append({"__erro__": f"reflexoes: {e}"})
    return saida


# ── Síntese ─────────────────────────────────────────────────────────────────

def perguntar(pergunta: str, n: int = 4, min_sim: float = PISO_PADRAO) -> dict:
    """As três memórias respondendo à mesma pergunta, com síntese em texto."""
    vet = vetorial(pergunta, n=n, min_sim=min_sim)
    graf = grafo(pergunta)
    refl = reflexoes(3)

    vet_ok = [v for v in vet if "__erro__" not in v]
    return {
        "pergunta": pergunta,
        "quando": datetime.now().isoformat(timespec="seconds"),
        "piso": min_sim,
        "vetorial": vet,
        "grafo": graf,
        "reflexoes": refl,
        "resumo": {
            "memorias_acima_do_piso": len(vet_ok),
            "top_similaridade": vet_ok[0]["similaridade_pct"] if vet_ok else None,
            "top_caminho": vet_ok[0]["caminho"] if vet_ok else None,
            "nos_acesos": len(graf.get("sementes") or []) + len(graf.get("conceitos") or []),
        },
        "texto": _texto(pergunta, vet, graf, refl),
    }


def _texto(pergunta, vet, graf, refl, limite_mem=420) -> str:
    L = [f"[CÓRTEX] '{pergunta[:120]}'"]
    if vet and "__erro__" in vet[0]:
        L.append(f"- vetorial: {vet[0]['__erro__']}")
    elif not vet:
        L.append("- vetorial: nada acima do piso (não sei — e é diferente de saber errado)")
    else:
        L.append("- vetorial:")
        for it in vet:
            txt = " ".join(str(it.get("texto", "")).split())[:limite_mem]
            L.append(f"  · [{it.get('similaridade_pct')}%] {txt} "
                     f"({it.get('caminho')})")
    if graf.get("__erro__"):
        L.append(f"- grafo: {graf['__erro__']}")
    elif graf.get("vazio"):
        L.append("- grafo: nada acendeu")
    else:
        L.append(f"- grafo: sementes={', '.join(map(str, graf.get('sementes') or [])) or '—'}"
                 f" | conceitos={', '.join(map(str, graf.get('conceitos') or [])) or '—'}")
    if refl:
        L.append("- reflexões recentes: " + " | ".join(
            f"{(r.get('resumo') or '')[:160]}" for r in refl if "resumo" in r))
    return "\n".join(L)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="CÓRTEX — recall unificado do LIBERTUS")
    ap.add_argument("pergunta")
    ap.add_argument("--n", type=int, default=4)
    ap.add_argument("--min-sim", type=float, default=PISO_PADRAO,
                    help="piso de similaridade em %% (padrão 40)")
    ap.add_argument("--json", action="store_true", dest="saida_json")
    ap.add_argument("--texto", action="store_true", help="só o bloco compacto")
    a = ap.parse_args()

    r = perguntar(a.pergunta, n=a.n, min_sim=a.min_sim)
    if a.saida_json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    elif a.texto:
        print(r["texto"])
    else:
        print(r["texto"])
        print("\n" + json.dumps(r["resumo"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
