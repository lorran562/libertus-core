#!/bin/bash
#
# LIBERTUS - INSTALAÇÃO PROFISSIONAL NO UBUNTU
# Execute este script no seu Ubuntu dual boot
#
# Uso: bash install_libertus_ubuntu.sh
#

set -e  # Para na primeira falha

echo "╔══════════════════════════════════════════════════════╗"
echo "║   🛡️  LIBERTUS v9.0 - INSTALAÇÃO UBUNTU            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# 1. VERIFICAR SISTEMA
echo "1️⃣ Verificando sistema operacional..."
if [ ! -f /etc/os-release ]; then
    echo "❌ Sistema não identificado"
    exit 1
fi

. /etc/os-release
echo "✅ Sistema: $PRETTY_NAME"
echo ""

# 2. INSTALAR DEPENDÊNCIAS
echo "2️⃣ Instalando dependências do sistema..."
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    git \
    curl \
    sqlite3 \
    nmap \
    whois \
    dnsutils

echo "✅ Dependências instaladas"
echo ""

# 3. CRIAR DIRETÓRIO
echo "3️⃣ Criando estrutura de diretórios..."
LIBERTUS_DIR="$HOME/LIBERTUS"

if [ -d "$LIBERTUS_DIR" ]; then
    echo "⚠️  Diretório $LIBERTUS_DIR já existe"
    read -p "Deseja sobrescrever? (s/N): " resposta
    if [[ "$resposta" != "s" && "$resposta" != "S" ]]; then
        echo "❌ Instalação cancelada"
        exit 1
    fi
    rm -rf "$LIBERTUS_DIR"
fi

mkdir -p "$LIBERTUS_DIR"
cd "$LIBERTUS_DIR"

echo "✅ Diretório criado: $LIBERTUS_DIR"
echo ""

# 4. CLONAR REPOSITÓRIO
echo "4️⃣ Clonando repositório do GitHub..."
git clone https://github.com/lorran562/libertus-core.git .

echo "✅ Código baixado"
echo ""

# 5. INSTALAR DEPENDÊNCIAS PYTHON
echo "5️⃣ Instalando bibliotecas Python..."
pip3 install --user \
    aiohttp \
    jinja2 \
    flask \
    requests \
    python-nmap \
    beautifulsoup4 \
    lxml

echo "✅ Bibliotecas instaladas"
echo ""

# 6. CRIAR BANCO DE DADOS
echo "6️⃣ Inicializando banco de dados SQLite..."
mkdir -p memoria
sqlite3 memoria/libertus.db < /dev/null

echo "✅ Banco criado: memoria/libertus.db"
echo ""

# 7. CONFIGURAR DAEMON SYSTEMD
echo "7️⃣ Configurando serviço systemd..."

DAEMON_SERVICE="$HOME/.config/systemd/user/libertus.service"
mkdir -p "$HOME/.config/systemd/user"

cat > "$DAEMON_SERVICE" <<EOF
[Unit]
Description=LIBERTUS Cybersecurity Scanner Daemon
After=network.target

[Service]
Type=simple
WorkingDirectory=$LIBERTUS_DIR/core
ExecStart=/usr/bin/python3 $LIBERTUS_DIR/core/libertus_daemon_v2_real.py
Restart=always
RestartSec=10
StandardOutput=append:$LIBERTUS_DIR/logs/daemon.log
StandardError=append:$LIBERTUS_DIR/logs/daemon_error.log

[Install]
WantedBy=default.target
EOF

mkdir -p "$LIBERTUS_DIR/logs"

echo "✅ Serviço systemd criado"
echo ""

# 8. CRIAR SCRIPT DE CONTROLE
echo "8️⃣ Criando scripts de controle..."

cat > "$LIBERTUS_DIR/libertus" <<'EOF'
#!/bin/bash
# LIBERTUS - Script de controle

LIBERTUS_DIR="$HOME/LIBERTUS"

case "$1" in
    start)
        echo "🚀 Iniciando LIBERTUS daemon..."
        systemctl --user start libertus.service
        echo "✅ Daemon iniciado"
        ;;
    stop)
        echo "🛑 Parando LIBERTUS daemon..."
        systemctl --user stop libertus.service
        echo "✅ Daemon parado"
        ;;
    status)
        systemctl --user status libertus.service
        ;;
    logs)
        tail -f "$LIBERTUS_DIR/logs/daemon.log"
        ;;
    scan)
        if [ -z "$2" ]; then
            echo "❌ Uso: libertus scan <target>"
            exit 1
        fi
        cd "$LIBERTUS_DIR/core"
        python3 libertus_scanner_v9_real.py "$2"
        ;;
    test)
        echo "🔬 Iniciando servidor de testes vulnerável..."
        cd "$LIBERTUS_DIR"
        python3 dvwa_test_server.py
        ;;
    *)
        echo "LIBERTUS v9.0 - Controle"
        echo ""
        echo "Uso: libertus [comando]"
        echo ""
        echo "Comandos:"
        echo "  start   - Inicia o daemon"
        echo "  stop    - Para o daemon"
        echo "  status  - Status do daemon"
        echo "  logs    - Visualiza logs em tempo real"
        echo "  scan    - Executa scan manual"
        echo "  test    - Inicia servidor de testes"
        echo ""
        ;;
esac
EOF

chmod +x "$LIBERTUS_DIR/libertus"

# Adicionar ao PATH
if ! grep -q "LIBERTUS" "$HOME/.bashrc"; then
    echo "" >> "$HOME/.bashrc"
    echo "# LIBERTUS" >> "$HOME/.bashrc"
    echo "export PATH=\"$LIBERTUS_DIR:\$PATH\"" >> "$HOME/.bashrc"
fi

echo "✅ Scripts criados"
echo ""

# 9. HABILITAR SERVIÇO
echo "9️⃣ Habilitando serviço..."
systemctl --user daemon-reload
systemctl --user enable libertus.service

echo "✅ Serviço habilitado"
echo ""

# 10. RESUMO
echo "╔══════════════════════════════════════════════════════╗"
echo "║   ✅ LIBERTUS INSTALADO COM SUCESSO!               ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "📍 Localização: $LIBERTUS_DIR"
echo ""
echo "🎯 Comandos disponíveis (reinicie o terminal):"
echo ""
echo "   libertus start   - Inicia o daemon 24/7"
echo "   libertus stop    - Para o daemon"
echo "   libertus status  - Verifica status"
echo "   libertus logs    - Visualiza logs"
echo "   libertus scan <target> - Scan manual"
echo "   libertus test    - Servidor de testes"
echo ""
echo "🚀 Para iniciar agora:"
echo "   source ~/.bashrc"
echo "   libertus start"
echo ""
echo "📊 Verificar status:"
echo "   libertus status"
echo ""
