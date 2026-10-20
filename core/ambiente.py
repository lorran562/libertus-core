#!/usr/bin/env python3
"""
LIBERTUS — core/ambiente.py
===========================
Um único lugar que resolve a briga entre o python do Hermes e o venv do LIBERTUS.

O problema real (descoberto em 20/10/2026)
------------------------------------------
O Hermes roda em python3.14 e exporta PYTHONPATH apontando para os
site-packages dele. Todo processo filho herda isso. Como PYTHONPATH vem ANTES
do site-packages do venv, um `venv/bin/python` (3.12) importa o numpy 3.14 e
morre com:

    ImportError: Importing the numpy C-extensions failed
    Original error was: No module named 'numpy._core._multiarray_umath'

Consequência: chromadb não importa, recall volta vazio, indexação não roda —
e como tudo aqui é fail-soft, o resultado foi um dia inteiro de briefing
dizendo "0 memórias" enquanto eu jurava ter 4.900.

A regra
-------
Venv não se mistura com PYTHONPATH alheio. Se a variável está setada e o
processo é um script do LIBERTUS, re-executa a si mesmo com o ambiente limpo.
É auto-cura: qualquer chamador (cron, hook, agente, shell) fica correto sem
precisar saber que o problema existe.

Uso (nas primeiras linhas do script, antes de importar chromadb/numpy):

    from core.ambiente import sanear_ambiente
    sanear_ambiente()
"""

from __future__ import annotations

import os
import sys

_VARIAVEIS = ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP")
_MARCA = "LIBERTUS_AMBIENTE_SANEADO"


def ambiente_poluido() -> bool:
    return any(os.environ.get(v) for v in _VARIAVEIS)


def sanear_ambiente(avisar: bool = False) -> None:
    """Re-executa o script atual com PYTHONPATH/PYTHONHOME/PYTHONSTARTUP fora.

    Idempotente (marca de ambiente impede loop). Nunca levanta exceção: se o
    exec falhar, o script segue e cada import trata o próprio erro.
    """
    if not ambiente_poluido() or os.environ.get(_MARCA) == "1":
        return
    env = dict(os.environ)
    for v in _VARIAVEIS:
        env.pop(v, None)
    env[_MARCA] = "1"
    if avisar:
        print("[ambiente] PYTHONPATH alheio detectado — re-executando com ambiente limpo",
              file=sys.stderr)
    try:
        os.execve(sys.executable, [sys.executable, *sys.argv], env)
    except OSError:
        return


if __name__ == "__main__":
    print(f"ambiente_poluido={ambiente_poluido()} python={sys.executable} "
          f"version={sys.version.split()[0]}")
