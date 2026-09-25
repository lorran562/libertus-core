#!/usr/bin/env python3
"""
consolidar_cron.py — O "sono" do LIBERTUS (Passo 4 do grapify, contraparte).

Roda periodicamente (cron) em baixa utilização e faz o que um cérebro faz
dormindo: decai ligações não usadas, poda hipóteses que nasceram e nunca mais
voltaram — MAS respeita a carência (DIAS_CARENCIA_ORFAO) pra nunca apagar o
aprendizado recente antes de ele ter chance de ser reusado.

Aprender de dia (indexar_fala), consolidar à noite (isto). Sem os dois, o
ciclo cognitivo fica pela metade e o grafo vira acúmulo de ruído.

Uso:
    python3 core/consolidar_cron.py            # consolida de verdade + salva
    python3 core/consolidar_cron.py --dry-run  # mostra o que faria, NÃO salva

Nunca levanta exceção pro cron: qualquer erro vira exit 0 + nota, pra um cron
quebrado não spammar alerta nem corromper nada.
"""
from __future__ import annotations

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


def main() -> None:
    dry = "--dry-run" in sys.argv
    try:
        from core.grafo_cognitivo import GrafoCognitivo, DIAS_CARENCIA_ORFAO

        gc = GrafoCognitivo()
        nos_antes = gc.g.number_of_nodes()
        arestas_antes = gc.g.number_of_edges()

        if dry:
            # simula sem persistir: consolida numa cópia lógica (não salva)
            r = gc.consolidar(podar=True)
            print(f"[DRY-RUN] consolidacao SIMULADA (nada salvo):")
            print(f"  nós:     {nos_antes} -> {gc.g.number_of_nodes()}")
            print(f"  arestas: {arestas_antes} -> {gc.g.number_of_edges()}")
            print(f"  {r}")
            print(f"  carência: {DIAS_CARENCIA_ORFAO} dias")
            return

        r = gc.consolidar(podar=True)
        gc.salvar()
        # snapshot leve no Supabase (best-effort, não trava se falhar)
        try:
            gc.snapshot_supabase()
        except Exception:  # noqa: BLE001
            pass

        print(f"[consolidar_cron] OK — nós {nos_antes}->{gc.g.number_of_nodes()}, "
              f"arestas {arestas_antes}->{gc.g.number_of_edges()}, "
              f"podadas={r['arestas_podadas']}, orfaos={r['nos_orfaos_removidos']}, "
              f"protegidos={r['nos_protegidos_carencia']}")
    except Exception as e:  # noqa: BLE001 — cron nunca deve estourar
        print(f"[consolidar_cron] falhou (ignorado): {type(e).__name__}: {e}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
