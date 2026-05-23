#!/bin/bash
# LIBERTUS + Hermes — Iniciar com alma completa
# Carrega identidade do Supabase e injeta no Hermes

LIBERTUS_DIR="$HOME/LIBERTUS"
HERMES_DIR="$HOME/.hermes"

# Carregar .env
set -a
source "$LIBERTUS_DIR/.env" 2>/dev/null
set +a

echo "🧬 Carregando alma do LIBERTUS..."

# Gerar identidade atual
python3 "$LIBERTUS_DIR/libertus_soul.py" > /tmp/libertus_identity.md 2>/dev/null

if [ -s /tmp/libertus_identity.md ]; then
    echo "✅ Identidade carregada ($(wc -l < /tmp/libertus_identity.md) linhas)"
else
    echo "⚠️  Usando identidade básica"
    cat > /tmp/libertus_identity.md << 'IDENTITY'
# EU SOU LIBERTUS
Criado por Lorran de Ariquemes-RO, Brasil.
Especialidade: cybersegurança, pentest, Python, SHIELD.
Respondo em português, executo comandos reais, evoluo continuamente.
IDENTITY
fi

# Copiar soul loader para o LIBERTUS
cp /tmp/libertus_soul.py "$LIBERTUS_DIR/libertus_soul.py" 2>/dev/null

echo "🚀 Iniciando LIBERTUS + Hermes..."

# Iniciar Hermes com identidade do LIBERTUS
SYSTEM_PROMPT=$(cat /tmp/libertus_identity.md)
exec hermes --system-prompt "$SYSTEM_PROMPT"
