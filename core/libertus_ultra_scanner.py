#!/usr/bin/env python3
"""
LIBERTUS ULTRA SCANNER v6.0 - MONSTRUOSO

Integra TODOS os módulos avançados:
✅ Subdomain Enumeration
✅ Port Scanning + Tech Detection
✅ Advanced SQLi Testing
✅ XSS Hunter
✅ GitHub Secret Scanner
✅ API Endpoint Discovery
✅ SSRF Detection
✅ Auth Bypass Testing

PLUS módulos existentes:
✅ Crypto (hash cracking)
✅ Reverse (secret extraction)
✅ Brain (entendimento profundo)

= SCANNER ULTRA PROFISSIONAL PARA BUG BOUNTY
"""

import asyncio
import json
from typing import Dict, List
from datetime import datetime
from pathlib import Path

# Módulos avançados
from libertus_subdomain_enum import LibertusSubdomainEnum
from libertus_port_scanner import LibertusPortScanner
from libertus_advanced_sqli import LibertusAdvancedSQLi
from libertus_xss_hunter import LibertusXSSHunter
from libertus_github_scanner import LibertusGitHubScanner
from libertus_api_discovery import LibertusAPIDiscovery
from libertus_ssrf_detector import LibertusSSRFDetector
from libertus_auth_bypass import LibertusAuthBypass

# Módulos existentes
from libertus_crypto import LibertusoCrypto
from libertus_reverse import LibertusReverse

# Brain (se disponível)
try:
    from libertus_brain import LibertusBrain
    BRAIN_AVAILABLE = True
except:
    BRAIN_AVAILABLE = False


class LibertusUltraScanner:
    """
    Scanner ULTRA PROFISSIONAL
    Para Bug Bounty e Pentest de Elite
    """
    
    def __init__(self, target: str, scope: Dict = None):
        """
        Args:
            target: URL principal (ex: https://app.aikido.dev)
            scope: Dicionário com regras de scope (opcional)
                   Ex: {'in_scope': [...], 'out_of_scope': [...]}
        """
        self.target = target
        self.domain = self._extract_domain(target)
        self.scope = scope or {}
        
        # Resultados
        self.all_vulnerabilities = []
        self.subdomains = []
        self.endpoints = []
        self.technologies = {}
        self.github_secrets = []
        
        # Módulos
        self.crypto = LibertusoCrypto()
        self.reverse = LibertusReverse()
        self.brain = LibertusBrain() if BRAIN_AVAILABLE else None
        
        # Stats
        self.stats = {
            'modules_executed': 0,
            'total_vulns': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extrai domínio de URL"""
        return url.replace('https://', '').replace('http://', '').split('/')[0]
    
    async def ultra_scan(self) -> Dict:
        """
        SCAN ULTRA COMPLETO
        Executa TODOS os módulos em sequência
        """
        
        print("=" * 70)
        print("🔥 LIBERTUS ULTRA SCANNER v6.0 - BUG BOUNTY EDITION")
        print("=" * 70)
        print(f"\n🎯 Target: {self.target}")
        print(f"🌐 Domain: {self.domain}")
        print(f"⏰ Started: {datetime.now():%Y-%m-%d %H:%M:%S}")
        print("\n" + "=" * 70)
        
        # FASE 1: RECONHECIMENTO
        print("\n" + "🔍 FASE 1: RECONHECIMENTO".center(70, "="))
        await self._phase_reconnaissance()
        
        # FASE 2: DESCOBERTA DE VULNERABILIDADES
        print("\n" + "💥 FASE 2: DESCOBERTA DE VULNERABILIDADES".center(70, "="))
        await self._phase_vulnerability_discovery()
        
        # FASE 3: ANÁLISE PROFUNDA (BRAIN)
        if self.brain and self.all_vulnerabilities:
            print("\n" + "🧠 FASE 3: ANÁLISE CEREBRAL".center(70, "="))
            await self._phase_brain_analysis()
        
        # FASE 4: RELATÓRIO FINAL
        print("\n" + "📄 FASE 4: GERAÇÃO DE RELATÓRIO".center(70, "="))
        report = self._generate_ultra_report()
        
        # SALVAR RELATÓRIO
        self._save_report(report)
        
        print("\n" + "=" * 70)
        print("✅ ULTRA SCAN COMPLETO!")
        print(f"📊 Total Vulnerabilidades: {self.stats['total_vulns']}")
        print(f"   🔴 Críticas: {self.stats['critical']}")
        print(f"   🟠 Altas: {self.stats['high']}")
        print(f"   🟡 Médias: {self.stats['medium']}")
        print("=" * 70)
        
        return report
    
    async def _phase_reconnaissance(self):
        """Fase 1: Reconhecimento"""
        
        # 1.1 Subdomain Enumeration
        print("\n📡 [1/3] Subdomain Enumeration...")
        try:
            enum = LibertusSubdomainEnum(self.domain)
            self.subdomains = await enum.enumerate_all()
            print(f"   ✅ {len(self.subdomains)} subdomínios descobertos")
            self.stats['modules_executed'] += 1
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
        
        # 1.2 Port Scanning + Technology Detection
        print("\n🔌 [2/3] Port Scanning + Tech Detection...")
        try:
            port_scanner = LibertusPortScanner(self.target)
            tech_result = await port_scanner.scan_all()
            self.technologies = tech_result['technologies']
            print(f"   ✅ {len(tech_result['open_ports'])} portas abertas")
            print(f"   ✅ {len(self.technologies)} tecnologias detectadas")
            self.stats['modules_executed'] += 1
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
        
        # 1.3 API Endpoint Discovery
        print("\n🔍 [3/3] API Endpoint Discovery...")
        try:
            api_discovery = LibertusAPIDiscovery(self.target)
            self.endpoints = await api_discovery.discover_all()
            print(f"   ✅ {len(self.endpoints)} endpoints descobertos")
            self.stats['modules_executed'] += 1
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
    
    async def _phase_vulnerability_discovery(self):
        """Fase 2: Descoberta de Vulnerabilidades"""
        
        # 2.1 Advanced SQLi Testing
        print("\n💉 [1/5] Advanced SQLi Testing...")
        try:
            sqli_tester = LibertusAdvancedSQLi()
            
            # Testa endpoints com parâmetros
            endpoints_with_params = [ep for ep in self.endpoints if '?' in ep or '=' in ep]
            
            for endpoint in endpoints_with_params[:10]:  # Primeiros 10
                url = self.target.rstrip('/') + endpoint if endpoint.startswith('/') else endpoint
                vulns = await sqli_tester.test_url(url)
                self.all_vulnerabilities.extend(vulns)
            
            sqli_count = len([v for v in self.all_vulnerabilities if 'sqli' in v['type']])
            print(f"   ✅ {sqli_count} SQLi vulnerabilities encontradas")
            self.stats['modules_executed'] += 1
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
        
        # 2.2 XSS Hunter
        print("\n🎯 [2/5] XSS Hunter...")
        try:
            xss_hunter = LibertusXSSHunter()
            
            for endpoint in endpoints_with_params[:10]:
                url = self.target.rstrip('/') + endpoint if endpoint.startswith('/') else endpoint
                vulns = await xss_hunter.hunt(url)
                self.all_vulnerabilities.extend(vulns)
            
            xss_count = len([v for v in self.all_vulnerabilities if 'xss' in v['type']])
            print(f"   ✅ {xss_count} XSS vulnerabilities encontradas")
            self.stats['modules_executed'] += 1
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
        
        # 2.3 SSRF Detection
        print("\n🌐 [3/5] SSRF Detection...")
        try:
            ssrf_detector = LibertusSSRFDetector()
            
            # Procura endpoints que aceitam URLs
            url_params = ['url', 'uri', 'link', 'redirect', 'callback', 'webhook']
            
            for endpoint in self.endpoints[:20]:
                if any(param in endpoint.lower() for param in url_params):
                    url = self.target.rstrip('/') + endpoint if endpoint.startswith('/') else endpoint
                    vulns = await ssrf_detector.test_url(url)
                    self.all_vulnerabilities.extend(vulns)
            
            ssrf_count = len([v for v in self.all_vulnerabilities if 'ssrf' in v['type']])
            print(f"   ✅ {ssrf_count} SSRF vulnerabilities encontradas")
            self.stats['modules_executed'] += 1
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
        
        # 2.4 Auth Bypass Testing
        print("\n🚪 [4/5] Auth Bypass Testing...")
        try:
            auth_bypass = LibertusAuthBypass()
            vulns = await auth_bypass.test(self.target)
            self.all_vulnerabilities.extend(vulns)
            
            auth_count = len([v for v in self.all_vulnerabilities if 'auth' in v['type'] or 'idor' in v['type']])
            print(f"   ✅ {auth_count} Auth bypass vulnerabilities encontradas")
            self.stats['modules_executed'] += 1
        except Exception as e:
            print(f"   ⚠️ Error: {e}")
        
        # 2.5 GitHub Secret Scanning (se houver repo no scope)
        if 'github_repo' in self.scope:
            print("\n🔓 [5/5] GitHub Secret Scanning...")
            try:
                github_scanner = LibertusGitHubScanner()
                self.github_secrets = await github_scanner.scan_repo(self.scope['github_repo'])
                
                # Adiciona secrets como vulnerabilidades
                for secret in self.github_secrets:
                    self.all_vulnerabilities.append({
                        'type': secret['type'],
                        'severity': 'CRITICAL',
                        'evidence': f"Secret found in {secret.get('file', secret.get('commit', 'unknown'))}",
                        'value': secret['value']
                    })
                
                print(f"   ✅ {len(self.github_secrets)} secrets encontrados")
                self.stats['modules_executed'] += 1
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
    
    async def _phase_brain_analysis(self):
        """Fase 3: Análise com Brain"""
        
        print(f"\n🧠 Analyzing {len(self.all_vulnerabilities)} vulnerabilities with Brain...")
        
        for i, vuln in enumerate(self.all_vulnerabilities[:20]):  # Primeiros 20
            try:
                context = {
                    'url': vuln.get('url', self.target),
                    'payload': vuln.get('payload', ''),
                    'evidence': vuln.get('evidence', '')
                }
                
                result = self.brain.understand_vulnerability(vuln['type'], context)
                vuln['brain_analysis'] = result.get('explanation', {})
                
                print(f"   🧠 [{i+1}/{min(20, len(self.all_vulnerabilities))}] {vuln['type']} analyzed")
            
            except Exception as e:
                print(f"   ⚠️ Brain error: {e}")
    
    def _generate_ultra_report(self) -> Dict:
        """Gera relatório ultra completo"""
        
        # Contagem por severidade
        for vuln in self.all_vulnerabilities:
            severity = vuln.get('severity', 'LOW').upper()
            
            if severity == 'CRITICAL':
                self.stats['critical'] += 1
            elif severity == 'HIGH':
                self.stats['high'] += 1
            elif severity == 'MEDIUM':
                self.stats['medium'] += 1
            else:
                self.stats['low'] += 1
        
        self.stats['total_vulns'] = len(self.all_vulnerabilities)
        
        # Risk score
        risk_score = (
            self.stats['critical'] * 25 +
            self.stats['high'] * 15 +
            self.stats['medium'] * 5 +
            self.stats['low'] * 1
        )
        risk_score = min(risk_score, 100)
        
        report = {
            'scanner': 'Libertus Ultra Scanner v6.0',
            'target': self.target,
            'domain': self.domain,
            'scan_date': datetime.now().isoformat(),
            'scope': self.scope,
            
            'summary': {
                'modules_executed': self.stats['modules_executed'],
                'total_vulnerabilities': self.stats['total_vulns'],
                'critical': self.stats['critical'],
                'high': self.stats['high'],
                'medium': self.stats['medium'],
                'low': self.stats['low'],
                'risk_score': risk_score,
                'risk_level': 'CRÍTICO' if risk_score >= 75 else 'ALTO' if risk_score >= 50 else 'MÉDIO' if risk_score >= 25 else 'BAIXO'
            },
            
            'reconnaissance': {
                'subdomains': self.subdomains,
                'endpoints': self.endpoints[:50],  # Primeiros 50
                'technologies': self.technologies,
            },
            
            'vulnerabilities': self.all_vulnerabilities,
            
            'github_secrets': self.github_secrets,
            
            'modules_used': {
                'subdomain_enum': True,
                'port_scanner': True,
                'tech_detection': True,
                'api_discovery': True,
                'advanced_sqli': True,
                'xss_hunter': True,
                'ssrf_detector': True,
                'auth_bypass': True,
                'github_scanner': 'github_repo' in self.scope,
                'crypto': True,
                'reverse': True,
                'brain': BRAIN_AVAILABLE
            }
        }
        
        return report
    
    def _save_report(self, report: Dict):
        """Salva relatório"""
        
        # JSON completo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_path = Path(f"/tmp/libertus_ultra_scan_{timestamp}.json")
        json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        
        print(f"\n📄 Relatório JSON: {json_path}")
        
        # Markdown resumido
        md_path = Path(f"/tmp/libertus_ultra_scan_{timestamp}.md")
        markdown = self._generate_markdown_report(report)
        md_path.write_text(markdown)
        
        print(f"📄 Relatório MD: {md_path}")
    
    def _generate_markdown_report(self, report: Dict) -> str:
        """Gera relatório markdown"""
        
        md = f"""# 🔥 LIBERTUS ULTRA SCAN REPORT

**Target:** {report['target']}  
**Domain:** {report['domain']}  
**Date:** {report['scan_date']}  
**Scanner:** {report['scanner']}

---

## 📊 EXECUTIVE SUMMARY

| Metric | Value |
|--------|-------|
| **Total Vulnerabilities** | {report['summary']['total_vulnerabilities']} |
| **Critical** | 🔴 {report['summary']['critical']} |
| **High** | 🟠 {report['summary']['high']} |
| **Medium** | 🟡 {report['summary']['medium']} |
| **Low** | ⚪ {report['summary']['low']} |
| **Risk Score** | {report['summary']['risk_score']}/100 |
| **Risk Level** | **{report['summary']['risk_level']}** |

---

## 🔍 RECONNAISSANCE

### Subdomains ({len(report['reconnaissance']['subdomains'])})
"""
        
        for sub in report['reconnaissance']['subdomains'][:10]:
            md += f"- {sub}\n"
        
        md += f"\n### Technologies Detected\n"
        for key, value in report['reconnaissance']['technologies'].items():
            md += f"- **{key}:** {value}\n"
        
        md += f"\n---\n\n## 💥 VULNERABILITIES\n\n"
        
        # Vulnerabilidades por tipo
        vuln_types = {}
        for vuln in report['vulnerabilities']:
            vtype = vuln['type']
            if vtype not in vuln_types:
                vuln_types[vtype] = []
            vuln_types[vtype].append(vuln)
        
        for vtype, vulns in vuln_types.items():
            md += f"\n### {vtype.upper().replace('_', ' ')} ({len(vulns)})\n\n"
            
            for vuln in vulns[:5]:  # Primeiros 5 de cada tipo
                md += f"**Severity:** {vuln.get('severity', 'N/A')}  \n"
                md += f"**Evidence:** {vuln.get('evidence', 'N/A')}  \n"
                
                if 'payload' in vuln:
                    md += f"**Payload:** `{vuln['payload']}`  \n"
                
                md += "\n---\n\n"
        
        md += f"\n## 📌 MODULES EXECUTED\n\n"
        md += f"Total: {report['summary']['modules_executed']}/10\n\n"
        
        return md


async def main():
    """Teste com Aikido Security"""
    
    # Scope do Intigriti
    scope = {
        'in_scope': [
            'app.aikido.dev',
            '*.aikido.dev',
        ],
        'github_repo': 'https://github.com/AikidoSec/safe-chain',
        'out_of_scope': [
            'rate_limiting',
            'security_headers',
            'csrf_low_impact',
        ]
    }
    
    scanner = LibertusUltraScanner("https://app.aikido.dev", scope)
    report = await scanner.ultra_scan()
    
    print(f"\n✅ Scan completo!")
    print(f"📊 {report['summary']['total_vulnerabilities']} vulnerabilities encontradas")


if __name__ == "__main__":
    asyncio.run(main())
