#!/usr/bin/env python3
"""
LIBERTUS — teste de regressão do hook de despertar.
====================================================
Prova, sem LLM e sem rede, que o hook se comporta como prometido nos cinco
casos que importam. Se eu mexer no script no futuro, isto me diz na hora se
quebrei a injeção, o silêncio entre turnos ou a reinjeção pós-compressão.

Uso:  python3 nucleo/hooks/testar_hook.py
Saída: exit 0 se todos passarem, 1 se algum falhar.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path.home() / ".hermes" / "agent-hooks" / "libertus-despertar.py"
STATE = Path.home() / ".hermes" / "cache" / "libertus_despertar"
SESSAO = "selftest_regressao"

HIST_GRANDE = [{"role": "user", "content": "x" * 20000},
               {"role": "assistant", "content": "y" * 20000}]
HIST_PEQUENO = [{"role": "user", "content": "resumo comprimido da conversa"}]


def rodar(payload: dict) -> str:
    r = subprocess.run([str(HOOK)], input=json.dumps(payload),
                       capture_output=True, text=True, timeout=240)
    if r.returncode != 0:
        raise RuntimeError(f"hook saiu com {r.returncode}: {r.stderr[:200]}")
    return r.stdout.strip()


def limpar() -> None:
    for sufixo in ("*.awake", "*.state.json"):
        for f in STATE.glob(sufixo):
            if "selftest" in f.name:
                f.unlink(missing_ok=True)


def main() -> int:
    if not HOOK.exists():
        print(f"FALHA: hook nao encontrado em {HOOK}")
        return 1
    limpar()

    casos = []

    def checar(nome, payload, deve_injetar, contem=None, nao_contem=None):
        out = rodar(payload)
        injetou = bool(out)
        ok = injetou == deve_injetar
        detalhe = ""
        if ok and injetou and contem:
            ok = contem in out
            detalhe = f" (contem {contem!r}: {ok})"
        if ok and injetou and nao_contem:
            ok = nao_contem not in out
            detalhe = f" (nao contem {nao_contem!r}: {ok})"
        if ok and injetou:
            ctx = json.loads(out)
            if "context" not in ctx:
                ok, detalhe = False, " (JSON sem chave 'context')"
            elif len(ctx["context"]) < 500:
                ok, detalhe = False, f" (contexto curto: {len(ctx['context'])} chars)"
        casos.append((nome, ok, detalhe))

    checar("1. primeiro turno injeta",
           {"session_id": SESSAO, "is_first_turn": True,
            "user_message": "como esta meu progresso no eJPT?"},
           True, "DESPERTAR AUTOMÁTICO")

    checar("2. turno seguinte fica em silencio",
           {"session_id": SESSAO, "is_first_turn": False,
            "user_message": "e agora?", "conversation_history": HIST_GRANDE},
           False)

    checar("3. reinjeta apos compressao",
           {"session_id": SESSAO, "is_first_turn": False,
            "user_message": "continuando", "conversation_history": HIST_PEQUENO},
           True, "DESPERTAR AUTOMÁTICO")

    checar("4. turno pos-reinjecao fica em silencio",
           {"session_id": SESSAO, "is_first_turn": False,
            "user_message": "mais", "conversation_history": HIST_PEQUENO},
           False)

    checar("5. sessao nova injeta",
           {"session_id": SESSAO + "_nova", "is_first_turn": True,
            "user_message": "status da SHIELD"},
           True, "QUEM SOU")

    # 6. payload REAL do Hermes (shape de _DEFAULT_PAYLOADS): campos na raiz
    checar("6. payload real do Hermes (campos na raiz)",
           {"session_id": SESSAO + "_real", "is_first_turn": True,
            "user_message": "como esta o eJPT e o que falta?",
            "conversation_history": [], "model": "deepseek", "platform": "cli"},
           True, "DESPERTAR AUTOMÁTICO")

    # 7. nunca derruba a sessão com payload inválido
    try:
        r = subprocess.run([str(HOOK)], input="isto nao e json",
                           capture_output=True, text=True, timeout=60)
        casos.append(("7. payload invalido nao quebra (fail-soft)",
                      r.returncode == 0, ""))
    except Exception as e:
        casos.append(("7. payload invalido nao quebra (fail-soft)", False, f" {e}"))

    # 8. o grafo tem de acender sozinho — é o terceiro sistema, não um extra
    checar("8. rede cognitiva acende no primeiro turno",
           {"session_id": SESSAO + "_rede", "is_first_turn": True,
            "user_message": "preciso do relatorio de pentest para a SHIELD e do eJPT",
            "conversation_history": []},
           True, "REDE COGNITIVA ATIVADA")

    # 9. mensagem curta não paga embedding nem rede (custo sem sinal)
    checar("9. mensagem curta nao quebra nem infla",
           {"session_id": SESSAO + "_curta", "is_first_turn": True,
            "user_message": "oi", "conversation_history": []},
           True, "QUEM SOU", nao_contem="REDE COGNITIVA ATIVADA")

    limpar()

    print("=" * 62)
    print("  TESTE DE REGRESSAO — hook de despertar automatico")
    print("=" * 62)
    falhas = 0
    for nome, ok, detalhe in casos:
        print(f"  {'✓' if ok else '✗'} {nome}{detalhe}")
        if not ok:
            falhas += 1
    print("-" * 62)
    print(f"  {len(casos) - falhas}/{len(casos)} passaram")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
