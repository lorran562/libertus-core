#!/usr/bin/env python3
"""
LIBERTUS MEMÓRIA v2.0 REAL
Sistema de memória útil que armazena:
- Histórico de scans
- Padrões recorrentes
- Vulnerabilidades por target
- Timeline de eventos
- Estatísticas e métricas
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class MemoriaV2:
    """
    Sistema de memória baseado em SQLite
    Armazena histórico útil e detecta padrões
    """
    
    def __init__(self, db_path: str = "/root/LIBERTUS/memoria/libertus.db"):
        self.db_path = db_path
        
        # Criar diretório
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar banco
        self._init_database()
    
    def _init_database(self):
        """Inicializa schema do banco"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de scans
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target TEXT NOT NULL,
                scan_date TIMESTAMP NOT NULL,
                risk_score INTEGER,
                severity TEXT,
                total_vulnerabilities INTEGER,
                critical_count INTEGER,
                high_count INTEGER,
                medium_count INTEGER,
                low_count INTEGER,
                scan_duration_seconds INTEGER,
                scan_type TEXT,
                raw_results TEXT
            )
        """)
        
        # Tabela de vulnerabilidades
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id INTEGER,
                target TEXT NOT NULL,
                vuln_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                first_seen TIMESTAMP NOT NULL,
                last_seen TIMESTAMP NOT NULL,
                occurrence_count INTEGER DEFAULT 1,
                fixed BOOLEAN DEFAULT 0,
                fixed_date TIMESTAMP,
                validation_status TEXT,
                payload TEXT,
                evidence TEXT,
                FOREIGN KEY (scan_id) REFERENCES scans(id)
            )
        """)
        
        # Tabela de padrões
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                description TEXT,
                targets TEXT,
                first_detected TIMESTAMP NOT NULL,
                last_detected TIMESTAMP NOT NULL,
                occurrence_count INTEGER DEFAULT 1,
                confidence REAL
            )
        """)
        
        # Tabela de estatísticas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                total_scans INTEGER,
                total_vulnerabilities INTEGER,
                avg_risk_score REAL,
                targets_scanned TEXT,
                UNIQUE(date)
            )
        """)
        
        # Índices
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scans_target 
            ON scans(target)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scans_date 
            ON scans(scan_date)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_vulns_target 
            ON vulnerabilities(target)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_vulns_type 
            ON vulnerabilities(vuln_type)
        """)
        
        conn.commit()
        conn.close()
    
    def save_scan(self, target: str, results: Dict, duration: int = 0) -> int:
        """
        Salva resultado de scan
        Retorna scan_id
        """
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Contar vulnerabilidades por severity
        vulns = results.get('vulnerabilities', [])
        critical = len([v for v in vulns if v.get('severity') == 'CRITICAL'])
        high = len([v for v in vulns if v.get('severity') == 'HIGH'])
        medium = len([v for v in vulns if v.get('severity') == 'MEDIUM'])
        low = len([v for v in vulns if v.get('severity') == 'LOW'])
        
        # Inserir scan
        cursor.execute("""
            INSERT INTO scans (
                target, scan_date, risk_score, severity,
                total_vulnerabilities, critical_count, high_count,
                medium_count, low_count, scan_duration_seconds,
                scan_type, raw_results
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            target,
            datetime.now(),
            results.get('risk_score', 0),
            results.get('severity', 'LOW'),
            len(vulns),
            critical, high, medium, low,
            duration,
            'full',
            json.dumps(results)
        ))
        
        scan_id = cursor.lastrowid
        
        # Salvar vulnerabilidades
        for vuln in vulns:
            self._save_vulnerability(cursor, scan_id, target, vuln)
        
        conn.commit()
        conn.close()
        
        # Atualizar estatísticas
        self._update_statistics()
        
        # Detectar padrões
        self._detect_patterns(target)
        
        return scan_id
    
    def _save_vulnerability(self, cursor, scan_id: int, target: str, vuln: Dict):
        """Salva ou atualiza vulnerabilidade"""
        
        vuln_type = vuln.get('type', 'Unknown')
        severity = vuln.get('severity', 'MEDIUM')
        
        # Verificar se vulnerabilidade já existe (mesmo tipo + target)
        cursor.execute("""
            SELECT id, occurrence_count FROM vulnerabilities
            WHERE target = ? AND vuln_type = ? AND fixed = 0
            ORDER BY last_seen DESC
            LIMIT 1
        """, (target, vuln_type))
        
        existing = cursor.fetchone()
        
        if existing:
            # Atualizar existente
            vuln_id, count = existing
            cursor.execute("""
                UPDATE vulnerabilities
                SET last_seen = ?,
                    occurrence_count = ?,
                    evidence = ?
                WHERE id = ?
            """, (
                datetime.now(),
                count + 1,
                vuln.get('evidence', ''),
                vuln_id
            ))
        else:
            # Inserir nova
            cursor.execute("""
                INSERT INTO vulnerabilities (
                    scan_id, target, vuln_type, severity,
                    first_seen, last_seen, validation_status,
                    payload, evidence
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                scan_id,
                target,
                vuln_type,
                severity,
                datetime.now(),
                datetime.now(),
                vuln.get('validation', 'DETECTED'),
                vuln.get('payload', ''),
                vuln.get('evidence', '')
            ))
    
    def get_target_history(self, target: str, days: int = 30) -> List[Dict]:
        """Retorna histórico de scans de um target"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            SELECT 
                id, scan_date, risk_score, severity,
                total_vulnerabilities, critical_count,
                high_count, medium_count, low_count
            FROM scans
            WHERE target = ? AND scan_date >= ?
            ORDER BY scan_date DESC
        """, (target, cutoff))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'scan_id': row[0],
                'date': row[1],
                'risk_score': row[2],
                'severity': row[3],
                'total_vulnerabilities': row[4],
                'critical': row[5],
                'high': row[6],
                'medium': row[7],
                'low': row[8]
            }
            for row in rows
        ]
    
    def get_recurring_vulnerabilities(self, target: str) -> List[Dict]:
        """Retorna vulnerabilidades recorrentes (2+ ocorrências)"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                vuln_type, severity, occurrence_count,
                first_seen, last_seen, fixed
            FROM vulnerabilities
            WHERE target = ? AND occurrence_count >= 2
            ORDER BY occurrence_count DESC, severity DESC
        """, (target,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'type': row[0],
                'severity': row[1],
                'occurrences': row[2],
                'first_seen': row[3],
                'last_seen': row[4],
                'fixed': bool(row[5])
            }
            for row in rows
        ]
    
    def mark_vulnerability_fixed(self, target: str, vuln_type: str):
        """Marca vulnerabilidade como corrigida"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE vulnerabilities
            SET fixed = 1, fixed_date = ?
            WHERE target = ? AND vuln_type = ? AND fixed = 0
        """, (datetime.now(), target, vuln_type))
        
        conn.commit()
        conn.close()
    
    def _detect_patterns(self, target: str):
        """Detecta padrões recorrentes"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Padrão 1: Mesma vulnerabilidade em múltiplos scans
        cursor.execute("""
            SELECT vuln_type, COUNT(*) as count
            FROM vulnerabilities
            WHERE target = ? AND fixed = 0
            GROUP BY vuln_type
            HAVING count >= 3
        """, (target,))
        
        recurring = cursor.fetchall()
        
        for vuln_type, count in recurring:
            self._save_pattern(
                cursor,
                'recurring_vulnerability',
                f'{vuln_type} detectada {count}x em {target}',
                [target],
                confidence=min(count / 10.0, 1.0)
            )
        
        # Padrão 2: Múltiplas vulnerabilidades HIGH/CRITICAL
        cursor.execute("""
            SELECT COUNT(DISTINCT vuln_type)
            FROM vulnerabilities
            WHERE target = ? AND severity IN ('HIGH', 'CRITICAL') AND fixed = 0
        """, (target,))
        
        high_count = cursor.fetchone()[0]
        
        if high_count >= 3:
            self._save_pattern(
                cursor,
                'high_risk_target',
                f'{target} tem {high_count} tipos de vulnerabilidades HIGH/CRITICAL',
                [target],
                confidence=min(high_count / 10.0, 1.0)
            )
        
        conn.commit()
        conn.close()
    
    def _save_pattern(self, cursor, pattern_type: str, description: str, 
                      targets: List[str], confidence: float):
        """Salva padrão detectado"""
        
        targets_json = json.dumps(targets)
        
        # Verificar se padrão já existe
        cursor.execute("""
            SELECT id, occurrence_count FROM patterns
            WHERE pattern_type = ? AND targets = ?
        """, (pattern_type, targets_json))
        
        existing = cursor.fetchone()
        
        if existing:
            # Atualizar
            pattern_id, count = existing
            cursor.execute("""
                UPDATE patterns
                SET last_detected = ?,
                    occurrence_count = ?,
                    confidence = ?
                WHERE id = ?
            """, (datetime.now(), count + 1, confidence, pattern_id))
        else:
            # Inserir
            cursor.execute("""
                INSERT INTO patterns (
                    pattern_type, description, targets,
                    first_detected, last_detected, confidence
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                pattern_type, description, targets_json,
                datetime.now(), datetime.now(), confidence
            ))
    
    def get_patterns(self, min_confidence: float = 0.5) -> List[Dict]:
        """Retorna padrões detectados"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                pattern_type, description, targets,
                occurrence_count, confidence, last_detected
            FROM patterns
            WHERE confidence >= ?
            ORDER BY confidence DESC, occurrence_count DESC
        """, (min_confidence,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'type': row[0],
                'description': row[1],
                'targets': json.loads(row[2]),
                'occurrences': row[3],
                'confidence': row[4],
                'last_detected': row[5]
            }
            for row in rows
        ]
    
    def _update_statistics(self):
        """Atualiza estatísticas diárias"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        # Estatísticas de hoje
        cursor.execute("""
            SELECT 
                COUNT(*) as total_scans,
                SUM(total_vulnerabilities) as total_vulns,
                AVG(risk_score) as avg_risk,
                GROUP_CONCAT(DISTINCT target) as targets
            FROM scans
            WHERE DATE(scan_date) = ?
        """, (today,))
        
        row = cursor.fetchone()
        
        if row[0] > 0:
            cursor.execute("""
                INSERT OR REPLACE INTO statistics (
                    date, total_scans, total_vulnerabilities,
                    avg_risk_score, targets_scanned
                ) VALUES (?, ?, ?, ?, ?)
            """, (today, row[0], row[1] or 0, row[2] or 0, row[3] or ''))
        
        conn.commit()
        conn.close()
    
    def get_statistics(self, days: int = 30) -> Dict:
        """Retorna estatísticas dos últimos N dias"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).date()
        
        cursor.execute("""
            SELECT 
                SUM(total_scans),
                SUM(total_vulnerabilities),
                AVG(avg_risk_score)
            FROM statistics
            WHERE date >= ?
        """, (cutoff,))
        
        total_scans, total_vulns, avg_risk = cursor.fetchone()
        
        # Vulnerabilidades por tipo
        cursor.execute("""
            SELECT vuln_type, COUNT(*) as count
            FROM vulnerabilities
            WHERE DATE(first_seen) >= ?
            GROUP BY vuln_type
            ORDER BY count DESC
            LIMIT 10
        """, (cutoff,))
        
        top_vulns = [
            {'type': row[0], 'count': row[1]}
            for row in cursor.fetchall()
        ]
        
        # Targets mais vulneráveis
        cursor.execute("""
            SELECT target, AVG(risk_score) as avg_risk
            FROM scans
            WHERE DATE(scan_date) >= ?
            GROUP BY target
            ORDER BY avg_risk DESC
            LIMIT 5
        """, (cutoff,))
        
        top_targets = [
            {'target': row[0], 'avg_risk': row[1]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'period_days': days,
            'total_scans': total_scans or 0,
            'total_vulnerabilities': total_vulns or 0,
            'avg_risk_score': round(avg_risk or 0, 2),
            'top_vulnerabilities': top_vulns,
            'riskiest_targets': top_targets
        }
    
    def export_target_report(self, target: str) -> Dict:
        """Exporta relatório completo de um target"""
        
        return {
            'target': target,
            'history': self.get_target_history(target, days=90),
            'recurring_vulnerabilities': self.get_recurring_vulnerabilities(target),
            'patterns': [
                p for p in self.get_patterns()
                if target in p['targets']
            ]
        }


# Teste
if __name__ == "__main__":
    memoria = MemoriaV2()
    
    print("💾 LIBERTUS MEMÓRIA v2.0 - TESTE")
    print("="*60)
    
    # Simular scan
    test_results = {
        'target': 'example.com',
        'risk_score': 45,
        'severity': 'HIGH',
        'vulnerabilities': [
            {'type': 'SQLi', 'severity': 'CRITICAL', 'validation': 'CONFIRMED'},
            {'type': 'XSS', 'severity': 'HIGH', 'validation': 'CONFIRMED'},
            {'type': 'Missing Security Header', 'severity': 'MEDIUM'}
        ]
    }
    
    print("\n1️⃣ Salvando scan...")
    scan_id = memoria.save_scan('example.com', test_results, duration=120)
    print(f"   ✅ Scan salvo: ID {scan_id}")
    
    print("\n2️⃣ Histórico do target...")
    history = memoria.get_target_history('example.com')
    print(f"   {len(history)} scans encontrados")
    for h in history:
        print(f"   - {h['date']}: {h['total_vulnerabilities']} vulns, risk {h['risk_score']}")
    
    print("\n3️⃣ Estatísticas...")
    stats = memoria.get_statistics(days=30)
    print(f"   Total scans: {stats['total_scans']}")
    print(f"   Total vulns: {stats['total_vulnerabilities']}")
    print(f"   Avg risk: {stats['avg_risk_score']}")
    
    print("\n4️⃣ Padrões detectados...")
    patterns = memoria.get_patterns()
    print(f"   {len(patterns)} padrões encontrados")
    for p in patterns:
        print(f"   - {p['type']}: {p['description']} (conf: {p['confidence']:.2f})")
    
    print("\n" + "="*60)
