#!/usr/bin/env python3
"""
LIBERTUS GITHUB SECRET SCANNER

Varre repositórios GitHub procurando:
1. API keys em código
2. Secrets em commits antigos
3. Senhas hardcoded
4. Tokens de acesso
5. Credenciais AWS, Stripe, etc
"""

import asyncio
import aiohttp
import re
from typing import List, Dict
import base64


class LibertusGitHubScanner:
    """Scanner de secrets em repositórios GitHub"""
    
    def __init__(self):
        # Patterns de secrets (do libertus_reverse.py)
        self.secret_patterns = {
            'aws_access_key': r'AKIA[0-9A-Z]{16}',
            'aws_secret_key': r'[0-9a-zA-Z/+=]{40}',
            'stripe_key': r'sk_live_[0-9a-zA-Z]{24,}',
            'github_token': r'ghp_[0-9a-zA-Z]{36}',
            'slack_token': r'xox[baprs]-[0-9a-zA-Z-]+',
            'google_api': r'AIza[0-9A-Za-z\\-_]{35}',
            'private_key': r'-----BEGIN (RSA|OPENSSH|DSA|EC|PGP) PRIVATE KEY-----',
            'jwt': r'eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*',
            'password': r'(?i)(password|passwd|pwd)\s*[:=]\s*["\']?([^"\'\s]+)',
            'api_key': r'(?i)(api[_-]?key|apikey)\s*[:=]\s*["\']?([^"\'\s]+)',
        }
    
    async def scan_repo(self, repo_url: str) -> List[Dict]:
        """Scan repositório GitHub completo"""
        
        secrets_found = []
        
        print(f"🔍 Scanning GitHub repo: {repo_url}")
        
        # Parse repo owner/name
        parts = repo_url.replace('https://github.com/', '').split('/')
        if len(parts) < 2:
            print("   ❌ URL inválida")
            return secrets_found
        
        owner = parts[0]
        repo = parts[1]
        
        # 1. Scan código atual
        print("\n📂 Scanning current code...")
        code_secrets = await self._scan_code(owner, repo)
        secrets_found.extend(code_secrets)
        
        # 2. Scan commits (últimos 100)
        print("\n📜 Scanning commit history...")
        commit_secrets = await self._scan_commits(owner, repo)
        secrets_found.extend(commit_secrets)
        
        print(f"\n✅ Total secrets found: {len(secrets_found)}")
        
        return secrets_found
    
    async def _scan_code(self, owner: str, repo: str) -> List[Dict]:
        """Scan código atual do repo"""
        
        secrets = []
        
        async with aiohttp.ClientSession() as session:
            # Lista arquivos do repo
            url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/main?recursive=1"
            
            try:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        print(f"   ⚠️ Não foi possível acessar repo (status {resp.status})")
                        return secrets
                    
                    data = await resp.json()
                    tree = data.get('tree', [])
                    
                    # Filtra apenas arquivos de código
                    code_files = [
                        f for f in tree 
                        if f.get('type') == 'blob' and 
                        any(f['path'].endswith(ext) for ext in [
                            '.js', '.py', '.php', '.java', '.go',
                            '.env', '.config', '.yaml', '.yml', '.json'
                        ])
                    ]
                    
                    print(f"   📄 {len(code_files)} code files to scan")
                    
                    # Scan cada arquivo (limita a 50 para não demorar muito)
                    for file_info in code_files[:50]:
                        file_secrets = await self._scan_file(session, owner, repo, file_info)
                        secrets.extend(file_secrets)
            
            except Exception as e:
                print(f"   ⚠️ Error scanning code: {e}")
        
        return secrets
    
    async def _scan_file(self, session, owner: str, repo: str, file_info: Dict) -> List[Dict]:
        """Scan arquivo individual"""
        
        secrets = []
        path = file_info['path']
        
        try:
            # Pega conteúdo do arquivo
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
            
            async with session.get(url) as resp:
                if resp.status != 200:
                    return secrets
                
                data = await resp.json()
                content = data.get('content', '')
                
                # Decode base64
                try:
                    decoded = base64.b64decode(content).decode('utf-8')
                except:
                    return secrets
                
                # Procura secrets
                for secret_type, pattern in self.secret_patterns.items():
                    matches = re.findall(pattern, decoded)
                    
                    for match in matches:
                        # Match pode ser tuple (quando tem grupos)
                        if isinstance(match, tuple):
                            match = match[1] if len(match) > 1 else match[0]
                        
                        secrets.append({
                            'type': f'github_{secret_type}',
                            'file': path,
                            'value': match[:50] + '...' if len(match) > 50 else match,
                            'severity': 'CRITICAL'
                        })
                        
                        print(f"      💥 {secret_type.upper()} in {path}")
        
        except Exception as e:
            pass
        
        return secrets
    
    async def _scan_commits(self, owner: str, repo: str) -> List[Dict]:
        """Scan histórico de commits"""
        
        secrets = []
        
        async with aiohttp.ClientSession() as session:
            # Lista commits
            url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=100"
            
            try:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        return secrets
                    
                    commits = await resp.json()
                    
                    print(f"   📝 Scanning {len(commits)} commits...")
                    
                    # Scan mensagens de commit (rápido)
                    for commit in commits:
                        msg = commit.get('commit', {}).get('message', '')
                        
                        # Procura secrets em mensagens
                        for secret_type, pattern in self.secret_patterns.items():
                            matches = re.findall(pattern, msg)
                            
                            for match in matches:
                                if isinstance(match, tuple):
                                    match = match[1] if len(match) > 1 else match[0]
                                
                                secrets.append({
                                    'type': f'github_{secret_type}_commit',
                                    'commit': commit.get('sha', '')[:8],
                                    'message': msg[:100],
                                    'value': match[:50] + '...',
                                    'severity': 'CRITICAL'
                                })
                                
                                print(f"      💥 {secret_type.upper()} in commit {commit.get('sha', '')[:8]}")
            
            except Exception as e:
                print(f"   ⚠️ Error scanning commits: {e}")
        
        return secrets


async def main():
    """Teste"""
    scanner = LibertusGitHubScanner()
    
    # Scan repo de exemplo
    secrets = await scanner.scan_repo("https://github.com/AikidoSec/safe-chain")
    
    print("\n" + "="*60)
    print(f"✅ Secrets found: {len(secrets)}")
    
    for secret in secrets[:10]:  # Primeiros 10
        print(f"\n🔓 {secret['type']}")
        print(f"   File/Commit: {secret.get('file', secret.get('commit', 'N/A'))}")
        print(f"   Value: {secret['value']}")


if __name__ == "__main__":
    asyncio.run(main())
