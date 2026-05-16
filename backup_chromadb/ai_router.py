from enum import Enum
from typing import Dict, Any
import asyncio
from logic_engine import LogicEngine, TaskType
from llm_backend_manager import LLMBackendManager
from rag_engine_v2 import RAGEngineV2

class ExecutionMode(Enum):
    LOGIC_ONLY = "logic_only"
    RAG_LOCAL = "rag_local"
    API_PRIMARY = "api_primary"
    HYBRID = "hybrid"

class AIRouter:
    """Roteador inteligente - decide qual backend usar"""
    
    def __init__(self):
        self.llm_manager = LLMBackendManager()
        self.rag_engine = RAGEngineV2()
        self.logic_engine = LogicEngine()
        
        self.task_routing = {
            TaskType.RISK_CALCULATION: ExecutionMode.LOGIC_ONLY,
            TaskType.REPORT_GENERATION: ExecutionMode.HYBRID,
            TaskType.VULNERABILITY_ANALYSIS: ExecutionMode.RAG_LOCAL,
            TaskType.DECISION_MAKING: ExecutionMode.LOGIC_ONLY,
        }
    
    async def execute(self, task_type: TaskType, context: Dict[str, Any]) -> Any:
        """Executa tarefa usando melhor backend"""
        preferred_mode = self.task_routing.get(task_type, ExecutionMode.API_PRIMARY)
        
        try:
            return await self._execute_mode(preferred_mode, task_type, context)
        except Exception as e:
            print(f"⚠️ {preferred_mode} falhou: {e}")
            return await self._fallback_execute(task_type, context, failed_mode=preferred_mode)
    
    async def _execute_mode(self, mode: ExecutionMode, task_type: TaskType, context: Dict) -> Any:
        """Executa usando modo específico"""
        
        if mode == ExecutionMode.LOGIC_ONLY:
            return self.logic_engine.execute(task_type, context)
        
        elif mode == ExecutionMode.RAG_LOCAL:
            is_technical = any(kw in context.get('query', '').lower() 
                             for kw in ['código', 'script', 'como', 'implementar'])
            
            knowledge = await self.rag_engine.retrieve(
                context.get('query', ''),
                top_k=3,
                prefer_code=is_technical
            )
            
            try:
                return await self.llm_manager.generate(
                    provider='ollama',
                    prompt=knowledge
                )
            except:
                # Fallback: API se Ollama falhar
                return await self.llm_manager.generate(
                    provider='groq',
                    prompt=knowledge
                )
        
        elif mode == ExecutionMode.API_PRIMARY:
            return await self.llm_manager.generate(
                provider='groq',
                prompt=self._build_prompt(context)
            )
        
        elif mode == ExecutionMode.HYBRID:
            logic_result = self.logic_engine.execute(task_type, context)
            
            prompt = f"Dados: {logic_result}\n\n{context.get('instruction', '')}"
            
            return await self.llm_manager.generate(
                provider='groq',
                prompt=prompt
            )
    
    async def _fallback_execute(self, task_type: TaskType, context: Dict, failed_mode: ExecutionMode) -> Any:
        """Fallback chain"""
        fallback_chain = [
            ExecutionMode.API_PRIMARY,
            ExecutionMode.RAG_LOCAL,
            ExecutionMode.LOGIC_ONLY,
        ]
        
        for mode in fallback_chain:
            if mode == failed_mode:
                continue
            try:
                return await self._execute_mode(mode, task_type, context)
            except Exception as e:
                print(f"⚠️ Fallback {mode} falhou: {e}")
                continue
        
        raise Exception("❌ Todos backends falharam!")
    
    def _build_prompt(self, context: Dict) -> str:
        """Constrói prompt genérico"""
        return context.get('instruction', '') + "\n\n" + str(context.get('data', ''))
