#!/bin/bash
# LIBERTUS — Script de inicialização automática
# Roda quando o PC liga e mantém tudo vivo

LIBERTUS_DIR="$HOME/LIBERTUS"
LOG_DIR="$LIBERTUS_DIR/logs"
mkdir -p "$LOG_DIR"

echo "🚀 LIBERTUS iniciando em $(date)" | tee -a "$LOG_DIR/startup.log"

# Carregar variáveis de ambiente
set -a
source "$LIBERTUS_DIR/.env" 2>/dev/null
set +a

# Função para matar processos anteriores
cleanup() {
    pkill -f "telegram_bot_rag.py" 2>/dev/null
    pkill -f "libertus_daemon.py" 2>/dev/null
    pkill -f "watchdog.py" 2>/dev/null
    pkill -f "libertus_loop.py" 2>/dev/null
    sleep 2
}

cleanup

cd "$LIBERTUS_DIR"

# Atualizar do GitHub
echo "📥 Atualizando..." | tee -a "$LOG_DIR/startup.log"
git config pull.rebase false
git pull origin main 2>&1 | tee -a "$LOG_DIR/startup.log"

# Iniciar bot Telegram em background
echo "🤖 Iniciando Bot..." | tee -a "$LOG_DIR/startup.log"
nohup python3 telegram_bot_rag.py >> "$LOG_DIR/telegram_bot.log" 2>&1 &
BOT_PID=$!
echo "Bot PID: $BOT_PID" | tee -a "$LOG_DIR/startup.log"

sleep 3

# Iniciar daemon coração
echo "💓 Iniciando Daemon..." | tee -a "$LOG_DIR/startup.log"
nohup python3 core/libertus_daemon.py >> "$LOG_DIR/daemon.log" 2>&1 &
DAEMON_PID=$!
echo "Daemon PID: $DAEMON_PID" | tee -a "$LOG_DIR/startup.log"

sleep 2

# Iniciar watchdog
echo "🐕 Iniciando Watchdog..." | tee -a "$LOG_DIR/startup.log"
nohup python3 watchdog.py >> "$LOG_DIR/watchdog.log" 2>&1 &
WATCHDOG_PID=$!
echo "Watchdog PID: $WATCHDOG_PID" | tee -a "$LOG_DIR/startup.log"

sleep 2

# Iniciar loop infinito de aprendizado
echo "🔄 Iniciando Loop Infinito..." | tee -a "$LOG_DIR/startup.log"
nohup python3 libertus_loop.py >> "$LOG_DIR/loop.log" 2>&1 &
LOOP_PID=$!
echo "Loop PID: $LOOP_PID" | tee -a "$LOG_DIR/startup.log"

echo "✅ LIBERTUS VIVO — $(date)" | tee -a "$LOG_DIR/startup.log"
echo "PIDs: Bot=$BOT_PID Daemon=$DAEMON_PID Watchdog=$WATCHDOG_PID Loop=$LOOP_PID"

# Salvar PIDs
echo "$BOT_PID $DAEMON_PID $WATCHDOG_PID $LOOP_PID" > "$LOG_DIR/pids.txt"
