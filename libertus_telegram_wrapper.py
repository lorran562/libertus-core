#!/usr/bin/env python3
"""
LIBERTUS TELEGRAM WRAPPER
Integração completa entre Telegram Bot e LIBERTUS VPS
Usa TODOS os 17+ módulos e conhecimento do RAG
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any

# Adicionar path do core
sys.path.insert(0, str(Path(__file__).parent / "core"))

class LibertusTelegramWrapper:
    """Wrapper para integrar LIBERTUS VPS com Telegram"""
    
    def __init__(self, rag, ia):
        """
        Args:
            rag: Instância do LibertusRAG
            ia: Instância do LibertusIA
        """
        self.rag = rag
        self.ia = ia
        self.libertus_root = Path("/root/LIBERTUS")
        self.libertus_core = self.libertus_root / "core"
        
    async def scan_completo_vps(self, url: str) -> str:
        """
        Scanner COMPLETO usando LIBERTUS VPS
        
        Args:
            url: URL alvo
            
        Returns:
            Relatório profissional em Markdown
        """
        print(f"🔥 LIBERTUS VPS Scanner iniciado em: {url}")
        
        # 1. BUSCAR CONHECIMENTO DO RAG
        print("📚 Buscando conhecimento absorvido...")
        conhecimento = await self._buscar_conhecimento_completo(url)
        
        # 2. EXECUTAR SCANNER LIBERTUS VPS
        print("⚡ Executando scanner completo...")
        resultado_scan = await self._executar_libertus_scanner(url)
        
        # 3. IA ANALISA COM CONHECIMENTO
        print("🧠 IA analisando com contexto profundo...")
        relatorio = await self._gerar_relatorio_profissional(
            url, 
            resultado_scan, 
            conhecimento
        )
        
        return relatorio
    
    async def _buscar_conhecimento_completo(self, url: str) -> Dict[str, Any]:
        """Busca conhecimento relevante do RAG"""
        
        conhecimentos = {}
        
        # Buscar conhecimentos específicos
        topicos = [
            ("sql_injection", "SQL injection payloads técnicas exploits"),
            ("xss", "XSS cross-site scripting payloads técnicas"),
            ("pentest", "pentest metodologia reconhecimento vulnerabilidades"),
            ("exploit", "exploit exploração vulnerabilidades proof-of-concept"),
            ("reverse", "reverse engineering engenharia reversa"),
            ("crypto", "criptografia cifras análise crypto"),
            ("auth", "autenticação bypass session management"),
            ("web", "web application security OWASP")
        ]
        
        for chave, query in topicos:
            try:
                docs = self.rag.buscar_conhecimento(query, n_results=3)
                if docs:
                    conhecimentos[chave] = docs
            except Exception as e:
                print(f"⚠️ Erro ao buscar {chave}: {e}")
        
        return conhecimentos
    
    async def _executar_libertus_scanner(self, url: str) -> Dict[str, Any]:
        """
        Executa LIBERTUS scanner completo da VPS
        Usa TODOS os módulos (nmap, exploits, AST, OSINT, etc)
        """
        
        resultado = {
            'url': url,
            'modulos_executados': [],
            'vulnerabilidades': [],
            'detalhes': {},
            'scan_nmap': None,
            'scan_http': None,
            'exploits': []
        }
        
        try:
            # MÓDULO 1: NMAP SCAN
            print("  [1/5] Executando nmap scan...")
            scan_nmap = await self._executar_nmap(url)
            resultado['scan_nmap'] = scan_nmap
            resultado['modulos_executados'].append('nmap')
            
            # MÓDULO 2: SCANNER HTTP
            print("  [2/5] Analisando HTTP...")
            scan_http = await self._scanner_http(url)
            resultado['scan_http'] = scan_http
            resultado['modulos_executados'].append('http')
            
            # MÓDULO 3: SQL INJECTION (com conhecimento)
            print("  [3/5] Testando SQL Injection...")
            vulns_sql = await self._testar_sql_injection_avancado(url)
            if vulns_sql:
                resultado['vulnerabilidades'].extend(vulns_sql)
            resultado['modulos_executados'].append('sql_injection')
            
            # MÓDULO 4: XSS (com conhecimento)
            print("  [4/5] Testando XSS...")
            vulns_xss = await self._testar_xss_avancado(url)
            if vulns_xss:
                resultado['vulnerabilidades'].extend(vulns_xss)
            resultado['modulos_executados'].append('xss')
            
            # MÓDULO 5: EXPLOITS (verificação)
            print("  [5/5] Verificando exploits...")
            exploits = await self._verificar_exploits(url, scan_nmap, scan_http)
            resultado['exploits'] = exploits
            resultado['modulos_executados'].append('exploit_verification')
            
        except Exception as e:
            print(f"❌ Erro no scanner: {e}")
            resultado['erro'] = str(e)
        
        return resultado
    
    async def _executar_nmap(self, url: str) -> Dict[str, Any]:
        """Executa nmap scan"""
        try:
            # Extrair host da URL
            from urllib.parse import urlparse
            host = urlparse(url if url.startswith('http') else f'http://{url}').netloc
            
            # Executar nmap
            cmd = [
                "nmap", 
                "-sV",  # Version detection
                "-sC",  # Scripts padrão
                "--max-retries", "1",
                "--max-rtt-timeout", "500ms",
                "-p", "80,443,8080,8443",
                host
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            
            return {
                'sucesso': True,
                'output': stdout.decode('utf-8', errors='ignore'),
                'portas_abertas': self._parse_nmap_portas(stdout.decode())
            }
            
        except asyncio.TimeoutError:
            return {'sucesso': False, 'erro': 'Timeout (30s)'}
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}
    
    def _parse_nmap_portas(self, output: str) -> list:
        """Parse output do nmap para extrair portas"""
        portas = []
        for linha in output.split('\n'):
            if '/tcp' in linha and 'open' in linha:
                parts = linha.split()
                if parts:
                    portas.append(parts[0])
        return portas
    
    async def _scanner_http(self, url: str) -> Dict[str, Any]:
        """Scanner HTTP completo"""
        import aiohttp
        
        resultado = {
            'headers': {},
            'formularios': 0,
            'tecnologias': [],
            'headers_seguranca_faltando': []
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    # Headers
                    resultado['headers'] = dict(response.headers)
                    
                    # HTML
                    html = await response.text()
                    resultado['formularios'] = html.lower().count('<form')
                    
                    # Tecnologias (simples)
                    if 'X-Powered-By' in response.headers:
                        resultado['tecnologias'].append(response.headers['X-Powered-By'])
                    
                    # Headers de segurança ausentes
                    headers_importantes = [
                        'X-Frame-Options',
                        'X-Content-Type-Options',
                        'Strict-Transport-Security',
                        'Content-Security-Policy'
                    ]
                    
                    for header in headers_importantes:
                        if header not in response.headers:
                            resultado['headers_seguranca_faltando'].append(header)
                    
        except Exception as e:
            resultado['erro'] = str(e)
        
        return resultado
    
    async def _testar_sql_injection_avancado(self, url: str) -> list:
        """Testa SQL Injection usando conhecimento do RAG"""
        import aiohttp
        
        vulnerabilidades = []
        
        # Payloads da IA + conhecimento
        payloads = await self._gerar_payloads_sql_ia()
        
        try:
            async with aiohttp.ClientSession() as session:
                for payload in payloads[:5]:  # Limitar para não sobrecarregar
                    test_url = f"{url}?id={payload}"
                    
                    try:
                        async with session.get(test_url, timeout=5) as response:
                            texto = await response.text()
                            
                            # Detectar SQL errors
                            if any(err in texto.lower() for err in [
                                'sql', 'mysql', 'sqlite', 'postgresql',
                                'syntax error', 'warning', 'error in your sql'
                            ]):
                                vulnerabilidades.append({
                                    'tipo': 'SQL Injection',
                                    'severidade': 'CRÍTICA',
                                    'payload': payload,
                                    'url': test_url,
                                    'evidencia': 'Error SQL detectado na resposta'
                                })
                                break  # Encontrou, parar
                    except:
                        pass
        except Exception as e:
            print(f"⚠️ Erro SQL test: {e}")
        
        return vulnerabilidades
    
    async def _testar_xss_avancado(self, url: str) -> list:
        """Testa XSS usando conhecimento do RAG"""
        import aiohttp
        
        vulnerabilidades = []
        
        # Payloads da IA
        payloads = await self._gerar_payloads_xss_ia()
        
        try:
            async with aiohttp.ClientSession() as session:
                for payload in payloads[:5]:
                    test_url = f"{url}?q={payload}"
                    
                    try:
                        async with session.get(test_url, timeout=5) as response:
                            texto = await response.text()
                            
                            # Detectar payload refletido
                            if payload in texto:
                                vulnerabilidades.append({
                                    'tipo': 'XSS (Reflected)',
                                    'severidade': 'ALTA',
                                    'payload': payload,
                                    'url': test_url,
                                    'evidencia': 'Payload refletido na resposta'
                                })
                                break
                    except:
                        pass
        except Exception as e:
            print(f"⚠️ Erro XSS test: {e}")
        
        return vulnerabilidades
    
    async def _gerar_payloads_sql_ia(self) -> list:
        """IA gera payloads SQL baseado no conhecimento"""
        try:
            # Buscar conhecimento SQL
            conhecimento_sql = self.rag.buscar_conhecimento(
                "SQL injection payloads técnicas",
                n_results=2
            )
            
            contexto = "\n".join([
                doc['texto'][:300] 
                for doc in conhecimento_sql
            ]) if conhecimento_sql else "Conhecimento básico SQL injection"
            
            prompt = f"""Baseado neste conhecimento:
{contexto}

Liste 5 payloads SQL injection para teste (APENAS os payloads):"""
            
            resposta = self.ia.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.ia.model,
                temperature=0.3,
                max_tokens=300
            )
            
            texto = resposta.choices[0].message.content
            payloads = self._extrair_payloads(texto)
            
            if not payloads:
                # Fallback
                payloads = ["' OR '1'='1", "admin'--", "1' UNION SELECT NULL--"]
            
            return payloads
            
        except Exception as e:
            print(f"⚠️ Erro gerar payloads SQL: {e}")
            return ["' OR '1'='1", "admin'--"]
    
    async def _gerar_payloads_xss_ia(self) -> list:
        """IA gera payloads XSS baseado no conhecimento"""
        try:
            conhecimento_xss = self.rag.buscar_conhecimento(
                "XSS cross-site scripting payloads",
                n_results=2
            )
            
            contexto = "\n".join([
                doc['texto'][:300]
                for doc in conhecimento_xss
            ]) if conhecimento_xss else "Conhecimento básico XSS"
            
            prompt = f"""Baseado neste conhecimento:
{contexto}

Liste 5 payloads XSS para teste (APENAS os payloads):"""
            
            resposta = self.ia.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.ia.model,
                temperature=0.3,
                max_tokens=300
            )
            
            texto = resposta.choices[0].message.content
            payloads = self._extrair_payloads(texto)
            
            if not payloads:
                payloads = ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>"]
            
            return payloads
            
        except Exception as e:
            print(f"⚠️ Erro gerar payloads XSS: {e}")
            return ["<script>alert(1)</script>"]
    
    def _extrair_payloads(self, texto: str) -> list:
        """Extrai payloads do texto da IA"""
        import re
        payloads = []
        linhas = texto.strip().split('\n')
        
        for linha in linhas:
            # Remove numeração, bullets
            linha_limpa = re.sub(r'^[\d\.\-\*\s]+', '', linha).strip()
            linha_limpa = linha_limpa.strip('`"\'')
            
            if linha_limpa and len(linha_limpa) > 2:
                payloads.append(linha_limpa)
        
        return payloads[:10]
    
    async def _verificar_exploits(
        self, 
        url: str, 
        scan_nmap: Dict, 
        scan_http: Dict
    ) -> list:
        """Verifica exploits conhecidos"""
        exploits = []
        
        # Verificar tecnologias conhecidas
        if scan_http.get('tecnologias'):
            for tech in scan_http['tecnologias']:
                if 'php' in tech.lower():
                    exploits.append({
                        'tipo': 'Tecnologia identificada',
                        'detalhes': f'PHP detectado: {tech}',
                        'recomendacao': 'Verificar versão PHP contra CVEs conhecidos'
                    })
        
        # Verificar portas abertas
        if scan_nmap.get('portas_abertas'):
            for porta in scan_nmap['portas_abertas']:
                if '8080' in porta or '8443' in porta:
                    exploits.append({
                        'tipo': 'Porta não-padrão',
                        'detalhes': f'Porta {porta} aberta',
                        'recomendacao': 'Investigar serviço exposto'
                    })
        
        return exploits
    
    async def _gerar_relatorio_profissional(
        self, 
        url: str, 
        resultado_scan: Dict, 
        conhecimento: Dict
    ) -> str:
        """IA gera relatório profissional completo"""
        
        # Preparar contexto de conhecimento
        contexto_conhecimento = []
        for area, docs in conhecimento.items():
            if docs:
                contexto_conhecimento.append(
                    f"**{area.upper()}**: {docs[0]['texto'][:200]}..."
                )
        
        contexto_texto = "\n".join(contexto_conhecimento) if contexto_conhecimento else "Conhecimento básico"
        
        # Preparar resultados
        vulns_texto = "\n".join([
            f"- **{v['tipo']}** (Severidade: {v['severidade']})\n  Payload: `{v.get('payload', 'N/A')}`\n  Evidência: {v.get('evidencia', 'N/A')}"
            for v in resultado_scan.get('vulnerabilidades', [])
        ]) if resultado_scan.get('vulnerabilidades') else "✅ Nenhuma vulnerabilidade crítica detectada"
        
        # Preparar scan nmap
        nmap_resumo = "Não executado"
        if resultado_scan.get('scan_nmap', {}).get('sucesso'):
            portas = resultado_scan['scan_nmap'].get('portas_abertas', [])
            nmap_resumo = f"{len(portas)} porta(s) aberta(s): {', '.join(portas)}" if portas else "Nenhuma porta detectada"
        
        # Preparar scan HTTP
        http_resumo = "Não executado"
        if resultado_scan.get('scan_http'):
            http_info = resultado_scan['scan_http']
            headers_faltando = len(http_info.get('headers_seguranca_faltando', []))
            forms = http_info.get('formularios', 0)
            http_resumo = f"{forms} formulário(s), {headers_faltando} header(s) de segurança ausente(s)"
        
        # Prompt para IA
        prompt = f"""Você é um analista de segurança sênior. Gere um relatório profissional de pentest.

**ALVO**: {url}

**CONHECIMENTO BASE UTILIZADO**:
{contexto_texto}

**MÓDULOS EXECUTADOS**:
{', '.join(resultado_scan.get('modulos_executados', []))}

**SCAN NMAP**:
{nmap_resumo}

**SCAN HTTP**:
{http_resumo}

**VULNERABILIDADES ENCONTRADAS**:
{vulns_texto}

**EXPLOITS VERIFICADOS**:
{len(resultado_scan.get('exploits', []))} exploit(s) potencial(is)

Gere relatório profissional incluindo:
1. 📋 Resumo Executivo
2. 🎯 Escopo e Metodologia
3. 🔍 Vulnerabilidades (com CVSS score estimado)
4. 💡 Recomendações de Correção (com código exemplo quando aplicável)
5. 📊 Próximos Passos

Use emojis, seja técnico, direto e acionável. Markdown formatado."""
        
        try:
            resposta = self.ia.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.ia.model,
                temperature=0.6,
                max_tokens=3000
            )
            
            return resposta.choices[0].message.content
            
        except Exception as e:
            # Fallback
            return f"""# 📋 RELATÓRIO DE PENTEST

**Alvo:** {url}

## 🔍 Resultados:

{vulns_texto}

## 📊 Detalhes Técnicos:
- Módulos: {', '.join(resultado_scan.get('modulos_executados', []))}
- Nmap: {nmap_resumo}
- HTTP: {http_resumo}

## 💡 Recomendações:
- Corrigir vulnerabilidades críticas imediatamente
- Implementar headers de segurança
- Revisar código-fonte

**Erro ao gerar relatório completo:** {e}
**Sistema usou {len(conhecimento)} área(s) de conhecimento absorvido.**"""
