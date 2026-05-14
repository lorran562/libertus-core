#!/usr/bin/env python3
"""
LIBERTUS INTEGRADOR REAL
Conecta scanner → brain → relatório → persistência
SEM SIMULAÇÃO - TUDO FUNCIONAL
"""

import json
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class LibertusIntegradorReal:
    """Integra TODOS os módulos de forma REAL"""
    
    def __init__(self):
        self.base_dir = Path.home() / "LIBERTUS"
        self.scans_dir = self.base_dir / "scans"
        self.reports_dir = self.base_dir / "relatorios"
        
        self.scans_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
    
    async def scan_target_real(self, target: str) -> Optional[Dict]:
        """
        Executa scan REAL e retorna resultado
        NÃO simula - executa código de verdade
        """
        print(f"🔍 Executando scan REAL em: {target}")
        
        try:
            # Importar scanner REAL
            import sys
            sys.path.insert(0, str(self.base_dir / "core"))
            
            from libertus_scanner_v10_complete import LibertusScannerV10
            
            # Executar scan
            scanner = LibertusScannerV10(target)
            resultado = await scanner.scan()
            
            # Salvar resultado
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            scan_file = self.scans_dir / f"scan_{target}_{timestamp}.json"
            
            with open(scan_file, 'w') as f:
                json.dump(resultado, f, indent=2, default=str)
            
            print(f"💾 Scan salvo: {scan_file}")
            
            return resultado
        
        except Exception as e:
            print(f"❌ Erro no scan: {e}")
            return None
    
    def analyze_with_brain_real(self, scan_result: Dict) -> Dict:
        """
        Analisa scan com Brain REAL
        NÃO simula - usa lógica real
        """
        print("🧠 Analisando com Brain...")
        
        try:
            import sys
            sys.path.insert(0, str(self.base_dir / "core"))
            
            from libertus_brain_v2_real import LibertusBrainV2
            
            brain = LibertusBrainV2()
            analise = brain.analyze(scan_result)
            
            print(f"📊 Risk Score: {analise.get('risk_score')}/100")
            print(f"⚠️ Severity: {analise.get('severity')}")
            
            return analise
        
        except Exception as e:
            print(f"❌ Erro na análise: {e}")
            return {}
    
    def generate_report_real(self, scan_result: Dict, brain_analysis: Dict, target: str) -> Optional[Path]:
        """
        Gera relatório REAL em markdown
        NÃO simula - cria arquivo de verdade
        """
        print("📝 Gerando relatório...")
        
        try:
            import sys
            sys.path.insert(0, str(self.base_dir / "core"))
            
            from gerador_relatorio_v2_real import GeradorRelatorioV2
            
            gerador = GeradorRelatorioV2()
            
            # Combinar dados
            dados_completos = {
                **scan_result,
                "brain_analysis": brain_analysis
            }
            
            # Gerar relatório
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.reports_dir / f"relatorio_{target}_{timestamp}.md"
            
            relatorio_md = gerador.generate(dados_completos)
            
            report_file.write_text(relatorio_md)
            
            print(f"✅ Relatório gerado: {report_file}")
            
            return report_file
        
        except Exception as e:
            print(f"❌ Erro ao gerar relatório: {e}")
            return None
    
    def save_to_supabase_real(self, scan_result: Dict, brain_analysis: Dict, target: str) -> bool:
        """
        Salva REALMENTE no Supabase
        NÃO simula - usa API real
        """
        print("☁️ Salvando no Supabase...")
        
        try:
            from supabase import create_client
            
            # Configuração real
            SUPABASE_URL = "https://jkgrmlfqgprcwfooovkx.supabase.co"
            SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Precisa configurar
            
            if not SUPABASE_KEY:
                print("⚠️ SUPABASE_KEY não configurada")
                return False
            
            client = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Inserir scan
            data = {
                "target": target,
                "scan_date": datetime.now().isoformat(),
                "scan_result": scan_result,
                "brain_analysis": brain_analysis,
                "risk_score": brain_analysis.get("risk_score", 0),
                "severity": brain_analysis.get("severity", "UNKNOWN")
            }
            
            result = client.table("libertus_scans").insert(data).execute()
            
            print(f"✅ Salvo no Supabase: {result.data}")
            
            return True
        
        except Exception as e:
            print(f"❌ Erro ao salvar no Supabase: {e}")
            return False
    
    def save_to_sqlite_real(self, scan_result: Dict, brain_analysis: Dict, target: str) -> bool:
        """
        Salva REALMENTE no SQLite
        NÃO simula - banco real
        """
        print("💾 Salvando no SQLite...")
        
        try:
            import sqlite3
            
            db_file = self.base_dir / "memoria" / "libertus.db"
            db_file.parent.mkdir(exist_ok=True)
            
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Criar tabela se não existir
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    scan_date TEXT NOT NULL,
                    risk_score INTEGER,
                    severity TEXT,
                    vulnerabilities_count INTEGER,
                    scan_data TEXT,
                    analysis_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Inserir scan
            cursor.execute("""
                INSERT INTO scans 
                (target, scan_date, risk_score, severity, vulnerabilities_count, scan_data, analysis_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                target,
                datetime.now().isoformat(),
                brain_analysis.get("risk_score", 0),
                brain_analysis.get("severity", "UNKNOWN"),
                len(scan_result.get("vulnerabilities", [])),
                json.dumps(scan_result),
                json.dumps(brain_analysis)
            ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Salvo no SQLite: {db_file}")
            
            return True
        
        except Exception as e:
            print(f"❌ Erro ao salvar no SQLite: {e}")
            return False
    
    def git_commit_real(self, message: str) -> bool:
        """
        Git commit + push REAL
        NÃO simula - executa git de verdade
        """
        print("📤 Fazendo commit no GitHub...")
        
        try:
            import os
            os.chdir(self.base_dir)
            
            # Add
            subprocess.run(["git", "add", "-A"], check=True, capture_output=True)
            
            # Commit
            subprocess.run(
                ["git", "commit", "-m", message],
                check=True,
                capture_output=True
            )
            
            # Push
            subprocess.run(
                ["git", "push", "origin", "main"],
                check=True,
                capture_output=True
            )
            
            print(f"✅ Commit realizado: {message}")
            
            return True
        
        except subprocess.CalledProcessError as e:
            print(f"❌ Git error: {e}")
            return False
    
    async def execute_full_workflow_real(self, target: str) -> Dict:
        """
        Workflow COMPLETO E REAL
        scan → brain → relatório → persistência → git
        
        TUDO EXECUTÁVEL - NADA SIMULADO
        """
        print("\n" + "="*60)
        print(f"🚀 WORKFLOW REAL INICIADO: {target}")
        print("="*60 + "\n")
        
        resultado_final = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }
        
        # Step 1: Scan REAL
        scan_result = await self.scan_target_real(target)
        resultado_final["steps"]["scan"] = scan_result is not None
        
        if not scan_result:
            print("❌ Workflow abortado: scan falhou")
            return resultado_final
        
        # Step 2: Brain REAL
        brain_analysis = self.analyze_with_brain_real(scan_result)
        resultado_final["steps"]["brain"] = bool(brain_analysis)
        
        # Step 3: Relatório REAL
        report_file = self.generate_report_real(scan_result, brain_analysis, target)
        resultado_final["steps"]["report"] = report_file is not None
        
        # Step 4: SQLite REAL
        sqlite_saved = self.save_to_sqlite_real(scan_result, brain_analysis, target)
        resultado_final["steps"]["sqlite"] = sqlite_saved
        
        # Step 5: Supabase REAL (opcional se key configurada)
        supabase_saved = self.save_to_supabase_real(scan_result, brain_analysis, target)
        resultado_final["steps"]["supabase"] = supabase_saved
        
        # Step 6: Git commit REAL
        git_committed = self.git_commit_real(
            f"📊 Scan automático: {target} - Risk {brain_analysis.get('risk_score', 0)}/100"
        )
        resultado_final["steps"]["git"] = git_committed
        
        print("\n" + "="*60)
        print("✅ WORKFLOW REAL COMPLETO")
        print("="*60)
        
        for step, success in resultado_final["steps"].items():
            status = "✅" if success else "❌"
            print(f"{status} {step}")
        
        return resultado_final


# CLI para testes
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python3 libertus_integrador_real.py <target>")
        print("Exemplo: python3 libertus_integrador_real.py exemplo.com")
        sys.exit(1)
    
    target = sys.argv[1]
    
    integrador = LibertusIntegradorReal()
    resultado = asyncio.run(integrador.execute_full_workflow_real(target))
    
    print("\n📊 RESULTADO FINAL:")
    print(json.dumps(resultado, indent=2))
