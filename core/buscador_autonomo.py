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

TAVILY_KEY = "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"


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
    # BUSCA WEB: Tavily (primário) + Wikipedia (complementar)
    # ------------------------------------------------------------------
    def _buscar_web(self, query: str, max_results: int = 5) -> str:
        """Busca com Tavily API + Wikipedia. Retorna conteúdo rico e limpo."""
        partes = []

        # 1. Tavily — feita para IA, resultados limpos e relevantes
        tavily = self._buscar_tavily(query, max_results)
        if tavily:
            partes.append(f"[TAVILY WEB]\n{tavily}")

        # 2. Wikipedia — conhecimento enciclopédico profundo
        wiki = self._buscar_wikipedia(query)
        if wiki:
            partes.append(f"[WIKIPEDIA]\n{wiki}")

        # 3. Fallback DuckDuckGo se ambos falharem
        if not partes:
            ddg = self._buscar_duckduckgo(query)
            if ddg:
                partes.append(f"[DUCKDUCKGO]\n{ddg}")

        return "\n\n".join(partes)

    def _buscar_tavily(self, query: str, max_results: int = 5) -> str:
        """Tavily API — otimizada para agentes de IA."""
        try:
            payload = json.dumps({
                "api_key": TAVILY_KEY,
                "query": query,
                "search_depth": "advanced",
                "max_results": max_results,
                "include_answer": True,
                "include_raw_content": False,
            }).encode()

            req = urllib.request.Request(
                "https://api.tavily.com/search",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())

            partes = []

            # Resposta direta gerada pela Tavily
            if data.get("answer"):
                partes.append(f"RESPOSTA: {data['answer']}")

            # Resultados individuais
            for r in data.get("results", [])[:max_results]:
                titulo   = r.get("title", "")
                conteudo = r.get("content", "")
                url      = r.get("url", "")
                if conteudo:
                    partes.append(f"• {titulo}\n  {conteudo[:400]}\n  Fonte: {url}")

            return "\n\n".join(partes)

        except Exception as e:
            print(f"  ⚠️  Tavily erro: {e}")
            return ""

    def _buscar_wikipedia(self, query: str) -> str:
        """Wikipedia API — conhecimento enciclopédico."""
        try:
            # Buscar artigo
            search_url = (
                "https://pt.wikipedia.org/api/rest_v1/page/summary/"
                + urllib.parse.quote(query.replace(" ", "_"))
            )
            req = urllib.request.Request(search_url, headers={
                "User-Agent": "LIBERTUS/4.0"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            extract = data.get("extract", "")
            title   = data.get("title", "")
            if extract and len(extract) > 50:
                return f"{title}: {extract[:800]}"

        except Exception:
            pass

        # Fallback: busca em inglês
        try:
            search_url = (
                "https://en.wikipedia.org/api/rest_v1/page/summary/"
                + urllib.parse.quote(query.replace(" ", "_"))
            )
            req = urllib.request.Request(search_url, headers={
                "User-Agent": "LIBERTUS/4.0"
            })
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            extract = data.get("extract", "")
            title   = data.get("title", "")
            if extract and len(extract) > 50:
                return f"{title}: {extract[:800]}"
        except Exception:
            pass

        return ""

    def _buscar_duckduckgo(self, query: str) -> str:
        """Fallback DuckDuckGo quando Tavily falhar."""
        try:
            query_encoded = urllib.parse.quote(query)
            url = f"https://api.duckduckgo.com/?q={query_encoded}&format=json&no_redirect=1&no_html=1"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 LIBERTUS/4.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            partes = []
            if data.get("AbstractText"):
                partes.append(data["AbstractText"])
            for t in data.get("RelatedTopics", [])[:3]:
                if isinstance(t, dict) and t.get("Text"):
                    partes.append(t["Text"][:200])
            return "\n".join(partes)
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
