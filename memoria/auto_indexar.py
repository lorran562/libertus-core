#!/usr/bin/env python3
"""
LIBERTUS — auto_indexar.py
==========================
Guardião da memória vetorial. Responde uma pergunta só:

    "eu já sei tudo que produzi, ou minha memória está desatualizada?"

Causa-raiz que este script resolve: entre 15/07/2026 e 14/10/2026 a indexação
simplesmente parou — ninguém chamava indexar_historico.py. Resultado: 3 meses
de trabalho (AbacatePay, APK RE, SHIELD, eJPT) invisíveis para busca semântica.
Memória sem manutenção automática apodrece, por melhor que seja o script.

Como funciona: compara o mtime/tamanho de cada arquivo com o manifest gravado
na última indexação. Se nada mudou, sai em milissegundos (não carrega modelo,
não encosta no banco). Se algo mudou, chama o indexador incremental.

Uso:
  venv/bin/python memoria/auto_indexar.py            # verifica e conserta
  venv/bin/python memoria/auto_indexar.py --quiet    # usado no briefing
  venv/bin/python memoria/auto_indexar.py --supabase # inclui memória do Supabase
  venv/bin/python memoria/auto_indexar.py --check    # só diz se está em dia
"""

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

MEM_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(MEM_DIR))

from fontes import FONTES, listar_arquivos, resolver_fontes  # noqa: E402

MANIFEST = MEM_DIR / "index_manifest.json"
SUPA_STATE = MEM_DIR / "ultimo_index_supabase.json"
SUPA_DUMP = MEM_DIR.parent / "backups" / "supabase" / "latest"


def _manifest() -> dict:
    if not MANIFEST.exists():
        return {}
    try:
        return json.loads(MANIFEST.read_text(encoding="utf-8")).get("fontes", {})
    except Exception:
        return {}


def _hash_arquivo(p: Path) -> str:
    """Mesmo algoritmo do indexador — comparação por CONTEÚDO, não por mtime.

    mtime gera falso-positivo (arquivo reescrito com conteúdo idêntico faz o
    guardião carregar o modelo por nada, ~11s perdidos em cada briefing).
    """
    try:
        # .strip() é obrigatório: o indexador hasheia o conteúdo JÁ normalizado.
        conteudo = p.read_text(encoding="utf-8", errors="replace").strip()
        return hashlib.md5(conteudo.encode()).hexdigest()[:12]
    except OSError:
        return ""


def pendencias(fontes_txt: str = "all") -> dict:
    """Arquivos novos/alterados/removidos em relação ao manifest da última indexação."""
    man = _manifest()
    if not man:
        return {"sem_manifest": True, "novos": -1, "alterados": -1, "removidos": -1,
                "arquivos": []}

    novos, alterados, arquivos = 0, 0, []
    vistos: dict[str, set[str]] = {}

    for nome in resolver_fontes(fontes_txt):
        raiz = FONTES[nome]["path"]
        vistos[nome] = set()
        for item in listar_arquivos([nome]):
            try:
                rel = str(item["path"].relative_to(raiz))
            except ValueError:
                rel = item["path"].name
            vistos[nome].add(rel)
            antigo = man.get(nome, {}).get(rel)
            if antigo is None:
                novos += 1
                arquivos.append(f"{nome}/{rel} (novo)")
            elif int(antigo.get("size", -1)) != item["tamanho"] or \
                    _hash_arquivo(item["path"]) != antigo.get("hash"):
                alterados += 1
                arquivos.append(f"{nome}/{rel} (alterado)")

    removidos = 0
    for nome, mapeados in man.items():
        if nome not in vistos:
            continue
        for rel in mapeados:
            if rel not in vistos[nome]:
                removidos += 1

    return {"sem_manifest": False, "novos": novos, "alterados": alterados,
            "removidos": removidos, "arquivos": arquivos,
            "total_manifesto": sum(len(v) for v in man.values())}


def _dump_idade_horas():
    """Idade do dump mais recente, em horas (None se não existe)."""
    if not SUPA_DUMP.exists():
        return None
    try:
        return (time.time() - SUPA_DUMP.resolve().stat().st_mtime) / 3600.0
    except OSError:
        return None


def _supabase_pendente() -> bool:
    """O dump do Supabase é mais novo que a última indexação dele?"""
    if not SUPA_DUMP.exists() or not SUPA_STATE.exists():
        return bool(SUPA_DUMP.exists())
    try:
        estado = json.loads(SUPA_STATE.read_text(encoding="utf-8"))
        dump_indexado = Path(estado.get("dump", "")).name
        return dump_indexado != SUPA_DUMP.resolve().name
    except Exception:
        return True


def main() -> int:
    import sys as _s
    from pathlib import Path as _P
    _s.path.insert(0, str(_P(__file__).resolve().parent.parent))
    from core.ambiente import sanear_ambiente
    sanear_ambiente()

    ap = argparse.ArgumentParser(
        description="LIBERTUS: mantém a memória vetorial em dia com o que eu produzo")
    ap.add_argument("--fontes", default="all", help="all | lista separada por vírgula")
    ap.add_argument("--quiet", action="store_true", help="Fala só quando há trabalho")
    ap.add_argument("--check", action="store_true", help="Só verifica, não indexa")
    ap.add_argument("--supabase", action="store_true",
                    help="Inclui a memória do Supabase (usa o dump local)")
    ap.add_argument("--baixar-supabase", action="store_true",
                    help="Atualiza o dump do Supabase antes de indexar (usa rede)")
    ap.add_argument("--idade-max-horas", type=float, default=6.0,
                    help="Com --baixar-supabase: só baixa se o dump for mais velho que isso")
    args = ap.parse_args()

    t0 = time.time()
    pend = pendencias(args.fontes)

    supa_pend = _supabase_pendente() if args.supabase or args.baixar_supabase else False

    # Decidir o download do dump ANTES do early-return: senão o briefing com
    # --baixar-supabase sairia em 0.07s concluindo "nada a fazer" com dump velho.
    baixar_supa = False
    if args.baixar_supabase:
        idade = _dump_idade_horas()
        baixar_supa = idade is None or idade >= args.idade_max_horas
        if not baixar_supa and not args.quiet:
            print(f"[memoria] dump do Supabase recente ({idade:.1f}h) — sem download")

    if pend["sem_manifest"]:
        situacao = "sem manifest — memória nunca indexada por este script"
        trabalho = True
    else:
        n = pend["novos"] + pend["alterados"]
        situacao = (f"{pend['novos']} novos, {pend['alterados']} alterados, "
                    f"{pend['removidos']} removidos") if n or pend["removidos"] \
            else f"em dia ({pend['total_manifesto']} arquivos no manifesto)"
        trabalho = bool(n)

    if args.check:
        print(f"[memoria] fontes={args.fontes} | {situacao}"
              + (" | supabase: dump novo" if supa_pend else ""))
        for a in pend["arquivos"][:15]:
            print(f"    - {a}")
        return 0 if not trabalho and not supa_pend else 1

    if not trabalho and not supa_pend and not baixar_supa:
        if not args.quiet:
            print(f"[memoria] {situacao} — nada a indexar ({time.time()-t0:.2f}s)")
        return 0

    if not args.quiet:
        print(f"[memoria] indexando: {situacao}")
        for a in pend["arquivos"][:15]:
            print(f"    - {a}")

    if trabalho or pend["sem_manifest"]:
        import indexar_historico
        indexar_historico._executar(args.fontes, "", False, False)

    falhou = False
    if supa_pend or baixar_supa or args.supabase:
        import indexar_supabase
        # O retorno era descartado: o indexador podia falhar e o processo sair 0,
        # então nem o cron nem o `if !` do wrapper percebiam o banco parado.
        if indexar_supabase.indexar(baixar=baixar_supa, dry_run=False) != 0:
            falhou = True
            import os
            print("[memoria] ERRO: indexacao do Supabase falhou.", file=sys.stderr)
            if os.environ.get("PYTHONPATH"):
                print(f"[memoria]   PYTHONPATH herdado: {os.environ['PYTHONPATH']}",
                      file=sys.stderr)
                print("[memoria]   sintoma classico: numpy de outro python quebra o venv. "
                      "Use ~/LIBERTUS/scripts/py (limpa PYTHONPATH).", file=sys.stderr)

    if not args.quiet and not falhou:
        print(f"[memoria] memória atualizada em {time.time()-t0:.1f}s")
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
