import asyncio
from typing import Optional
import aiohttp
import os
import subprocess

class LLMBackendManager:
    """Multi-provider LLM manager: Groq + Ollama + Claude"""
    
    def __init__(self):
        self.providers = {
            'groq': self._groq_generate,
            'ollama': self._ollama_generate,
        }
        self.ollama_model = 'llama3.2:3b'
    
    async def generate(self, provider: str, prompt: str, **kwargs) -> str:
        """Gera resposta usando o provedor especificado"""
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} não suportado")
        return await self.providers[provider](prompt, **kwargs)
    
    async def _groq_generate(self, prompt: str, **kwargs) -> str:
        """Groq API"""
        from groq import AsyncGroq
        
        client = AsyncGroq(api_key=os.getenv('GROQ_API_KEY'))
        
        response = await client.chat.completions.create(
            model=kwargs.get('model', 'llama-3.3-70b-versatile'),
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=kwargs.get('max_tokens', 4000),
            temperature=kwargs.get('temperature', 0.7),
        )
        
        return response.choices[0].message.content
    
    async def _ollama_generate(self, prompt: str, **kwargs) -> str:
        """Ollama Local"""
        if not await self._check_ollama_running():
            raise Exception("Ollama não está rodando")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': kwargs.get('model', self.ollama_model),
                    'prompt': prompt,
                    'stream': False,
                    'options': {
                        'temperature': kwargs.get('temperature', 0.7),
                        'num_predict': kwargs.get('max_tokens', 2000),
                    }
                }
            ) as response:
                result = await response.json()
                return result['response']
    
    async def _check_ollama_running(self) -> bool:
        """Verifica se Ollama está acessível"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:11434/api/tags', 
                                     timeout=aiohttp.ClientTimeout(total=2)) as response:
                    return response.status == 200
        except:
            return False
