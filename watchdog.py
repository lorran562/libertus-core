#!/usr/bin/env python3
"""
LIBERTUS WATCHDOG - Garante que daemon nunca morra
"""
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime

LIBERTUS_ROOT = Path(__file__).parent.resolve()  # relativo ao arquivo
DAEMON_SCRIPT = LIBERTUS_ROOT / "core" / "libertus_daemon.py"
HEARTBEAT_FILE = LIBERTUS_ROOT / "memory" / "heartbeat.json"
WATCHDOG_LOG = LIBERTUS_ROOT / "evolution_logs" / "watchdog.log"
PID_FILE = Path("/tmp/libertus_daemon.pid")

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}\n"
    print(line.strip())
    WATCHDOG_LOG.write_text(
        WATCHDOG_LOG.read_text() + line if WATCHDOG_LOG.exists() else line
    )

def is_daemon_alive():
    """Verifica se daemon está rodando via PID + heartbeat"""
    try:
        # Check 1: PID existe?
        if not PID_FILE.exists():
            return False
        
        pid = int(PID_FILE.read_text().strip())
        
        # Check 2: Processo existe?
        try:
            subprocess.run(
                ["ps", "-p", str(pid)],
                check=True,
                capture_output=True,
                timeout=2
            )
        except:
            return False
        
        # Check 3: Heartbeat recente? (< 5 minutos)
        if HEARTBEAT_FILE.exists():
            data = json.loads(HEARTBEAT_FILE.read_text())
            heartbeat_time = datetime.fromisoformat(data["timestamp"])
            age = (datetime.now() - heartbeat_time).total_seconds()
            
            if age > 300:  # 5 minutos
                log(f"⚠️  Heartbeat antigo: {age:.0f}s")
                return False
        
        return True
        
    except Exception as e:
        log(f"❌ Erro ao verificar daemon: {e}")
        return False

def start_daemon():
    """Inicia daemon e retorna PID"""
    try:
        # Mata processos antigos
        subprocess.run(
            ["pkill", "-9", "-f", "libertus_daemon.py"],
            capture_output=True,
            timeout=5
        )
        time.sleep(2)
        
        # Inicia novo
        log("🚀 Iniciando daemon...")
        proc = subprocess.Popen(
            ["python3", str(DAEMON_SCRIPT)],
            cwd=str(LIBERTUS_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True
        )
        
        PID_FILE.write_text(str(proc.pid))
        log(f"✅ Daemon iniciado - PID: {proc.pid}")
        return proc.pid
        
    except Exception as e:
        log(f"❌ Erro ao iniciar daemon: {e}")
        return None

def main():
    log("🐕 LIBERTUS Watchdog iniciado")
    log("📋 Monitorando daemon 24/7...")
    
    check_interval = 60  # 1 minuto
    restart_count = 0
    
    while True:
        try:
            if not is_daemon_alive():
                log("💀 Daemon morto! Reiniciando...")
                pid = start_daemon()
                
                if pid:
                    restart_count += 1
                    log(f"♻️  Restart #{restart_count} completo")
                    time.sleep(10)  # Aguarda inicialização
                else:
                    log("❌ Falha ao reiniciar! Tentando novamente em 30s...")
                    time.sleep(30)
            
            # Daemon vivo, aguarda próximo check
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            log("🛑 Watchdog interrompido pelo usuário")
            break
        except Exception as e:
            log(f"❌ Erro no watchdog: {e}")
            time.sleep(30)

if __name__ == "__main__":
    main()
