#!/usr/bin/env python3
"""
LIBERTUS ANTI-BLOCK SYSTEM
Sistema de evasão de bloqueio e detecção

Funcionalidades:
- Delay aleatório entre requests
- Retry inteligente com backoff exponencial
- User-Agent rotation
- Detecção de bloqueio (WAF/rate limit)
- Estratégia adaptativa

Autor: Libertus v10.0 Production
Data: 2026-05-14
"""

import asyncio
import aiohttp
import random
from typing import Optional, Callable, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger('ANTI_BLOCK')


@dataclass
class RequestConfig:
    """Configuração de request anti-bloqueio"""
    min_delay: float = 1.0  # segundos
    max_delay: float = 3.0  # segundos
    max_retries: int = 3
    backoff_factor: float = 2.0
    timeout: int = 30
    rotate_user_agent: bool = True


class AntiBlockSystem:
    """
    Sistema anti-bloqueio para requests HTTP
    
    Estratégias:
    1. Delay aleatório entre requests
    2. Retry com backoff exponencial
    3. User-Agent rotation
    4. Detecção de bloqueio
    5. Troca de estratégia se bloqueado
    """
    
    USER_AGENTS = [
        # Chrome Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Chrome macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        # Firefox Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        # Firefox macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        # Safari macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        # Edge Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        # Chrome Linux
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    ]
    
    # Indicadores de bloqueio
    BLOCK_INDICATORS = [
        'captcha',
        'blocked',
        'forbidden',
        'access denied',
        'rate limit',
        'too many requests',
        'cloudflare',
        'security check',
        'unusual activity',
        'suspicious'
    ]
    
    def __init__(self, config: Optional[RequestConfig] = None):
        self.config = config or RequestConfig()
        self.current_user_agent_index = 0
        self.blocked_count = 0
        self.total_requests = 0
    
    def get_random_user_agent(self) -> str:
        """Retorna User-Agent aleatório"""
        return random.choice(self.USER_AGENTS)
    
    def get_next_user_agent(self) -> str:
        """Retorna próximo User-Agent (rotação sequencial)"""
        ua = self.USER_AGENTS[self.current_user_agent_index]
        self.current_user_agent_index = (self.current_user_agent_index + 1) % len(self.USER_AGENTS)
        return ua
    
    async def delay_random(self):
        """Delay aleatório entre requests"""
        delay = random.uniform(self.config.min_delay, self.config.max_delay)
        logger.debug(f"Delay: {delay:.2f}s")
        await asyncio.sleep(delay)
    
    def is_blocked(self, response_text: str, status_code: int) -> bool:
        """
        Detecta se request foi bloqueado
        
        Indicadores:
        - Status 403, 429, 503
        - Keywords de bloqueio no HTML
        """
        # Status codes de bloqueio
        if status_code in [403, 429, 503]:
            return True
        
        # Keywords no response
        response_lower = response_text.lower()
        
        for indicator in self.BLOCK_INDICATORS:
            if indicator in response_lower:
                return True
        
        return False
    
    async def request_with_retry(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        **kwargs
    ) -> Optional[aiohttp.ClientResponse]:
        """
        Faz request com retry inteligente
        
        Backoff exponencial: 1s → 2s → 4s → 8s
        """
        self.total_requests += 1
        
        for attempt in range(self.config.max_retries):
            try:
                # User-Agent rotation
                if self.config.rotate_user_agent:
                    headers = kwargs.get('headers', {})
                    headers['User-Agent'] = self.get_next_user_agent()
                    kwargs['headers'] = headers
                
                # Timeout
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                kwargs['timeout'] = timeout
                
                # Request
                logger.debug(f"Request #{attempt + 1}: {method} {url}")
                
                async with session.request(method, url, **kwargs) as resp:
                    response_text = await resp.text()
                    
                    # Verificar bloqueio
                    if self.is_blocked(response_text, resp.status):
                        self.blocked_count += 1
                        
                        logger.warning(f"⚠️ BLOQUEIO DETECTADO (tentativa {attempt + 1}/{self.config.max_retries})")
                        logger.warning(f"Status: {resp.status}")
                        
                        # Trocar User-Agent e tentar novamente
                        if attempt < self.config.max_retries - 1:
                            # Backoff exponencial
                            backoff = self.config.min_delay * (self.config.backoff_factor ** attempt)
                            logger.info(f"↻ Retry em {backoff:.1f}s com novo User-Agent...")
                            await asyncio.sleep(backoff)
                            continue
                        else:
                            logger.error("❌ Bloqueado após todos os retries")
                            return None
                    
                    # Sucesso
                    logger.debug(f"✅ Request sucesso: {resp.status}")
                    return resp
            
            except asyncio.TimeoutError:
                logger.warning(f"⏱️ Timeout (tentativa {attempt + 1}/{self.config.max_retries})")
                
                if attempt < self.config.max_retries - 1:
                    backoff = self.config.min_delay * (self.config.backoff_factor ** attempt)
                    await asyncio.sleep(backoff)
                    continue
            
            except aiohttp.ClientError as e:
                logger.warning(f"⚠️ Erro de rede: {e} (tentativa {attempt + 1}/{self.config.max_retries})")
                
                if attempt < self.config.max_retries - 1:
                    backoff = self.config.min_delay * (self.config.backoff_factor ** attempt)
                    await asyncio.sleep(backoff)
                    continue
            
            except Exception as e:
                logger.error(f"❌ Erro inesperado: {e}")
                return None
        
        return None
    
    async def safe_request(
        self,
        session: aiohttp.ClientSession,
        method: str,
        url: str,
        with_delay: bool = True,
        **kwargs
    ) -> Optional[tuple]:
        """
        Request seguro com anti-bloqueio
        
        Retorna: (response, text) ou None se falhou
        """
        # Delay antes do request
        if with_delay:
            await self.delay_random()
        
        # Request com retry
        resp = await self.request_with_retry(session, method, url, **kwargs)
        
        if resp:
            text = await resp.text()
            return (resp, text)
        
        return None
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do sistema anti-bloqueio"""
        block_rate = (self.blocked_count / self.total_requests * 100) if self.total_requests > 0 else 0
        
        return {
            'total_requests': self.total_requests,
            'blocked_count': self.blocked_count,
            'block_rate': f"{block_rate:.1f}%",
            'current_user_agent': self.USER_AGENTS[self.current_user_agent_index],
            'config': {
                'min_delay': self.config.min_delay,
                'max_delay': self.config.max_delay,
                'max_retries': self.config.max_retries,
                'rotate_user_agent': self.config.rotate_user_agent
            }
        }


# CLI para testes
async def test_anti_block():
    """Teste do sistema anti-bloqueio"""
    
    logging.basicConfig(level=logging.DEBUG)
    
    config = RequestConfig(
        min_delay=0.5,
        max_delay=1.5,
        max_retries=3
    )
    
    anti_block = AntiBlockSystem(config)
    
    async with aiohttp.ClientSession() as session:
        print("="*70)
        print("TESTE: Anti-Block System")
        print("="*70)
        
        # Teste 1: Request normal
        print("\n1. Request normal:")
        result = await anti_block.safe_request(session, 'GET', 'http://exemplo.com')
        
        if result:
            resp, text = result
            print(f"✅ Sucesso: {resp.status} ({len(text)} bytes)")
        else:
            print("❌ Falhou")
        
        # Teste 2: Request sem delay
        print("\n2. Request sem delay:")
        result = await anti_block.safe_request(session, 'GET', 'http://exemplo.com', with_delay=False)
        
        if result:
            resp, text = result
            print(f"✅ Sucesso: {resp.status}")
        
        # Estatísticas
        print("\n" + "="*70)
        print("ESTATÍSTICAS:")
        print("="*70)
        stats = anti_block.get_stats()
        
        import json
        print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    asyncio.run(test_anti_block())
