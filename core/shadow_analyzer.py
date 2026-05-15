"""
SHADOW ANALYZER - Sistema de Decisão Inteligente
COM GOVERNANÇA (kill switch, limite de confiança, auditoria)
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class ShadowAnalyzer:
    """
    Analisa comparações Prod vs Router com GOVERNANÇA.
    
    TRAVAS DE SEGURANÇA:
    1. KILL SWITCH - diferença crítica força modo seguro
    2. LIMITE DE CONFIANÇA - mínimo 10 comparações
    3. LOG DE DECISÃO - auditoria completa
    """
    
    # CONSTANTES DE GOVERNANÇA
    MAX_ALLOWED_DIFF = 50  # Kill switch
    MIN_COMPARISONS = 10   # Limite de confiança
    MIN_WIN_RATE = 0.6     # 60% para migração
    MAX_CRITICAL_RATE = 0.2  # 20% max divergência crítica
    
    def __init__(self):
        self.log_file = Path.home() / "LIBERTUS" / "logs" / "shadow_mode.log"
        self.metrics_file = Path.home() / "LIBERTUS" / "logs" / "shadow_metrics.json"
        self.db_file = Path.home() / "LIBERTUS" / "memoria" / "shadow_analysis.db"
        self.decision_log = Path.home() / "LIBERTUS" / "logs" / "shadow_decisions.log"
        
        # Garantir diretórios
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self.decision_log.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar database
        self._init_database()
        
        # Contadores
        self.metrics = {
            'total_comparisons': 0,
            'router_better': 0,
            'prod_better': 0,
            'divergence_high': 0,
            'divergence_critical': 0,
            'kill_switch_triggered': 0,  # NOVO
            'router_avg_risk': 0,
            'prod_avg_risk': 0,
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
            kill_switch_triggered INTEGER DEFAULT 0,
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
        
        cursor.execute("SELECT COUNT(*) FROM comparisons")
        self.metrics['total_comparisons'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE winner = 'router'")
        self.metrics['router_better'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE winner = 'prod'")
        self.metrics['prod_better'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE diff > 20")
        self.metrics['divergence_high'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE diff > 50")
        self.metrics['divergence_critical'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM comparisons WHERE kill_switch_triggered = 1")
        self.metrics['kill_switch_triggered'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(router_risk), AVG(prod_risk) FROM comparisons")
        router_avg, prod_avg = cursor.fetchone()
        self.metrics['router_avg_risk'] = router_avg if router_avg else 0
        self.metrics['prod_avg_risk'] = prod_avg if prod_avg else 0
        
        conn.close()
    
    def _log_decision(self, message: str):
        """Log de decisão (AUDITORIA)"""
        timestamp = datetime.now().isoformat()
        with open(self.decision_log, 'a') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def _save_to_db(self, comparison: Dict):
        """Salva comparação no SQLite"""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO comparisons 
        (target, prod_risk, router_risk, diff, winner, kill_switch_triggered,
         critical_count, high_count, medium_count, low_count, total_vulns, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            comparison['target'],
            comparison['prod_risk'],
            comparison['router_risk'],
            comparison['diff'],
            comparison['decision'],
            comparison.get('kill_switch_triggered', 0),
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
        Analisa comparação COM GOVERNANÇA.
        
        TRAVAS:
        1. Kill switch se diff > 50
        2. Só decide com 10+ comparações
        3. Auditoria completa
        """
        diff = abs(prod_risk - router_risk)
        
        # 🚨 KILL SWITCH (TRAVA DE SEGURANÇA)
        kill_switch_triggered = False
        if diff > self.MAX_ALLOWED_DIFF:
            kill_switch_triggered = True
            self._log_decision(
                f"🚨 KILL SWITCH: {target} | Diff={diff} > {self.MAX_ALLOWED_DIFF} | "
                f"Prod={prod_risk} Router={router_risk}"
            )
        
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
            'kill_switch_triggered': 1 if kill_switch_triggered else 0,
            'vulnerabilities': {
                'critical': vuln_critical,
                'high': vuln_high,
                'medium': vuln_medium,
                'low': vuln_low,
                'total': len(vulnerabilities)
            },
            'decision': decision
        }
        
        # PERSISTIR
        self._save_to_db(comparison)
        
        # Atualizar métricas
        self.metrics['total_comparisons'] += 1
        
        if decision == 'router':
            self.metrics['router_better'] += 1
        elif decision == 'prod':
            self.metrics['prod_better'] += 1
        
        if diff > 20:
            self.metrics['divergence_high'] += 1
        if diff > 50:
            self.metrics['divergence_critical'] += 1
        
        if kill_switch_triggered:
            self.metrics['kill_switch_triggered'] += 1
        
        # Recalcular médias
        self._load_metrics_from_db()
        
        return comparison
    
    def _decide_winner(self, prod_risk: int, router_risk: int,
                       critical: int, high: int, medium: int, low: int) -> str:
        """LÓGICA DE DECISÃO"""
        
        if critical > 0 or high > 0:
            if router_risk > 40 and prod_risk <= 40:
                return 'router'
            elif prod_risk > 40 and router_risk <= 40:
                return 'prod'
            else:
                return 'tie'
        
        elif medium > 0 and critical == 0 and high == 0:
            router_in_range = 20 <= router_risk <= 40
            prod_in_range = 20 <= prod_risk <= 40
            
            if router_in_range and not prod_in_range:
                return 'router'
            elif prod_in_range and not router_in_range:
                return 'prod'
            else:
                return 'tie'
        
        elif low > 0 and critical == 0 and high == 0 and medium == 0:
            if router_risk < 20 and prod_risk >= 20:
                return 'router'
            elif prod_risk < 20 and router_risk >= 20:
                return 'prod'
            else:
                return 'tie'
        
        return 'tie'
    
    def should_use_router(self) -> bool:
        """
        DECISÃO FINAL COM GOVERNANÇA.
        
        Critérios:
        1. Mínimo 10 comparações (LIMITE DE CONFIANÇA)
        2. Router win rate >= 60%
        3. Divergência crítica < 20%
        4. Kill switch < 20% (novo)
        """
        # LIMITE DE CONFIANÇA
        if self.metrics['total_comparisons'] < self.MIN_COMPARISONS:
            self._log_decision(
                f"⚠️ DADOS INSUFICIENTES: {self.metrics['total_comparisons']}/{self.MIN_COMPARISONS}"
            )
            return False
        
        router_win_rate = self.metrics['router_better'] / self.metrics['total_comparisons']
        critical_rate = self.metrics['divergence_critical'] / self.metrics['total_comparisons']
        kill_switch_rate = self.metrics['kill_switch_triggered'] / self.metrics['total_comparisons']
        
        # LOG DE DECISÃO (AUDITORIA)
        self._log_decision(
            f"📊 MÉTRICAS: Total={self.metrics['total_comparisons']} | "
            f"Router Win={router_win_rate*100:.1f}% | Critical={critical_rate*100:.1f}% | "
            f"Kill Switch={kill_switch_rate*100:.1f}%"
        )
        
        # DECISÃO
        can_migrate = (
            router_win_rate >= self.MIN_WIN_RATE and 
            critical_rate < self.MAX_CRITICAL_RATE and
            kill_switch_rate < self.MAX_CRITICAL_RATE
        )
        
        if can_migrate:
            self._log_decision("✅ DECISÃO: MIGRAR PARA ROUTER")
        else:
            self._log_decision(f"⚠️ DECISÃO: MANTER PRODUÇÃO (win={router_win_rate:.1%} crit={critical_rate:.1%} kill={kill_switch_rate:.1%})")
        
        return can_migrate
    
    def get_recommendation(self) -> str:
        """Recomendação com governança"""
        if self.metrics['total_comparisons'] < self.MIN_COMPARISONS:
            return f"COLETAR MAIS DADOS ({self.metrics['total_comparisons']}/{self.MIN_COMPARISONS})"
        
        router_win_rate = self.metrics['router_better'] / self.metrics['total_comparisons']
        prod_win_rate = self.metrics['prod_better'] / self.metrics['total_comparisons']
        kill_switch_rate = self.metrics['kill_switch_triggered'] / self.metrics['total_comparisons']
        
        # Kill switch muito ativo = INSTÁVEL
        if kill_switch_rate >= self.MAX_CRITICAL_RATE:
            return f"🚨 ROUTER INSTÁVEL (kill switch: {kill_switch_rate*100:.1f}%) - MANTER PRODUÇÃO"
        
        if self.should_use_router():
            return f"✅ MIGRAR PARA ROUTER (win: {router_win_rate*100:.1f}%)"
        elif prod_win_rate >= self.MIN_WIN_RATE:
            return f"⚠️ MANTER PRODUÇÃO (prod win: {prod_win_rate*100:.1f}%)"
        else:
            return f"🤔 HÍBRIDO RECOMENDADO (empate técnico)"
    
    def get_history(self, limit: int = 20) -> List[Dict]:
        """Busca histórico"""
        conn = sqlite3.connect(str(self.db_file))
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT target, prod_risk, router_risk, diff, winner, kill_switch_triggered,
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
                'kill_switch': row[5],
                'vulns': {
                    'critical': row[6],
                    'high': row[7],
                    'medium': row[8],
                    'low': row[9]
                },
                'timestamp': row[10]
            })
        
        return history
    
    def print_report(self):
        """Relatório com governança"""
        print("="*70)
        print("📊 SHADOW MODE - ANÁLISE COM GOVERNANÇA")
        print("="*70)
        print(f"Database: {self.db_file}")
        print(f"Decision Log: {self.decision_log}")
        print(f"\nComparações: {self.metrics['total_comparisons']} (min: {self.MIN_COMPARISONS})")
        print(f"Router melhor: {self.metrics['router_better']} ({self.metrics['router_better']/max(self.metrics['total_comparisons'],1)*100:.1f}%)")
        print(f"Prod melhor: {self.metrics['prod_better']} ({self.metrics['prod_better']/max(self.metrics['total_comparisons'],1)*100:.1f}%)")
        print(f"\nDivergência alta (>20): {self.metrics['divergence_high']}")
        print(f"Divergência crítica (>50): {self.metrics['divergence_critical']}")
        print(f"🚨 Kill switch acionado: {self.metrics['kill_switch_triggered']}")
        print(f"\nRisk médio - Router: {self.metrics['router_avg_risk']:.1f}")
        print(f"Risk médio - Prod: {self.metrics['prod_avg_risk']:.1f}")
        print(f"\n{'='*70}")
        print(f"RECOMENDAÇÃO: {self.get_recommendation()}")
        print("="*70)

if __name__ == "__main__":
    analyzer = ShadowAnalyzer()
    analyzer.print_report()
