"""Shadow Analyzer - Versão SIMPLIFICADA sem ChromaDB"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class ShadowAnalyzer:
    """Analisa comparações Prod vs Router - SQLite PURO"""
    
    MIN_COMPARISONS = 10
    MIN_WIN_RATE = 0.6
    MAX_CRITICAL_RATE = 0.2
    MAX_ALLOWED_DIFF = 50
    
    def __init__(self):
        self.db_file = Path.home() / "LIBERTUS" / "memoria" / "shadow_analysis.db"
        self.metrics_file = Path.home() / "LIBERTUS" / "logs" / "shadow_metrics.json"
        self.decision_log = Path.home() / "LIBERTUS" / "logs" / "shadow_decisions.log"
        
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self.decision_log.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
        self.metrics = self._load_metrics_from_db()
    
    def _init_database(self):
        """Inicializa SQLite"""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target TEXT,
            prod_risk INTEGER,
            router_risk INTEGER,
            diff INTEGER,
            winner TEXT,
            kill_switch INTEGER DEFAULT 0,
            created_at TEXT
        )
        """)
        conn.commit()
        conn.close()
    
    def _load_metrics_from_db(self):
        """Carrega métricas do SQLite"""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM comparisons")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE winner = 'router'")
        router_better = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE winner = 'prod'")
        prod_better = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE diff > 20")
        div_high = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE diff > 50")
        div_critical = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE kill_switch = 1")
        kill_switch = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_comparisons': total,
            'router_better': router_better,
            'prod_better': prod_better,
            'divergence_high': div_high,
            'divergence_critical': div_critical,
            'kill_switch_triggered': kill_switch
        }
    
    def _log_decision(self, message: str):
        """Log de decisão"""
        with open(self.decision_log, 'a') as f:
            f.write(f"[{datetime.now().isoformat()}] {message}\n")
    
    def analyze_comparison(self, prod_risk: int, router_risk: int, target: str, vulnerabilities: List[Dict]) -> Dict:
        """Analisa comparação"""
        diff = abs(prod_risk - router_risk)
        kill_switch = 1 if diff > self.MAX_ALLOWED_DIFF else 0
        
        if kill_switch:
            self._log_decision(f"🚨 KILL SWITCH: {target} diff={diff}")
        
        decision = 'router' if router_risk > prod_risk else 'prod'
        
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO comparisons (target, prod_risk, router_risk, diff, winner, kill_switch, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (target, prod_risk, router_risk, diff, decision, kill_switch, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        self.metrics = self._load_metrics_from_db()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'target': target,
            'prod_risk': prod_risk,
            'router_risk': router_risk,
            'diff': diff,
            'decision': decision,
            'kill_switch_triggered': kill_switch,
            'vulnerabilities': {'total': len(vulnerabilities)}
        }
    
    def get_recommendation(self):
        """Recomendação"""
        if self.metrics['total_comparisons'] < self.MIN_COMPARISONS:
            return f"COLETAR MAIS DADOS ({self.metrics['total_comparisons']}/{self.MIN_COMPARISONS})"
        
        router_win_rate = self.metrics['router_better'] / self.metrics['total_comparisons']
        
        if router_win_rate >= self.MIN_WIN_RATE:
            return f"✅ MIGRAR PARA ROUTER (win: {router_win_rate*100:.1f}%)"
        else:
            return f"⚠️ MANTER PRODUÇÃO"
    
    def print_report(self):
        """Relatório"""
        print("="*70)
        print("📊 SHADOW MODE - ANÁLISE")
        print("="*70)
        print(f"Comparações: {self.metrics['total_comparisons']}/{self.MIN_COMPARISONS}")
        print(f"Router melhor: {self.metrics['router_better']}")
        print(f"Prod melhor: {self.metrics['prod_better']}")
        print(f"Divergência alta: {self.metrics['divergence_high']}")
        print(f"Kill switch: {self.metrics['kill_switch_triggered']}")
        print(f"\nRECOMENDAÇÃO: {self.get_recommendation()}")
        print("="*70)
