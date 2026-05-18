#!/usr/bin/env python3
"""
LIBERTUS SCANNER INTELIGENTE
Scanner que usa conhecimento absorvido de PDFs para encontrar vulnerabilidades
Quanto mais PDFs, mais vulnerabilidades ele encontra!
"""

import re
import asyncio
import aiohttp
from typing import List, Dict, Any
from urllib.parse import urlparse, urljoin

class LibertusScannerInteligente:
    """Scanner que evolui com conhecimento absorvido"""
    
    def __init__(self, rag, ia):
        """
        Inicializa scanner inteligente
        
        Args:
            rag: Instância do LibertusRAG
            ia: Instância do LibertusIA
        """
        self.rag = rag
        self.ia = ia
        self.resultados = {}
    
    async def scan_completo(self, url: str) -> Dict[str, Any]:
        """
        Scanner inteligente completo usando conhecimento do RAG
        
        Args:
            url: URL do site alvo
            
        Returns:
            Relatório completo gerado pela IA
        """
        print(f"🔍 Iniciando scan inteligente em: {url}")
        
        self.resultados = {
            'url': url,
            'vulnerabilidades': [],
            'detalhes': {}
        }
        
        # 1. BUSCAR CONHECIMENTO NO RAG
        print("📚 Buscando conhecimento absorvido...")
        conhecimento_sql = self.rag.buscar_conhecimento("SQL injection payloads técnicas", n_results=3)
        conhecimento_xss = self.rag.buscar_conhecimento("XSS cross-site scripting payloads", n_results=3)
        conhecimento_auth = self.rag.buscar_conhecimento("autenticação bypass vulnerabilidades", n_results=3)
        conhecimento_geral = self.rag.buscar_conhecimento("vulnerabilidades web pentest", n_results=5)
        
        # 2. IA GERA PAYLOADS BASEADO NO CONHECIMENTO
        print("🧠 IA gerando payloads baseado nos PDFs...")
        payloads = await self._gerar_payloads_inteligentes(
            conhecimento_sql, 
            conhecimento_xss,
            conhecimento_auth
        )
        
        # 3. TESTAR SITE
        print(f"⚡ Testando {len(payloads)} vulnerabilidades...")
        async with aiohttp.ClientSession() as session:
            # Testar SQL Injection
            await self._testar_sql_injection(session, url, payloads.get('sql', []))
            
            # Testar XSS
            await self._testar_xss(session, url, payloads.get('xss', []))
            
            # Análise de headers
            await self._analisar_headers(session, url)
            
            # Descobrir formulários
            await self._analisar_formularios(session, url)
        
        # 4. IA ANALISA RESULTADOS
        print("📊 IA analisando resultados...")
        relatorio = await self._gerar_relatorio_inteligente(conhecimento_geral)
        
        return relatorio
    
    async def _gerar_payloads_inteligentes(
        self, 
        conhecimento_sql: List[Dict],
        conhecimento_xss: List[Dict],
        conhecimento_auth: List[Dict]
    ) -> Dict[str, List[str]]:
        """IA gera payloads baseado no conhecimento absorvido"""
        
        # Contexto de SQL
        contexto_sql = "\n".join([doc['texto'][:500] for doc in conhecimento_sql]) if conhecimento_sql else "Conhecimento básico de SQL injection"
        
        # Contexto de XSS
        contexto_xss = "\n".join([doc['texto'][:500] for doc in conhecimento_xss]) if conhecimento_xss else "Conhecimento básico de XSS"
        
        # Prompt para IA gerar payloads
        prompt_sql = f"""Baseado neste conhecimento sobre SQL Injection:
{contexto_sql}

Liste 5 payloads SQL injection para testar (APENAS os payloads, sem explicação):"""

        prompt_xss = f"""Baseado neste conhecimento sobre XSS:
{contexto_xss}

Liste 5 payloads XSS para testar (APENAS os payloads, sem explicação):"""
        
        try:
            # IA gera payloads SQL
            resposta_sql = self.ia.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt_sql}],
                model=self.ia.model,
                temperature=0.3,
                max_tokens=500
            )
            payloads_sql_text = resposta_sql.choices[0].message.content
            payloads_sql = self._extrair_payloads(payloads_sql_text)
            
            # IA gera payloads XSS
            resposta_xss = self.ia.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt_xss}],
                model=self.ia.model,
                temperature=0.3,
                max_tokens=500
            )
            payloads_xss_text = resposta_xss.choices[0].message.content
            payloads_xss = self._extrair_payloads(payloads_xss_text)
            
        except Exception as e:
            print(f"⚠️ Erro ao gerar payloads com IA: {e}")
            # Fallback: payloads básicos
            payloads_sql = ["' OR '1'='1", "admin'--", "1' UNION SELECT NULL--"]
            payloads_xss = ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"]
        
        return {
            'sql': payloads_sql,
            'xss': payloads_xss
        }
    
    def _extrair_payloads(self, texto: str) -> List[str]:
        """Extrai payloads do texto gerado pela IA"""
        payloads = []
        linhas = texto.strip().split('\n')
        
        for linha in linhas:
            # Remove numeração, bullets, etc
            linha_limpa = re.sub(r'^[\d\.\-\*\s]+', '', linha).strip()
            linha_limpa = linha_limpa.strip('`"\'')
            
            if linha_limpa and len(linha_limpa) > 2:
                payloads.append(linha_limpa)
        
        return payloads[:10]  # Máximo 10 payloads
    
    async def _testar_sql_injection(self, session: aiohttp.ClientSession, url: str, payloads: List[str]):
        """Testa SQL Injection"""
        if not payloads:
            return
        
        for payload in payloads:
            try:
                # Testar na URL
                test_url = f"{url}?id={payload}"
                async with session.get(test_url, timeout=10) as response:
                    texto = await response.text()
                    
                    # Detectar sinais de SQL injection
                    if any(erro in texto.lower() for erro in ['sql', 'mysql', 'sqlite', 'postgresql', 'syntax error', 'warning']):
                        self.resultados['vulnerabilidades'].append({
                            'tipo': 'SQL Injection',
                            'severidade': 'CRÍTICA',
                            'payload': payload,
                            'local': test_url
                        })
                        break  # Encontrou, não precisa testar mais
            except Exception:
                pass
    
    async def _testar_xss(self, session: aiohttp.ClientSession, url: str, payloads: List[str]):
        """Testa XSS"""
        if not payloads:
            return
        
        for payload in payloads:
            try:
                # Testar na URL
                test_url = f"{url}?q={payload}"
                async with session.get(test_url, timeout=10) as response:
                    texto = await response.text()
                    
                    # Detectar se payload foi refletido
                    if payload in texto:
                        self.resultados['vulnerabilidades'].append({
                            'tipo': 'XSS (Cross-Site Scripting)',
                            'severidade': 'ALTA',
                            'payload': payload,
                            'local': test_url
                        })
                        break
            except Exception:
                pass
    
    async def _analisar_headers(self, session: aiohttp.ClientSession, url: str):
        """Analisa headers de segurança"""
        try:
            async with session.get(url, timeout=10) as response:
                headers = response.headers
                
                # Headers de segurança importantes
                headers_seguranca = {
                    'X-Frame-Options': 'Proteção contra Clickjacking',
                    'X-Content-Type-Options': 'Proteção contra MIME sniffing',
                    'Strict-Transport-Security': 'Força HTTPS',
                    'Content-Security-Policy': 'Proteção XSS',
                    'X-XSS-Protection': 'Proteção XSS (legado)'
                }
                
                faltando = []
                for header, descricao in headers_seguranca.items():
                    if header not in headers:
                        faltando.append(f"{header} ({descricao})")
                
                if faltando:
                    self.resultados['vulnerabilidades'].append({
                        'tipo': 'Headers de Segurança Ausentes',
                        'severidade': 'MÉDIA',
                        'detalhes': faltando
                    })
                
                self.resultados['detalhes']['headers'] = dict(headers)
        except Exception as e:
            print(f"⚠️ Erro ao analisar headers: {e}")
    
    async def _analisar_formularios(self, session: aiohttp.ClientSession, url: str):
        """Descobre e analisa formulários"""
        try:
            async with session.get(url, timeout=10) as response:
                texto = await response.text()
                
                # Contar formulários
                num_forms = texto.lower().count('<form')
                
                if num_forms > 0:
                    self.resultados['detalhes']['formularios_encontrados'] = num_forms
                    
                    # Verificar se formulários usam HTTPS
                    if 'http://' in url and '<form' in texto.lower():
                        self.resultados['vulnerabilidades'].append({
                            'tipo': 'Formulários em HTTP',
                            'severidade': 'ALTA',
                            'detalhes': f'{num_forms} formulário(s) em conexão não-segura'
                        })
        except Exception as e:
            print(f"⚠️ Erro ao analisar formulários: {e}")
    
    async def _gerar_relatorio_inteligente(self, conhecimento_geral: List[Dict]) -> str:
        """IA gera relatório profissional baseado nos resultados"""
        
        # Preparar contexto
        contexto_conhecimento = "\n".join([
            f"- {doc['texto'][:300]}" 
            for doc in conhecimento_geral[:3]
        ]) if conhecimento_geral else "Conhecimento básico de pentest"
        
        # Preparar resultados
        vulns_texto = "\n".join([
            f"- {v['tipo']} (Severidade: {v['severidade']})"
            for v in self.resultados['vulnerabilidades']
        ]) if self.resultados['vulnerabilidades'] else "Nenhuma vulnerabilidade detectada"
        
        prompt = f"""Você é um analista de segurança experiente.

CONHECIMENTO BASE:
{contexto_conhecimento}

SCAN REALIZADO EM: {self.resultados['url']}

VULNERABILIDADES ENCONTRADAS:
{vulns_texto}

DETALHES TÉCNICOS:
- Formulários: {self.resultados['detalhes'].get('formularios_encontrados', 0)}
- Headers analisados: Sim

Gere um relatório profissional de pentest incluindo:
1. Resumo executivo
2. Vulnerabilidades encontradas (com severidade e impacto)
3. Recomendações de correção
4. Próximos passos

Seja técnico, direto e profissional."""
        
        try:
            resposta = self.ia.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.ia.model,
                temperature=0.5,
                max_tokens=2000
            )
            
            return resposta.choices[0].message.content
            
        except Exception as e:
            # Fallback: relatório básico
            return f"""# RELATÓRIO DE PENTEST

**Alvo:** {self.resultados['url']}

## Vulnerabilidades Encontradas:
{vulns_texto}

## Recomendações:
- Corrigir vulnerabilidades críticas imediatamente
- Implementar headers de segurança
- Revisar código-fonte

Erro ao gerar relatório completo: {e}"""
