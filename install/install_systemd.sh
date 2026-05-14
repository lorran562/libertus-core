#!/bin/bash
echo "🔧 Instalando LIBERTUS Systemd Service..."

# Criar diretório de logs
mkdir -p ~/LIBERTUS/logs

# Instalar service file
mkdir -p ~/.config/systemd/user
cp ~/LIBERTUS/install/libertus.service ~/.config/systemd/user/libertus.service

# Recarregar systemd
systemctl --user daemon-reload

echo "✅ Service instalado!"
echo ""
echo "Para iniciar:"
echo "  systemctl --user start libertus"
echo ""
echo "Para habilitar no boot:"
echo "  systemctl --user enable libertus"
echo ""
echo "Para ver status:"
echo "  systemctl --user status libertus"
