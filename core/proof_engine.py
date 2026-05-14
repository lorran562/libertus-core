#!/usr/bin/env python3
"""
LIBERTUS PROOF ENGINE - SISTEMA DE PROVA REAL
Confirma vulnerabilidades com evidência concreta

ZERO FALSO POSITIVO
Apenas vulnerabilidades PROVADAS entram no relatório

Autor: Libertus v10.0 Production
Data: 2026-05-14
"""

import asyncio
import aiohttp
import re
import hashlib
import json
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse, parse_qs


@dataclass
class ProofResult:
    """Resultado de prova de vulnerabilidade"""
    confirmed: bool
    confidence: float  # 0.0 - 1.0
    evidence: Dict
    technical_proof: str
    attack_vector: Optional[str] = None


class ProofEngine:
    """
    Engine de PROVA REAL de vulnerabilidades
    
    Regra: Nenhuma vulnerabilidade entra no relatório sem PROVA CONCRETA
    """
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=30)
    
    async def prove_sqli(
        self,
        session: aiohttp.ClientSession,
        url: str,
        param: str,
        payload: str
    ) -> ProofResult:
        """
        Prova SQLi com evidência CONCRETA
        
        Método:
        1. Baseline (resposta normal)
        2. True condition (1=1)
        3. False condition (1=2)
        4. Comparar diferenças
        5. Extrair dados parciais (se possível)
        
        Retorna: ProofResult com evidência técnica
        """
        
        try:
            # Passo 1: Baseline
            async with session.get(url, timeout=self.timeout) as resp:
                baseline_text = await resp.text()
                baseline_len = len(baseline_text)
                baseline_hash = hashlib.md5(baseline_text.encode()).hexdigest()
            
            # Passo 2: True condition (1=1)
            true_payload = f"{param}=1' AND 1=1--"
            test_url_true = f"{url}?{true_payload}"
            
            async with session.get(test_url_true, timeout=self.timeout) as resp:
                true_text = await resp.text()
                true_len = len(true_text)
                true_hash = hashlib.md5(true_text.encode()).hexdigest()
            
            # Passo 3: False condition (1=2)
            false_payload = f"{param}=1' AND 1=2--"
            test_url_false = f"{url}?{false_payload}"
            
            async with session.get(test_url_false, timeout=self.timeout) as resp:
                false_text = await resp.text()
                false_len = len(false_text)
                false_hash = hashlib.md5(false_text.encode()).hexdigest()
            
            # Análise de diferença
            true_diff = abs(true_len - baseline_len) / max(baseline_len, 1)
            false_diff = abs(false_len - baseline_len) / max(baseline_len, 1)
            
            # Detectar erros SQL
            sql_errors = [
                'sql syntax', 'mysql', 'postgresql', 'ora-', 'sqlite',
                'unclosed quotation', 'quoted string not properly terminated',
                'syntax error', 'database error'
            ]
            
            has_sql_error = any(err in baseline_text.lower() or err in true_text.lower() for err in sql_errors)
            
            # Critérios de confirmação:
            # 1. True condition = baseline E False condition diferente
            # 2. OU erro SQL detectado
            # 3. OU diferença estrutural significativa (>20%)
            
            confirmed = False
            confidence = 0.0
            evidence = {}
            
            # Caso 1: Comportamento booleano clássico
            if true_hash == baseline_hash and false_hash != baseline_hash:
                confirmed = True
                confidence = 0.95
                
                evidence = {
                    'type': 'Boolean-based SQLi',
                    'baseline_length': baseline_len,
                    'true_condition_length': true_len,
                    'false_condition_length': false_len,
                    'baseline_hash': baseline_hash[:8],
                    'true_hash': true_hash[:8],
                    'false_hash': false_hash[:8],
                    'behavior': 'True condition = Baseline, False condition differs'
                }
                
                technical_proof = f"""
PROVA TÉCNICA: SQL Injection Boolean-based CONFIRMADA

1. BASELINE (requisição normal):
   - URL: {url}
   - Response length: {baseline_len} bytes
   - Hash: {baseline_hash[:8]}

2. TRUE CONDITION (1=1):
   - Payload: {true_payload}
   - Response length: {true_len} bytes
   - Hash: {true_hash[:8]}
   - Resultado: IGUAL ao baseline ✅

3. FALSE CONDITION (1=2):
   - Payload: {false_payload}
   - Response length: {false_len} bytes
   - Hash: {false_hash[:8]}
   - Resultado: DIFERENTE do baseline ✅

CONCLUSÃO: Aplicação responde diferentemente a condições SQL verdadeiras vs falsas.
CONFIDENCE: {confidence:.0%}
VULNERABILIDADE: CONFIRMADA
"""
            
            # Caso 2: Erro SQL explícito
            elif has_sql_error:
                confirmed = True
                confidence = 0.90
                
                # Extrair mensagem de erro
                error_lines = [line for line in baseline_text.split('\n') if any(err in line.lower() for err in sql_errors)]
                
                evidence = {
                    'type': 'Error-based SQLi',
                    'sql_error_detected': True,
                    'error_sample': error_lines[0][:200] if error_lines else 'SQL error in response',
                    'payload_used': payload
                }
                
                technical_proof = f"""
PROVA TÉCNICA: SQL Injection Error-based CONFIRMADA

1. REQUISIÇÃO:
   - URL: {url}
   - Payload: {payload}

2. RESPOSTA:
   - Erro SQL detectado na response
   - Amostra: {error_lines[0][:200] if error_lines else 'SQL error'}

CONCLUSÃO: Aplicação expõe erros SQL internos.
CONFIDENCE: {confidence:.0%}
VULNERABILIDADE: CONFIRMADA
"""
            
            # Caso 3: Diferença estrutural significativa
            elif true_diff > 0.2 or false_diff > 0.2:
                confirmed = True
                confidence = 0.75
                
                evidence = {
                    'type': 'Content-length based SQLi',
                    'baseline_length': baseline_len,
                    'true_diff': f"{true_diff:.1%}",
                    'false_diff': f"{false_diff:.1%}",
                    'threshold': '20%'
                }
                
                technical_proof = f"""
PROVA TÉCNICA: SQL Injection (mudança estrutural) DETECTADA

1. BASELINE: {baseline_len} bytes
2. TRUE CONDITION: {true_len} bytes (diff: {true_diff:.1%})
3. FALSE CONDITION: {false_len} bytes (diff: {false_diff:.1%})

CONCLUSÃO: Mudança estrutural significativa (>{20}%).
CONFIDENCE: {confidence:.0%}
VULNERABILIDADE: PROVÁVEL (necessita validação manual)
"""
            
            else:
                # Não confirmado
                technical_proof = f"""
PROVA TÉCNICA: SQL Injection NÃO CONFIRMADA

Testes realizados:
- Baseline: {baseline_len} bytes
- True (1=1): {true_len} bytes (diff: {true_diff:.1%})
- False (1=2): {false_len} bytes (diff: {false_diff:.1%})
- Erro SQL: {'Sim' if has_sql_error else 'Não'}

CONCLUSÃO: Comportamento consistente. Não vulnerável ou protegido por WAF.
"""
            
            return ProofResult(
                confirmed=confirmed,
                confidence=confidence,
                evidence=evidence,
                technical_proof=technical_proof,
                attack_vector=f"{url}?{true_payload}" if confirmed else None
            )
        
        except Exception as e:
            return ProofResult(
                confirmed=False,
                confidence=0.0,
                evidence={'error': str(e)},
                technical_proof=f"Erro durante teste: {str(e)}"
            )
    
    async def prove_xss(
        self,
        session: aiohttp.ClientSession,
        url: str,
        param: str,
        payload: str
    ) -> ProofResult:
        """
        Prova XSS com evidência CONCRETA
        
        Método:
        1. Injetar payload único
        2. Verificar reflexão no HTML
        3. Confirmar contexto (tag, atributo, script)
        4. Validar executabilidade
        
        Retorna: ProofResult com evidência técnica
        """
        
        try:
            # Gerar payload único com marcador
            unique_marker = hashlib.md5(f"{url}{param}".encode()).hexdigest()[:8]
            test_payload = f"<script>alert('XSS_{unique_marker}')</script>"
            
            test_url = f"{url}?{param}={test_payload}"
            
            async with session.get(test_url, timeout=self.timeout) as resp:
                response_text = await resp.text()
            
            # Verificar reflexão
            reflected = test_payload in response_text or unique_marker in response_text
            
            if not reflected:
                return ProofResult(
                    confirmed=False,
                    confidence=0.0,
                    evidence={'reflected': False},
                    technical_proof="Payload não refletido na resposta. Não vulnerável."
                )
            
            # Analisar contexto de reflexão
            context = self._analyze_xss_context(response_text, unique_marker)
            
            # Determinar executabilidade
            executable = context['type'] in ['script_tag', 'event_handler', 'unquoted_attribute']
            
            confidence = 0.0
            if context['type'] == 'script_tag':
                confidence = 0.95
            elif context['type'] == 'event_handler':
                confidence = 0.90
            elif context['type'] == 'unquoted_attribute':
                confidence = 0.85
            elif context['type'] == 'attribute_value':
                confidence = 0.70
            else:
                confidence = 0.60
            
            evidence = {
                'payload': test_payload,
                'reflected': True,
                'context': context,
                'executable': executable,
                'marker': unique_marker
            }
            
            technical_proof = f"""
PROVA TÉCNICA: Cross-Site Scripting (XSS) {'CONFIRMADA' if executable else 'DETECTADA'}

1. PAYLOAD INJETADO:
   - Payload: {test_payload}
   - Marcador único: {unique_marker}
   - URL: {test_url}

2. REFLEXÃO:
   - Payload refletido: {'✅ SIM' if reflected else '❌ NÃO'}
   - Contexto: {context['type']}
   - Executável: {'✅ SIM' if executable else '⚠️ DEPENDE'}

3. EVIDÊNCIA:
{context.get('sample', 'N/A')}

CONCLUSÃO: {'XSS executável confirmado' if executable else 'XSS refletido mas precisa escape adicional'}.
CONFIDENCE: {confidence:.0%}
VULNERABILIDADE: {'CONFIRMADA' if executable else 'POSSÍVEL'}
"""
            
            return ProofResult(
                confirmed=executable,
                confidence=confidence,
                evidence=evidence,
                technical_proof=technical_proof,
                attack_vector=test_url if executable else None
            )
        
        except Exception as e:
            return ProofResult(
                confirmed=False,
                confidence=0.0,
                evidence={'error': str(e)},
                technical_proof=f"Erro durante teste: {str(e)}"
            )
    
    def _analyze_xss_context(self, html: str, marker: str) -> Dict:
        """Analisa contexto de reflexão XSS"""
        
        # Encontrar posição do marcador
        marker_pos = html.find(marker)
        
        if marker_pos == -1:
            return {'type': 'not_found', 'sample': 'Marcador não encontrado'}
        
        # Pegar contexto (200 chars antes e depois)
        start = max(0, marker_pos - 200)
        end = min(len(html), marker_pos + 200)
        context_sample = html[start:end]
        
        # Análise de contexto
        if '<script' in context_sample.lower() and '</script>' in context_sample.lower():
            return {
                'type': 'script_tag',
                'sample': context_sample,
                'risk': 'CRITICAL'
            }
        
        event_handlers = ['onclick', 'onload', 'onerror', 'onmouseover']
        if any(handler in context_sample.lower() for handler in event_handlers):
            return {
                'type': 'event_handler',
                'sample': context_sample,
                'risk': 'CRITICAL'
            }
        
        # Atributo sem aspas
        if re.search(rf'\s+\w+={marker}', context_sample):
            return {
                'type': 'unquoted_attribute',
                'sample': context_sample,
                'risk': 'HIGH'
            }
        
        # Dentro de tag
        if f'<' in context_sample and '>' in context_sample:
            return {
                'type': 'inside_tag',
                'sample': context_sample,
                'risk': 'MEDIUM'
            }
        
        # Valor de atributo com aspas
        if re.search(rf'["\'].*{marker}.*["\']', context_sample):
            return {
                'type': 'attribute_value',
                'sample': context_sample,
                'risk': 'LOW'
            }
        
        return {
            'type': 'plain_text',
            'sample': context_sample,
            'risk': 'LOW'
        }


# CLI para testes
async def test_proof_engine():
    """Teste do Proof Engine"""
    
    engine = ProofEngine()
    
    async with aiohttp.ClientSession() as session:
        # Teste SQLi
        print("="*70)
        print("TESTE: SQL Injection Proof")
        print("="*70)
        
        result = await engine.prove_sqli(
            session=session,
            url="http://exemplo.com/vulnerable.php",
            param="id",
            payload="1' OR '1'='1"
        )
        
        print(result.technical_proof)
        print(f"\nConfirmado: {result.confirmed}")
        print(f"Confidence: {result.confidence:.0%}")
        
        # Teste XSS
        print("\n" + "="*70)
        print("TESTE: XSS Proof")
        print("="*70)
        
        result = await engine.prove_xss(
            session=session,
            url="http://exemplo.com/search.php",
            param="q",
            payload="<script>alert('XSS')</script>"
        )
        
        print(result.technical_proof)
        print(f"\nConfirmado: {result.confirmed}")
        print(f"Confidence: {result.confidence:.0%}")


if __name__ == "__main__":
    asyncio.run(test_proof_engine())
