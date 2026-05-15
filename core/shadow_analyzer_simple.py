"""Shadow Analyzer SIMPLIFICADO - Sem ChromaDB"""
import json
from pathlib import Path
from datetime import datetime

class ShadowAnalyzer:
    def __init__(self):
        self.metrics_file = Path.home() / "LIBERTUS" / "logs" / "shadow_metrics.json"
        self.metrics = {'total_comparisons': 0, 'router_better': 0, 'prod_better': 0}
        self._load_metrics()
    
    def _load_metrics(self):
        if self.metrics_file.exists():
            with open(self.metrics_file) as f:
                self.metrics = json.load(f)
    
    def _save_metrics(self):
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def analyze_comparison(self, prod_risk, router_risk, target, vulnerabilities):
        diff = abs(prod_risk - router_risk)
        decision = 'router' if router_risk > prod_risk else 'prod'
        
        self.metrics['total_comparisons'] += 1
        if decision == 'router':
            self.metrics['router_better'] += 1
        else:
            self.metrics['prod_better'] += 1
        
        self._save_metrics()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'target': target,
            'prod_risk': prod_risk,
            'router_risk': router_risk,
            'diff': diff,
            'decision': decision,
            'vulnerabilities': {'total': len(vulnerabilities)}
        }
    
    def get_recommendation(self):
        if self.metrics['total_comparisons'] < 10:
            return f"COLETAR MAIS DADOS ({self.metrics['total_comparisons']}/10)"
        return "DADOS SUFICIENTES"
    
    def print_report(self):
        print(f"Comparações: {self.metrics['total_comparisons']}")
        print(f"Router melhor: {self.metrics['router_better']}")
        print(f"Prod melhor: {self.metrics['prod_better']}")
