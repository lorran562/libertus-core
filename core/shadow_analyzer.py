"""
SHADOW ANALYZER - Sistema de Decisão Inteligente
Compara Produção vs Router e DECIDE qual é melhor.
PERSISTÊNCIA EM SQLITE (crítico para não perder dados)
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class ShadowAnalyzer:
    """
    Analisa logs shadow mode e gera métricas de decisão.
    PERSISTE TUDO em SQLite.
    """
    
    def __init__(self):
        self.log_file = Path.home() / "LIBERTUS" / "logs" / "shadow_mode.log"
        self.metrics_file = Path.home() / "LIBERTUS" / "logs" / "shadow_metrics.json"
        self.db_file = Path.home() / "LIBERTUS" / "memoria" / "shadow_analysis.db"
        
        # Garantir diretório existe
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar database
        self._init_database()
        
        # Contadores de decisão
        self.metrics = {
            'total_comparisons': 0,
            'router_better': 0,
            'prod_better': 0,
            'divergence_high': 0,
            'divergence_critical': 0,
            'router_avg_risk': 0,
            'prod_avg_risk': 0,
            'comparisons': []
        }
        
        self._load_metrics_from_db()
    
    def _init_database(self):
        """Inicializa tabelas SQLite"""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT NOT NULL,
            prod_risk INTEGER NOT NULL,
            router_risk INTEGER NOT NULL,
            diff INTEGER NOT NULL,
            winner TEXT NOT NULL,
            critical_count INTEGER DEFAULT 0,
            high_count INTEGER DEFAULT 0,
            medium_count INTEGER DEFAULT 0,
            low_count INTEGER DEFAULT 0,
            total_vulns INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at 
        ON comparisons(created_at DESC)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_winner 
        ON comparisons(winner)
        """)
        
        conn.commit()
        conn.close()
    
    def _load_metrics_from_db(self):
        """Carrega métricas do SQLite"""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        # Total comparações
        cursor.execute("SELECT COUNT(*) FROM comparisons")
        self.metrics['total_comparisons'] = cursor.fetchone()[0]
        
        # Win rates
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE winner = 'router'")
        self.metrics['router_better'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE winner = 'prod'")
        self.metrics['prod_better'] = cursor.fetchone()[0]
        
        # Divergências
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE diff > 20")
        self.metrics['divergence_high'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE diff > 50")
        self.metrics['divergence_critical'] = cursor.fetchone()[0]
        
        # Médias
        cursor.execute("SELECT AVG(router_risk), AVG(prod_risk) FROM comparisons")
        router_avg, prod_avg = cursor.fetchone()
        self.metrics['router_avg_risk'] = router_avg if router_avg else 0
        self.metrics['prod_avg_risk'] = prod_avg if prod_avg else 0
        
        conn.close()
    
    def _save_to_db(self, comparison: Dict):
        """Salva comparação no SQLite (PERSISTÊNCIA CRÍTICA)"""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO comparisons 
        (target, prod_risk, router_risk, diff, winner, 
         critical_count, high_count, medium_count, low_count, total_vulns, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            comparison['target'],
            comparison['prod_risk'],
            comparison['router_risk'],
            comparison['diff'],
            comparison['decision'],
            comparison['vulnerabilities']['critical'],
            comparison['vulnerabilities']['high'],
            comparison['vulnerabilities']['medium'],
            comparison['vulnerabilities']['low'],
            comparison['vulnerabilities']['total'],
            comparison['timestamp']
        ))
        
        conn.commit()
        conn.close()
    
    def analyze_comparison(self, prod_risk: int, router_risk: int, 
                          target: str, vulnerabilities: List[Dict]) -> Dict:
        """
        Analisa uma comparação Prod vs Router.
        DECIDE quem está certo + PERSISTE no SQLite.
        """
        diff = abs(prod_risk - router_risk)
        
        # Classificar vulnerabilidades
        vuln_critical = len([v for v in vulnerabilities if v.get('severity') == 'CRITICAL'])
        vuln_high = len([v for v in vulnerabilities if v.get('severity') == 'HIGH'])
        vuln_medium = len([v for v in vulnerabilities if v.get('severity') == 'MEDIUM'])
        vuln_low = len([v for v in vulnerabilities if v.get('severity') == 'LOW'])
        
        # LÓGICA DE DECISÃO
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
        
        # PERSISTIR NO SQLITE
        self._save_to_db(comparison)
        
        # Atualizar métricas em memória
        self.metrics['total_comparisons'] += 1
        
        if decision == 'router':
            self.metrics['router_better'] += 1
        elif decision == 'prod':
            self.metrics['prod_better'] += 1
        
        if diff > 20:
            self.metrics['divergence_high'] += 1
        if diff > 50:
            self.metrics['divergence_critical'] += 1
        
        # Recalcular médias do DB
        self._load_metrics_from_db()
        
        return comparison
    
    def _decide_winner(self, prod_risk: int, router_risk: int,
                       critical: int, high: int, medium: int, low: int) -> str:
        """LÓGICA DE DECISÃO: Quem está certo?"""
        
        # CRITICAL ou HIGH presente
        if critical > 0 or high > 0:
            if router_risk > 40 and prod_risk <= 40:
                return 'router'
            elif prod_risk > 40 and router_risk <= 40:
                return 'prod'
            else:
                return 'tie'
        
        # Só MEDIUM
        elif medium > 0 and critical == 0 and high == 0:
            router_in_range = 20 <= router_risk <= 40
            prod_in_range = 20 <= prod_risk <= 40
            
            if router_in_range and not prod_in_range:
                return 'router'
            elif prod_in_range and not router_in_range:
                return 'prod'
            else:
                return 'tie'
        
        # Só LOW
        elif low > 0 and critical == 0 and high == 0 and medium == 0:
            if router_risk < 20 and prod_risk >= 20:
                return 'router'
            elif prod_risk < 20 and router_risk >= 20:
                return 'prod'
            else:
                return 'tie'
        
        return 'tie'
    
    def should_use_router(self) -> bool:
        """DECISÃO FINAL: Usar router em produção?"""
        if self.metrics['total_comparisons'] < 10:
            return False
        
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
    
    def get_history(self, limit: int = 20) -> List[Dict]:
        """Busca histórico do SQLite"""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT target, prod_risk, router_risk, diff, winner, 
               critical_count, high_count, medium_count, low_count, created_at
        FROM comparisons
        ORDER BY created_at DESC
        LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'target': row[0],
                'prod_risk': row[1],
                'router_risk': row[2],
                'diff': row[3],
                'winner': row[4],
                'vulns': {
                    'critical': row[5],
                    'high': row[6],
                    'medium': row[7],
                    'low': row[8]
                },
                'timestamp': row[9]
            })
        
        return history
    
    def print_report(self):
        """Relatório visual"""
        print("="*70)
        print("📊 SHADOW MODE - ANÁLISE COMPARATIVA (PERSISTENTE)")
        print("="*70)
        print(f"Database: {self.db_file}")
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
    
    # Mostrar últimas 5 comparações
    history = analyzer.get_history(5)
    if history:
        print("\n📜 ÚLTIMAS 5 COMPARAÇÕES:")
        for i, h in enumerate(history, 1):
            print(f"{i}. {h['target']}: Prod={h['prod_risk']} Router={h['router_risk']} Winner={h['winner']}")
