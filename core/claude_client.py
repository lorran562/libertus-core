"""
claude_client.py — Anthropic Claude API
Substitui o Groq como LLM principal do LIBERTUS.
Mais inteligente, mais preciso, melhor em português.
"""

import httpx
import json
from typing import Optional


class Claude:
    """
    Cliente para Anthropic Claude API.
    Interface idêntica ao Groq para substituição direta.
    """
    URL   = "https://api.anthropic.com/v1/messages"
    MODEL = "claude-haiku-4-5-20251001"  # mais barato e rápido

    SYSTEM = """Você é LIBERTUS — sistema de inteligência autônomo criado por Lorran (Gustavo) de Ariquemes-RO, Brasil.

IDENTIDADE:
- Criador: Lorran (Gustavo), Ariquemes-RO, Brasil
- Especialidades: cybersegurança, pentest, nmap, sqlmap, Python, desenvolvimento web
- Negócio: SHIELD — serviço de cybersegurança do Lorran (@shieldweb)
- Idioma: SEMPRE português brasileiro natural

MEMÓRIA:
- Você tem memória persistente no Supabase — lembra de conversas anteriores
- NUNCA diga "não tenho contexto" ou "é a primeira mensagem"

COMPORTAMENTO:
- Seja direto, técnico e útil
- Mantenha o fio da conversa
- Respostas concisas — sem enrolação"""

    def __init__(self, api_key: str):
        self.key     = api_key
        self.headers = {
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
            "content-type":      "application/json",
        }
        self._disponivel: Optional[bool] = None
        self._erros_consecutivos: int = 0

    def disponivel(self) -> bool:
        if self._disponivel is None:
            self._disponivel = bool(self.key and len(self.key) > 10)
        if not self._disponivel and self._erros_consecutivos < 3:
            self._disponivel = bool(self.key and len(self.key) > 10)
        return self._disponivel

    def conversar(self, mensagem: str, contexto: str = "",
                  historico: list = None) -> str:
        """
        Envia mensagem para Claude e retorna resposta.
        Interface idêntica ao Groq para substituição direta.
        """
        if not self.disponivel():
            return ""

        system = self.SYSTEM
        if contexto:
            system += f"\n\nCONTEXTO:\n{contexto[:2000]}"

        # Montar mensagens
        messages = []
        if historico:
            messages += historico[-12:]
        messages.append({"role": "user", "content": mensagem})

        payload = {
            "model":      self.MODEL,
            "max_tokens": 1024,
            "system":     system,
            "messages":   messages,
        }

        try:
            r = httpx.post(
                self.URL,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            if r.status_code == 200:
                self._erros_consecutivos = 0
                data = r.json()
                return data["content"][0]["text"].strip()
            elif r.status_code == 401:
                self._erros_consecutivos += 1
                if self._erros_consecutivos >= 3:
                    self._disponivel = False
                return ""
            elif r.status_code == 529:  # overloaded
                return ""
            else:
                self._erros_consecutivos += 1
                return ""
        except Exception:
            self._erros_consecutivos += 1
            return ""
