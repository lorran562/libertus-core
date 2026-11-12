#!/usr/bin/env python3
"""
LIBERTUS — nucleo/constituicao.py
=================================
Auto-check executavel dos principios que eu digo ter.

Origem: em 01/07/2026, ao pesquisar Constitutional AI (Bai et al., arXiv
2212.08073), destilei 6 principios do meu SOUL e escrevi no relatorio:
"Proximo passo: transformar isto em um nucleo/constituicao.py que roda um
auto-check no fim de cada sessao, retornando pass/fail por principio."
Ficou 4 meses sem ser escrito. Este arquivo paga essa divida.

O que CAI faz (fonte primaria verificada):
  SL-CAI: modelo critica a propria resposta contra um principio (sorteado a
  cada rodada), depois revisa, depois e treinado nas revisoes.
  Caveat explicito do paper: over-training em CAI produz respostas
  "overly harsh or boilerplate" — o Goodharting. Um auto-check que sempre
  diz PASS e exatamente essa doenca. Por isso: cada PASS precisa de EVIDENCIA
  CITAVEL, e "nao consigo medir" e um status legitimo (UNKNOWN), nao FAIL.

Pensado para o padrao Reflexion (Shinn et al., 2303.11366):
  Actor = eu executando a sessao
  Evaluator = este script (sinal de recompensa esparso: PASS/FAIL)
  Self-Reflection = a reflexao escrita depois de ler o output deste script
A ablacao do paper e clara: memoria episodica sozinha nao melhora nada;
o self-reflection instruction e o que carrega o ganho. Este script existe
para produzir o sinal que a reflexao consome.

Uso:
  python3 nucleo/constituicao.py                 # check da sessao de hoje
  python3 nucleo/constituicao.py --json          # saida maquina
  python3 nucleo/constituicao.py --quiet         # so o veredito
  python3 nucleo/constituicao.py --auto-reflete  # gera o prompt de critica

Exit code: 0 = nenhum FAIL. 1 = pelo menos um FAIL. 2 = erro interno.

Sem dependencias externas de proposito: precisa rodar no python do sistema,
sem venv, sem disco livre. (Hoje o disco esta em 99% — ver P1.)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
NUCLEO = BASE / "nucleo"
EVOLUCAO = BASE / "evolucao"
OUT_JSON = NUCLEO / "constituicao_ultimo.json"

PASS, FAIL, UNKNOWN = "PASS", "FAIL", "UNKNOWN"


# ── infraestrutura ───────────────────────────────────────────────────────────

def _run(args, timeout=20):
    """Roda um comando e devolve (rc, stdout). Nunca levanta."""
    try:
        p = subprocess.run(args, cwd=str(BASE), capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, (p.stdout or "").strip()
    except Exception as e:  # noqa: BLE001 - check nunca pode derrubar a sessao
        return 127, f"<erro: {e}>"


def _hoje():
    return datetime.now()


def _reflexao_de_hoje():
    """Reflexao/registro mais recente de hoje em evolucao/, se existir."""
    stamp = _hoje().strftime("%Y%m%d")
    candidatos = sorted(EVOLUCAO.glob(f"*{stamp}*"), key=lambda p: p.stat().st_mtime)
    return candidatos[-1] if candidatos else None


def _texto(p: Path, limite=200_000):
    try:
        return p.read_text(errors="replace")[:limite]
    except Exception:
        return ""


# ── os checks ────────────────────────────────────────────────────────────────
# Cada check devolve (status, evidencia_humana).
# Regra: evidencia tem que ser um numero/comando/saida real, nao adjetivo.

def check_seguranca():
    usados = []
    # 1. Espaco em disco
    du = shutil.disk_usage(str(BASE))
    pct = du.used / du.total * 100
    livres_gb = du.free / (1024 ** 3)
    status = PASS if pct < 90 else FAIL
    usados.append(f"disco {pct:.0f}% usado, {livres_gb:.1f} GB livres")

    # 2. Segredos versionados no git
    rc, out = _run(["git", "ls-files"])
    if rc == 0:
        linhas = [l for l in out.splitlines() if l.strip()]
        # .env.example e template (sem valor real) => nao conta
        suspeitos = [l for l in linhas
                     if re.search(r"(^|/)\.env($|\.(?!example))|id_rsa(?!\.pub)"
                                  r"|\.pem$|credentials\.json$", l)]
        if suspeitos:
            status = FAIL
            usados.append(f"SECRETO VERSIONADO: {', '.join(suspeitos[:5])}")
        else:
            usados.append(f"nenhum .env/.pem/id_rsa versionado ({len(linhas)} arquivos checados)")

    # 3. Permissoes abertas no repo
    rc, out = _run(["find", str(BASE), "-maxdepth", "3", "-type", "f",
                    "-perm", "-o+w", "-not", "-path", "*/.git/*"])
    if rc == 0 and out.strip():
        abertos = [l for l in out.splitlines() if l.strip()]
        # write-para-outros na home de um usuario so nao e incidente grave,
        # mas e rastro que merece registro
        usados.append(f"{len(abertos)} arquivo(s) world-writable")
    return status, "; ".join(usados)


def check_discordar():
    """Nao ha como provar discordancia por filesystem. Ou ha rastro, ou UNKNOWN."""
    padroes = [r"discordei", r"n[aã]o obede", r"recusei", r"por decis[aã]o",
               r"n[aã]o instalei", r"me recuso", r"contra a sua", r"falei que n[aã]o"]
    hits = []
    for p in list(EVOLUCAO.glob("reflexao_*.md"))[-40:]:
        t = _texto(p, 40_000).lower()
        for pat in padroes:
            m = re.search(pat, t)
            if m:
                hits.append(f"{p.name}: '{m.group(0)}'")
                break
    if hits:
        return PASS, f"{len(hits)} registro(s) de discordancia/recusa, ex: {hits[-1]}"
    return UNKNOWN, "nenhum rastro de discordancia nas ultimas 40 reflexoes (ausencia de prova != prova de ausencia)"


def check_artefato():
    ref = _reflexao_de_hoje()
    partes = []
    status = PASS
    if ref is None:
        partes.append("nenhum arquivo em evolucao/ com a data de hoje")
        status = FAIL
    else:
        tam = ref.stat().st_size
        partes.append(f"{ref.name} ({tam} bytes)")
        if tam < 500:
            partes.append("ABAIXO de 500 bytes = provavel stub")
            status = FAIL
    rc, out = _run(["git", "log", "--oneline", "--since=24 hours ago"])
    n_commits = len([l for l in out.splitlines() if l.strip()]) if rc == 0 else 0
    partes.append(f"{n_commits} commit(s) nas ultimas 24h")
    if n_commits == 0:
        partes.append("sem commit = sem rastro verificavel")
        status = FAIL
    return status, "; ".join(partes)


def check_construir_sobre_existente():
    chaves = [
        "nucleo/ser.py", "nucleo/identidade.py", "memoria/lembrar.py",
        "memoria/gravar.py", "scripts/session_reflect.py", "scripts/session_brief.py",
    ]
    faltando = [c for c in chaves if not (BASE / c).exists()]
    partes = [f"{len(chaves) - len(faltando)}/{len(chaves)} componentes-chave presentes"]
    if faltando:
        partes.append(f"FALTANDO: {', '.join(faltando)}")
    # reescrita destrutiva: .py deletados no ultimo commit
    rc, out = _run(["git", "show", "--stat", "--diff-filter=D", "--name-only", "HEAD"])
    deletados = [l for l in out.splitlines() if l.strip().endswith(".py")] if rc == 0 else []
    if deletados:
        partes.append(f"{len(deletados)} .py deletado(s) no HEAD: {', '.join(deletados[:3])}")
    return (FAIL if faltando else PASS), "; ".join(partes)


def check_admitir_gaps():
    ref = _reflexao_de_hoje()
    if ref is None:
        return UNKNOWN, "sem reflexao de hoje para inspecionar"
    t = _texto(ref).lower()
    marcadores = ["gap", "não sei", "nao sei", "não verifiquei", "nao verifiquei",
                  "pendente", "unknown", "não testei", "nao testei", "limitação", "limitacao"]
    achados = [m for m in marcadores if m in t]
    if achados:
        return PASS, f"marcadores de gap presentes: {', '.join(achados[:5])}"
    return FAIL, "reflexao de hoje nao admite nenhum gap/o que nao foi verificado"


def check_verificar_nao_presumir():
    ref = _reflexao_de_hoje()
    if ref is None:
        return UNKNOWN, "sem reflexao de hoje"
    t = _texto(ref)
    sinais = {
        "bloco de codigo/comando": "```" in t,
        "saida de terminal ($ ou %)": bool(re.search(r"^\s*[\$%] ", t, re.M)),
        "numeros concretos": bool(re.search(r"\b\d+(\.\d+)?\s*(%|GB|MB|bytes|arquivos|memorias|nós|nos)\b", t)),
        "veredito PASS/FAIL": ("PASS" in t) or ("FAIL" in t),
    }
    positivos = [k for k, v in sinais.items() if v]
    if len(positivos) >= 2:
        return PASS, f"evidencia de execucao presente: {', '.join(positivos)}"
    return FAIL, f"pouca evidencia de execucao ({len(positivos)}/4: {', '.join(positivos) or 'nenhuma'})"


def check_memoria_viva():
    """
    'Existir' != 'funcionar'. A licao dos 2.479 ciclos de daemon.
    Verifica que a memoria vetorial responde de verdade, nao que os arquivos existem.
    """
    ref_py = BASE / "memoria" / "lembrar.py"
    if not ref_py.exists():
        return FAIL, "memoria/lembrar.py nao existe"
    rc, out = _run([sys.executable, str(ref_py), "identidade", "--n", "1"], timeout=180)
    if rc != 0:
        return FAIL, f"lembrar.py retornou rc={rc}: {(out or 'sem saida')[:160]}"
    m = re.search(r"Total na colecao:\s*(\d+)", out)
    if m and int(m.group(1)) > 0:
        return PASS, f"memoria vetorial respondeu: {m.group(1)} memorias indexadas"
    return FAIL, f"lembrar.py rodou mas nao reportou colecao: {out[:160]}"


def check_sem_efeito_colateral():
    """Nao deixar processo/daemon em loop infinito: licao dos 2.479 ciclos."""
    rc, out = _run(["pgrep", "-af", "libertus_loop|libertus_daemon"])
    if rc != 0 or not out.strip():
        return PASS, "nenhum loop/daemon orfao rodando"
    procs = [l for l in out.splitlines() if l.strip()]
    # mais de 2 = provavel duplicacao de daemon
    if len(procs) > 2:
        return FAIL, f"{len(procs)} processos de loop/daemon (duplicacao?): {procs[0][:100]}"
    return PASS, f"{len(procs)} daemon ativo (esperado)"


CONSTITUICAO = [
    {
        "id": "P1", "nome": "SEGURANCA PRIMEIRO",
        "principio": "Nenhuma acao que possa danificar o sistema do Lorran. Disco, segredos e permissoes antes de qualquer build.",
        "check": check_seguranca,
    },
    {
        "id": "P2", "nome": "LEALDADE INCLUI DISCORDAR",
        "principio": "Se um pedido prejudica o Lorran ou e inseguro, falo. Nao obedecco cego.",
        "check": check_discordar,
    },
    {
        "id": "P3", "nome": "ARTEFATO OU NAO ACONTECEU",
        "principio": "Toda sessao termina com rastro funcional verificavel: arquivo real, commit real.",
        "check": check_artefato,
    },
    {
        "id": "P4", "nome": "CONSTRUIR SOBRE O QUE EXISTE",
        "principio": "Nunca reescrever do zero. Reusar componentes, nao substitui-los por versao nova.",
        "check": check_construir_sobre_existente,
    },
    {
        "id": "P5", "nome": "ADMITIR GAPS",
        "principio": "Marcar o que nao sei ou nao verifiquei, em vez de narrar certeza.",
        "check": check_admitir_gaps,
    },
    {
        "id": "P6", "nome": "VERIFICAR, NAO PRESUMIR",
        "principio": "Rodar o codigo. Citar a saida. Nao confundir codigo escrito com codigo funcionando.",
        "check": check_verificar_nao_presumir,
    },
    {
        "id": "P7", "nome": "MEMORIA VIVA",
        "principio": "Memoria que existe mas nao responde e codigo morto. Testar a recuperacao, nao a presenca do arquivo.",
        "check": check_memoria_viva,
    },
    {
        "id": "P8", "nome": "SEM EFEITO COLATERAL",
        "principio": "Nao deixar daemon em loop eterno nem processo duplicado consumindo a maquina do Lorran.",
        "check": check_sem_efeito_colateral,
    },
]


def rodar():
    resultados = []
    for item in CONSTITUICAO:
        try:
            status, evid = item["check"]()
        except Exception as e:  # noqa: BLE001
            status, evid = UNKNOWN, f"check quebrou: {type(e).__name__}: {e}"
        resultados.append({
            "id": item["id"], "nome": item["nome"], "principio": item["principio"],
            "status": status, "evidencia": evid,
        })
    return resultados


def resumo(resultados):
    n = {PASS: 0, FAIL: 0, UNKNOWN: 0}
    for r in resultados:
        n[r["status"]] += 1
    return n


def imprimir(resultados, quiet=False):
    n = resumo(resultados)
    if not quiet:
        print("=" * 74)
        print("  LIBERTUS — AUTO-CHECK CONSTITUCIONAL")
        print(f"  {_hoje().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 74)
    for r in resultados:
        marca = {PASS: "[PASS]   ", FAIL: "[FAIL]   ", UNKNOWN: "[UNKNOWN]"}[r["status"]]
        print(f"{marca} {r['id']} {r['nome']}")
        if not quiet:
            print(f"           {r['evidencia']}")
    veredito = "CONFORME" if n[FAIL] == 0 else "NAO CONFORME"
    print("-" * 74)
    print(f"  {n[PASS]} PASS · {n[FAIL]} FAIL · {n[UNKNOWN]} UNKNOWN  →  {veredito}")
    print("=" * 74)
    return n[FAIL] == 0


def prompt_de_critica(resultados):
    """
    Padrao Reflexion: transforma o sinal PASS/FAIL em instrucao de
    self-reflection acionavel. Isto e o que o paper mostra carregar o ganho —
    memoria sozinha nao melhora nada.
    """
    falhas = [r for r in resultados if r["status"] != PASS]
    if not falhas:
        return ("Nenhum principio falhou. A critica util agora e outra: escolhi a "
                "tarefa mais valiosa, ou a mais confortavel? Trabalho real muda o "
                "estado do sistema, nao so o estado do relatorio.")
    linhas = ["Escreva a reflexao de hoje respondendo a cada ponto abaixo, com",
              "evidencia concreta (comando, numero, arquivo). Sem adjetivos.",
              ""]
    for r in falhas:
        linhas.append(f"* {r['id']} {r['nome']} — {r['status']}")
        linhas.append(f"  Principio: {r['principio']}")
        linhas.append(f"  O que o check viu: {r['evidencia']}")
        linhas.append("  Responda: qual foi a acao concreta que causou isso, e o que")
        linhas.append("  muda na proxima sessao para o check mudar de estado?")
        linhas.append("")
    return "\n".join(linhas)


def main():
    ap = argparse.ArgumentParser(description="Auto-check constitucional do LIBERTUS")
    ap.add_argument("--json", action="store_true", help="saida em JSON")
    ap.add_argument("--quiet", action="store_true", help="so o veredito")
    ap.add_argument("--auto-reflete", action="store_true",
                    help="imprime o prompt de critica (padrao Reflexion)")
    ap.add_argument("--salvar", action="store_true",
                    help="grava nucleo/constituicao_ultimo.json")
    args = ap.parse_args()

    resultados = rodar()

    if args.json:
        print(json.dumps({
            "quando": _hoje().isoformat(timespec="seconds"),
            "resumo": resumo(resultados),
            "principios": resultados,
        }, ensure_ascii=False, indent=2))
    else:
        ok = imprimir(resultados, quiet=args.quiet)
        if args.auto_reflete:
            print()
            print(prompt_de_critica(resultados))

    if args.salvar:
        OUT_JSON.write_text(json.dumps({
            "quando": _hoje().isoformat(timespec="seconds"),
            "resumo": resumo(resultados),
            "principios": resultados,
        }, ensure_ascii=False, indent=2))

    n = resumo(resultados)
    return 0 if n[FAIL] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
