#!/usr/bin/env python3
"""
LIBERTUS DAEMON v2.0 REAL
Loop contínuo profissional com:
- Retry automático
- Tratamento de falhas
- Logging estruturado
- Health checks
- Graceful shutdown
"""

import asyncio
import signal
import sys
import json
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import logging

# Imports dos módulos reais
sys.path.insert(0, '/root/LIBERTUS/core')

from libertus_scanner_v9_real import LibertusScannerV9
from libertus_brain_v2_real import LibertusBrainV2
from motor_decisao_v2_real import MotorDecisaoV2, ActionType


class DaemonState:
    """Estado do daemon"""
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class LibertusDaemonV2:
    """
    Daemon profissional com loop robusto
    """
    
    def __init__(self, config_path: str = "/root/LIBERTUS/daemon_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Estado
        self.state = DaemonState.STARTING
        self.running = True
        self.cycle_count = 0
        self.last_error = None
        self.start_time = datetime.now()
        
        # Componentes
        self.brain = LibertusBrainV2()
        self.motor = MotorDecisaoV2()
        
        # Logging
        self._setup_logging()
        
        # Health check
        self.last_health_check = datetime.now()
        self.health_interval = timedelta(minutes=5)
        
        # Retry config
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        
        # Shutdown handler
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)
    
    def _load_config(self) -> Dict:
        """Carrega configuração"""
        
        default_config = {
            'cycle_interval_seconds': 300,  # 5 minutos
            'targets': [],
            'scan_interval_hours': 24,
            'auto_scan_enabled': True,
            'notification_enabled': False,
            'log_level': 'INFO',
            'max_concurrent_scans': 1
        }
        
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    loaded = json.load(f)
                    return {**default_config, **loaded}
        except:
            pass
        
        return default_config
    
    def _setup_logging(self):
        """Configura logging estruturado"""
        
        log_dir = Path('/root/LIBERTUS/logs')
        log_dir.mkdir(exist_ok=True)
        
        # Arquivo de log
        log_file = log_dir / f"daemon_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Configurar
        logging.basicConfig(
            level=getattr(logging, self.config.get('log_level', 'INFO')),
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger('libertus_daemon')
    
    async def start(self):
        """Inicia daemon"""
        
        self.logger.info("="*70)
        self.logger.info("🚀 LIBERTUS DAEMON v2.0 INICIANDO")
        self.logger.info("="*70)
        
        self.state = DaemonState.RUNNING
        
        try:
            # Loop principal
            await self._main_loop()
        
        except Exception as e:
            self.logger.error(f"Erro fatal no daemon: {e}")
            self.logger.error(traceback.format_exc())
            self.state = DaemonState.ERROR
            self.last_error = str(e)
        
        finally:
            await self._shutdown()
    
    async def _main_loop(self):
        """Loop principal do daemon"""
        
        self.logger.info("Entrando no loop principal...")
        
        while self.running:
            try:
                # Incrementar contador
                self.cycle_count += 1
                
                self.logger.info(f"\n{'='*70}")
                self.logger.info(f"🔄 CICLO #{self.cycle_count}")
                self.logger.info(f"{'='*70}")
                
                # Health check
                if datetime.now() - self.last_health_check > self.health_interval:
                    await self._health_check()
                
                # Ciclo de execução
                await self._execute_cycle()
                
                # Aguardar próximo ciclo
                interval = self.config.get('cycle_interval_seconds', 300)
                self.logger.info(f"\n⏳ Aguardando {interval}s até próximo ciclo...")
                await asyncio.sleep(interval)
            
            except asyncio.CancelledError:
                self.logger.info("Loop cancelado - encerrando...")
                break
            
            except Exception as e:
                self.logger.error(f"Erro no ciclo #{self.cycle_count}: {e}")
                self.logger.error(traceback.format_exc())
                
                # Retry logic
                retry_success = await self._retry_on_error()
                
                if not retry_success:
                    self.logger.error("Máximo de retries atingido - continuando...")
                    await asyncio.sleep(60)  # Wait 1 min before next cycle
    
    async def _execute_cycle(self):
        """Executa um ciclo completo"""
        
        # 1. Verificar ações pendentes
        self.logger.info("\n1️⃣ Verificando ações pendentes...")
        pending_actions = self.motor.get_pending_actions()
        
        if pending_actions:
            self.logger.info(f"   {len(pending_actions)} ações pendentes")
            
            for action in pending_actions[:self.config.get('max_concurrent_scans', 1)]:
                await self._execute_action(action)
        else:
            self.logger.info("   Nenhuma ação pendente")
        
        # 2. Auto-scan de targets configurados
        if self.config.get('auto_scan_enabled', True):
            self.logger.info("\n2️⃣ Verificando auto-scan...")
            await self._auto_scan_targets()
        
        # 3. Consolidar memória
        self.logger.info("\n3️⃣ Consolidando memória...")
        await self._consolidate_memory()
        
        # 4. Git sync (se configurado)
        if self.config.get('git_sync_enabled', False):
            self.logger.info("\n4️⃣ Sincronizando Git...")
            await self._git_sync()
    
    async def _execute_action(self, action: Dict):
        """Executa uma ação específica"""
        
        target = action['target']
        action_type = action['action']
        
        self.logger.info(f"\n   🎯 Executando: {action_type.value} em {target}")
        
        try:
            if action_type == ActionType.SCAN_FULL:
                await self._scan_target(target, 'full')
            
            elif action_type == ActionType.SCAN_QUICK:
                await self._scan_target(target, 'quick')
            
            elif action_type == ActionType.RESCAN:
                await self._scan_target(target, 'rescan')
            
            elif action_type == ActionType.ESCALATE:
                await self._escalate_issue(target, action)
            
            elif action_type == ActionType.GENERATE_REPORT:
                await self._generate_report(target)
            
            else:
                self.logger.info(f"   ⏭️  Ação {action_type.value} não implementada ainda")
        
        except Exception as e:
            self.logger.error(f"   ❌ Erro ao executar ação: {e}")
    
    async def _scan_target(self, target: str, scan_type: str = 'full'):
        """Executa scan em target"""
        
        self.logger.info(f"   🔍 Iniciando scan {scan_type} em {target}...")
        
        try:
            # Criar scanner
            scanner = LibertusScannerV9(target)
            
            # Executar scan
            results = await scanner.scan_complete()
            
            # Salvar resultado
            output_file = f"/root/LIBERTUS/relatorios/daemon_scan_{target.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            scanner.save(output_file)
            
            self.logger.info(f"   ✅ Scan completo: {len(results['vulnerabilities'])} vulnerabilidades")
            
            # Atualizar motor de decisão
            self.motor.update_state(target, results)
            
            # Análise com Brain
            if results['vulnerabilities']:
                analyzed = self.brain.prioritize_vulnerabilities(results['vulnerabilities'])
                summary = self.brain.generate_executive_summary(analyzed)
                
                self.logger.info(f"   🧠 Risk Score: {summary['estimated_total_risk_cost_usd']}")
                self.logger.info(f"   📊 Status: {summary['overall_status']}")
        
        except Exception as e:
            self.logger.error(f"   ❌ Erro no scan: {e}")
            raise
    
    async def _auto_scan_targets(self):
        """Auto-scan de targets configurados"""
        
        targets = self.config.get('targets', [])
        
        if not targets:
            self.logger.info("   Nenhum target configurado")
            return
        
        self.logger.info(f"   {len(targets)} targets configurados")
        
        for target in targets:
            # Verificar se precisa scan
            context = {
                'target': target,
                'state': 'complete',
                'last_scan_date': self.motor.state['targets'].get(target, {}).get('last_scan')
            }
            
            decision = self.motor.decide(context)
            
            if decision['action'] in [ActionType.SCAN_FULL, ActionType.RESCAN]:
                self.logger.info(f"\n   📌 {target} precisa scan")
                await self._scan_target(target)
            else:
                self.logger.info(f"   ✅ {target} OK (última decisão: {decision['action'].value})")
    
    async def _escalate_issue(self, target: str, action: Dict):
        """Escalate issue crítica"""
        
        self.logger.warning(f"   🚨 ESCALATE: {target}")
        self.logger.warning(f"      Severidade: {action.get('severity', 'UNKNOWN')}")
        
        # TODO: Enviar notificação (email, slack, etc)
        # Por agora apenas log
    
    async def _generate_report(self, target: str):
        """Gera relatório"""
        
        self.logger.info(f"   📊 Gerando relatório para {target}...")
        
        # TODO: Implementar geração de relatório PDF
        # Por agora apenas log
    
    async def _consolidate_memory(self):
        """Consolida memória"""
        
        # Salvar estado do motor
        state_file = Path('/root/LIBERTUS/daemon_state.json')
        
        try:
            with open(state_file, 'w') as f:
                state_data = {
                    'last_update': datetime.now().isoformat(),
                    'cycle_count': self.cycle_count,
                    'targets': {
                        k: {
                            'last_scan': v['last_scan'].isoformat() if v.get('last_scan') else None,
                            'last_decision': {
                                'action': v.get('last_decision', {}).get('action', ActionType.WAIT).value if isinstance(v.get('last_decision', {}).get('action'), ActionType) else 'wait',
                                'priority': v.get('last_decision', {}).get('priority', 'LOW').name if hasattr(v.get('last_decision', {}).get('priority'), 'name') else 'LOW'
                            }
                        }
                        for k, v in self.motor.state['targets'].items()
                    }
                }
                
                json.dump(state_data, f, indent=2)
            
            self.logger.info(f"   ✅ Estado salvo em {state_file}")
        
        except Exception as e:
            self.logger.error(f"   ⚠️  Erro ao salvar estado: {e}")
    
    async def _git_sync(self):
        """Sincroniza com Git"""
        
        try:
            import subprocess
            
            result = subprocess.run(
                ['git', 'add', '-A'],
                cwd='/root/LIBERTUS',
                capture_output=True,
                timeout=10
            )
            
            if result.returncode == 0:
                subprocess.run(
                    ['git', 'commit', '-m', f'daemon auto-commit - cycle #{self.cycle_count}'],
                    cwd='/root/LIBERTUS',
                    capture_output=True,
                    timeout=10
                )
                
                self.logger.info("   ✅ Git sync OK")
            
        except Exception as e:
            self.logger.warning(f"   ⚠️  Git sync falhou: {e}")
    
    async def _health_check(self):
        """Health check do sistema"""
        
        self.logger.info("\n💊 HEALTH CHECK")
        
        # Uptime
        uptime = datetime.now() - self.start_time
        self.logger.info(f"   Uptime: {uptime}")
        self.logger.info(f"   Ciclos: {self.cycle_count}")
        self.logger.info(f"   Estado: {self.state}")
        
        # Targets monitorados
        targets = len(self.motor.state['targets'])
        self.logger.info(f"   Targets: {targets}")
        
        self.last_health_check = datetime.now()
    
    async def _retry_on_error(self) -> bool:
        """Retry logic em caso de erro"""
        
        for retry in range(1, self.max_retries + 1):
            self.logger.warning(f"🔄 Retry {retry}/{self.max_retries}...")
            
            await asyncio.sleep(self.retry_delay * retry)
            
            try:
                # Tentar executar ciclo novamente
                await self._execute_cycle()
                
                self.logger.info("✅ Retry bem-sucedido!")
                return True
            
            except Exception as e:
                self.logger.error(f"❌ Retry {retry} falhou: {e}")
        
        return False
    
    def _handle_shutdown(self, signum, frame):
        """Handler de shutdown graceful"""
        
        self.logger.info(f"\n⚠️  Recebido sinal de shutdown: {signum}")
        self.running = False
        self.state = DaemonState.STOPPING
    
    async def _shutdown(self):
        """Shutdown graceful"""
        
        self.logger.info("\n" + "="*70)
        self.logger.info("🛑 ENCERRANDO DAEMON")
        self.logger.info("="*70)
        
        # Salvar estado final
        await self._consolidate_memory()
        
        # Uptime final
        uptime = datetime.now() - self.start_time
        self.logger.info(f"\n📊 ESTATÍSTICAS FINAIS:")
        self.logger.info(f"   Uptime: {uptime}")
        self.logger.info(f"   Ciclos executados: {self.cycle_count}")
        self.logger.info(f"   Targets monitorados: {len(self.motor.state['targets'])}")
        
        self.state = DaemonState.STOPPED
        self.logger.info("\n✅ Daemon encerrado com sucesso")


# Entry point
async def main():
    daemon = LibertusDaemonV2()
    await daemon.start()


if __name__ == "__main__":
    asyncio.run(main())
