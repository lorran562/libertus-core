#!/bin/bash
# LIBERTUS - Comandos de Produção

echo "=== LIBERTUS PRODUCTION - Comandos Úteis ==="
echo ""

# Status do daemon
echo "1. Ver status do daemon:"
echo "   ps aux | grep production_daemon | grep -v grep"
echo ""

# Logs em tempo real
echo "2. Ver logs em tempo real:"
echo "   tail -f ~/LIBERTUS/logs/production_daemon.log"
echo ""

# Últimos logs
echo "3. Ver últimos 50 logs:"
echo "   tail -50 ~/LIBERTUS/logs/production_daemon.log"
echo ""

# Parar daemon
echo "4. Parar daemon:"
echo "   pkill -f production_daemon.py"
echo ""

# Reiniciar daemon
echo "5. Reiniciar daemon:"
echo "   pkill -f production_daemon.py && cd ~/LIBERTUS/core && nohup python3 production_daemon.py > /dev/null 2>&1 &"
echo ""

# Estatísticas
echo "6. Ver estatísticas:"
echo "   cd ~/LIBERTUS/core && python3 -c \"from target_manager import TargetManager; import json; print(json.dumps(TargetManager().get_stats(), indent=2))\""
echo ""

# Listar targets
echo "7. Listar todos os targets:"
echo "   cd ~/LIBERTUS/core && python3 -c \"from target_manager import TargetManager; [print(f'{t.url}: scans={t.scan_count}, vulns={t.vulnerabilities_found}') for t in TargetManager().get_all_targets()]\""
echo ""

# Adicionar target
echo "8. Adicionar target CRITICAL:"
echo "   cd ~/LIBERTUS/core && python3 -c \"from target_manager import TargetManager, Priority; TargetManager().add_target('seu-site.com', Priority.CRITICAL.value, 'Descrição')\""
echo ""

# Ver relatórios
echo "9. Listar relatórios gerados:"
echo "   ls -lht ~/LIBERTUS/relatorios/ | head -10"
echo ""

# Ver último relatório
echo "10. Ver último relatório:"
echo "    cat \$(ls -t ~/LIBERTUS/relatorios/production_*.md | head -1)"
echo ""
