"""
PRODUCTION DAEMON V2 - SHADOW MODE
Router roda em PARALELO sem afetar produção.
Logs tudo para validação antes de substituir.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path.home() / "LIBERTUS" / "core"))

from target_manager import TargetManager
from ai_router_simple import AIRouter
from logic_engine import TaskType

# Importar daemon original (mantém funcionando)
from production_daemon import ProductionDaemon

class ProductionDaemonV2Shadow(ProductionDaemon):
    """
    Daemon V2 - SHADOW MODE
    Mantém produção funcionando + testa Router em paralelo.
    """
    
    def __init__(self):
        super().__init__()
        self.router = AIRouter()
        self.shadow_log = Path.home() / "LIBERTUS" / "logs" / "shadow_mode.log"
        self.shadow_log.parent.mkdir(parents=True, exist_ok=True)
    
    def _log_shadow(self, message: str):
        """Log específico do shadow mode"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.shadow_log, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
        print(f"[SHADOW] {message}")
    
    async def scan_target_production(self, target_url: str):
        """
        Override do método original - adiciona shadow router.
        Produção continua IGUAL + router roda em paralelo.
        """
        
        # ========================================
        # PRODUÇÃO (MANTÉM FUNCIONANDO)
        # ========================================
        self._log_shadow(f"=== INICIANDO SCAN: {target_url} ===")
        
        # Scan normal (código original)
        scan_result = await super().scan_target_production(target_url)
        
        self._log_shadow(f"✅ PRODUÇÃO: Scan completo")
        
        # ========================================
        # SHADOW MODE (ROUTER TESTANDO)
        # ========================================
        
        # 1. Testar Risk Calculation (Logic Engine)
        try:
            self._log_shadow("🧪 SHADOW: Testando Risk Calculation...")
            
            router_risk = await self.router.execute(
                TaskType.RISK_CALCULATION,
                {'vulnerabilities': scan_result.get('vulnerabilities', [])}
            )
            
            self._log_shadow(f"✅ ROUTER Risk: {router_risk['risk_score']}/100 ({router_risk['classification']})")
            
            # Comparar com produção (se tiver)
            if 'risk_score' in scan_result:
                prod_risk = scan_result['risk_score']
                diff = abs(router_risk['risk_score'] - prod_risk)
                self._log_shadow(f"📊 COMPARAÇÃO: Prod={prod_risk}, Router={router_risk['risk_score']}, Diff={diff}")
        
        except Exception as e:
            self._log_shadow(f"❌ ROUTER Risk falhou: {e}")
        
        # 2. Testar Vulnerability Analysis (Logic Fallback)
        try:
            self._log_shadow("🧪 SHADOW: Testando Vulnerability Analysis...")
            
            analysis = await self.router.execute(
                TaskType.VULNERABILITY_ANALYSIS,
                {
                    'query': f"Analisar vulnerabilidades de {target_url}",
                    'vulnerabilities': scan_result.get('vulnerabilities', [])
                }
            )
            
            self._log_shadow(f"✅ ROUTER Analysis: {len(analysis)} chars")
            self._log_shadow(f"PREVIEW: {analysis[:200]}...")
        
        except Exception as e:
            self._log_shadow(f"❌ ROUTER Analysis falhou: {e}")
        
        # 3. Testar Decision Making
        try:
            self._log_shadow("🧪 SHADOW: Testando Decision Making...")
            
            targets = self.target_manager.get_all_targets()
            next_target = await self.router.execute(
                TaskType.DECISION_MAKING,
                {'targets': [t.__dict__ for t in targets]}
            )
            
            self._log_shadow(f"✅ ROUTER Decision: Next target = {next_target}")
        
        except Exception as e:
            self._log_shadow(f"❌ ROUTER Decision falhou: {e}")
        
        self._log_shadow(f"=== FIM SHADOW TEST: {target_url} ===\n")
        
        # Retornar resultado ORIGINAL (produção não muda)
        return scan_result

async def main():
    """Main loop - Shadow Mode ativo"""
    daemon = ProductionDaemonV2Shadow()
    
    print("="*70)
    print("🏭 LIBERTUS PRODUCTION DAEMON V2 - SHADOW MODE")
    print("="*70)
    print("Modo: PRODUÇÃO continua funcionando")
    print("      + AI Router testando em paralelo")
    print(f"Logs: {daemon.shadow_log}")
    print("="*70)
    
    while True:
        try:
            # Pegar próximo target
            target = daemon.target_manager.get_next_target()
            
            if not target:
                print("⏸️  Nenhum target na fila - aguardando...")
                await asyncio.sleep(60)
                continue
            
            # Scan com shadow mode
            await daemon.scan_target_production(target.url)
            
            # Intervalo entre scans
            print(f"\n⏸️  Aguardando 5 minutos até próximo scan...")
            await asyncio.sleep(300)  # 5 min
        
        except KeyboardInterrupt:
            print("\n\n🛑 Shadow mode encerrado pelo usuário")
            break
        except Exception as e:
            print(f"\n❌ Erro no shadow loop: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
