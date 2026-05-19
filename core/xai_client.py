"""
xai_client.py — xAI API (Grok)
Cliente compatível com LIBERTUS
"""

import httpx
from typing import Optional


class XAI:
    """
    Cliente para xAI API — Grok
    Interface compatível com Groq
    """
    URL   = "https://api.x.ai/v1/chat/completions"
    MODEL = "grok-beta"

    SYSTEM = """Você é LIBERTUS — sistema de inteligência criado por Lorran (Gustavo) 
de Ariquemes-RO. Responda sempre em português brasileiro natural.
Seja direto, útil e conciso. Você conhece os projetos de Lorran:
T7 Vapor (loja de vape), PixSwap (PIX→cripto), Ashen Roots (jogo Godot),
LorranStack (marketplace SaaS). Use esse contexto quando relevante."""

    def __init__(self, api_key: str):
        self.key     = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        }
        self._disponivel: Optional[bool] = None

    def disponivel(self) -> bool:
        if self._disponivel is None:
            self._disponivel = bool(self.key and len(self.key) > 10)
        return self._disponivel

    def conversar(self, mensagem: str, contexto: str = "") -> str:
        """
        Envia mensagem para xAI e retorna resposta.
        Contexto é injetado no system prompt se fornecido.
        """
        if not self.disponivel():
            return ""

        system = self.SYSTEM
        if contexto:
            system += f"\n\nCONTEXTO DO VAULT:\n{contexto[:800]}"

        payload = {
            "model": self.MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": mensagem}
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        try:
            with httpx.Client(timeout=60) as client:
                r = client.post(self.URL, headers=self.headers, json=payload)
                if r.status_code != 200:
                    return f"Erro xAI: {r.status_code}"
                data = r.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Erro ao chamar xAI: {e}"
