"""
LIBERTUS — Buscador Autônomo
==============================
O LIBERTUS detecta o que não sabe, busca na web,
absorve o conhecimento e marca a curiosidade como respondida.

Fluxo:
    1. Auto-Curiosidade detecta lacuna → salva pergunta
    2. BuscadorAutonomo.ciclo() roda periodicamente
    3. Pega pergunta mais urgente da fila
    4. Busca na web via DuckDuckGo (grátis, sem API key)
    5. Groq resume o resultado
    6. Salva na libertus_memoria
    7. Marca curiosidade como respondida

Uso:
    from buscador_autonomo import BuscadorAutonomo
    ba = BuscadorAutonomo(groq_client, supabase_client)
    ba.ciclo()              # busca a próxima pergunta da fila
    ba.ciclo(limite=3)      # busca as 3 mais urgentes
"""

import json
import urllib.request
import urllib.parse
from datetime import datetime


class BuscadorAutonomo:

    PROMPT_RESUMIR = """Você é o sistema de aprendizado do LIBERTUS.

Encontrei estas informações na web sobre a pergunta: "{pergunta}"

RESULTADOS DA BUSCA:
{resultados}

Resuma em 3-5 parágrafos o que aprendi sobre isso.
Foque em aspectos práticos e técnicos relevantes para pentest e cybersegurança.
Seja direto e denso — sem introdução, só o conhecimento.
Responda em português brasileiro."""

    def __init__(self, groq_client=None, supabase_client=None):
        self.groq = groq_client
        self.sb   = supabase_client

    # ------------------------------------------------------------------
    # CICLO PRINCIPAL: busca e aprende
    # ------------------------------------------------------------------
    def ciclo(self, limite: int = 1) -> list[dict]:
        """
        Busca as N perguntas mais urgentes e aprende sobre elas.
        Retorna lista de curiosidades respondidas.
        """
        if not self.sb or not self.groq:
            return []

        # Pegar perguntas mais urgentes
        pendentes = self.sb.get(
            "libertus_fila_estudo",
            f"limit={limite}"
        ) or []

        respondidas = []
        for c in pendentes:
            resultado = self._buscar_e_aprender(c)
            if resultado:
                respondidas.append(resultado)

        return respondidas

    # ------------------------------------------------------------------
    # BUSCAR E APRENDER: para uma curiosidade específica
    # ------------------------------------------------------------------
    def _buscar_e_aprender(self, curiosidade: dict) -> dict | None:
        """Busca na web e salva o conhecimento na memória."""
        pergunta = curiosidade.get("pergunta", "")
        if not pergunta:
            return None

        print(f"\n  🔍 Buscando: {pergunta[:70]}")

        # 1. Buscar na web
        resultados = self._buscar_web(pergunta)
        if not resultados:
            print(f"  ⚠️  Nenhum resultado encontrado")
            return None

        # 2. Resumir com Groq
        resumo = self._resumir(pergunta, resultados)
        if not resumo or len(resumo) < 50:
            print(f"  ⚠️  Resumo inválido")
            return None

        print(f"  ✅ Aprendido: {len(resumo)} chars")

        # 3. Salvar na memória
        self._salvar_memoria(pergunta, resumo, curiosidade.get("dominio", "geral"))

        # 4. Marcar curiosidade como respondida
        self._marcar_respondida(curiosidade.get("id"), resumo)

        return {
            "pergunta": pergunta,
            "resumo": resumo[:200],
            "dominio": curiosidade.get("dominio", "geral")
        }

    # ------------------------------------------------------------------
    # BUSCA WEB: DuckDuckGo sem API key
    # ------------------------------------------------------------------
    def _buscar_web(self, query: str, max_results: int = 5) -> str:
        """Busca no DuckDuckGo e retorna texto dos resultados."""
        try:
            # DuckDuckGo instant answer API (grátis, sem key)
            query_encoded = urllib.parse.quote(query + " pentest cybersecurity")
            url = f"https://api.duckduckgo.com/?q={query_encoded}&format=json&no_redirect=1&no_html=1"

            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 LIBERTUS/4.0"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            partes = []

            # Abstract (resposta direta)
            if data.get("AbstractText"):
                partes.append(f"RESUMO: {data['AbstractText']}")

            # Related topics
            for topic in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(topic, dict) and topic.get("Text"):
                    partes.append(f"- {topic['Text'][:300]}")

            # Answer direto
            if data.get("Answer"):
                partes.append(f"RESPOSTA DIRETA: {data['Answer']}")

            if partes:
                return "\n\n".join(partes)

            # Fallback: busca HTML simples
            return self._buscar_html(query)

        except Exception as e:
            print(f"  ⚠️  Erro DuckDuckGo: {e}")
            return self._buscar_html(query)

    def _buscar_html(self, query: str) -> str:
        """Fallback: busca via HTML do DuckDuckGo."""
        try:
            query_encoded = urllib.parse.quote(query)
            url = f"https://html.duckduckgo.com/html/?q={query_encoded}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 LIBERTUS/4.0"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            # Extrair snippets simples
            import re
            snippets = re.findall(r'class="result__snippet"[^>]*>([^<]{50,500})', html)
            titles = re.findall(r'class="result__title"[^>]*>.*?<a[^>]*>([^<]{10,200})', html)

            partes = []
            for i, (t, s) in enumerate(zip(titles[:5], snippets[:5])):
                partes.append(f"{t.strip()}: {s.strip()}")

            return "\n\n".join(partes) if partes else ""
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # RESUMIR: Groq processa os resultados
    # ------------------------------------------------------------------
    def _resumir(self, pergunta: str, resultados: str) -> str:
        """Usa Groq para resumir os resultados da busca."""
        if not self.groq or not resultados:
            return resultados[:500] if resultados else ""
        try:
            prompt = self.PROMPT_RESUMIR.format(
                pergunta=pergunta,
                resultados=resultados[:2000]
            )
            return self.groq.conversar(prompt, "")
        except Exception:
            return resultados[:500]

    # ------------------------------------------------------------------
    # SALVAR NA MEMÓRIA
    # ------------------------------------------------------------------
    def _salvar_memoria(self, pergunta: str, resumo: str, dominio: str):
        """Salva o conhecimento aprendido na libertus_memoria."""
        if not self.sb:
            return
        try:
            self.sb.post("libertus_memoria", {
                "tipo": "auto_aprendizado",
                "titulo": f"[AUTO] {pergunta[:80]}",
                "conteudo": resumo[:1500],
                "tags": ["auto_aprendizado", dominio, "web"],
                "projeto": "LIBERTUS",
                "peso_vivo": 7.0,
                "decaimento_ativo": True
            })
        except Exception as e:
            print(f"  ⚠️  Erro ao salvar memória: {e}")

    # ------------------------------------------------------------------
    # MARCAR RESPONDIDA
    # ------------------------------------------------------------------
    def _marcar_respondida(self, curiosidade_id: str, resposta: str):
        if not self.sb or not curiosidade_id:
            return
        try:
            self.sb.patch(
                "libertus_curiosidades",
                f"id=eq.{curiosidade_id}",
                {
                    "status": "respondida",
                    "resposta": resposta[:600],
                    "fonte_resposta": "web_duckduckgo",
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # STATUS
    # ------------------------------------------------------------------
    def status(self):
        if not self.sb:
            return
        pendentes = self.sb.get("libertus_fila_estudo", "limit=5") or []
        respondidas = self.sb.get(
            "libertus_curiosidades",
            "status=eq.respondida&select=id&limit=1000"
        ) or []
        print(f"\n🔍 BUSCADOR AUTÔNOMO")
        print(f"  Perguntas pendentes: {len(pendentes)}")
        print(f"  Já aprendidas:       {len(respondidas)}")
        if pendentes:
            print(f"  Próxima: {pendentes[0].get('pergunta','?')[:60]}")
