#!/bin/bash
# LIBERTUS — Script de inicialização automática
# Roda quando o PC liga e mantém tudo vivo.
#
# ARQUITETURA (corrigida em 21/10/2026):
#   UM supervisor só: libertus-watchdog.service (systemd user, linger=yes,
#   Restart=on-failure, KillMode=process). Ele inicia e reinicia
#   libertus_daemon.py e libertus_loop.py.
#
#   Por que este script é mínimo: /etc/systemd/system/libertus.service é
#   Type=forking (root-owned, Restart=on-failure, RestartSec=30). Se o
#   ExecStart demora, o systemd mata o cgroup com SIGTERM e reinicia —
#   observado em 21/10 como restart-loop e, antes, como daemon/loop
#   duplicados (este script subia daemon+loop E o watchdog subia de novo).
#   Então: se o supervisor já está ativo, sai limpo e imediatamente.
#   Nada de pkill de watchdog ativo — era isso que derrubava o user unit.

LIBERTUS_DIR="$HOME/LIBERTUS"
LOG_DIR="$LIBERTUS_DIR/logs"
mkdir -p "$LOG_DIR"

export XDG_RUNTIME_DIR="/run/user/$(id -u)"
export DBUS_SESSION_BUS_ADDRESS="${DBUS_SESSION_BUS_ADDRESS:-unix:path=/run/user/$(id -u)/bus}"

echo "🚀 LIBERTUS iniciando em $(date)" | tee -a "$LOG_DIR/startup.log"

# Caminho normal: supervisor de usuário já no ar (linger). Nada a fazer.
if systemctl --user is-active --quiet libertus-watchdog.service; then
    echo "✅ Supervisor já ativo (libertus-watchdog.service) — boot sem intervenção" \
        | tee -a "$LOG_DIR/startup.log"
    exit 0
fi

# Carregar variáveis de ambiente (watchdog também carrega o .env por conta própria)
set -a
source "$LIBERTUS_DIR/.env" 2>/dev/null
set +a

# Padrões ancorados em ^python3: pkill -f solto matava shells/agentes
# cujo cmdline apenas citasse o nome do script.
cleanup() {
    pkill -f "^python3 .*telegram_bot_rag[.]py" 2>/dev/null
    pkill -f "^python3 .*libertus_daemon[.]py" 2>/dev/null
    pkill -f "^python3 .*watchdog[.]py" 2>/dev/null
    pkill -f "^python3 .*libertus_loop[.]py" 2>/dev/null
    sleep 2
}

cleanup

cd "$LIBERTUS_DIR" || exit 1

# Atualizar do GitHub (não bloqueia o boot se falhar)
echo "📥 Atualizando..." | tee -a "$LOG_DIR/startup.log"
git config pull.rebase false
timeout 60 git pull origin main 2>&1 | tee -a "$LOG_DIR/startup.log"

# Bot Telegram: APOSENTADO. O canal oficial agora é o gateway Hermes
# (hermes gateway run), que faz long-polling no mesmo token.

echo "🐕 Subindo supervisor (systemd user: libertus-watchdog.service)..." | tee -a "$LOG_DIR/startup.log"

if systemctl --user start libertus-watchdog.service >> "$LOG_DIR/startup.log" 2>&1; then
    echo "✅ Supervisor: libertus-watchdog.service (user)" | tee -a "$LOG_DIR/startup.log"
else
    echo "⚠️  systemd user indisponível — fallback nohup watchdog" | tee -a "$LOG_DIR/startup.log"
    nohup python3 watchdog.py >> "$LOG_DIR/watchdog.log" 2>&1 &
fi

echo "✅ LIBERTUS VIVO — $(date)" | tee -a "$LOG_DIR/startup.log"

# Âncora do unit system: /etc/systemd/system/libertus.service é Type=forking
# sem PIDFile, então se o script sai sem deixar filho vivo o systemd considera
# falha e entra em restart-loop de 30s (observado 21/10). Este processo inerte
# segura o unit "started"; quem supervisiona daemon/loop é o user unit acima.
nohup sleep infinity >/dev/null 2>&1 &

exit 0
