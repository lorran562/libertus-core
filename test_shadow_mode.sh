#!/bin/bash

echo "🧪 TESTE SHADOW MODE - 1 CICLO"
echo ""
echo "Vai rodar:"
echo "  1. Scan normal (produção)"
echo "  2. Router em paralelo (shadow)"
echo "  3. Comparar resultados"
echo "  4. Logs em ~/LIBERTUS/logs/shadow_mode.log"
echo ""

cd ~/LIBERTUS/core

# Exportar GROQ_API_KEY
export GROQ_API_KEY="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"

# Rodar 1 ciclo de shadow
timeout 180 python3 << 'EOF'
import asyncio
import sys
sys.path.insert(0, '/root/LIBERTUS/core')

from production_daemon_v2_shadow import ProductionDaemonV2Shadow

async def test_one_cycle():
    daemon = ProductionDaemonV2Shadow()
    
    # Pegar primeiro target
    target = daemon.target_manager.get_next_target()
    
    if target:
        print(f"\n🎯 Testando shadow mode com: {target.url}\n")
        await daemon.scan_target_production(target.url)
    else:
        print("❌ Nenhum target disponível para teste")

asyncio.run(test_one_cycle())
EOF

echo ""
echo "="*70
echo "✅ SHADOW MODE TESTE COMPLETO"
echo "="*70
echo ""
echo "📄 Ver logs completos:"
echo "   cat ~/LIBERTUS/logs/shadow_mode.log"
