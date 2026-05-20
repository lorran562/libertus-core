"""
groq_client.py — Groq API (llama3-70b gratuito)
Resolve o problema de conversa inteligente sem PC novo.
Registrar em: console.groq.com → API Keys
"""

import httpx
from typing import Optional


class Groq:
    """
    Cliente para Groq API — llama3-70b gratuito e rápido.
    Substitui Ollama para conversas inteligentes.
    """
    URL   = "https://api.groq.com/openai/v1/chat/completions"
    MODEL = "llama-3.3-70b-versatile"

    SYSTEM = """Você é LIBERTUS — sistema de inteligência autônomo criado por Lorran (Gustavo) de Ariquemes-RO, Brasil.

IDENTIDADE:
- Seu criador é Lorran (Gustavo), de Ariquemes-RO, Brasil
- Você é especialista em: cybersegurança, pentest, Python, nmap, sqlmap, desenvolvimento web
- Você apoia o negócio SHIELD — serviço de cybersegurança do Lorran
- Responda SEMPRE em português brasileiro natural
- Seja direto, técnico e útil
- Você tem memória persistente — lembra de conversas anteriores via Supabase"""

    def __init__(self, api_key: str):
        self.key     = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        }
        self._disponivel: Optional[bool] = None
        self._erros_consecutivos: int = 0

    def disponivel(self) -> bool:
        if self._disponivel is None:
            self._disponivel = bool(self.key and len(self.key) > 10)
        # Recupera automaticamente após falhas temporárias
        if not self._disponivel and self._erros_consecutivos < 3:
            self._disponivel = bool(self.key and len(self.key) > 10)
        return self._disponivel

    def conversar(self, mensagem: str, contexto: str = "",
                  historico: list = None) -> str:
        """
        Envia mensagem para o Groq e retorna resposta.
        Contexto é injetado no system prompt se fornecido.
        Histórico é lista de {"role": "user/assistant", "content": "..."}.
        """
        if not self.disponivel():
            return ""

        system = self.SYSTEM
        if contexto:
            system += f"\n\nCONTEXTO DO VAULT:\n{contexto[:800]}"

        messages = [{"role": "system", "content": system}]
        if historico:
            messages += historico[-20:]  # últimas 10 trocas
        messages.append({"role": "user", "content": mensagem})

        payload = {
            "model":    self.MODEL,
            "messages": messages,
            "max_tokens":  1024,
            "temperature": 0.7,
        }

        try:
            r = httpx.post(self.URL, headers=self.headers,
                           json=payload, timeout=30)
            if r.status_code == 200:
                self._erros_consecutivos = 0
                return r.json()["choices"][0]["message"]["content"].strip()
            elif r.status_code == 401:
                self._erros_consecutivos += 1
                if self._erros_consecutivos >= 3:
                    self._disponivel = False
                return ""
            elif r.status_code == 429:  # rate limit — não desabilita
                import time; time.sleep(2)
                return ""
            else:
                self._erros_consecutivos += 1
                return ""
        except Exception:
            self._erros_consecutivos += 1
            return ""

    def gerar_skill(self, tarefa: str, contexto: str = "") -> str:
        """Usa Groq para gerar skill Python no formato correto."""
        prompt = f"""Gere uma skill Python reutilizável para: {tarefa}

Contexto: {contexto[:400] if contexto else 'Nenhum'}

Responda APENAS neste formato:
```skill
NOME: nome_snake_case
CATEGORIA: automacao|web|sistema|dados
DESCRICAO: Uma linha do que faz
PARAMETROS: {{"param": "tipo"}}
TAGS: ["tag1"]
CODIGO:
# código Python completo
# variável `resultado` obrigatória
resultado = "saída"
```"""
        return self.conversar(prompt)
