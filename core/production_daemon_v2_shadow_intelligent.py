"""
PRODUCTION DAEMON V2 - SHADOW INTELLIGENT
Router roda em paralelo + ANALYZER decide qual é melhor.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "LIBERTUS" / "core"))

from production_daemon_v2_shadow import ProductionDaemonV2Shadow
from shadow_analyzer_simple import ShadowAnalyzer

class ProductionDaemonV2Intelligent(ProductionDaemonV2Shadow):
    """
    Shadow Mode INTELIGENTE
    Compara resultados e DECIDE automaticamente.
    """
    
    def __init__(self):
        super().__init__()
        self.analyzer = ShadowAnalyzer()
    
    async def scan_target_production(self, target_url: str):
        """
        Override - adiciona análise inteligente.
        """
        self._log_shadow(f"=== SCAN INTELIGENTE: {target_url} ===")
        
        # Scan normal (produção)
        from libertus_scanner_final import LibertusScannerFinal
        scanner = LibertusScannerFinal(target_url)
        scan_result = await scanner.scan_complete()
        
        prod_risk = scan_result.get('risk_score', 0)
        vulnerabilities = scan_result.get('vulnerabilities', [])
        
        self._log_shadow(f"✅ PRODUÇÃO: Risk={prod_risk}/100")
        
        # ========================================
        # ROUTER + ANALYZER
        # ========================================
        
        try:
            # Risk Calculation com Router
            from ai_router_simple import AIRouter
            from logic_engine import TaskType
            
            router = AIRouter()
            
            router_result = await router.execute(
                TaskType.RISK_CALCULATION,
                {'vulnerabilities': vulnerabilities}
            )
            
            # Router retorna dict com risk_score
            router_risk = router_result.get('risk_score', 0) if isinstance(router_result, dict) else 0
            
            self._log_shadow(f"✅ ROUTER: Risk={router_risk}/100")
            
            # ========================================
            # ANÁLISE COMPARATIVA (O IMPORTANTE!)
            # ========================================
            
            # Análise comparativa
            # Garantir que vulnerabilities é uma lista
            if not isinstance(vulnerabilities, list):
                vulnerabilities = []
            
            comparison = self.analyzer.analyze_comparison(
                prod_risk=prod_risk,
                router_risk=router_risk,
                target=target_url,
                vulnerabilities=vulnerabilities
            )
            
            diff = comparison['diff']
            decision = comparison['decision']
            
            self._log_shadow(f"📊 COMPARAÇÃO:")
            self._log_shadow(f"   Prod: {prod_risk} | Router: {router_risk} | Diff: {diff}")
            self._log_shadow(f"   Decisão: {decision.upper()}")
            
            # Alertas
            if diff > 20:
                self._log_shadow(f"⚠️  ALERTA: Divergência alta ({diff} pontos)")
            
            if diff > 50:
                self._log_shadow(f"🚨 CRÍTICO: Divergência crítica! Investigar!")
            
            # Recomendação após N comparações
            if self.analyzer.metrics['total_comparisons'] % 5 == 0:  # A cada 5 scans
                recommendation = self.analyzer.get_recommendation()
                self._log_shadow(f"\n{'='*60}")
                self._log_shadow(f"💡 RECOMENDAÇÃO: {recommendation}")
                self._log_shadow(f"{'='*60}\n")
        
        except Exception as e:
            self._log_shadow(f"❌ Analyzer falhou: {e}")
        
        self._log_shadow(f"=== FIM SCAN INTELIGENTE ===\n")
        
        return scan_result

async def main():
    """Main - Shadow Intelligent"""
    daemon = ProductionDaemonV2Intelligent()
    
    print("="*70)
    print("🧠 LIBERTUS PRODUCTION DAEMON V2 - SHADOW INTELLIGENT")
    print("="*70)
    print("Modo: PRODUÇÃO + AI Router + Analyzer")
    print("      Sistema DECIDE automaticamente qual é melhor")
    print(f"Logs: {daemon.shadow_log}")
    print(f"Métricas: ~/LIBERTUS/logs/shadow_metrics.json")
    print("="*70)
    
    # Mostrar estado atual
    daemon.analyzer.print_report()
    
    print("\n▶️  Iniciando loop shadow intelligent...\n")
    
    while True:
        try:
            target = daemon.target_manager.get_next_target()
            
            if not target:
                print("⏸️  Nenhum target - aguardando...")
                await asyncio.sleep(60)
                continue
            
            await daemon.scan_target_production(target.url)
            
            # A cada 5 scans, mostrar relatório
            if daemon.analyzer.metrics['total_comparisons'] % 5 == 0:
                print("\n" + "="*70)
                daemon.analyzer.print_report()
                print("="*70 + "\n")
            
            await asyncio.sleep(300)  # 5 min
        
        except KeyboardInterrupt:
            print("\n\n🛑 Shadow intelligent encerrado")
            daemon.analyzer.print_report()
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
