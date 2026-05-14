#!/usr/bin/env python3
"""
LIBERTUS DAEMON REAL - SEM SIMULAÇÃO
Loop autônomo que executa ações reais
"""

import asyncio
import json
import os
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - LIBERTUS - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.expanduser('~/LIBERTUS/logs/daemon_real.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('LIBERTUS')


class LibertusExecutor:
    """Executor REAL de ações - sem simulação"""
    
    def __init__(self):
        self.base_dir = Path.home() / "LIBERTUS"
        self.logs_dir = self.base_dir / "logs"
        self.scans_dir = self.base_dir / "scans"
        self.reports_dir = self.base_dir / "relatorios"
        
        # Criar diretórios
        self.logs_dir.mkdir(exist_ok=True)
        self.scans_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
    
    def execute_python_script(self, script_path: str, *args) -> dict:
        """Executa script Python REAL e retorna resultado"""
        try:
            cmd = ["python3", str(self.base_dir / "core" / script_path)] + list(args)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout após 5 minutos"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def git_auto_commit(self, message: str) -> bool:
        """Git commit + push REAL"""
        try:
            os.chdir(self.base_dir)
            
            # Git add
            subprocess.run(["git", "add", "-A"], check=True, capture_output=True)
            
            # Git commit
            subprocess.run(
                ["git", "commit", "-m", message],
                check=True,
                capture_output=True
            )
            
            # Git push
            subprocess.run(
                ["git", "push", "origin", "main"],
                check=True,
                capture_output=True
            )
            
            logger.info(f"✅ Git commit + push: {message}")
            return True
        
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Git error: {e}")
            return False
    
    def save_to_file(self, filepath: Path, data: dict) -> bool:
        """Salva dados REAIS em arquivo JSON"""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"💾 Arquivo salvo: {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Erro ao salvar {filepath}: {e}")
            return False


class LibertusMotorDecisao:
    """Motor de decisão COM LÓGICA REAL"""
    
    def __init__(self, executor: LibertusExecutor):
        self.executor = executor
        self.base_dir = Path.home() / "LIBERTUS"
    
    def should_learn_next_topic(self) -> bool:
        """Decide se deve aprender próximo tópico"""
        objetivo_file = self.base_dir / "objetivos" / "objetivo_ativo.json"
        
        if not objetivo_file.exists():
            return False
        
        try:
            with open(objetivo_file) as f:
                objetivo = json.load(f)
            
            # Se tem menos de 3 conhecimentos adquiridos hoje, aprender mais
            conhecimentos_hoje = [
                c for c in objetivo["progresso"]["conhecimento_adquirido"]
                if c["timestamp"].startswith(datetime.now().strftime("%Y-%m-%d"))
            ]
            
            return len(conhecimentos_hoje) < 3
        
        except Exception as e:
            logger.error(f"Erro ao verificar objetivo: {e}")
            return False
    
    def get_next_action(self) -> dict:
        """Retorna próxima ação REAL a executar"""
        
        # Regra 1: Aprender se necessário
        if self.should_learn_next_topic():
            return {
                "action": "learn",
                "priority": "HIGH",
                "description": "Aprender próximo tópico do objetivo"
            }
        
        # Regra 2: Atualizar código (1x por dia)
        last_update_file = self.base_dir / "logs" / "last_git_pull.txt"
        if not last_update_file.exists() or self._is_outdated(last_update_file):
            return {
                "action": "git_pull",
                "priority": "MEDIUM",
                "description": "Atualizar código do repositório"
            }
        
        # Regra 3: Idle (nada a fazer agora)
        return {
            "action": "idle",
            "priority": "LOW",
            "description": "Sistema em espera"
        }
    
    def _is_outdated(self, file: Path) -> bool:
        """Verifica se arquivo tem mais de 24h"""
        try:
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            return (datetime.now() - mtime).total_seconds() > 86400
        except:
            return True


class LibertusDaemonReal:
    """Daemon REAL que executa ações de verdade"""
    
    def __init__(self):
        self.executor = LibertusExecutor()
        self.motor = LibertusMotorDecisao(self.executor)
        self.running = True
    
    async def execute_action(self, action: dict):
        """Executa ação REAL baseada no motor de decisão"""
        
        action_type = action["action"]
        
        if action_type == "learn":
            await self.action_learn()
        
        elif action_type == "git_pull":
            self.action_git_pull()
        
        elif action_type == "idle":
            logger.info("⏸️ Sistema em espera")
    
    async def action_learn(self):
        """Aprende próximo tópico REAL"""
        try:
            # Carregar objetivo
            objetivo_file = Path.home() / "LIBERTUS" / "objetivos" / "objetivo_ativo.json"
            
            with open(objetivo_file) as f:
                objetivo = json.load(f)
            
            # Obter próximo tópico
            from objetivo_system import ObjetivoSystem
            sistema = ObjetivoSystem()
            proximo_topico = sistema.get_proximo_topico_aprendizado()
            
            if not proximo_topico:
                logger.info("✅ Todos os tópicos já foram estudados")
                return
            
            logger.info(f"🎓 Aprendendo: {proximo_topico}")
            
            # Executar learning engine REAL
            from learning_engine import LearningEngine
            from groq import AsyncGroq
            
            groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
            engine = LearningEngine(groq_client=groq_client)
            
            # Buscar papers
            result = await engine.learn_from_arxiv(proximo_topico, max_papers=2)
            
            if result.get("success"):
                # Registrar conhecimento
                sistema.adicionar_conhecimento(
                    topico=proximo_topico,
                    fonte="arxiv_autonomous"
                )
                
                sistema.atualizar_progresso("papers_lidos", result.get("papers_count", 0))
                
                logger.info(f"✅ Conhecimento adquirido: {proximo_topico}")
                
                # Git commit
                self.executor.git_auto_commit(
                    f"🎓 Aprendizado autônomo: {proximo_topico}"
                )
            
            else:
                logger.error(f"❌ Falha ao aprender: {result.get('error')}")
        
        except Exception as e:
            logger.error(f"❌ Erro no aprendizado: {e}")
    
    def action_git_pull(self):
        """Atualiza código REAL do repositório"""
        try:
            os.chdir(Path.home() / "LIBERTUS")
            
            result = subprocess.run(
                ["git", "pull", "origin", "main"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("✅ Código atualizado do GitHub")
                
                # Marcar última atualização
                last_update_file = Path.home() / "LIBERTUS" / "logs" / "last_git_pull.txt"
                last_update_file.write_text(datetime.now().isoformat())
            else:
                logger.error(f"❌ Git pull falhou: {result.stderr}")
        
        except Exception as e:
            logger.error(f"❌ Erro no git pull: {e}")
    
    async def run(self):
        """Loop principal REAL - executa ações de verdade"""
        
        logger.info("🚀 LIBERTUS DAEMON REAL INICIADO")
        logger.info("📊 Modo: EXECUÇÃO REAL (sem simulação)")
        
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"🔄 Iteração #{iteration} - {datetime.now()}")
                logger.info(f"{'='*60}")
                
                # Obter próxima ação
                action = self.motor.get_next_action()
                
                logger.info(f"🎯 Ação: {action['action']} (Prioridade: {action['priority']})")
                logger.info(f"📝 {action['description']}")
                
                # Executar ação REAL
                await self.execute_action(action)
                
                # Esperar antes da próxima iteração
                # Ações HIGH: 5 min, MEDIUM: 15 min, LOW: 30 min
                wait_times = {"HIGH": 300, "MEDIUM": 900, "LOW": 1800}
                wait_time = wait_times.get(action["priority"], 1800)
                
                logger.info(f"⏱️ Próxima verificação em {wait_time//60} minutos")
                
                await asyncio.sleep(wait_time)
            
            except KeyboardInterrupt:
                logger.info("\n⏹️ Interrupção detectada - finalizando...")
                self.running = False
            
            except Exception as e:
                logger.error(f"❌ Erro na iteração: {e}")
                await asyncio.sleep(60)  # Esperar 1 min em caso de erro


if __name__ == "__main__":
    daemon = LibertusDaemonReal()
    asyncio.run(daemon.run())
