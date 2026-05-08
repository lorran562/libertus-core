#!/bin/bash
echo "🔍 ESCANEANDO EMPRESAS LOCAIS DE ARIQUEMES/RO"
echo ""

# Lista de empresas locais (exemplos - você adiciona as reais)
SITES=(
    "https://exemplo1.com.br"
    "https://exemplo2.com.br"
    "https://exemplo3.com.br"
)

for site in "${SITES[@]}"; do
    echo "═══════════════════════════════════════════"
    echo "🎯 Target: $site"
    echo "═══════════════════════════════════════════"
    
    # Scan básico
    python3 /root/LIBERTUS/libertus_scanner.py "$site"
    
    echo ""
    echo "✅ Scan concluído para $site"
    echo ""
    sleep 5
done

echo "✅ TODOS OS SCANS CONCLUÍDOS!"
echo "📁 Relatórios salvos em: /root/LIBERTUS/evolution_logs/"
