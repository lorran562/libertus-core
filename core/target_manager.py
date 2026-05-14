#!/usr/bin/env python3
"""
LIBERTUS TARGET MANAGEMENT SYSTEM
Sistema de gerenciamento inteligente de targets

Funcionalidades:
- Lista persistente de targets
- Priorização automática
- Scheduling inteligente
- Histórico de scans

Autor: Libertus v10.0 Production
Data: 2026-05-14
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from enum import Enum


class Priority(Enum):
    """Níveis de prioridade"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class Target:
    """Target de scan"""
    url: str
    priority: int  # 1=CRITICAL, 2=HIGH, 3=MEDIUM, 4=LOW
    last_scan: Optional[str] = None  # ISO timestamp
    scan_count: int = 0
    vulnerabilities_found: int = 0
    highest_severity: Optional[str] = None
    notes: Optional[str] = None
    enabled: bool = True
    added_date: Optional[str] = None


class TargetManager:
    """
    Gerenciador inteligente de targets
    
    Regras de priorização:
    1. Target nunca testado = ALTA prioridade
    2. Target com vulnerabilidades = re-testar periodicamente
    3. Target limpo há muito tempo = baixar prioridade
    4. Target com CRITICAL = manter monitoramento
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path.home() / "LIBERTUS" / "memoria" / "targets.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
    
    def _init_database(self):
        """Inicializa banco de dados de targets"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                priority INTEGER DEFAULT 3,
                last_scan TEXT,
                scan_count INTEGER DEFAULT 0,
                vulnerabilities_found INTEGER DEFAULT 0,
                highest_severity TEXT,
                notes TEXT,
                enabled BOOLEAN DEFAULT 1,
                added_date TEXT DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_url TEXT NOT NULL,
                scan_date TEXT NOT NULL,
                risk_score INTEGER,
                vulnerabilities_count INTEGER,
                severity TEXT,
                scan_duration_seconds INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (target_url) REFERENCES targets(url)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_target(
        self,
        url: str,
        priority: int = Priority.MEDIUM.value,
        notes: Optional[str] = None
    ) -> bool:
        """
        Adiciona novo target
        
        Retorna: True se adicionado, False se já existe
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO targets (url, priority, notes, added_date)
                VALUES (?, ?, ?, ?)
            """, (url, priority, notes, datetime.now().isoformat()))
            
            conn.commit()
            return True
        
        except sqlite3.IntegrityError:
            # Target já existe
            return False
        
        finally:
            conn.close()
    
    def add_targets_bulk(self, urls: List[str], priority: int = Priority.MEDIUM.value) -> int:
        """
        Adiciona múltiplos targets
        
        Retorna: Número de targets adicionados
        """
        added = 0
        
        for url in urls:
            if self.add_target(url, priority):
                added += 1
        
        return added
    
    def get_next_target(self) -> Optional[Target]:
        """
        Retorna próximo target para scan (priorização inteligente)
        
        Regras:
        1. Enabled = True
        2. Ordem: priority ASC (1=CRITICAL primeiro)
        3. Nunca testado (last_scan IS NULL) tem prioridade
        4. Depois: testado há mais tempo
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT url, priority, last_scan, scan_count, 
                   vulnerabilities_found, highest_severity, notes, enabled, added_date
            FROM targets
            WHERE enabled = 1
            ORDER BY 
                priority ASC,
                CASE WHEN last_scan IS NULL THEN 0 ELSE 1 END,
                last_scan ASC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Target(
                url=row[0],
                priority=row[1],
                last_scan=row[2],
                scan_count=row[3],
                vulnerabilities_found=row[4],
                highest_severity=row[5],
                notes=row[6],
                enabled=bool(row[7]),
                added_date=row[8]
            )
        
        return None
    
    def update_after_scan(
        self,
        url: str,
        scan_result: Dict
    ):
        """
        Atualiza target após scan
        
        Também ajusta prioridade automaticamente:
        - Se CRITICAL found → priority = CRITICAL
        - Se HIGH found → priority = HIGH
        - Se limpo → priority = MEDIUM (ou menor)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Determinar nova prioridade baseada no resultado
        severity = scan_result.get('severity', 'UNKNOWN')
        vulns_count = len(scan_result.get('vulnerabilities', []))
        
        new_priority = Priority.MEDIUM.value
        
        if severity == 'CRITICAL':
            new_priority = Priority.CRITICAL.value
        elif severity == 'HIGH':
            new_priority = Priority.HIGH.value
        elif severity == 'MEDIUM':
            new_priority = Priority.MEDIUM.value
        else:
            new_priority = Priority.LOW.value
        
        # Atualizar target
        cursor.execute("""
            UPDATE targets
            SET last_scan = ?,
                scan_count = scan_count + 1,
                vulnerabilities_found = ?,
                highest_severity = ?,
                priority = ?
            WHERE url = ?
        """, (
            datetime.now().isoformat(),
            vulns_count,
            severity,
            new_priority,
            url
        ))
        
        # Adicionar ao histórico
        cursor.execute("""
            INSERT INTO scan_history 
            (target_url, scan_date, risk_score, vulnerabilities_count, severity)
            VALUES (?, ?, ?, ?, ?)
        """, (
            url,
            datetime.now().isoformat(),
            scan_result.get('risk_score', 0),
            vulns_count,
            severity
        ))
        
        conn.commit()
        conn.close()
    
    def get_pending_targets(self, limit: int = 10) -> List[Target]:
        """Retorna targets pendentes de scan (nunca testados ou há muito tempo)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Targets nunca testados OU testados há >7 dias
        seven_days_ago = (datetime.now() - timedelta(days=7)).isoformat()
        
        cursor.execute("""
            SELECT url, priority, last_scan, scan_count, 
                   vulnerabilities_found, highest_severity, notes, enabled, added_date
            FROM targets
            WHERE enabled = 1
              AND (last_scan IS NULL OR last_scan < ?)
            ORDER BY priority ASC, last_scan ASC
            LIMIT ?
        """, (seven_days_ago, limit))
        
        targets = []
        
        for row in cursor.fetchall():
            targets.append(Target(
                url=row[0],
                priority=row[1],
                last_scan=row[2],
                scan_count=row[3],
                vulnerabilities_found=row[4],
                highest_severity=row[5],
                notes=row[6],
                enabled=bool(row[7]),
                added_date=row[8]
            ))
        
        conn.close()
        
        return targets
    
    def get_all_targets(self) -> List[Target]:
        """Retorna todos os targets"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT url, priority, last_scan, scan_count, 
                   vulnerabilities_found, highest_severity, notes, enabled, added_date
            FROM targets
            ORDER BY priority ASC, url ASC
        """)
        
        targets = []
        
        for row in cursor.fetchall():
            targets.append(Target(
                url=row[0],
                priority=row[1],
                last_scan=row[2],
                scan_count=row[3],
                vulnerabilities_found=row[4],
                highest_severity=row[5],
                notes=row[6],
                enabled=bool(row[7]),
                added_date=row[8]
            ))
        
        conn.close()
        
        return targets
    
    def disable_target(self, url: str):
        """Desabilita target (não será mais testado)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE targets SET enabled = 0 WHERE url = ?", (url,))
        
        conn.commit()
        conn.close()
    
    def enable_target(self, url: str):
        """Habilita target"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE targets SET enabled = 1 WHERE url = ?", (url,))
        
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas do sistema de targets"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total targets
        cursor.execute("SELECT COUNT(*) FROM targets WHERE enabled = 1")
        stats['total_enabled'] = cursor.fetchone()[0]
        
        # Nunca testados
        cursor.execute("SELECT COUNT(*) FROM targets WHERE enabled = 1 AND last_scan IS NULL")
        stats['never_scanned'] = cursor.fetchone()[0]
        
        # Com vulnerabilidades
        cursor.execute("SELECT COUNT(*) FROM targets WHERE enabled = 1 AND vulnerabilities_found > 0")
        stats['with_vulnerabilities'] = cursor.fetchone()[0]
        
        # Por prioridade
        cursor.execute("""
            SELECT priority, COUNT(*) 
            FROM targets 
            WHERE enabled = 1
            GROUP BY priority
        """)
        
        stats['by_priority'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total scans realizados
        cursor.execute("SELECT COUNT(*) FROM scan_history")
        stats['total_scans'] = cursor.fetchone()[0]
        
        conn.close()
        
        return stats


# CLI para testes
if __name__ == "__main__":
    manager = TargetManager()
    
    # Adicionar targets de exemplo
    print("=== ADICIONANDO TARGETS ===")
    manager.add_target("exemplo.com", Priority.HIGH.value, "Site principal")
    manager.add_target("app.exemplo.com", Priority.CRITICAL.value, "Aplicação crítica")
    manager.add_target("blog.exemplo.com", Priority.LOW.value, "Blog")
    
    # Estatísticas
    print("\n=== ESTATÍSTICAS ===")
    stats = manager.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Próximo target
    print("\n=== PRÓXIMO TARGET ===")
    next_target = manager.get_next_target()
    if next_target:
        print(f"URL: {next_target.url}")
        print(f"Priority: {next_target.priority}")
        print(f"Last scan: {next_target.last_scan}")
    
    # Targets pendentes
    print("\n=== TARGETS PENDENTES ===")
    pending = manager.get_pending_targets(limit=5)
    for t in pending:
        print(f"- {t.url} (priority={t.priority}, scans={t.scan_count})")
