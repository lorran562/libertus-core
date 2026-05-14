#!/usr/bin/env python3
"""
LIBERTUS MULTI-AGENT ORCHESTRA
Sistema de evolução autônoma com múltiplos Claude workers

Arquitetura:
- Lorran (usuário) → Claude Principal (orchestrator)
- Claude Principal → Claude Workers (especialistas)
- Workers → Executam tarefas específicas
- Results → Consolidados pelo orchestrator
"""

import os
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


@dataclass
class Task:
    """Tarefa para um worker"""
    task_id: str
    worker_type: str  # researcher, coder, reporter
    description: str
    priority: int  # 1-5
    status: str = "pending"  # pending, running, completed, failed
    result: Optional[Dict] = None


class ClaudeWorker:
    """
    Worker Claude especializado
    """
    
    def __init__(self, api_key: str, worker_type: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.worker_type = worker_type
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """System prompt baseado no tipo de worker"""
        
        prompts = {
            "researcher": """Você é um pesquisador especializado em cybersecurity.

Suas tarefas:
- Buscar papers no ArXiv
- Pesquisar CVEs no NVD
- Explorar exploits no GitHub
- Resumir findings técnicos

Output: JSON estruturado com findings.""",
            
            "coder": """Você é um engenheiro de código especializado.

Suas tarefas:
- Escrever novos módulos Python
- Atualizar scanner com payloads
- Criar testes unitários
- Documentar código

Output: Código Python pronto para commit.""",
            
            "reporter": """Você é um analista técnico especializado.

Suas tarefas:
- Consolidar resultados de pesquisa
- Gerar relatórios profissionais
- Atualizar documentação
- Criar sumários executivos

Output: Relatórios em Markdown."""
        }
        
        return prompts.get(self.worker_type, "")
    
    async def execute_task(self, task: Task) -> Dict:
        """Executa uma tarefa"""
        
        try:
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                system=self.system_prompt,
                messages=[{
                    "role": "user",
                    "content": task.description
                }]
            )
            
            result = {
                "success": True,
                "output": response.content[0].text,
                "worker_type": self.worker_type,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "worker_type": self.worker_type
            }


class MultiAgentOrchestra:
    """
    Orchestrador principal do sistema multi-agent
    
    Coordena múltiplos Claude workers para evolução do LIBERTUS
    """
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.workers = self._init_workers()
        self.tasks: List[Task] = []
        self.results: Dict = {}
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Carrega configuração"""
        
        default_config = {
            "orchestrator_api_key": os.getenv("CLAUDE_ORCHESTRATOR_KEY", ""),
            "worker_api_keys": {
                "researcher": os.getenv("CLAUDE_RESEARCHER_KEY", ""),
                "coder": os.getenv("CLAUDE_CODER_KEY", ""),
                "reporter": os.getenv("CLAUDE_REPORTER_KEY", "")
            },
            "max_parallel_tasks": 3
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _init_workers(self) -> Dict[str, ClaudeWorker]:
        """Inicializa workers"""
        
        workers = {}
        
        for worker_type, api_key in self.config["worker_api_keys"].items():
            if api_key:
                workers[worker_type] = ClaudeWorker(api_key, worker_type)
        
        return workers
    
    async def plan_evolution(self, user_request: str) -> List[Task]:
        """
        Planejar evolução baseado no pedido do usuário
        
        Usa Claude orchestrator para decompor em tarefas
        """
        
        if not self.config["orchestrator_api_key"]:
            print("⚠️ Orchestrator API key não configurada")
            return []
        
        client = anthropic.AsyncAnthropic(
            api_key=self.config["orchestrator_api_key"]
        )
        
        prompt = f"""Você é o orchestrador do LIBERTUS.

Pedido do usuário: {user_request}

Decomponha isso em tarefas específicas para os workers:
- researcher: pesquisar informações
- coder: escrever código
- reporter: gerar relatórios

Output em JSON:
[
  {{
    "worker_type": "researcher",
    "description": "...",
    "priority": 1-5
  }},
  ...
]"""
        
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # Parse tasks
        tasks_json = response.content[0].text
        
        # Extrair JSON (pode vir com markdown)
        if "```json" in tasks_json:
            tasks_json = tasks_json.split("```json")[1].split("```")[0]
        
        tasks_data = json.loads(tasks_json)
        
        # Criar objetos Task
        tasks = []
        for i, task_data in enumerate(tasks_data):
            task = Task(
                task_id=f"task_{i}",
                worker_type=task_data["worker_type"],
                description=task_data["description"],
                priority=task_data.get("priority", 3)
            )
            tasks.append(task)
        
        self.tasks = tasks
        return tasks
    
    async def execute_tasks(self) -> Dict:
        """Executa todas as tarefas em paralelo"""
        
        print(f"\n🚀 Executando {len(self.tasks)} tarefas...\n")
        
        # Agrupar por tipo de worker
        tasks_by_worker = {}
        for task in self.tasks:
            if task.worker_type not in tasks_by_worker:
                tasks_by_worker[task.worker_type] = []
            tasks_by_worker[task.worker_type].append(task)
        
        # Executar em paralelo
        results = {}
        
        async def execute_worker_tasks(worker_type: str, tasks: List[Task]):
            worker = self.workers.get(worker_type)
            if not worker:
                print(f"⚠️ Worker {worker_type} não disponível")
                return
            
            for task in tasks:
                print(f"  ▶️ {worker_type}: {task.description[:50]}...")
                task.status = "running"
                
                result = await worker.execute_task(task)
                
                task.status = "completed" if result["success"] else "failed"
                task.result = result
                
                results[task.task_id] = result
                
                status_emoji = "✅" if result["success"] else "❌"
                print(f"  {status_emoji} {worker_type}: Concluído")
        
        # Executar todos os workers em paralelo
        await asyncio.gather(*[
            execute_worker_tasks(worker_type, tasks)
            for worker_type, tasks in tasks_by_worker.items()
        ])
        
        self.results = results
        return results
    
    async def consolidate_results(self) -> str:
        """Consolida resultados de todos os workers"""
        
        if not self.config["orchestrator_api_key"]:
            return "⚠️ Orchestrator não configurado"
        
        client = anthropic.AsyncAnthropic(
            api_key=self.config["orchestrator_api_key"]
        )
        
        # Preparar contexto
        context = "RESULTADOS DOS WORKERS:\n\n"
        
        for task in self.tasks:
            context += f"Task: {task.description}\n"
            context += f"Worker: {task.worker_type}\n"
            context += f"Status: {task.status}\n"
            
            if task.result:
                context += f"Output: {task.result.get('output', 'N/A')[:500]}\n"
            
            context += "\n---\n\n"
        
        prompt = f"""{context}

Consolide os resultados acima em um sumário executivo.

Inclua:
1. O que foi aprendido
2. O que foi implementado
3. Próximos passos recomendados"""
        
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def evolve(self, user_request: str) -> str:
        """
        Workflow completo de evolução
        """
        
        print(f"\n{'='*60}")
        print(f"🌳 LIBERTUS MULTI-AGENT EVOLUTION")
        print(f"{'='*60}\n")
        print(f"📝 Pedido: {user_request}\n")
        
        # 1. Planejar
        print("1️⃣ Planejando tarefas...")
        tasks = await self.plan_evolution(user_request)
        
        print(f"   ✅ {len(tasks)} tarefas criadas\n")
        
        # 2. Executar
        print("2️⃣ Executando workers...")
        await self.execute_tasks()
        print()
        
        # 3. Consolidar
        print("3️⃣ Consolidando resultados...")
        summary = await self.consolidate_results()
        
        print(f"\n{'='*60}")
        print("✅ EVOLUÇÃO COMPLETA")
        print(f"{'='*60}\n")
        print(summary)
        
        return summary


# CLI para teste
async def main():
    print("╔══════════════════════════════════════════════════════╗")
    print("║   🌳 LIBERTUS MULTI-AGENT ORCHESTRA               ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    
    if not HAS_ANTHROPIC:
        print("❌ Biblioteca anthropic não instalada")
        print("   pip3 install --break-system-packages anthropic")
        return
    
    orchestra = MultiAgentOrchestra()
    
    # Exemplo de uso
    user_request = "Aprender sobre SQL Injection em GraphQL APIs e atualizar o scanner"
    
    await orchestra.evolve(user_request)


if __name__ == "__main__":
    asyncio.run(main())
