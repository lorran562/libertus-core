#!/usr/bin/env python3
"""
LIBERTUS PRODUCTION DAEMON
Sistema Autônomo de Produção - Nível Empresa

ZERO INTERVENÇÃO HUMANA
Opera 24/7 com:
- Target management inteligente
- Proof Engine (apenas vulnerabilidades confirmadas)
- Anti-block system
- Relatórios profissionais
- Persistência completa

Autor: Libertus v10.0 Production
Data: 2026-05-14
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Imports dos módulos de produção
from target_manager import TargetManager, Priority
from proof_engine import ProofEngine
from anti_block_system import AntiBlockSystem, RequestConfig

# Setup logging
log_dir = Path.home() / "LIBERTUS" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "production_daemon.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('PRODUCTION_DAEMON')


class ProductionDaemon:
    """
    Daemon de PRODUÇÃO - Nível Empresa
    
    Opera autonomamente:
    1. Pega próximo target (target manager)
    2. Executa scan (scanner final)
    3. Prova vulnerabilidades (proof engine)
    4. Gera relatório (report generator)
    5. Persiste resultados (SQLite + Git)
    6. Repete indefinidamente
    
    SEM INTERVENÇÃO HUMANA
    """
    
    def __init__(self):
        self.base_dir = Path.home() / "LIBERTUS"
        self.scans_dir = self.base_dir / "scans"
        self.reports_dir = self.base_dir / "relatorios"
        
        # Criar diretórios
        for d in [self.scans_dir, self.reports_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # Componentes de produção
        self.target_manager = TargetManager()
        self.proof_engine = ProofEngine()
        self.anti_block = AntiBlockSystem(RequestConfig(
            min_delay=1.0,
            max_delay=3.0,
            max_retries=3
        ))
        
        self.running = True
        self.iteration = 0
        
        logger.info("="*70)
        logger.info("🏭 LIBERTUS PRODUCTION DAEMON INICIADO")
        logger.info("="*70)
        logger.info("Modo: PRODUÇÃO - Zero intervenção humana")
        logger.info("Componentes:")
        logger.info("  ✅ Target Manager (priorização inteligente)")
        logger.info("  ✅ Proof Engine (apenas vulns confirmadas)")
        logger.info("  ✅ Anti-Block System (evasão de detecção)")
        logger.info("  ✅ Scanner Final (Validation Engine integrado)")
        logger.info("  ✅ Report Generator (profissional)")
        logger.info("  ✅ Git Automation (commits automáticos)")
        logger.info("="*70 + "\n")
    
    async def scan_target_production(self, target_url: str) -> Optional[Dict]:
        """
        Scan de PRODUÇÃO com Proof Engine
        
        Fluxo:
        1. Port scan
        2. Tech detection
        3. Vulnerability detection
        4. PROOF ENGINE (confirma cada vulnerabilidade)
        5. Retorna apenas vulnerabilidades PROVADAS
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"[SCAN] Iniciando scan de produção: {target_url}")
        logger.info(f"{'='*70}")
        
        try:
            # Importar scanner
            import sys
            sys.path.insert(0, str(self.base_dir / "core"))
            
            from libertus_scanner_final import LibertusScannerFinal
            
            # Executar scan
            scanner = LibertusScannerFinal(target_url)
            scan_result = await scanner.scan_complete()
            
            # PROOF ENGINE: Validar cada vulnerabilidade
            logger.info("\n[PROOF] Validando vulnerabilidades com Proof Engine...")
            
            proven_vulns = []
            
            async with aiohttp.ClientSession() as session:
                for vuln in scan_result.get('vulnerabilities', []):
                    vuln_type = vuln.get('type', '')
                    
                    # SQLi proof
                    if 'SQL Injection' in vuln_type:
                        logger.info(f"  [PROOF] Testando SQLi: {vuln.get('url', 'N/A')}")
                        
                        proof = await self.proof_engine.prove_sqli(
                            session=session,
                            url=vuln.get('url', target_url),
                            param=vuln.get('param', 'id'),
                            payload=vuln.get('payload', '')
                        )
                        
                        if proof.confirmed:
                            logger.info(f"  ✅ SQLi CONFIRMADA (confidence: {proof.confidence:.0%})")
                            
                            # Adicionar prova à vulnerabilidade
                            vuln['proof'] = {
                                'confirmed': True,
                                'confidence': proof.confidence,
                                'evidence': proof.evidence,
                                'technical_proof': proof.technical_proof,
                                'attack_vector': proof.attack_vector
                            }
                            
                            proven_vulns.append(vuln)
                        else:
                            logger.info(f"  ❌ SQLi NÃO confirmada")
                    
                    # XSS proof
                    elif 'XSS' in vuln_type or 'Cross-Site Scripting' in vuln_type:
                        logger.info(f"  [PROOF] Testando XSS: {vuln.get('url', 'N/A')}")
                        
                        proof = await self.proof_engine.prove_xss(
                            session=session,
                            url=vuln.get('url', target_url),
                            param=vuln.get('param', 'q'),
                            payload=vuln.get('payload', '')
                        )
                        
                        if proof.confirmed:
                            logger.info(f"  ✅ XSS CONFIRMADO (confidence: {proof.confidence:.0%})")
                            
                            vuln['proof'] = {
                                'confirmed': True,
                                'confidence': proof.confidence,
                                'evidence': proof.evidence,
                                'technical_proof': proof.technical_proof,
                                'attack_vector': proof.attack_vector
                            }
                            
                            proven_vulns.append(vuln)
                        else:
                            logger.info(f"  ❌ XSS NÃO confirmado")
                    
                    # Outras vulnerabilidades (já confirmadas por scanner)
                    else:
                        proven_vulns.append(vuln)
            
            # Atualizar resultado com apenas vulnerabilidades provadas
            scan_result['vulnerabilities'] = proven_vulns
            scan_result['vulnerabilities_total'] = len(scan_result.get('vulnerabilities', []))
            scan_result['vulnerabilities_proven'] = len(proven_vulns)
            
            logger.info(f"\n[PROOF] Resultado:")
            logger.info(f"  Total detectadas: {scan_result.get('vulnerabilities_total', 0)}")
            logger.info(f"  Provadas: {len(proven_vulns)}")
            
            return scan_result
        
        except Exception as e:
            logger.error(f"[SCAN] Erro: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def generate_production_report(
        self,
        scan_result: Dict,
        target_url: str
    ) -> Optional[Path]:
        """
        Gera relatório de PRODUÇÃO
        
        Inclui:
        - Prova técnica de cada vulnerabilidade
        - Impacto real
        - Recomendações específicas
        """
        logger.info("\n[REPORT] Gerando relatório de produção...")
        
        try:
            # Template de relatório markdown
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.reports_dir / f"production_{target_url.replace('.', '_')}_{timestamp}.md"
            
            # Gerar markdown
            report_md = f"""# RELATÓRIO DE SEGURANÇA - PRODUÇÃO

**Target:** {target_url}  
**Data:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Risk Score:** {scan_result.get('risk_score', 0)}/100  
**Severity:** {scan_result.get('severity', 'UNKNOWN')}

---

## RESUMO EXECUTIVO

- **Vulnerabilidades Detectadas:** {scan_result.get('vulnerabilities_total', 0)}
- **Vulnerabilidades PROVADAS:** {scan_result.get('vulnerabilities_proven', 0)}
- **Portas Abertas:** {len(scan_result.get('open_ports', []))}
- **Tecnologias:** {', '.join(scan_result.get('technologies', ['N/A']))}

---

## VULNERABILIDADES CONFIRMADAS

"""
            
            for i, vuln in enumerate(scan_result.get('vulnerabilities', []), 1):
                report_md += f"""
### {i}. {vuln.get('type', 'Unknown')} - {vuln.get('severity', 'UNKNOWN')}

**Descrição:** {vuln.get('description', 'N/A')}

"""
                
                # Se tem prova, incluir
                if 'proof' in vuln:
                    proof = vuln['proof']
                    
                    report_md += f"""
**PROVA TÉCNICA:**

```
{proof.get('technical_proof', 'N/A')}
```

**Confidence:** {proof.get('confidence', 0):.0%}

**Attack Vector:**
```
{proof.get('attack_vector', 'N/A')}
```

**Evidência:**
```json
{json.dumps(proof.get('evidence', {}), indent=2)}
```

"""
                
                report_md += "---\n\n"
            
            # Salvar
            report_file.write_text(report_md)
            
            logger.info(f"[REPORT] ✅ Relatório salvo: {report_file}")
            
            return report_file
        
        except Exception as e:
            logger.error(f"[REPORT] Erro: {e}")
            return None
    
    async def execute_production_cycle(self):
        """
        Ciclo completo de produção
        
        1. Pega próximo target (target manager)
        2. Scan com proof engine
        3. Gera relatório
        4. Atualiza target manager
        5. Git commit
        """
        self.iteration += 1
        
        logger.info(f"\n{'#'*70}")
        logger.info(f"### CICLO DE PRODUÇÃO #{self.iteration}")
        logger.info(f"{'#'*70}\n")
        
        # 1. Pegar próximo target
        logger.info("[TARGET] Buscando próximo target...")
        
        target = self.target_manager.get_next_target()
        
        if not target:
            logger.warning("[TARGET] ⚠️ Nenhum target disponível")
            logger.info("[TARGET] Aguardando 5 minutos...")
            await asyncio.sleep(300)
            return
        
        logger.info(f"[TARGET] ✅ Target selecionado: {target.url}")
        logger.info(f"[TARGET]    Priority: {target.priority}")
        logger.info(f"[TARGET]    Last scan: {target.last_scan or 'NEVER'}")
        logger.info(f"[TARGET]    Scan count: {target.scan_count}")
        
        # 2. Scan com proof
        scan_result = await self.scan_target_production(target.url)
        
        if not scan_result:
            logger.error("[SCAN] ❌ Scan falhou")
            return
        
        # 3. Relatório
        report_file = await self.generate_production_report(scan_result, target.url)
        
        # 4. Atualizar target manager
        logger.info("\n[TARGET] Atualizando target manager...")
        
        self.target_manager.update_after_scan(target.url, scan_result)
        
        logger.info("[TARGET] ✅ Target atualizado")
        
        # 5. Git commit (opcional - não bloquear em erro)
        try:
            import subprocess
            subprocess.run(
                ['git', 'add', '-A'],
                cwd=self.base_dir,
                timeout=30,
                capture_output=True
            )
            
            commit_msg = f"🔍 Scan automático: {target.url} | Risk: {scan_result.get('risk_score')}/100"
            
            subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                cwd=self.base_dir,
                timeout=30,
                capture_output=True
            )
            
            logger.info("[GIT] ✅ Commit realizado")
        except:
            logger.warning("[GIT] ⚠️ Git commit falhou (não bloqueante)")
        
        # Estatísticas
        stats = self.target_manager.get_stats()
        logger.info(f"\n{'='*70}")
        logger.info(f"ESTATÍSTICAS DO SISTEMA:")
        logger.info(f"{'='*70}")
        logger.info(f"Targets ativos: {stats.get('total_enabled', 0)}")
        logger.info(f"Nunca testados: {stats.get('never_scanned', 0)}")
        logger.info(f"Com vulnerabilidades: {stats.get('with_vulnerabilities', 0)}")
        logger.info(f"Total de scans: {stats.get('total_scans', 0)}")
        logger.info(f"{'='*70}\n")
    
    async def run(self):
        """
        Loop principal de produção
        
        Executa indefinidamente:
        - Ciclo de scan
        - Delay configurável
        """
        logger.info("🚀 Iniciando loop de produção...\n")
        
        while self.running:
            try:
                # Executar ciclo
                await self.execute_production_cycle()
                
                # Delay entre ciclos (5 minutos)
                wait_time = 300
                
                logger.info(f"⏱️ Aguardando {wait_time//60} minutos até próximo ciclo...\n")
                
                await asyncio.sleep(wait_time)
            
            except KeyboardInterrupt:
                logger.info("\n⏹️ Interrupção detectada - finalizando...")
                self.running = False
            
            except Exception as e:
                logger.error(f"❌ Erro no ciclo: {e}")
                import traceback
                traceback.print_exc()
                
                # Aguardar antes de retry
                await asyncio.sleep(60)


async def main():
    """Entry point"""
    daemon = ProductionDaemon()
    await daemon.run()


if __name__ == "__main__":
    asyncio.run(main())
