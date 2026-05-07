"""
ollama_client.py — Ollama local (fallback offline)
Usado quando Groq e Claude não estão disponíveis.
"""

import httpx
from typing import Optional, List


class Ollama:
    MODELOS = ["deepseek-r1:1.5b","qwen2.5:0.5b","phi3:mini",
               "llama3.2:1b","deepseek-coder","mistral"]

    SYSTEM = """Você é LIBERTUS — IA pessoal de Lorran de Ariquemes-RO.
Responda em português. Seja direto e útil."""

    def __init__(self, url: str = "http://localhost:11434"):
        self.url   = url
        self.model = self._detectar_modelo()

    def _detectar_modelo(self) -> Optional[str]:
        try:
            r = httpx.get(f"{self.url}/api/tags", timeout=5)
            if r.status_code != 200:
                return None
            modelos_local = [m["name"] for m in r.json().get("models", [])]
            for preferido in self.MODELOS:
                for local in modelos_local:
                    if preferido in local:
                        return local
            return modelos_local[0] if modelos_local else None
        except Exception:
            return None

    def gerar(self, prompt: str, contexto: str = "") -> str:
        if not self.model:
            return ""
        mensagem = prompt
        if contexto:
            mensagem = f"Contexto:\n{contexto[:400]}\n\nPergunta: {prompt}"
        try:
            r = httpx.post(
                f"{self.url}/api/generate",
                json={"model": self.model, "prompt": mensagem,
                      "system": self.SYSTEM, "stream": False},
                timeout=60
            )
            if r.status_code == 200:
                return r.json().get("response", "").strip()
        except Exception:
            pass
        return ""

    def listar(self) -> List[str]:
        try:
            r = httpx.get(f"{self.url}/api/tags", timeout=5)
            if r.status_code == 200:
                return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            pass
        return []
