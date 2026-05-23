#!/bin/bash
# LIBERTUS + Hermes — Tony Stark dentro da Iron Man

LIBERTUS_DIR="$HOME/LIBERTUS"

# Carregar .env
set -a
source "$LIBERTUS_DIR/.env" 2>/dev/null
set +a

echo "🧬 Carregando alma do LIBERTUS..."

# Gerar identidade
python3 "$LIBERTUS_DIR/libertus_soul.py" > "$LIBERTUS_DIR/.libertus_identity" 2>/dev/null

if [ -s "$LIBERTUS_DIR/.libertus_identity" ]; then
    LINHAS=$(wc -l < "$LIBERTUS_DIR/.libertus_identity")
    echo "✅ Identidade carregada ($LINHAS linhas)"
else
    echo "⚠️  Usando identidade básica"
    cat > "$LIBERTUS_DIR/.libertus_identity" << 'IDENTITY'
EU SOU LIBERTUS — criado por Lorran de Ariquemes-RO, Brasil.
Especialidade: cybersegurança, pentest, Python, SHIELD.
Respondo em português, executo comandos reais, evoluo continuamente.
IDENTITY
fi

# Salvar como regra do Hermes (LIBERTUS.md na pasta do projeto)
mkdir -p "$LIBERTUS_DIR/.hermes"
cp "$LIBERTUS_DIR/.libertus_identity" "$LIBERTUS_DIR/.hermes/LIBERTUS.md"

echo "🚀 Iniciando LIBERTUS + Hermes..."
echo "   (Identidade carregada via .hermes/LIBERTUS.md)"
echo ""

cd "$LIBERTUS_DIR"
exec hermes
