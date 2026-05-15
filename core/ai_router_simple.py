"""AI Router SIMPLIFICADO - Sem RAG"""
import asyncio
from enum import Enum

class TaskType(Enum):
    RISK_CALCULATION = "risk_calculation"
    VULNERABILITY_ANALYSIS = "vulnerability_analysis" 
    REPORT_GENERATION = "report_generation"

class AIRouter:
    async def execute(self, task_type, data):
        from logic_engine import LogicEngine
        logic = LogicEngine()
        return await logic.calculate_risk(data.get('vulnerabilities', []))
