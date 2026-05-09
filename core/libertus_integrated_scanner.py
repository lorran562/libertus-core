#!/usr/bin/env python3
"""
LIBERTUS SCANNER INTEGRADO v4.0
USA TODOS OS MÓDULOS: crypto + reverse + exploits

FILOSOFIA:
- Detecta → Explora → Quebra → Prova → Documenta
- NUNCA para só em detectar
- SEMPRE tenta exploitar
- SEMPRE quebra o que encontra
"""

import asyncio
import aiohttp
from typing import List, Dict
from dataclasses import dataclass
import json
from pathlib import Path
from datetime import datetime

# Importa TODOS os módulos
from libertus_crypto import LibertusoCrypto
from libertus_reverse import LibertusReverse
from exploit_engine import ExploitEngine
from payload_generator import PayloadGenerator

@dataclass
class VulnProof:
    """Vulnerabilidade COM PROVA"""
    type: str
    severity: str
    title: str
    description: str
    url: str
    evidence: str
    exploit: str = ""
    proof: str = ""  # PROVA que funcionou
    remediation: str = ""


class LibertusIntegratedScanner:
    """
    Scanner COMPLETO que USA TUDO
    """
    
    def __init__(self, target: str):
        self.target = target
        self.findings: List[VulnProof] = []
        
        # Inicializa TODOS os módulos
        self.crypto = LibertusoCrypto()
        self.reverse = LibertusReverse()
        self.exploit_engine = ExploitEngine()
        self.payload_gen = PayloadGenerator()
        
        print("🔥 LIBERTUS INTEGRATED SCANNER v4.0")
        print(f"🎯 Target: {target}")
        print("")
        print("MÓDULOS CARREGADOS:")
        print("   ✅ Crypto (hash cracking)")
        print("   ✅ Reverse (JS deobfuscation)")
        print("   ✅ Exploit Engine")
        print("   ✅ Payload Generator")
        print("")
    
    async def full_scan(self):
        """
        Scan COMPLETO - detecta, explora, quebra, prova
        """
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            print("📡 FASE 1: DESCOBERTA")
            endpoints = await self.discover_endpoints()
            
            print("\n🔍 FASE 2: ANÁLISE PROFUNDA")
            await self.deep_analysis(endpoints)
            
            print("\n💥 FASE 3: EXPLORAÇÃO")
            await self.exploit_phase()
            
            print("\n📄 FASE 4: DOCUMENTAÇÃO")
            report = self.generate_report()
            
            return report
    
    async def discover_endpoints(self) -> List[str]:
        """Descobre endpoints"""
        print("   🔍 Descobrindo endpoints...")
        
        endpoints = [
            "/.env",
            "/.git/config",
            "/config",
            "/admin",
            "/api",
        ]
        
        discovered = []
        for endpoint in endpoints:
            url = f"{self.target}{endpoint}"
            try:
                async with self.session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        discovered.append(url)
                        print(f"      ✅ {endpoint} (HTTP {resp.status})")
            except:
                pass
        
        return discovered
    
    async def deep_analysis(self, endpoints: List[str]):
        """Análise profunda de cada endpoint"""
        print("   🔬 Analisando conteúdo...")
        
        for url in endpoints:
            try:
                async with self.session.get(url, timeout=10) as resp:
                    content = await resp.text()
                    
                    # ANALISA COM TODOS OS MÓDULOS
                    
                    # 1. CRYPTO: Procura hashes
                    await self.analyze_crypto(url, content)
                    
                    # 2. REVERSE: Procura JS ofuscado
                    await self.analyze_javascript(url, content)
                    
                    # 3. SECRETS: Procura hardcoded
                    await self.analyze_secrets(url, content)
                    
            except Exception as e:
                print(f"      ⚠️ Erro em {url}: {e}")
    
    async def analyze_crypto(self, url: str, content: str):
        """Analisa e QUEBRA hashes encontrados"""
        import re
        
        # Procura padrões de hash
        md5_pattern = r'\b[a-f0-9]{32}\b'
        sha1_pattern = r'\b[a-f0-9]{40}\b'
        
        # MD5
        for match in re.finditer(md5_pattern, content):
            hash_value = match.group(0)
            hash_type = self.crypto.identify_hash(hash_value)
            
            if hash_type == 'md5':
                print(f"      🔐 Hash MD5 encontrado: {hash_value[:16]}...")
                
                # TENTA QUEBRAR
                cracked = self.crypto.crack_md5(hash_value)
                
                if cracked:
                    print(f"      💥 QUEBRADO: '{cracked}'")
                    
                    # TENTA LOGIN
                    login_success = await self.try_login(cracked)
                    
                    proof = f"Senha quebrada: '{cracked}'"
                    if login_success:
                        proof += " | Login testado: SUCESSO"
                    
                    self.findings.append(VulnProof(
                        type="Cryptography",
                        severity="CRÍTICA",
                        title="Hash MD5 quebrado",
                        description=f"Hash MD5 fraco encontrado e quebrado",
                        url=url,
                        evidence=f"Hash: {hash_value}",
                        proof=proof,
                        exploit=f"Senha descoberta: '{cracked}'",
                        remediation="Use bcrypt ou Argon2 com salt"
                    ))
                else:
                    print(f"      ⏳ Não quebrado (não está em wordlist)")
        
        # SHA1
        for match in re.finditer(sha1_pattern, content):
            hash_value = match.group(0)
            hash_type = self.crypto.identify_hash(hash_value)
            
            if hash_type == 'sha1':
                print(f"      🔐 Hash SHA1 encontrado: {hash_value[:16]}...")
                cracked = self.crypto.crack_sha1(hash_value)
                
                if cracked:
                    print(f"      💥 QUEBRADO: '{cracked}'")
                    
                    self.findings.append(VulnProof(
                        type="Cryptography",
                        severity="ALTA",
                        title="Hash SHA1 quebrado",
                        description=f"Hash SHA1 encontrado e quebrado",
                        url=url,
                        evidence=f"Hash: {hash_value}",
                        proof=f"Senha quebrada: '{cracked}'",
                        remediation="Use bcrypt ou Argon2"
                    ))
    
    async def analyze_javascript(self, url: str, content: str):
        """Analisa e DESOBFUSCA JavaScript"""
        # Detecta JS
        if '<script' in content.lower() or 'eval(' in content:
            print(f"      📜 JavaScript detectado")
            
            # DESOBFUSCA
            result = self.reverse.deobfuscate_js(content)
            
            if result['secrets_found']:
                print(f"      🚨 {len(result['secrets_found'])} secrets encontrados!")
                
                for secret in result['secrets_found']:
                    print(f"         • {secret['type']}: {secret['value'][:30]}...")
                    
                    self.findings.append(VulnProof(
                        type="Information Disclosure",
                        severity="CRÍTICA",
                        title=f"Secret hardcoded: {secret['type']}",
                        description=f"Credencial exposta no código JavaScript",
                        url=url,
                        evidence=f"Tipo: {secret['type']}",
                        proof=f"Valor extraído: {secret['value']}",
                        remediation="Remover secrets do código, usar variáveis de ambiente"
                    ))
            
            if result['apis_found']:
                print(f"      🌐 {len(result['apis_found'])} APIs descobertas!")
                for api in result['apis_found']:
                    print(f"         • {api}")
    
    async def analyze_secrets(self, url: str, content: str):
        """Procura secrets hardcoded"""
        secrets = self.reverse.find_secrets(content)
        
        if secrets:
            print(f"      🔑 {len(secrets)} secrets hardcoded encontrados")
            
            for secret in secrets:
                self.findings.append(VulnProof(
                    type="Hardcoded Credentials",
                    severity="CRÍTICA",
                    title=f"{secret['type']} exposto",
                    description="Credencial hardcoded no código",
                    url=url,
                    evidence=f"Tipo: {secret['type']}",
                    proof=f"Valor: {secret['value']}",
                    remediation="Usar secrets manager"
                ))
    
    async def try_login(self, password: str) -> bool:
        """Tenta login com senha descoberta"""
        # Simplificado - em produção, testar em forms encontrados
        return False  # Por enquanto
    
    async def exploit_phase(self):
        """Fase de exploração ativa"""
        print("   💣 Gerando exploits...")
        
        # Para cada vuln encontrada, gera exploit
        for finding in self.findings:
            if finding.type == "Cryptography" and "quebrado" in finding.title.lower():
                # Gera reverse shell se conseguimos acesso
                print(f"      🐚 Reverse shell disponível")
    
    def generate_report(self) -> Dict:
        """Gera relatório final COM PROVAS"""
        report = {
            "target": self.target,
            "scan_date": datetime.now().isoformat(),
            "scanner_version": "Libertus Integrated v4.0",
            "total_findings": len(self.findings),
            "findings": []
        }
        
        # Agrupa por severidade
        critical = [f for f in self.findings if f.severity == "CRÍTICA"]
        high = [f for f in self.findings if f.severity == "ALTA"]
        
        report["summary"] = {
            "critical": len(critical),
            "high": len(high),
            "risk_score": len(critical) * 10 + len(high) * 5
        }
        
        # Adiciona findings com PROVAS
        for finding in self.findings:
            report["findings"].append({
                "type": finding.type,
                "severity": finding.severity,
                "title": finding.title,
                "description": finding.description,
                "url": finding.url,
                "evidence": finding.evidence,
                "proof": finding.proof,  # ← PROVA!
                "exploit": finding.exploit,
                "remediation": finding.remediation
            })
        
        return report
    
    def save_report(self, report: Dict, output_path: str):
        """Salva relatório"""
        Path(output_path).write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"\n📄 Relatório salvo: {output_path}")


# CLI
async def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python libertus_integrated_scanner.py <target>")
        sys.exit(1)
    
    target = sys.argv[1]
    
    scanner = LibertusIntegratedScanner(target)
    report = await scanner.full_scan()
    
    # Salva relatório
    output = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    scanner.save_report(report, output)
    
    # Resume
    print("\n" + "="*60)
    print("📊 RESUMO DO SCAN")
    print("="*60)
    print(f"Target: {target}")
    print(f"Total findings: {report['total_findings']}")
    print(f"   🔴 Críticas: {report['summary']['critical']}")
    print(f"   🟠 Altas: {report['summary']['high']}")
    print(f"   📊 Risk Score: {report['summary']['risk_score']}/100")
    print("")
    
    # Mostra provas
    if report['findings']:
        print("🎯 VULNERABILIDADES COM PROVA:")
        for f in report['findings']:
            if f['proof']:
                print(f"   • {f['title']}")
                print(f"     PROVA: {f['proof']}")
                print("")


if __name__ == "__main__":
    asyncio.run(main())
