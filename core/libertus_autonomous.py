#!/usr/bin/env python3
"""
LIBERTUS AUTONOMOUS DAEMON
Roda 24/7 executando ciclos autônomos
"""

import asyncio
import time
import subprocess
from pathlib import Path
from datetime import datetime
import json
import sys

sys.path.insert(0, '/root/LIBERTUS/core')

class LibertusAutonomous:
    """Daemon autônomo do Libertus"""
    
    def __init__(self):
        self.base_dir = Path("/root/LIBERTUS")
        self.log_file = self.base_dir / "autonomous.log"
        self.running = True
        
    def log(self, msg):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {msg}"
        print(log_msg)
        
        with open(self.log_file, "a") as f:
            f.write(log_msg + "\n")
    
    async def ciclo_git_sync(self):
        """Git auto-sync a cada 4 horas"""
        try:
            self.log("🔄 Git sync iniciado...")
            
            os.chdir("/root/LIBERTUS")
            
            # Add all
            subprocess.run(["git", "add", "-A"], capture_output=True)
            
            # Check if there are changes
            result = subprocess.run(
                ["git", "diff", "--staged", "--quiet"],
                capture_output=True
            )
            
            if result.returncode != 0:  # Has changes
                # Commit
                commit_msg = f"auto: {datetime.now().strftime('%Y%m%d_%H%M%S')}"
                subprocess.run(
                    ["git", "commit", "-m", commit_msg],
                    capture_output=True
                )
                
                # Push
                push_result = subprocess.run(
                    ["git", "push", "origin", "main"],
                    capture_output=True,
                    text=True
                )
                
                if push_result.returncode == 0:
                    self.log("   ✅ Git sync realizado")
                else:
                    self.log(f"   ⚠️ Push falhou: {push_result.stderr[:100]}")
            else:
                self.log("   ℹ️ Sem mudanças para commitar")
                
        except Exception as e:
            self.log(f"   ❌ Erro git sync: {e}")
    
    async def ciclo_observacao(self):
        """Observa estado do sistema"""
        try:
            # Verifica memórias
            mem_count = len(list(self.base_dir.glob("evolution_logs/*.json")))
            
            # Verifica espaço em disco
            disk_result = subprocess.run(
                ["df", "-h", "/root"],
                capture_output=True,
                text=True
            )
            
            self.log(f"📊 Observação: {mem_count} scans, disco OK")
            
        except Exception as e:
            self.log(f"❌ Erro observação: {e}")
    
    async def main_loop(self):
        """Loop principal autônomo"""
        self.log("🚀 LIBERTUS AUTONOMOUS DAEMON INICIADO")
        self.log("=" * 60)
        
        last_git_sync = 0
        last_observation = 0
        
        iteration = 0
        
        while self.running:
            try:
                iteration += 1
                current_time = time.time()
                
                # Observação a cada 5 minutos
                if current_time - last_observation >= 300:
                    await self.ciclo_observacao()
                    last_observation = current_time
                
                # Git sync a cada 4 horas
                if current_time - last_git_sync >= 14400:  # 4h = 14400s
                    await self.ciclo_git_sync()
                    last_git_sync = current_time
                
                # Heartbeat a cada 100 iterações
                if iteration % 100 == 0:
                    self.log(f"💓 Heartbeat: {iteration} iterações, uptime: {int(current_time - self.start_time)}s")
                
                # Sleep 30s
                await asyncio.sleep(30)
                
            except KeyboardInterrupt:
                self.log("⚠️ Interrupção manual detectada")
                self.running = False
                break
                
            except Exception as e:
                self.log(f"❌ Erro no loop: {e}")
                await asyncio.sleep(60)  # Wait antes de tentar novamente
        
        self.log("🛑 Daemon finalizado")
    
    def run(self):
        """Inicia o daemon"""
        self.start_time = time.time()
        
        try:
            asyncio.run(self.main_loop())
        except Exception as e:
            self.log(f"💥 Erro fatal: {e}")
            raise


if __name__ == "__main__":
    import os
    
    # Cria PID file
    pid_file = Path("/root/LIBERTUS/autonomous.pid")
    pid_file.write_text(str(os.getpid()))
    
    try:
        daemon = LibertusAutonomous()
        daemon.run()
    finally:
        # Remove PID file ao terminar
        if pid_file.exists():
            pid_file.unlink()
