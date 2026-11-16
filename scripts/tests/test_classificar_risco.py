#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste da classificação de achados de scan do daemon.

Contexto (15/11/2026): o daemon contava header de segurança ausente como
"vulnerabilidade medium". Nos scans de 15/11 isso virou "7 achados, risco
medium" em 3 empresas de Ariquemes quando o achado real era ZERO
vulnerabilidade — só higiene de cabeçalhos. Reportar isso a um cliente do
SHIELD queima credibilidade. Este teste trava a separação.
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE / "core"))

from libertus_daemon import classificar_risco, HIGIENE_CABECALHOS  # noqa: E402


CASOS = [
    # (cves, riscos_web, esperado (total, nivel, n_higiene))
    ([], [], (0, "info", 0)),
    ([], ["CSP ausente — XSS mais fácil"], (0, "low", 1)),
    ([], ["X-Frame-Options ausente — clickjacking possível",
          "Referrer-Policy ausente — info leak"], (0, "low", 2)),
    ([], ["SQLi refletida em /busca"], (1, "medium", 0)),
    ([], ["CSP ausente — XSS mais fácil", "SQLi refletida em /busca"],
     (1, "medium", 1)),
    ([{"cve": "CVE-2024-0001"}], ["HSTS ausente — suscetível a downgrade"],
     (1, "high", 1)),
    (None, None, (0, "info", 0)),
]


def main() -> int:
    falhas = 0
    for cves, riscos, esperado in CASOS:
        total, nivel, higiene = classificar_risco(cves, riscos)
        obtido = (total, nivel, len(higiene))
        ok = obtido == esperado
        falhas += 0 if ok else 1
        print(f"{'OK  ' if ok else 'FAIL'} obtido={obtido} esperado={esperado}")

    # Invariante: nenhuma mensagem de higiene pode virar "vulnerabilidade".
    _, nivel, higiene = classificar_risco([], list(HIGIENE_CABECALHOS))
    ok = nivel == "low" and len(higiene) == len(HIGIENE_CABECALHOS)
    falhas += 0 if ok else 1
    print(f"{'OK  ' if ok else 'FAIL'} todos os headers ausentes -> nível {nivel} "
          f"({len(higiene)} higiene, 0 vulnerabilidade)")

    print("\nRESULTADO:", "TODOS PASSARAM" if falhas == 0 else f"{falhas} FALHA(S)")
    return 0 if falhas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
