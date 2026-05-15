"""
SHADOW ANALYZER - Sistema de Decisão Inteligente
Compara Produção vs Router e DECIDE qual é melhor.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class ShadowAnalyzer:
    """
    Analisa logs shadow mode e gera métricas de decisão.
    """
    
    def __init__(self):
        self.log_file = Path.home() / "LIBERTUS" / "logs" / "shadow_mode.log"
        self.metrics_file = Path.home() / "LIBERTUS" / "logs" / "shadow_metrics.json"
        
        # Contadores de decisão
        self.metrics = {
            'total_comparisons': 0,
            'router_better': 0,
            'prod_better': 0,
            'divergence_high': 0,  # diff > 20
            'divergence_critical': 0,  # diff > 50
            'router_consistent': True,
            'router_avg_risk': 0,
            'prod_avg_risk': 0,
            'comparisons': []
        }
        
        self._load_metrics()
    
    def _load_metrics(self):
        """Carrega métricas existentes"""
        if self.metrics_file.exists():
            with open(self.metrics_file) as f:
                self.metrics = json.load(f)
    
    def _save_metrics(self):
        """Salva métricas"""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def analyze_comparison(self, prod_risk: int, router_risk: int, 
                          target: str, vulnerabilities: List[Dict]) -> Dict:
        """
        Analisa uma comparação Prod vs Router.
        DECIDE quem está certo.
        """
        diff = abs(prod_risk - router_risk)
        
        # Classificar vulnerabilidades
        vuln_critical = len([v for v in vulnerabilities if v.get('severity') == 'CRITICAL'])
        vuln_high = len([v for v in vulnerabilities if v.get('severity') == 'HIGH'])
        vuln_medium = len([v for v in vulnerabilities if v.get('severity') == 'MEDIUM'])
        vuln_low = len([v for v in vulnerabilities if v.get('severity') == 'LOW'])
        
        # LÓGICA DE DECISÃO: Quem está certo?
        decision = self._decide_winner(
            prod_risk, router_risk,
            vuln_critical, vuln_high, vuln_medium, vuln_low
        )
        
        comparison = {
            'timestamp': datetime.now().isoformat(),
            'target': target,
            'prod_risk': prod_risk,
            'router_risk': router_risk,
            'diff': diff,
            'vulnerabilities': {
                'critical': vuln_critical,
                'high': vuln_high,
                'medium': vuln_medium,
                'low': vuln_low,
                'total': len(vulnerabilities)
            },
            'decision': decision
        }
        
        # Atualizar métricas
        self.metrics['total_comparisons'] += 1
        self.metrics['comparisons'].append(comparison)
        
        if decision == 'router':
            self.metrics['router_better'] += 1
        elif decision == 'prod':
            self.metrics['prod_better'] += 1
        
        if diff > 20:
            self.metrics['divergence_high'] += 1
        if diff > 50:
            self.metrics['divergence_critical'] += 1
        
        # Calcular médias
        all_router = [c['router_risk'] for c in self.metrics['comparisons']]
        all_prod = [c['prod_risk'] for c in self.metrics['comparisons']]
        
        self.metrics['router_avg_risk'] = sum(all_router) / len(all_router) if all_router else 0
        self.metrics['prod_avg_risk'] = sum(all_prod) / len(all_prod) if all_prod else 0
        
        self._save_metrics()
        
        return comparison
    
    def _decide_winner(self, prod_risk: int, router_risk: int,
                       critical: int, high: int, medium: int, low: int) -> str:
        """
        LÓGICA DE DECISÃO: Quem está certo?
        
        Regras:
        1. Se tem CRITICAL/HIGH → risk deve ser alto (>40)
        2. Se só tem MEDIUM → risk deve ser médio (20-40)
        3. Se só tem LOW → risk deve ser baixo (<20)
        """
        
        # Regra 1: CRITICAL ou HIGH presente
        if critical > 0 or high > 0:
            # Risk deveria ser alto (>40)
            if router_risk > 40 and prod_risk <= 40:
                return 'router'  # Router detectou a gravidade
            elif prod_risk > 40 and router_risk <= 40:
                return 'prod'
            else:
                return 'tie'
        
        # Regra 2: Só MEDIUM
        elif medium > 0 and critical == 0 and high == 0:
            # Risk deveria ser médio (20-40)
            router_in_range = 20 <= router_risk <= 40
            prod_in_range = 20 <= prod_risk <= 40
            
            if router_in_range and not prod_in_range:
                return 'router'
            elif prod_in_range and not router_in_range:
                return 'prod'
            else:
                return 'tie'
        
        # Regra 3: Só LOW
        elif low > 0 and critical == 0 and high == 0 and medium == 0:
            # Risk deveria ser baixo (<20)
            if router_risk < 20 and prod_risk >= 20:
                return 'router'
            elif prod_risk < 20 and router_risk >= 20:
                return 'prod'
            else:
                return 'tie'
        
        # Padrão: empate
        return 'tie'
    
    def should_use_router(self) -> bool:
        """
        DECISÃO FINAL: Usar router em produção?
        
        Critérios:
        - Router melhor em 60%+ dos casos
        - Divergência crítica < 20%
        - Mínimo 10 comparações
        """
        if self.metrics['total_comparisons'] < 10:
            return False  # Poucos dados
        
        router_win_rate = self.metrics['router_better'] / self.metrics['total_comparisons']
        critical_rate = self.metrics['divergence_critical'] / self.metrics['total_comparisons']
        
        if router_win_rate >= 0.6 and critical_rate < 0.2:
            return True
        
        return False
    
    def get_recommendation(self) -> str:
        """Recomendação baseada nos dados"""
        if self.metrics['total_comparisons'] < 10:
            return f"COLETAR MAIS DADOS ({self.metrics['total_comparisons']}/10 comparações)"
        
        router_win_rate = self.metrics['router_better'] / self.metrics['total_comparisons']
        prod_win_rate = self.metrics['prod_better'] / self.metrics['total_comparisons']
        
        if self.should_use_router():
            return f"✅ MIGRAR PARA ROUTER (win rate: {router_win_rate*100:.1f}%)"
        elif prod_win_rate >= 0.6:
            return f"⚠️ MANTER PRODUÇÃO (prod win rate: {prod_win_rate*100:.1f}%)"
        else:
            return f"🤔 HÍBRIDO RECOMENDADO (empate técnico)"
    
    def print_report(self):
        """Relatório visual"""
        print("="*70)
        print("📊 SHADOW MODE - ANÁLISE COMPARATIVA")
        print("="*70)
        print(f"\nComparações totais: {self.metrics['total_comparisons']}")
        print(f"Router melhor: {self.metrics['router_better']} ({self.metrics['router_better']/max(self.metrics['total_comparisons'],1)*100:.1f}%)")
        print(f"Prod melhor: {self.metrics['prod_better']} ({self.metrics['prod_better']/max(self.metrics['total_comparisons'],1)*100:.1f}%)")
        print(f"\nDivergência alta (>20): {self.metrics['divergence_high']}")
        print(f"Divergência crítica (>50): {self.metrics['divergence_critical']}")
        print(f"\nRisk médio - Router: {self.metrics['router_avg_risk']:.1f}")
        print(f"Risk médio - Prod: {self.metrics['prod_avg_risk']:.1f}")
        print(f"\n{'='*70}")
        print(f"RECOMENDAÇÃO: {self.get_recommendation()}")
        print("="*70)

if __name__ == "__main__":
    analyzer = ShadowAnalyzer()
    analyzer.print_report()
