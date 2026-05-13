#!/usr/bin/env python3
"""
LIBERTUS PORT SCANNER + TECHNOLOGY DETECTION

Descobre:
1. Portas abertas (top 100)
2. Serviços rodando
3. Tecnologias usadas (Wappalyzer-style)
4. CMS detection
5. Framework detection
"""

import asyncio
import socket
import re
from typing import Dict, List
import aiohttp


class LibertusPortScanner:
    """Scanner de portas e tecnologias"""
    
    # Top 100 portas mais comuns
    COMMON_PORTS = [
        21, 22, 23, 25, 53, 80, 110, 111, 135, 139,
        143, 443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080,
        8443, 8000, 8888, 9000, 9090, 27017, 5432, 6379, 11211,
        # Web específicas
        81, 280, 300, 591, 593, 832, 981, 1010, 1311,
        2082, 2087, 2095, 2096, 2480, 3000, 3128, 3333, 4243,
        4567, 4711, 4712, 4993, 5000, 5104, 5108, 5800, 6543,
        7000, 7396, 7474, 8001, 8008, 8014, 8042, 8069, 8081,
        8088, 8090, 8091, 8118, 8123, 8172, 8222, 8243, 8280,
        8281, 8333, 8500, 8834, 8880, 8887, 8983, 9043, 9060,
        9080, 9090, 9091, 9200, 9443, 9800, 9943, 9980, 9981,
        12443, 16080, 18091, 18092, 20720, 28017
    ]
    
    def __init__(self, target: str):
        self.target = target.replace('https://', '').replace('http://', '').split('/')[0]
        self.open_ports: List[int] = []
        self.technologies: Dict = {}
    
    async def scan_all(self) -> Dict:
        """Scan completo"""
        
        print(f"🔍 Scanning {self.target}")
        print("="*60)
        
        # 1. Port scan
        await self._scan_ports()
        
        # 2. Technology detection
        await self._detect_technologies()
        
        return {
            "target": self.target,
            "open_ports": self.open_ports,
            "technologies": self.technologies
        }
    
    async def _scan_ports(self):
        """Scan portas TCP"""
        
        print("\n🔌 Port Scanning (top 100)...")
        
        tasks = []
        
        for port in self.COMMON_PORTS:
            tasks.append(self._check_port(port))
        
        # Executa em batches
        for i in range(0, len(tasks), 50):
            batch = tasks[i:i+50]
            await asyncio.gather(*batch, return_exceptions=True)
        
        print(f"   ✅ {len(self.open_ports)} portas abertas")
    
    async def _check_port(self, port: int):
        """Verifica se porta está aberta"""
        
        try:
            # Timeout muito curto para speed
            conn = asyncio.open_connection(self.target, port)
            reader, writer = await asyncio.wait_for(conn, timeout=1)
            
            writer.close()
            await writer.wait_closed()
            
            self.open_ports.append(port)
            print(f"   ✅ Port {port} OPEN")
        
        except:
            pass  # Porta fechada
    
    async def _detect_technologies(self):
        """Detecta tecnologias via HTTP"""
        
        print("\n🔎 Technology Detection...")
        
        async with aiohttp.ClientSession() as session:
            for protocol in ['https', 'http']:
                try:
                    url = f"{protocol}://{self.target}"
                    
                    async with session.get(url, timeout=10) as resp:
                        headers = resp.headers
                        html = await resp.text()
                        
                        # Detecta tecnologias
                        self._detect_from_headers(headers)
                        self._detect_from_html(html)
                        self._detect_cms(html)
                        
                        break
                
                except:
                    continue
        
        print(f"   ✅ {len(self.technologies)} tecnologias detectadas")
    
    def _detect_from_headers(self, headers: Dict):
        """Detecta via headers HTTP"""
        
        # Server header
        server = headers.get('Server', '')
        if server:
            self.technologies['server'] = server
        
        # X-Powered-By
        powered = headers.get('X-Powered-By', '')
        if powered:
            self.technologies['powered_by'] = powered
        
        # Framework headers
        if 'X-AspNet-Version' in headers:
            self.technologies['framework'] = 'ASP.NET'
        
        if 'X-Django-Version' in headers:
            self.technologies['framework'] = 'Django'
        
        # CDN
        if 'CF-RAY' in headers or 'cf-ray' in headers:
            self.technologies['cdn'] = 'Cloudflare'
        
        if 'X-Amz-Cf-Id' in headers:
            self.technologies['cdn'] = 'AWS CloudFront'
    
    def _detect_from_html(self, html: str):
        """Detecta via HTML"""
        
        # JavaScript frameworks
        if 'react' in html.lower() or '_next' in html:
            self.technologies['frontend'] = 'React/Next.js'
        
        if 'vue' in html.lower() or 'nuxt' in html.lower():
            self.technologies['frontend'] = 'Vue.js'
        
        if 'angular' in html.lower():
            self.technologies['frontend'] = 'Angular'
        
        # Meta tags
        generator_match = re.search(r'<meta name="generator" content="([^"]+)"', html, re.I)
        if generator_match:
            self.technologies['generator'] = generator_match.group(1)
    
    def _detect_cms(self, html: str):
        """Detecta CMS"""
        
        cms_signatures = {
            'WordPress': ['/wp-content/', '/wp-includes/', 'wp-json'],
            'Drupal': ['/sites/default/', 'Drupal.settings'],
            'Joomla': ['/components/com_', '/media/jui/'],
            'Magento': ['/skin/frontend/', 'Mage.Cookies'],
            'Shopify': ['cdn.shopify.com', 'Shopify.theme'],
            'Wix': ['wix.com', 'wixstatic.com'],
            'Squarespace': ['squarespace.com', 'squarespace-cdn'],
        }
        
        for cms, signatures in cms_signatures.items():
            for sig in signatures:
                if sig in html:
                    self.technologies['cms'] = cms
                    return


async def main():
    """Teste"""
    scanner = LibertusPortScanner("app.aikido.dev")
    result = await scanner.scan_all()
    
    print("\n" + "="*60)
    print("📊 RESULTADO:")
    print(f"\n🔌 Portas abertas: {result['open_ports']}")
    print(f"\n🔎 Tecnologias:")
    for key, value in result['technologies'].items():
        print(f"   • {key}: {value}")


if __name__ == "__main__":
    asyncio.run(main())
