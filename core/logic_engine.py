from typing import Dict, Any
from enum import Enum

class TaskType(Enum):
    RISK_CALCULATION = "risk_calc"
    REPORT_GENERATION = "report_gen"
    VULNERABILITY_ANALYSIS = "vuln_analysis"
    DECISION_MAKING = "decision"

class LogicEngine:
    """Motor lógico PURO - zero LLM"""
    
    def execute(self, task_type: TaskType, context: Dict[str, Any]) -> Any:
        """Executa lógica baseada no tipo"""
        
        if task_type == TaskType.RISK_CALCULATION:
            return self.calculate_risk(context)
        elif task_type == TaskType.DECISION_MAKING:
            return self.make_decision(context)
        else:
            raise ValueError(f"Task {task_type} não suportada")
    
    def calculate_risk(self, context: Dict) -> Dict:
        """Cálculo de risco SEM LLM"""
        vulns = context.get('vulnerabilities', [])
        
        risk_score = 0
        severity_weights = {
            'CRITICAL': 40,
            'HIGH': 20,
            'MEDIUM': 10,
            'LOW': 5
        }
        
        for vuln in vulns:
            severity = vuln.get('severity', 'LOW')
            risk_score += severity_weights.get(severity, 0)
        
        risk_score = min(risk_score, 100)
        
        if risk_score >= 70:
            classification = 'CRITICAL'
        elif risk_score >= 40:
            classification = 'HIGH'
        elif risk_score >= 20:
            classification = 'MEDIUM'
        else:
            classification = 'LOW'
        
        return {
            'risk_score': risk_score,
            'classification': classification,
            'total_vulnerabilities': len(vulns),
            'breakdown': {
                sev: len([v for v in vulns if v.get('severity') == sev])
                for sev in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
            }
        }
    
    def make_decision(self, context: Dict) -> str:
        """Decisão baseada em regras - qual target next?"""
        targets = context.get('targets', [])
        
        scored_targets = []
        for target in targets:
            score = 0
            score += (5 - target.get('priority', 4)) * 100
            
            if target.get('scan_count', 0) == 0:
                score += 500
            
            score += target.get('vulnerabilities_found', 0) * 50
            
            days_since = target.get('days_since_last_scan', 999)
            if days_since > 30:
                score += 200
            
            scored_targets.append((target, score))
        
        if scored_targets:
            best_target = max(scored_targets, key=lambda x: x[1])
            return best_target[0]['url']
        
        return None
