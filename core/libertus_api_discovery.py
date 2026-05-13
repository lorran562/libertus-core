#!/usr/bin/env python3
"""
LIBERTUS API ENDPOINT DISCOVERY

Descobre endpoints de API usando:
1. JavaScript parsing (fetch, axios, XMLHttpRequest)
2. Swagger/OpenAPI discovery
3. GraphQL introspection
4. Common API paths
5. Fuzzing inteligente
"""

import asyncio
import aiohttp
import re
from typing import List, Set, Dict
from urllib.parse import urljoin


class LibertusAPIDiscovery:
    """Descoberta avançada de endpoints de API"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.endpoints: Set[str] = set()
        
        # Common API paths
        self.common_paths = [
            '/api',
            '/api/v1',
            '/api/v2',
            '/v1',
            '/v2',
            '/rest',
            '/graphql',
            '/swagger.json',
            '/openapi.json',
            '/api-docs',
            '/docs',
            '/api/docs',
        ]
        
        # Common API endpoints
        self.common_endpoints = [
            'users', 'user', 'auth', 'login', 'logout',
            'register', 'profile', 'account', 'settings',
            'admin', 'dashboard', 'search', 'data',
            'posts', 'comments', 'products', 'items',
            'orders', 'payments', 'upload', 'download',
        ]
    
    async def discover_all(self) -> List[str]:
        """Descobre TODOS endpoints"""
        
        print(f"🔍 Discovering API endpoints: {self.base_url}")
        print("="*60)
        
        # 1. JavaScript parsing
        await self._discover_from_javascript()
        
        # 2. Swagger/OpenAPI
        await self._discover_swagger()
        
        # 3. GraphQL
        await self._discover_graphql()
        
        # 4. Common paths fuzzing
        await self._fuzz_common_paths()
        
        print(f"\n✅ Total endpoints discovered: {len(self.endpoints)}")
        
        return sorted(list(self.endpoints))
    
    async def _discover_from_javascript(self):
        """Parse JavaScript procurando endpoints"""
        
        print("\n📜 Parsing JavaScript...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, timeout=10) as resp:
                    html = await resp.text()
                    
                    # Encontra scripts
                    script_pattern = r'<script[^>]*src=["\']([^"\']+)["\']'
                    scripts = re.findall(script_pattern, html)
                    
                    # Inline scripts
                    inline_pattern = r'<script[^>]*>(.*?)</script>'
                    inline_scripts = re.findall(inline_pattern, html, re.DOTALL)
                    
                    # Parse cada script
                    for script_url in scripts[:20]:  # Limita a 20
                        full_url = urljoin(self.base_url, script_url)
                        await self._parse_script(session, full_url)
                    
                    # Parse inline scripts
                    for script in inline_scripts:
                        self._extract_endpoints_from_js(script)
                    
                    print(f"   ✅ {len(self.endpoints)} endpoints from JS")
            
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
    
    async def _parse_script(self, session, url: str):
        """Parse arquivo JavaScript"""
        
        try:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    js_code = await resp.text()
                    self._extract_endpoints_from_js(js_code)
        except:
            pass
    
    def _extract_endpoints_from_js(self, js_code: str):
        """Extrai endpoints de código JavaScript"""
        
        # Patterns de API calls
        patterns = [
            r'fetch\(["\']([^"\']+)["\']',
            r'axios\.(?:get|post|put|delete)\(["\']([^"\']+)["\']',
            r'XMLHttpRequest.*?open\(["\'](?:GET|POST|PUT|DELETE)["\']\s*,\s*["\']([^"\']+)["\']',
            r'\.(?:get|post|put|delete)\(["\']([^"\']+)["\']',
            r'url:\s*["\']([^"\']+)["\']',
            r'endpoint:\s*["\']([^"\']+)["\']',
            r'path:\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, js_code, re.IGNORECASE)
            
            for match in matches:
                # Limpa e valida
                endpoint = match.strip()
                
                if endpoint.startswith('/') or endpoint.startswith('http'):
                    # Remove template vars
                    endpoint = re.sub(r'\$\{[^}]+\}', ':id', endpoint)
                    endpoint = re.sub(r'\{[^}]+\}', ':id', endpoint)
                    
                    self.endpoints.add(endpoint)
    
    async def _discover_swagger(self):
        """Descobre via Swagger/OpenAPI"""
        
        print("\n📖 Checking Swagger/OpenAPI...")
        
        swagger_urls = [
            '/swagger.json',
            '/openapi.json',
            '/api-docs',
            '/api/swagger.json',
            '/api/openapi.json',
            '/v1/swagger.json',
            '/v2/swagger.json',
        ]
        
        async with aiohttp.ClientSession() as session:
            for path in swagger_urls:
                url = urljoin(self.base_url, path)
                
                try:
                    async with session.get(url, timeout=5) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            
                            # Parse OpenAPI spec
                            paths = data.get('paths', {})
                            
                            for path_key in paths.keys():
                                self.endpoints.add(path_key)
                            
                            print(f"   ✅ Found Swagger at {path}")
                            print(f"   📊 {len(paths)} endpoints")
                            
                            break
                
                except:
                    continue
    
    async def _discover_graphql(self):
        """Descobre GraphQL endpoints"""
        
        print("\n🔮 Checking GraphQL...")
        
        graphql_paths = [
            '/graphql',
            '/api/graphql',
            '/v1/graphql',
            '/query',
        ]
        
        async with aiohttp.ClientSession() as session:
            for path in graphql_paths:
                url = urljoin(self.base_url, path)
                
                # Introspection query
                query = {
                    'query': '''
                    {
                        __schema {
                            queryType { name }
                            mutationType { name }
                        }
                    }
                    '''
                }
                
                try:
                    async with session.post(url, json=query, timeout=5) as resp:
                        if resp.status == 200:
                            self.endpoints.add(path)
                            print(f"   ✅ GraphQL found at {path}")
                            break
                
                except:
                    continue
    
    async def _fuzz_common_paths(self):
        """Fuzzing de caminhos comuns"""
        
        print("\n🔨 Fuzzing common API paths...")
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # Testa base paths
            for base in self.common_paths:
                for endpoint in self.common_endpoints:
                    path = f"{base}/{endpoint}"
                    tasks.append(self._check_endpoint(session, path))
            
            # Executa em batches
            for i in range(0, len(tasks), 20):
                batch = tasks[i:i+20]
                await asyncio.gather(*batch, return_exceptions=True)
        
        print(f"   ✅ Fuzzing complete")
    
    async def _check_endpoint(self, session, path: str):
        """Verifica se endpoint existe"""
        
        url = urljoin(self.base_url, path)
        
        try:
            async with session.get(url, timeout=3) as resp:
                # 200-299 = existe
                # 401/403 = existe mas protegido
                # 404/405 = não existe
                if resp.status < 500 and resp.status != 404:
                    self.endpoints.add(path)
                    print(f"   ✅ {path} [{resp.status}]")
        
        except:
            pass


async def main():
    """Teste"""
    discovery = LibertusAPIDiscovery("https://app.aikido.dev")
    endpoints = await discovery.discover_all()
    
    print("\n" + "="*60)
    print("🎯 API ENDPOINTS:")
    for ep in endpoints[:20]:
        print(f"   • {ep}")


if __name__ == "__main__":
    asyncio.run(main())
