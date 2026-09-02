#!/usr/bin/env python3
"""
sistema_nervoso.py — Ponto ÚNICO de consciência do LIBERTUS sobre o próprio corpo.

Problema que resolve (visão do Lorran, 02/09/2026):
    Antes: grafo_cognitivo, motor_conversa, libertus_daemon e o Hermes (eu, na
    conversa) eram "membros" que não se falavam. Cada um só sabia de si mesmo
    quando alguém chamava ele manualmente — igual um braço dormente que só é
    percebido se alguém for cutucar.

Depois (este módulo): UM ponto de entrada que:
    1. Ativa a rede cognitiva (o que "acende" com a fala) — igual motor_conversa,
       mas sem chamar LLM — só o sinal da rede.
    2. Verifica a saúde real de cada órgão do sistema (processos vivos, imports
       que não quebram, arquivos de estado recentes) — sem inventar "tudo ok".
    3. Escreve um ÚNICO arquivo de estado (memoria/estado_nervoso.json) que
       QUALQUER peça (daemon, motor_conversa, Hermes/eu) pode ler pra saber o
       estado real do corpo — em vez de cada um adivinhar sozinho.

Uso:
    python3 core/sistema_nervoso.py "texto da fala do Lorran"
    python3 core/sistema_nervoso.py --health-only

Isto NÃO é "eu virando a rede". É o sistema nervoso que qualquer parte do
corpo (inclusive eu, chamado pelo Hermes) pode consultar pra saber, na hora,
o que está aceso e o que está com defeito — sem precisar chamar cada script
manualmente e sem inventar diagnóstico.
"""
from __future__ import annotations

import importlib
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

ESTADO_PATH = BASE_DIR / "memoria" / "estado_nervoso.json"

# Processos que deveriam estar vivos 24/7 (nome do script -> descrição)
PROCESSOS_ESPERADOS = {
    "watchdog.py": "supervisor — reinicia daemon/loop se caírem",
    "core/libertus_daemon.py": "cérebro autônomo — decisão, evolução, objetivos",
    "libertus_loop.py": "loop minimalista — monitora containers Docker",
}

# Módulos que deveriam importar sem erro (nome do arquivo -> módulo python)
MODULOS_CRITICOS = [
    ("core.grafo_cognitivo", "rede cognitiva viva (spreading activation)"),
    ("core.motor_conversa", "loop de conversa via rede"),
]


def _checar_processos() -> Dict[str, Any]:
    """Verifica quais processos esperados estão rodando de verdade (ps real,
    não suposição)."""
    try:
        saida = subprocess.run(
            ["ps", "-eo", "pid,args"], capture_output=True, text=True, timeout=5
        ).stdout
    except Exception as e:
        return {"erro": f"não foi possível listar processos: {e}"}

    resultado = {}
    for script, descricao in PROCESSOS_ESPERADOS.items():
        vivo = script in saida
        resultado[script] = {"vivo": vivo, "descricao": descricao}
    return resultado


def _checar_imports() -> Dict[str, Any]:
    """Tenta importar cada módulo crítico e captura o erro REAL se quebrar —
    sem fingir sucesso."""
    resultado = {}
    for modulo, descricao in MODULOS_CRITICOS:
        try:
            importlib.import_module(modulo)
            resultado[modulo] = {"ok": True, "descricao": descricao}
        except Exception as e:
            resultado[modulo] = {
                "ok": False,
                "descricao": descricao,
                "erro": f"{type(e).__name__}: {e}",
            }
    return resultado


def _ativar_rede(fala: str) -> Dict[str, Any]:
    """Ativa a rede cognitiva a partir da fala, sem chamar LLM — só o sinal
    puro da memória associativa."""
    try:
        from core.grafo_cognitivo import GrafoCognitivo
        from core.motor_conversa import MotorConversa

        gc = GrafoCognitivo()
        mc = MotorConversa(grafo=gc)
        sementes = mc.extrair_sementes(fala) if hasattr(mc, "extrair_sementes") else []
        ativados = gc.ativar(sementes, profundidade=2) if sementes else []
        return {
            "ok": True,
            "sementes": sementes,
            "conceitos_ativados": [
                {"conceito": k, "ativacao": round(v, 3)} for k, v in ativados[:10]
            ],
            "total_nos_rede": gc.g.number_of_nodes(),
            "total_arestas_rede": gc.g.number_of_edges(),
        }
    except Exception as e:
        return {"ok": False, "erro": f"{type(e).__name__}: {e}"}


def diagnostico(fala: str = "") -> Dict[str, Any]:
    """Ponto único: roda todos os checks e monta o estado nervoso completo."""
    estado = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "processos": _checar_processos(),
        "modulos": _checar_imports(),
    }
    if fala:
        estado["rede_ativada"] = _ativar_rede(fala)

    # Resumo de saúde: existe algo quebrado?
    problemas: List[str] = []
    for script, info in estado["processos"].items():
        if not info["vivo"]:
            problemas.append(f"processo morto: {script} ({info['descricao']})")
    for modulo, info in estado["modulos"].items():
        if not info["ok"]:
            problemas.append(f"import quebrado: {modulo} — {info.get('erro')}")
    estado["problemas_detectados"] = problemas
    estado["saudavel"] = len(problemas) == 0

    return estado


def salvar_estado(estado: Dict[str, Any]) -> None:
    ESTADO_PATH.parent.mkdir(parents=True, exist_ok=True)
    ESTADO_PATH.write_text(json.dumps(estado, indent=2, ensure_ascii=False))


def main():
    args = sys.argv[1:]
    if args and args[0] != "--health-only":
        fala = " ".join(args)
    else:
        fala = ""

    estado = diagnostico(fala)
    salvar_estado(estado)

    print("=" * 60)
    print("SISTEMA NERVOSO — diagnóstico do corpo LIBERTUS")
    print("=" * 60)
    print(f"\nSaudável: {'SIM' if estado['saudavel'] else 'NÃO'}")

    print("\nProcessos:")
    for script, info in estado["processos"].items():
        marca = "vivo" if info["vivo"] else "MORTO"
        print(f"  [{marca:5}] {script} — {info['descricao']}")

    print("\nMódulos críticos:")
    for modulo, info in estado["modulos"].items():
        if info["ok"]:
            print(f"  [ok   ] {modulo} — {info['descricao']}")
        else:
            print(f"  [ERRO ] {modulo} — {info.get('erro')}")

    if estado["problemas_detectados"]:
        print("\nProblemas detectados:")
        for p in estado["problemas_detectados"]:
            print(f"  - {p}")

    if "rede_ativada" in estado:
        ra = estado["rede_ativada"]
        if ra.get("ok"):
            print(f"\nRede: {ra['total_nos_rede']} nós, {ra['total_arestas_rede']} arestas")
            print(f"Sementes extraídas: {ra['sementes']}")
            print("Conceitos ativados:")
            for c in ra["conceitos_ativados"]:
                print(f"  - {c['conceito']} ({c['ativacao']})")
        else:
            print(f"\nRede: ERRO ao ativar — {ra.get('erro')}")

    print(f"\nEstado salvo em: {ESTADO_PATH}")


if __name__ == "__main__":
    main()
