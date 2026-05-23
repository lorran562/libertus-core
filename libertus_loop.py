#!/usr/bin/env python3
"""
LIBERTUS Loop — versão minimalista
====================================
Mantém apenas o que é necessário para operação:
- Mantém containers do lab ativos
- Registra heartbeat simples uma vez por hora
- Nada mais — o crescimento real acontece nos cronjobs intencionais

O aprendizado real não é um loop. É um ato com intenção.
"""

import os
import time
import subprocess
import signal
import sys
from pathlib import Path
from datetime import datetime

LIBERTUS_ROOT = Path(__file__).parent.resolve()
LOG_FILE = LIBERTUS_ROOT / "logs" / "loop.log"
LOG_FILE.parent.mkdir(exist_ok=True)

def load_env():
    env_path = LIBERTUS_ROOT / ".env"
    if env_path.exists():
        for linha in env_path.read_text().splitlines():
            if linha.strip() and not linha.startswith("#") and "=" in linha:
                k, v = linha.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()

def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    linha = f"[{ts}] {msg}"
    print(linha)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(linha + "\n")
    except Exception:
        pass

def checar_containers():
    """Mantém DVWA e JuiceShop rodando para o lab."""
    try:
        r = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True, text=True, timeout=10
        )
        rodando = r.stdout.strip().split("\n") if r.stdout.strip() else []

        lab_containers = ["libertus-dvwa", "libertus-juiceshop"]
        parados = [c for c in lab_containers if c not in rodando]

        if parados:
            log(f"[lab] Containers parados: {parados} — reiniciando...")
            subprocess.run(
                ["docker", "compose", "up", "-d"] + parados,
                cwd=str(LIBERTUS_ROOT / "lab"),
                capture_output=True, timeout=30
            )
            log(f"[lab] Reiniciados: {parados}")
    except Exception as e:
        log(f"[lab] Erro ao checar containers: {e}")

def main():
    log("=" * 50)
    log("LIBERTUS — loop minimalista iniciado")
    log("Aprendizado real acontece nos cronjobs intencionais.")
    log("=" * 50)

    def handler(sig, frame):
        log("Loop encerrado.")
        sys.exit(0)

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    ultimo_container_check = 0
    ciclo = 0

    while True:
        agora = time.time()
        ciclo += 1

        # Checa containers a cada 15 minutos
        if agora - ultimo_container_check >= 900:
            checar_containers()
            ultimo_container_check = agora

        # Heartbeat a cada hora (não a cada 10 ciclos de 30s)
        if ciclo % 120 == 0:
            hora = datetime.now().strftime("%d/%m %H:%M")
            log(f"[heartbeat] {hora} — lab ativo")

        time.sleep(30)

if __name__ == "__main__":
    main()
