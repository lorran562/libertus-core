#!/usr/bin/env python3
"""
LIBERTUS SUBDOMAIN ENUMERATOR

Descobre TODOS os subdomínios do target usando múltiplas técnicas:
1. Certificate Transparency logs (crt.sh)
2. DNS brute force
3. Search engine scraping
4. Common subdomain wordlist
"""

import asyncio
import aiohttp
import dns.resolver
from typing import List, Set
import re


class LibertusSubdomainEnum:
    """Enumerador de subdomínios profissional"""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.subdomains: Set[str] = set()
        
        # Wordlist comum de subdomínios
        self.common_subdomains = [
            "www", "mail", "ftp", "localhost", "webmail", "smtp",
            "pop", "ns1", "webdisk", "ns2", "cpanel", "whm",
            "autodiscover", "autoconfig", "m", "imap", "test",
            "ns", "blog", "pop3", "dev", "www2", "admin",
            "forum", "news", "vpn", "ns3", "mail2", "new",
            "mysql", "old", "lists", "support", "mobile", "mx",
            "static", "docs", "beta", "shop", "sql", "secure",
            "demo", "cp", "calendar", "wiki", "web", "media",
            "email", "images", "img", "www1", "intranet", "portal",
            "video", "sip", "dns2", "api", "cdn", "stats",
            "dns1", "ns4", "www3", "dns", "search", "staging",
            "server", "mx1", "chat", "wap", "my", "svn",
            "mail1", "sites", "proxy", "ads", "host", "crm",
            "cms", "backup", "mx2", "lyncdiscover", "info", "apps",
            "download", "remote", "db", "forums", "store", "relay",
            "files", "newsletter", "app", "live", "owa", "en",
            "start", "sms", "office", "exchange", "ipv4", "git",
            # Bug bounty específicos
            "internal", "private", "secret", "hidden", "temp",
            "backup", "dev-api", "test-api", "staging-api",
            "admin-panel", "dashboard", "control", "manage"
        ]
    
    async def enumerate_all(self) -> List[str]:
        """Executa todas técnicas de enumeração"""
        
        print(f"🔍 Enumerando subdomínios de {self.domain}")
        print("="*60)
        
        # 1. Certificate Transparency
        await self._enum_crtsh()
        
        # 2. DNS Brute Force
        await self._enum_dns_brute()
        
        # 3. Verificar se subdomínios estão ativos
        active = await self._check_active()
        
        print(f"\n✅ Subdomínios encontrados: {len(active)}")
        
        return sorted(list(active))
    
    async def _enum_crtsh(self):
        """Certificate Transparency via crt.sh"""
        
        print("\n📜 Certificate Transparency (crt.sh)...")
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://crt.sh/?q=%.{self.domain}&output=json"
                
                async with session.get(url, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        for cert in data:
                            name = cert.get('name_value', '')
                            
                            # Parse CN e SANs
                            for line in name.split('\n'):
                                line = line.strip().lower()
                                
                                if line.endswith(self.domain):
                                    # Remove wildcard
                                    subdomain = line.replace('*.', '')
                                    self.subdomains.add(subdomain)
                        
                        print(f"   ✅ {len(self.subdomains)} via crt.sh")
        
        except Exception as e:
            print(f"   ⚠️ crt.sh error: {e}")
    
    async def _enum_dns_brute(self):
        """DNS Brute Force"""
        
        print("\n🔨 DNS Brute Force...")
        
        resolver = dns.resolver.Resolver()
        resolver.timeout = 2
        resolver.lifetime = 2
        
        tasks = []
        
        for sub in self.common_subdomains:
            full_domain = f"{sub}.{self.domain}"
            tasks.append(self._check_dns(full_domain, resolver))
        
        # Limita concorrência
        for i in range(0, len(tasks), 20):
            batch = tasks[i:i+20]
            await asyncio.gather(*batch, return_exceptions=True)
        
        print(f"   ✅ {len(self.subdomains)} total após brute force")
    
    async def _check_dns(self, domain: str, resolver):
        """Verifica se domínio resolve"""
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: resolver.resolve(domain, 'A')
            )
            
            self.subdomains.add(domain)
        
        except:
            pass  # Não resolveu
    
    async def _check_active(self) -> List[str]:
        """Verifica quais subdomínios estão ativos (HTTP/HTTPS)"""
        
        print("\n✅ Verificando subdomínios ativos...")
        
        active = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            for subdomain in self.subdomains:
                tasks.append(self._check_http(session, subdomain))
            
            # Limita concorrência
            for i in range(0, len(tasks), 10):
                batch = tasks[i:i+10]
                results = await asyncio.gather(*batch, return_exceptions=True)
                
                for result in results:
                    if result:
                        active.append(result)
        
        return active
    
    async def _check_http(self, session, subdomain: str) -> str:
        """Verifica se subdomain responde HTTP/HTTPS"""
        
        for protocol in ['https', 'http']:
            try:
                url = f"{protocol}://{subdomain}"
                
                async with session.get(url, timeout=5, allow_redirects=True) as resp:
                    if resp.status < 500:
                        print(f"   ✅ {url} [{resp.status}]")
                        return url
            
            except:
                continue
        
        return None


async def main():
    """Teste"""
    enum = LibertusSubdomainEnum("aikido.dev")
    subdomains = await enum.enumerate_all()
    
    print("\n" + "="*60)
    print("🎯 SUBDOMÍNIOS ATIVOS:")
    for sub in subdomains:
        print(f"   • {sub}")


if __name__ == "__main__":
    asyncio.run(main())
