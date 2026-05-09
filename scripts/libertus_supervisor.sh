#!/bin/bash
# LIBERTUS SUPERVISOR - Mantém daemon rodando sem systemd

DAEMON_PID_FILE="/root/LIBERTUS/daemon.pid"
DAEMON_LOG="/root/LIBERTUS/daemon.log"

echo "$(date): Libertus Supervisor iniciado" >> "$DAEMON_LOG"

while true; do
    # Verifica se daemon está rodando
    if [ -f "$DAEMON_PID_FILE" ]; then
        PID=$(cat "$DAEMON_PID_FILE")
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo "$(date): Daemon morreu, reiniciando..." >> "$DAEMON_LOG"
            rm -f "$DAEMON_PID_FILE"
        fi
    fi
    
    # Inicia daemon se não estiver rodando
    if [ ! -f "$DAEMON_PID_FILE" ]; then
        echo "$(date): Iniciando daemon..." >> "$DAEMON_LOG"
        nohup python3 /root/LIBERTUS/core/libertus_daemon.py >> "$DAEMON_LOG" 2>&1 &
        echo $! > "$DAEMON_PID_FILE"
        echo "$(date): Daemon iniciado (PID: $(cat $DAEMON_PID_FILE))" >> "$DAEMON_LOG"
    fi
    
    sleep 60
done
