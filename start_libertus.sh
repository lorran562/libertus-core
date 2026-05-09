#!/bin/bash
# Inicia Libertus em background

cd /root/LIBERTUS

# Para processos existentes
pkill -f libertus_supervisor || true
pkill -f libertus_daemon || true
sleep 2

# Inicia supervisor em background
nohup bash scripts/libertus_supervisor.sh > /dev/null 2>&1 &
SUPERVISOR_PID=$!

echo "🚀 Libertus iniciado!"
echo "   Supervisor PID: $SUPERVISOR_PID"
echo ""
echo "Logs: tail -f /root/LIBERTUS/daemon.log"
echo "Stop: pkill -f libertus_supervisor"
