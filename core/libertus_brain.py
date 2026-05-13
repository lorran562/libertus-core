#!/usr/bin/env python3
"""
LIBERTUS BRAIN - Motor de Raciocínio

OBJETIVO:
Libertus não só DETECTA bugs, ele ENTENDE bugs.

Para cada vulnerabilidade encontrada, o Brain explica:
1. Padrão identificado (o que é)
2. Como funciona tecnicamente (por que é vulnerável)
3. Impacto real (o que pode acontecer)
4. Como reproduzir (prova de conceito)
5. Correção específica (código correto)

Usa Groq API para gerar explicações profissionais.
"""

import os
import json
from typing import Dict, List, Optional
from groq import Groq

class LibertusBrain:
    """
    Motor de raciocínio que ENTENDE vulnerabilidades
    """
    
    def __init__(self):
        # Groq API (já configurado no Libertus)
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY não configurada")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        
        # Base de conhecimento OWASP Top 10
        self.knowledge_base = self._load_owasp_top10()
    
    def _load_owasp_top10(self) -> Dict:
        """Carrega conhecimento base OWASP Top 10"""
        return {
            "sqli": {
                "nome": "SQL Injection",
                "owasp": "A03:2021 – Injection",
                "cwe": "CWE-89",
                "descricao": "Permite executar comandos SQL maliciosos"
            },
            "xss": {
                "nome": "Cross-Site Scripting (XSS)",
                "owasp": "A03:2021 – Injection",
                "cwe": "CWE-79",
                "descricao": "Permite injetar JavaScript malicioso"
            },
            "broken_auth": {
                "nome": "Broken Authentication",
                "owasp": "A07:2021 – Identification and Authentication Failures",
                "cwe": "CWE-287",
                "descricao": "Falhas em autenticação e sessão"
            },
            "sensitive_data": {
                "nome": "Sensitive Data Exposure",
                "owasp": "A02:2021 – Cryptographic Failures",
                "cwe": "CWE-200",
                "descricao": "Exposição de dados sensíveis"
            },
            "broken_access": {
                "nome": "Broken Access Control",
                "owasp": "A01:2021 – Broken Access Control",
                "cwe": "CWE-639",
                "descricao": "Falhas em controle de acesso"
            }
        }
    
    def understand_vulnerability(self, vuln_type: str, context: Dict) -> Dict:
        """
        ENTENDE uma vulnerabilidade completamente
        
        Args:
            vuln_type: Tipo de vulnerabilidade (sqli, xss, etc)
            context: Contexto da vulnerabilidade (URL, payload, etc)
        
        Returns:
            Dict com explicação completa
        """
        
        # Busca conhecimento base
        base_knowledge = self.knowledge_base.get(vuln_type.lower(), {})
        
        # Monta prompt para Groq
        prompt = self._build_explanation_prompt(vuln_type, context, base_knowledge)
        
        # Chama Groq
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """Você é um especialista em segurança cibernética.
                        Explique vulnerabilidades de forma CLARA e PROFISSIONAL para clientes não-técnicos.
                        
                        SEMPRE inclua:
                        1. O que é (simples)
                        2. Como funciona (técnico mas compreensível)
                        3. Impacto real (em dinheiro e risco)
                        4. Prova de conceito (exemplo)
                        5. Correção (código específico)
                        
                        Use linguagem profissional mas acessível.
                        Mencione LGPD quando aplicável.
                        Calcule multas reais.
                        """
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Baixa temperatura = mais preciso
                max_tokens=1500
            )
            
            explanation = response.choices[0].message.content
            
            # Estrutura resposta
            return {
                "vulnerability_type": vuln_type,
                "owasp_category": base_knowledge.get("owasp", ""),
                "cwe": base_knowledge.get("cwe", ""),
                "explanation": self._parse_explanation(explanation),
                "context": context,
                "generated_by": "Libertus Brain v1.0"
            }
            
        except Exception as e:
            # Fallback se Groq falhar
            return self._fallback_explanation(vuln_type, context, base_knowledge)
    
    def _build_explanation_prompt(self, vuln_type: str, context: Dict, knowledge: Dict) -> str:
        """Constrói prompt para Groq"""
        
        url = context.get("url", "site do cliente")
        payload = context.get("payload", "")
        evidence = context.get("evidence", "")
        
        prompt = f"""Explique esta vulnerabilidade para um cliente empresarial:

VULNERABILIDADE: {knowledge.get('nome', vuln_type)}
OWASP: {knowledge.get('owasp', '')}
CWE: {knowledge.get('cwe', '')}

CONTEXTO:
- URL: {url}
- Payload testado: {payload}
- Evidência: {evidence}

Forneça explicação estruturada:

1. O QUE É:
(Explique em 1-2 frases simples)

2. COMO FUNCIONA:
(Explique tecnicamente mas de forma compreensível)

3. IMPACTO REAL:
(Consequências práticas: dados vazados, dinheiro perdido, multas LGPD)

4. PROVA DE CONCEITO:
(Demonstração simples de como explorar)

5. CORREÇÃO:
(Código específico para corrigir - antes/depois)
"""
        return prompt
    
    def _parse_explanation(self, text: str) -> Dict:
        """Parse resposta do Groq em estrutura"""
        
        sections = {
            "what_is": "",
            "how_it_works": "",
            "real_impact": "",
            "proof_of_concept": "",
            "fix": ""
        }
        
        # Parse simples por seções
        current_section = None
        
        for line in text.split('\n'):
            line = line.strip()
            
            if "O QUE É" in line.upper() or "WHAT IS" in line.upper():
                current_section = "what_is"
            elif "COMO FUNCIONA" in line.upper() or "HOW IT WORKS" in line.upper():
                current_section = "how_it_works"
            elif "IMPACTO" in line.upper() or "IMPACT" in line.upper():
                current_section = "real_impact"
            elif "PROVA" in line.upper() or "PROOF" in line.upper() or "POC" in line.upper():
                current_section = "proof_of_concept"
            elif "CORREÇÃO" in line.upper() or "FIX" in line.upper() or "SOLUTION" in line.upper():
                current_section = "fix"
            elif current_section and line:
                sections[current_section] += line + "\n"
        
        return sections
    
    def _fallback_explanation(self, vuln_type: str, context: Dict, knowledge: Dict) -> Dict:
        """Explicação fallback se Groq falhar"""
        
        templates = {
            "sqli": {
                "what_is": "SQL Injection permite executar comandos SQL não autorizados no banco de dados.",
                "how_it_works": "O sistema não valida entrada do usuário, permitindo quebrar a query SQL original e executar comandos maliciosos.",
                "real_impact": "Acesso total ao banco de dados, roubo de credenciais, exposição de dados de clientes. Multa LGPD: R$50.000 a R$50.000.000.",
                "proof_of_concept": f"Payload testado: {context.get('payload', '')} retornou dados não autorizados.",
                "fix": "Usar prepared statements: cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))"
            },
            "xss": {
                "what_is": "Cross-Site Scripting permite injetar JavaScript malicioso na página.",
                "how_it_works": "Input não sanitizado é renderizado diretamente no HTML, executando código JavaScript.",
                "real_impact": "Roubo de cookies, sessões, redirecionamento para sites maliciosos, phishing.",
                "proof_of_concept": f"Payload testado: {context.get('payload', '')} executou JavaScript.",
                "fix": "Sanitizar input: htmlspecialchars($input, ENT_QUOTES, 'UTF-8')"
            }
        }
        
        template = templates.get(vuln_type.lower(), {
            "what_is": f"Vulnerabilidade {vuln_type} detectada",
            "how_it_works": "Falha de validação permite comportamento não esperado",
            "real_impact": "Risco de segurança para dados e sistema",
            "proof_of_concept": f"Evidência: {context.get('evidence', '')}",
            "fix": "Implementar validação adequada e seguir OWASP guidelines"
        })
        
        return {
            "vulnerability_type": vuln_type,
            "owasp_category": knowledge.get("owasp", ""),
            "cwe": knowledge.get("cwe", ""),
            "explanation": template,
            "context": context,
            "generated_by": "Libertus Brain v1.0 (fallback)"
        }
    
    def generate_professional_report(self, vulnerability: Dict) -> str:
        """
        Gera relatório profissional em markdown
        """
        
        exp = vulnerability.get("explanation", {})
        ctx = vulnerability.get("context", {})
        
        report = f"""
## {vulnerability.get('vulnerability_type', 'Vulnerabilidade').upper()}

**Categoria OWASP:** {vulnerability.get('owasp_category', 'N/A')}  
**CWE:** {vulnerability.get('cwe', 'N/A')}  
**URL:** {ctx.get('url', 'N/A')}  

---

### 📋 O QUE É

{exp.get('what_is', '')}

---

### ⚙️ COMO FUNCIONA

{exp.get('how_it_works', '')}

---

### 💰 IMPACTO REAL

{exp.get('real_impact', '')}

---

### 🔬 PROVA DE CONCEITO

{exp.get('proof_of_concept', '')}

---

### ✅ CORREÇÃO

{exp.get('fix', '')}

---

*Análise gerada por: {vulnerability.get('generated_by', 'Libertus Brain')}*
"""
        
        return report


# CLI para testes
if __name__ == "__main__":
    brain = LibertusBrain()
    
    # Teste SQLi
    context = {
        "url": "https://example.com/buscar?nome=",
        "payload": "' OR '1'='1' --",
        "evidence": "Retornou todos os registros do banco"
    }
    
    print("🧠 LIBERTUS BRAIN - TESTE")
    print("=" * 60)
    print("")
    
    result = brain.understand_vulnerability("sqli", context)
    report = brain.generate_professional_report(result)
    
    print(report)
