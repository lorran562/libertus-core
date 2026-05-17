#!/usr/bin/env python3
"""
LIBERTUS SCANNER FINAL - INTEGRAÇÃO TOTAL REAL
Validation Engine INTEGRADO (SQLi + XSS)

ZERO SIMULAÇÃO - TUDO EXECUTÁVEL

Autor: Libertus v10.0
Data: 2026-05-14
"""

import asyncio
import aiohttp
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Import REAL Validation Engine
try:
    from validation_engine_v1 import SQLiEngine, XSSEngine
    HAS_VALIDATION = True
except ImportError:
    HAS_VALIDATION = False
    print("⚠️ Validation Engine não encontrado - usando fallback")


class LibertusScannerFinal:
    """
    Scanner COMPLETO com Validation Engine REAL integrado
    
    Pipeline REAL:
    1. Port scan
    2. Tech detection
    3. SQLi validation (23 payloads REAL)
    4. XSS validation (21 payloads REAL)
    5. Security headers
    6. Risk calculation
    
    SEM PLACEHOLDERS - TUDO EXECUTÁVEL
    """
    
    def __init__(self, target: str):
        self.target = target.replace('http://', '').replace('https://', '').split('/')[0]
        self.base_url = f"http://{self.target}"
        
        self.results = {
            'target': self.target,
            'scan_date': datetime.now().isoformat(),
            'vulnerabilities': [],
            'risk_score': 0,
            'severity': 'UNKNOWN'
        }
        
        # Validation Engine REAL
        if HAS_VALIDATION:
            self.sqli_engine = SQLiEngine()
            self.xss_engine = XSSEngine()
            print("✅ Validation Engine carregado (SQLi + XSS)")
        else:
            self.sqli_engine = None
            self.xss_engine = None
            print("⚠️ Fallback mode (sem validation engine)")
    
    async def scan_complete(self) -> Dict:
        """
        Scan COMPLETO com todas as fases
        """
        print(f"\n{'='*70}")
        print(f"🔍 LIBERTUS SCANNER FINAL - {self.target}")
        print(f"{'='*70}\n")
        
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # Fase 1: Port Scan
            await self._port_scan()
            
            # Fase 2: Tech Detection
            await self._detect_technology()
            
            # Fase 3: Vulnerability Testing (VALIDATION ENGINE INTEGRADO)
            await self._test_vulnerabilities_real()
            
            # Fase 4: Security Headers
            await self._test_security_headers()
        
        # Fase 5: Risk Calculation
        self._calculate_risk()
        
        print(f"\n{'='*70}")
        print(f"✅ SCAN COMPLETO")
        print(f"{'='*70}")
        print(f"📊 Risk Score: {self.results['risk_score']}/100")
        print(f"🔴 Severity: {self.results['severity']}")
        print(f"⚠️ Vulnerabilidades: {len(self.results['vulnerabilities'])}")
        print(f"{'='*70}\n")
        
        return self.results
    
    async def _port_scan(self):
        """Port scan básico"""
        print("1️⃣ Port Scanning...")
        
        common_ports = [80, 443, 3306, 5432, 27017, 6379, 22, 21]
        
        open_ports = []
        
        for port in common_ports:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.target, port),
                    timeout=2
                )
                writer.close()
                await writer.wait_closed()
                open_ports.append(port)
            except:
                pass
        
        if open_ports:
            print(f"   ✅ Portas abertas: {open_ports}")
            
            # Portas sensíveis
            sensitive = [p for p in open_ports if p in [3306, 5432, 27017, 6379]]
            if sensitive:
                for port in sensitive:
                    self.results['vulnerabilities'].append({
                        'type': 'Exposed Database Port',
                        'severity': 'CRITICAL',
                        'port': port,
                        'description': f'Porta {port} exposta publicamente',
                        'validation': 'CONFIRMED'
                    })
        else:
            print("   ℹ️ Nenhuma porta comum aberta")
        
        self.results['open_ports'] = open_ports
    
    async def _detect_technology(self):
        """Detecção de tecnologias"""
        print("\n2️⃣ Technology Detection...")
        
        try:
            async with self.session.get(self.base_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                headers = dict(resp.headers)
                html = await resp.text()
                
                tech = []
                
                # Server
                if 'Server' in headers:
                    tech.append(f"Server: {headers['Server']}")
                
                # WordPress
                if 'wp-content' in html or 'wp-includes' in html:
                    tech.append("WordPress")
                    
                    # Versão WordPress
                    wp_version = re.search(r'wordpress (\d+\.\d+)', html, re.I)
                    if wp_version:
                        version = wp_version.group(1)
                        tech.append(f"WordPress {version}")
                        
                        # Versões antigas
                        try:
                            if float(version) < 6.0:
                                self.results['vulnerabilities'].append({
                                    'type': 'Outdated WordPress',
                                    'severity': 'HIGH',
                                    'version': version,
                                    'description': f'WordPress {version} desatualizado (< 6.0)',
                                    'validation': 'CONFIRMED'
                                })
                        except:
                            pass
                
                # PHP
                if 'X-Powered-By' in headers and 'PHP' in headers['X-Powered-By']:
                    tech.append(headers['X-Powered-By'])
                
                print(f"   ✅ Tecnologias: {', '.join(tech) if tech else 'Nenhuma detectada'}")
                
                self.results['technologies'] = tech
        
        except Exception as e:
            print(f"   ⚠️ Erro: {e}")
    
    async def _test_vulnerabilities_real(self):
        """
        Testa vulnerabilidades com VALIDATION ENGINE REAL
        
        SE HAS_VALIDATION = True:
            → USA SQLiEngine.test_url() (23 payloads)
            → USA XSSEngine.test_url() (21 payloads)
        
        SE HAS_VALIDATION = False:
            → Fallback com payloads básicos
        """
        print("\n3️⃣ Vulnerability Testing (VALIDATION ENGINE INTEGRADO)...")
        
        if HAS_VALIDATION and self.sqli_engine and self.xss_engine:
            # VALIDATION ENGINE REAL
            await self._test_with_validation_engine()
        else:
            # Fallback básico
            await self._test_with_fallback()
    
    async def _test_with_validation_engine(self):
        """
        USA VALIDATION ENGINE REAL (NÃO É PLACEHOLDER)
        
        Chama SQLiEngine.test_url() e XSSEngine.test_url()
        """
        print("   🧪 Usando Validation Engine REAL...")
        
        # SQLi Testing REAL
        print("      • SQL Injection (23 payloads)...")
        
        try:
            # Obter parâmetros testáveis
            test_params = await self._find_testable_params()
            
            if test_params:
                for param_data in test_params[:3]:  # Top 3 params
                    url = param_data['url']
                    param = param_data['param']
                    
                    # CHAMADA REAL ao Validation Engine
                    sqli_vulns = await self.sqli_engine.test_url(
                        session=self.session,
                        url=url,
                        param=param
                    )
                    
                    if sqli_vulns:
                        self.results['vulnerabilities'].extend(sqli_vulns)
                        print(f"         🚨 SQLi confirmado: {url}?{param}")
            else:
                print("         ℹ️ Nenhum parâmetro testável encontrado")
        
        except Exception as e:
            print(f"         ⚠️ Erro SQLi: {e}")
        
        # XSS Testing REAL
        print("      • Cross-Site Scripting (21 payloads)...")
        
        try:
            if test_params:
                for param_data in test_params[:3]:
                    url = param_data['url']
                    param = param_data['param']
                    
                    # CHAMADA REAL ao Validation Engine
                    xss_vulns = await self.xss_engine.test_url(
                        session=self.session,
                        url=url,
                        param=param
                    )
                    
                    if xss_vulns:
                        self.results['vulnerabilities'].extend(xss_vulns)
                        print(f"         🚨 XSS confirmado: {url}?{param}")
            else:
                print("         ℹ️ Nenhum parâmetro testável encontrado")
        
        except Exception as e:
            print(f"         ⚠️ Erro XSS: {e}")
    
    async def _test_with_fallback(self):
        """Fallback se Validation Engine não disponível"""
        print("   ⚠️ Usando fallback (payloads básicos)...")
        
        # SQLi básico
        sqli_payloads = ["' OR '1'='1", "' UNION SELECT NULL--"]
        
        try:
            async with self.session.get(self.base_url) as resp:
                baseline_len = len(await resp.text())
            
            for payload in sqli_payloads:
                test_url = f"{self.base_url}?id={payload}"
                
                try:
                    async with self.session.get(test_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        response_text = await resp.text()
                        
                        # Validação simples
                        if 'sql' in response_text.lower() or abs(len(response_text) - baseline_len) / baseline_len > 0.2:
                            self.results['vulnerabilities'].append({
                                'type': 'SQL Injection',
                                'severity': 'CRITICAL',
                                'url': test_url,
                                'payload': payload,
                                'validation': 'BASIC'
                            })
                            break
                except:
                    continue
        
        except:
            pass
    
    async def _find_testable_params(self) -> List[Dict]:
        """Encontra parâmetros testáveis"""
        params = []
        
        try:
            async with self.session.get(self.base_url) as resp:
                html = await resp.text()
                
                # Buscar forms
                forms = re.findall(r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>', html, re.I)
                
                for form_action in forms[:2]:
                    # Buscar inputs
                    inputs = re.findall(r'<input[^>]*name=["\']([^"\']*)["\'][^>]*>', html, re.I)
                    
                    for input_name in inputs[:2]:
                        params.append({
                            'url': self.base_url + form_action if form_action.startswith('/') else form_action,
                            'param': input_name
                        })
                
                # Parâmetros comuns
                if not params:
                    for common_param in ['id', 'page', 'query', 'search']:
                        params.append({
                            'url': self.base_url,
                            'param': common_param
                        })
        
        except:
            pass
        
        return params[:5]  # Top 5
    
    async def _test_security_headers(self):
        """Testa headers de segurança"""
        print("\n4️⃣ Security Headers Analysis...")
        
        required_headers = {
            'Strict-Transport-Security': 'HSTS não configurado',
            'X-Frame-Options': 'Clickjacking possível',
            'X-Content-Type-Options': 'MIME sniffing possível',
            'Content-Security-Policy': 'CSP não configurado'
        }
        
        try:
            async with self.session.get(self.base_url) as resp:
                headers = dict(resp.headers)
                
                missing = 0
                
                for header, description in required_headers.items():
                    if header not in headers:
                        self.results['vulnerabilities'].append({
                            'type': 'Missing Security Header',
                            'severity': 'MEDIUM',
                            'header': header,
                            'description': description,
                            'validation': 'CONFIRMED'
                        })
                        missing += 1
                
                if missing > 0:
                    print(f"   🚨 {missing} headers faltando")
                else:
                    print("   ✅ Headers OK")
        
        except:
            pass
    
    def _calculate_risk(self):
        """Calcula risk score REAL"""
        vulns = self.results['vulnerabilities']
        
        critical = len([v for v in vulns if v.get('severity') == 'CRITICAL'])
        high = len([v for v in vulns if v.get('severity') == 'HIGH'])
        medium = len([v for v in vulns if v.get('severity') == 'MEDIUM'])
        
        # Score: CRITICAL=10, HIGH=5, MEDIUM=2
        score = (critical * 10) + (high * 5) + (medium * 2)
        
        # Cap em 100
        score = min(score, 100)
        
        self.results['risk_score'] = score
        
        # Severity
        if score >= 80:
            severity = 'CRITICAL'
        elif score >= 60:
            severity = 'HIGH'
        elif score >= 30:
            severity = 'MEDIUM'
        else:
            severity = 'LOW'
        
        self.results['severity'] = severity


# CLI para testes
async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python3 libertus_scanner_final.py <target>")
        sys.exit(1)
    
    target = sys.argv[1]
    
    scanner = LibertusScannerFinal(target)
    result = await scanner.scan_complete()
    
    # Salvar resultado
    output_dir = Path.home() / "LIBERTUS" / "scans"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"scan_{target.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_file.write_text(json.dumps(result, indent=2))
    
    print(f"\n💾 Resultado salvo: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())
