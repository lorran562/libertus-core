#!/bin/bash
# instalar_daemon.sh — Instala o Libertus como serviço systemd
# Uso: bash instalar_daemon.sh

set -e

LIBERTUS_ROOT="$HOME/LIBERTUS"
USUARIO="$(whoami)"
SERVICE_FILE="/etc/systemd/system/libertus.service"

echo "=== LIBERTUS Daemon — Instalação ==="
echo "Usuário: $USUARIO"
echo "Root: $LIBERTUS_ROOT"
echo ""

# 1. Verifica estrutura
if [ ! -f "$LIBERTUS_ROOT/core/libertus_daemon.py" ]; then
    echo "ERRO: libertus_daemon.py não encontrado em $LIBERTUS_ROOT/core/"
    echo "Clone o repositório primeiro: git clone ... ~/LIBERTUS"
    exit 1
fi

# 2. Cria pastas necessárias
mkdir -p "$LIBERTUS_ROOT/memory/decisions"
mkdir -p "$LIBERTUS_ROOT/memory/goals"
mkdir -p "$LIBERTUS_ROOT/memory/feedback"
mkdir -p "$LIBERTUS_ROOT/memory/.backups"
mkdir -p "$LIBERTUS_ROOT/evolution_logs"
mkdir -p "$LIBERTUS_ROOT/plans"

# 3. Instala dependências Python se necessário
echo "→ Verificando dependências Python..."
pip3 install httpx colorama anthropic --break-system-packages --quiet 2>/dev/null || \
    pip3 install httpx colorama anthropic --quiet

# 4. Cria arquivo .env com variáveis (se não existir)
if [ ! -f "$LIBERTUS_ROOT/.env" ]; then
    echo "→ Criando $LIBERTUS_ROOT/.env"
    cat > "$LIBERTUS_ROOT/.env" << EOF
LIBERTUS_OBSIDIAN=$LIBERTUS_ROOT
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-configure_aqui}
GROQ_API_KEY=${GROQ_API_KEY:-configure_aqui}
OLLAMA_URL=http://localhost:11434
EOF
    echo "   ⚠️  Edite $LIBERTUS_ROOT/.env com suas chaves reais"
fi

# 5. Cria arquivo de serviço
echo "→ Instalando serviço systemd..."
sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=LIBERTUS Cognitive Daemon
Documentation=https://github.com/lorran562/libertus-core
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=300
StartLimitBurst=5

[Service]
Type=simple
User=$USUARIO
WorkingDirectory=$LIBERTUS_ROOT/core
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=-$LIBERTUS_ROOT/.env
ExecStart=/usr/bin/python3 $LIBERTUS_ROOT/core/libertus_daemon.py
Restart=always
RestartSec=10
StandardOutput=append:$LIBERTUS_ROOT/evolution_logs/daemon_stdout.log
StandardError=append:$LIBERTUS_ROOT/evolution_logs/daemon_stderr.log

# Segurança
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

# 6. Recarrega systemd e ativa
echo "→ Ativando serviço..."
sudo systemctl daemon-reload
sudo systemctl enable libertus.service

# 7. Pergunta se inicia agora
echo ""
echo "✓ Instalação concluída!"
echo ""
echo "Comandos úteis:"
echo "  sudo systemctl start libertus     # inicia o daemon"
echo "  sudo systemctl stop libertus      # para o daemon"
echo "  sudo systemctl status libertus    # ver status"
echo "  sudo systemctl restart libertus   # reinicia"
echo "  journalctl -u libertus -f         # ver logs em tempo real"
echo "  tail -f $LIBERTUS_ROOT/evolution_logs/daemon.log  # log do daemon"
echo ""
echo "Para iniciar agora:"
echo "  sudo systemctl start libertus"
