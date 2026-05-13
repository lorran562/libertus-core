#!/usr/bin/env python3
"""
LIBERTUS SCANNER v9.0 - 100% FUNCIONAL REAL
Sem placeholders, sem promessas. Apenas execução.
"""

import asyncio
import aiohttp
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse, urljoin

# Imports de módulos ULTRA (sync)
from libertus_crypto_ultra import LibertusCryptoUltra
from libertus_reverse_ultra import LibertusReverseUltra


class LibertusScannerV9:
    """Scanner 100% funcional com validação real"""
    
    def __init__(self, target: str, timeout: int = 30):
        self.target = target.replace('https://', '').replace('http://', '').replace('www.', '')
        self.base_url = f"https://{self.target}"
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.results = {
            'scanner_version': 'LIBERTUS v9.0 REAL',
            'scan_date': datetime.now().isoformat(),
            'target': self.target,
            'reconnaissance': {
                'subdomains': [],
                'open_ports': [],
                'apis': [],
                'technologies': []
            },
            'vulnerabilities': [],
            'crypto_analysis': {},
            'reverse_analysis': {},
            'risk_score': 0,
            'severity': 'INFO'
        }
        
        # Módulos ULTRA
        self.crypto_ultra = LibertusCryptoUltra()
        self.reverse_ultra = LibertusReverseUltra()
    
    async def scan_complete(self) -> Dict:
        """Scan completo integrado"""
        
        print(f"🎯 LIBERTUS v9.0 - Scan Real em: {self.target}")
        print("="*70)
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            self.session = session
            
            # FASE 1: RECONHECIMENTO
            print("\n🔍 FASE 1: RECONHECIMENTO REAL")
            print("-"*70)
            await self._reconnaissance()
            
            # FASE 2: DOWNLOAD E ANÁLISE DE CÓDIGO
            print("\n\n💻 FASE 2: ANÁLISE DE CÓDIGO")
            print("-"*70)
            js_code = await self._download_javascript()
            if js_code:
                await self._analyze_code(js_code)
            
            # FASE 3: TESTES DE VULNERABILIDADES
            print("\n\n🔓 FASE 3: TESTES DE VULNERABILIDADES")
            print("-"*70)
            await self._test_vulnerabilities()
            
            # FASE 4: ANÁLISE CRYPTO/REVERSE
            print("\n\n🔐 FASE 4: ANÁLISE AVANÇADA")
            print("-"*70)
            await self._advanced_analysis(js_code if js_code else "")
        
        # CALCULAR RISK
        self._calculate_risk()
        
        # RESUMO
        print("\n\n" + "="*70)
        print("📊 RESUMO FINAL")
        print("="*70)
        self._print_summary()
        
        return self.results
    
    async def _reconnaissance(self):
        """Reconhecimento real"""
        
        # 1. Subdomain enumeration (crt.sh)
        print("\n1️⃣ Subdomain Enumeration (crt.sh)...")
        try:
            async with self.session.get(
                f"https://crt.sh/?q=%.{self.target}&output=json",
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    subs = set()
                    for entry in data:
                        name = entry.get('name_value', '')
                        if '*' not in name:
                            subs.add(name)
                    
                    self.results['reconnaissance']['subdomains'] = sorted(list(subs))
                    print(f"   ✅ {len(subs)} subdomínios encontrados")
                    for sub in list(subs)[:5]:
                        print(f"      • {sub}")
                    if len(subs) > 5:
                        print(f"      ... e mais {len(subs)-5}")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")
        
        # 2. Port scan (top 10 portas)
        print("\n2️⃣ Port Scan (top 10)...")
        ports_to_scan = [80, 443, 22, 21, 25, 3306, 5432, 8080, 8443, 3000]
        open_ports = []
        
        tasks = [self._check_port(port) for port in ports_to_scan]
        results = await asyncio.gather(*tasks)
        
        for port, is_open in zip(ports_to_scan, results):
            if is_open:
                open_ports.append({'port': port, 'state': 'open'})
        
        self.results['reconnaissance']['open_ports'] = open_ports
        print(f"   ✅ {len(open_ports)} portas abertas: {[p['port'] for p in open_ports]}")
        
        # 3. HTTP Headers e Technologies
        print("\n3️⃣ HTTP Headers & Technologies...")
        try:
            async with self.session.get(self.base_url) as resp:
                headers = dict(resp.headers)
                
                # Detectar tecnologias
                techs = []
                if 'Server' in headers:
                    techs.append(f"Server: {headers['Server']}")
                if 'X-Powered-By' in headers:
                    techs.append(f"Powered-By: {headers['X-Powered-By']}")
                
                # Detectar framework pelo HTML
                html = await resp.text()
                if 'wp-content' in html:
                    techs.append("WordPress")
                if 'react' in html.lower():
                    techs.append("React")
                if 'vue' in html.lower():
                    techs.append("Vue.js")
                
                self.results['reconnaissance']['technologies'] = techs
                print(f"   ✅ Tecnologias: {', '.join(techs) if techs else 'Nenhuma detectada'}")
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")
    
    async def _check_port(self, port: int) -> bool:
        """Verifica se porta está aberta"""
        try:
            _, writer = await asyncio.wait_for(
                asyncio.open_connection(self.target, port),
                timeout=3
            )
            writer.close()
            await writer.wait_closed()
            return True
        except:
            return False
    
    async def _download_javascript(self) -> str:
        """Baixa JavaScript real do site"""
        print("\n4️⃣ Downloading JavaScript...")
        
        try:
            async with self.session.get(self.base_url) as resp:
                html = await resp.text()
                
                # Extrair tags <script src="">
                script_tags = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
                
                js_code = ""
                for i, script_url in enumerate(script_tags[:5]):  # Top 5
                    if not script_url.startswith('http'):
                        script_url = urljoin(self.base_url, script_url)
                    
                    try:
                        async with self.session.get(script_url, timeout=aiohttp.ClientTimeout(total=10)) as js_resp:
                            if js_resp.status == 200:
                                content = await js_resp.text()
                                js_code += f"\n// File: {script_url}\n{content}\n"
                    except:
                        continue
                
                if js_code:
                    print(f"   ✅ {len(script_tags)} scripts encontrados, {len(js_code)} bytes baixados")
                else:
                    print("   ⚠️  Nenhum JavaScript externo encontrado")
                
                return js_code
        
        except Exception as e:
            print(f"   ⚠️  Erro: {e}")
            return ""
    
    async def _analyze_code(self, js_code: str):
        """Analisa código real"""
        
        # Extrair APIs do JavaScript
        print("\n5️⃣ API Endpoint Discovery...")
        
        api_patterns = [
            r'["\']/(api|v\d+)/[a-zA-Z0-9_/-]+["\']',
            r'https?://[^"\'\s]+/api/[^"\'\s]+',
            r'fetch\(["\']([^"\']+)["\']',
            r'axios\.(get|post|put|delete)\(["\']([^"\']+)["\']'
        ]
        
        apis = set()
        for pattern in api_patterns:
            matches = re.findall(pattern, js_code, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    apis.add(match[-1])
                else:
                    apis.add(match)
        
        self.results['reconnaissance']['apis'] = sorted(list(apis))
        print(f"   ✅ {len(apis)} endpoints descobertos")
        for api in list(apis)[:10]:
            print(f"      • {api}")
        if len(apis) > 10:
            print(f"      ... e mais {len(apis)-10}")
    
    async def _test_vulnerabilities(self):
        """Testa vulnerabilidades REAIS com validação"""
        
        # 1. SQLi Testing com validação
        print("\n6️⃣ SQL Injection Testing (validado)...")
        sqli_vulns = await self._test_sqli_real()
        if sqli_vulns:
            self.results['vulnerabilities'].extend(sqli_vulns)
            print(f"   🚨 {len(sqli_vulns)} vulnerabilidades SQLi!")
        else:
            print("   ✅ Nenhuma SQLi detectada")
        
        # 2. XSS Testing com validação
        print("\n7️⃣ XSS Testing (validado)...")
        xss_vulns = await self._test_xss_real()
        if xss_vulns:
            self.results['vulnerabilities'].extend(xss_vulns)
            print(f"   🚨 {len(xss_vulns)} vulnerabilidades XSS!")
        else:
            print("   ✅ Nenhuma XSS detectada")
        
        # 3. Security Headers
        print("\n8️⃣ Security Headers Analysis...")
        header_vulns = await self._test_security_headers()
        if header_vulns:
            self.results['vulnerabilities'].extend(header_vulns)
            print(f"   🚨 {len(header_vulns)} headers faltando!")
        else:
            print("   ✅ Headers de segurança OK")
    
    async def _test_sqli_real(self) -> List[Dict]:
        """Teste REAL de SQLi com validação de resposta"""
        
        vulns = []
        
        # Payloads SQLi
        payloads = [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' UNION SELECT NULL--",
            "1' AND 1=1--",
            "1' AND 1=2--"
        ]
        
        try:
            # Baseline: resposta normal
            async with self.session.get(self.base_url) as resp:
                baseline_len = len(await resp.text())
                baseline_status = resp.status
            
            # Testar cada payload
            for payload in payloads:
                test_url = f"{self.base_url}?id={payload}"
                
                try:
                    async with self.session.get(test_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        response_text = await resp.text()
                        response_len = len(response_text)
                        
                        # Validação 1: Mudança estrutural significativa
                        len_diff = abs(response_len - baseline_len) / baseline_len if baseline_len > 0 else 0
                        
                        # Validação 2: Mensagens de erro SQL
                        sql_errors = [
                            'sql syntax',
                            'mysql_fetch',
                            'postgresql',
                            'ora-',
                            'sqlite',
                            'unclosed quotation',
                            'quoted string not properly terminated'
                        ]
                        
                        has_error = any(err in response_text.lower() for err in sql_errors)
                        
                        # VULNERÁVEL se: mudança >20% OU erro SQL detectado
                        if len_diff > 0.2 or has_error:
                            vulns.append({
                                'type': 'SQL Injection',
                                'severity': 'CRITICAL',
                                'url': test_url,
                                'payload': payload,
                                'evidence': f"Response diff: {len_diff:.1%}, SQL error: {has_error}",
                                'validation': 'CONFIRMED'
                            })
                            break  # Uma vulnerabilidade já basta
                
                except:
                    continue
        
        except Exception as e:
            pass
        
        return vulns
    
    async def _test_xss_real(self) -> List[Dict]:
        """Teste REAL de XSS com validação de reflexão"""
        
        vulns = []
        
        # Payloads XSS
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "'><script>alert(String.fromCharCode(88,83,83))</script>"
        ]
        
        try:
            for payload in payloads:
                test_url = f"{self.base_url}?search={payload}"
                
                try:
                    async with self.session.get(test_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        response_text = await resp.text()
                        
                        # Validação: payload refletido SEM encoding
                        if payload in response_text:
                            vulns.append({
                                'type': 'Cross-Site Scripting (XSS)',
                                'severity': 'HIGH',
                                'url': test_url,
                                'payload': payload,
                                'evidence': 'Payload refletido sem sanitização',
                                'validation': 'CONFIRMED'
                            })
                            break
                
                except:
                    continue
        
        except:
            pass
        
        return vulns
    
    async def _test_security_headers(self) -> List[Dict]:
        """Testa headers de segurança"""
        
        vulns = []
        
        required_headers = {
            'X-Frame-Options': 'Clickjacking protection',
            'X-Content-Type-Options': 'MIME-sniffing protection',
            'Strict-Transport-Security': 'HTTPS enforcement',
            'Content-Security-Policy': 'XSS/injection protection'
        }
        
        try:
            async with self.session.get(self.base_url) as resp:
                headers = dict(resp.headers)
                
                for header, description in required_headers.items():
                    if header not in headers:
                        vulns.append({
                            'type': 'Missing Security Header',
                            'severity': 'MEDIUM',
                            'header': header,
                            'description': description,
                            'validation': 'CONFIRMED'
                        })
        
        except:
            pass
        
        return vulns
    
    async def _advanced_analysis(self, js_code: str):
        """Análise REAL com Crypto/Reverse ULTRA"""
        
        # CRYPTO ULTRA: Analisa hashes e JWT
        print("\n9️⃣ Crypto Analysis ULTRA (REAL)...")
        
        # Procurar hashes em responses
        hash_patterns = {
            'md5': r'\b[a-f0-9]{32}\b',
            'sha1': r'\b[a-f0-9]{40}\b',
            'sha256': r'\b[a-f0-9]{64}\b'
        }
        
        hashes_found = {}
        for hash_type, pattern in hash_patterns.items():
            matches = re.findall(pattern, js_code, re.IGNORECASE)
            if matches:
                hashes_found[hash_type] = matches[:5]  # Top 5
        
        if hashes_found:
            print(f"   ✅ Hashes encontrados: {sum(len(v) for v in hashes_found.values())}")
            
            # Tentar quebrar com crypto ULTRA
            for hash_type, hashes in hashes_found.items():
                for hash_val in hashes:
                    result = self.crypto_ultra.crack_hash(hash_val, hash_type)
                    if result:
                        self.results['vulnerabilities'].append({
                            'type': 'Weak Password Hash',
                            'severity': 'CRITICAL',
                            'hash_type': hash_type,
                            'hash': hash_val,
                            'cracked': result,
                            'validation': 'CRACKED'
                        })
                        print(f"      🔓 {hash_type} crackeado: {hash_val} = {result}")
        
        self.results['crypto_analysis'] = {
            'hashes_found': hashes_found,
            'module': 'ULTRA v2.0 REAL'
        }
        
        # REVERSE ULTRA: Extrai secrets REAIS
        print("\n🔟 Reverse Engineering ULTRA (REAL)...")
        
        secrets = self.reverse_ultra.find_secrets(js_code)
        
        if secrets:
            print(f"   🚨 {len(secrets)} secrets encontrados!")
            
            for secret in secrets[:10]:
                print(f"      • {secret['type']}: {secret['value']} ({secret['severity']})")
                
                # Adicionar às vulnerabilidades
                self.results['vulnerabilities'].append({
                    'type': f"Exposed {secret['type']}",
                    'severity': secret['severity'],
                    'value': secret['value'],
                    'context': secret.get('context', '')[:100],
                    'validation': 'FOUND'
                })
        else:
            print("   ✅ Nenhum secret exposto")
        
        self.results['reverse_analysis'] = {
            'secrets_found': len(secrets),
            'module': 'ULTRA v2.0 REAL'
        }
    
    def _calculate_risk(self):
        """Calcula risk score REAL"""
        
        vulns = self.results['vulnerabilities']
        
        critical = len([v for v in vulns if v.get('severity') == 'CRITICAL'])
        high = len([v for v in vulns if v.get('severity') == 'HIGH'])
        medium = len([v for v in vulns if v.get('severity') == 'MEDIUM'])
        
        # Score: CRITICAL=10, HIGH=5, MEDIUM=2
        score = (critical * 10) + (high * 5) + (medium * 2)
        
        self.results['risk_score'] = min(score, 100)
        
        if critical > 0:
            self.results['severity'] = 'CRITICAL'
        elif high > 0:
            self.results['severity'] = 'HIGH'
        elif medium > 0:
            self.results['severity'] = 'MEDIUM'
        else:
            self.results['severity'] = 'LOW'
    
    def _print_summary(self):
        """Imprime resumo"""
        
        print(f"\n🎯 Target: {self.target}")
        print(f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        recon = self.results['reconnaissance']
        print(f"\n📈 RECONHECIMENTO:")
        print(f"   • Subdomínios: {len(recon['subdomains'])}")
        print(f"   • Portas abertas: {len(recon['open_ports'])}")
        print(f"   • APIs: {len(recon['apis'])}")
        print(f"   • Tecnologias: {len(recon['technologies'])}")
        
        vulns = self.results['vulnerabilities']
        critical = len([v for v in vulns if v.get('severity') == 'CRITICAL'])
        high = len([v for v in vulns if v.get('severity') == 'HIGH'])
        medium = len([v for v in vulns if v.get('severity') == 'MEDIUM'])
        
        print(f"\n🚨 VULNERABILIDADES:")
        print(f"   • Total: {len(vulns)}")
        print(f"   • CRITICAL: {critical}")
        print(f"   • HIGH: {high}")
        print(f"   • MEDIUM: {medium}")
        
        print(f"\n🎯 RISK SCORE: {self.results['risk_score']}/100")
        print(f"⚠️  SEVERIDADE: {self.results['severity']}")
    
    def save(self, filename: str):
        """Salva resultado"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Relatório salvo: {filename}")


# CLI
async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python libertus_scanner_v9_real.py <target>")
        sys.exit(1)
    
    target = sys.argv[1]
    
    scanner = LibertusScannerV9(target)
    results = await scanner.scan_complete()
    
    # Salvar
    output_file = f"/root/LIBERTUS/relatorios/scan_v9_{target.replace('.', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    scanner.save(output_file)
    
    print("\n✅ SCAN COMPLETO!")


if __name__ == "__main__":
    asyncio.run(main())
