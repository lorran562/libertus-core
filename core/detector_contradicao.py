"""
LIBERTUS — Detector de Contradição
====================================
Quando dois documentos dizem coisas opostas,
o LIBERTUS não escolhe um e descarta o outro.
Ele registra a tensão, gera uma hipótese, e fica mais inteligente.

Fluxo:
    1. absorvedor.py absorve um novo documento → chama detectar()
    2. detectar() compara o novo conteúdo com memórias existentes via Groq
    3. Contradições encontradas → salvas em libertus_contradicoes
    4. LIBERTUS gera hipótese automática para cada contradição
    5. Durante respostas, contradições abertas enriquecem o contexto

Uso:
    from detector_contradicao import DetectorContradicao
    dc = DetectorContradicao(groq_client, supabase_client)

    # Após absorver um documento:
    contradicoes = dc.detectar(novo_conteudo, titulo_fonte)

    # Durante uma resposta:
    tensoes = dc.buscar_tensoes_relevantes("pentest SQL injection")

    # Resolver manualmente:
    dc.resolver(contradicao_id, resolucao="A versão B é mais atual")
"""

import os
import json
import uuid
from datetime import datetime
from typing import Optional


class DetectorContradicao:

    PROMPT_DETECTAR = """Você é um detector de contradições intelectuais do LIBERTUS.

Analise se o NOVO CONTEÚDO contradiz alguma das MEMÓRIAS EXISTENTES.

NOVO CONTEÚDO (fonte: {fonte}):
{novo}

MEMÓRIAS EXISTENTES:
{memorias}

Responda APENAS em JSON válido, sem explicações, sem markdown:
{{
  "contradicoes": [
    {{
      "memoria_titulo": "título da memória que conflita",
      "tema": "sobre o que é o conflito (máx 80 chars)",
      "afirmacao_nova": "o que o novo documento afirma",
      "afirmacao_antiga": "o que a memória existente afirma",
      "tipo": "direto|parcial|temporal|contextual",
      "peso_tensao": 7.5,
      "hipotese": "hipótese do LIBERTUS para explicar ou resolver a tensão"
    }}
  ]
}}

Se não houver contradições, retorne: {{"contradicoes": []}}
Seja preciso. Só marque contradição real, não apenas diferença de perspectiva."""

    PROMPT_HIPOTESE = """Você é o cérebro do LIBERTUS. Existe uma contradição não resolvida:

TEMA: {tema}
AFIRMAÇÃO A ({fonte_a}): {afirmacao_a}
AFIRMAÇÃO B ({fonte_b}): {afirmacao_b}

Gere UMA hipótese inteligente que explique por que ambas podem estar certas,
ou qual deve prevalecer e por quê. Seja direto. Máximo 3 frases."""

    def __init__(self, groq_client=None, supabase_client=None):
        self.groq = groq_client
        self.sb   = supabase_client
        self._mem_cache = []

    # ------------------------------------------------------------------
    # DETECTAR: chamado após absorver um novo documento
    # ------------------------------------------------------------------
    def detectar(self, novo_conteudo: str, titulo_fonte: str,
                 memoria_nova_id: str = None) -> list[dict]:
        """
        Compara novo_conteudo com memórias existentes.
        Salva contradições encontradas. Retorna lista de contradições.
        """
        if not self.groq or not self.sb:
            return []

        # Busca memórias relevantes pelo mesmo tema
        memorias = self._buscar_memorias_relevantes(novo_conteudo)
        if not memorias:
            return []

        # Formata para o prompt
        memorias_fmt = "\n\n".join(
            f"[{i+1}] TÍTULO: {m.get('titulo','?')}\n"
            f"    CONTEÚDO: {m.get('conteudo','')[:400]}"
            for i, m in enumerate(memorias)
        )

        prompt = self.PROMPT_DETECTAR.format(
            fonte=titulo_fonte,
            novo=novo_conteudo[:1500],
            memorias=memorias_fmt
        )

        try:
            resposta = self.groq.conversar(prompt, "")
            dados = self._parse_json(resposta)
            contradicoes_raw = dados.get("contradicoes", [])
        except Exception as e:
            print(f"  ⚠️  Detector: erro ao chamar Groq: {e}")
            return []

        # Processa e salva cada contradição
        salvas = []
        for c in contradicoes_raw:
            if not c.get("tema") or not c.get("afirmacao_nova"):
                continue

            # Acha o ID da memória antiga pelo título
            mem_antiga = next(
                (m for m in memorias if m.get("titulo") == c.get("memoria_titulo")),
                None
            )

            contradicao = {
                "tema":             c.get("tema", "")[:200],
                "afirmacao_a":      c.get("afirmacao_nova", "")[:500],
                "afirmacao_b":      c.get("afirmacao_antiga", "")[:500],
                "memoria_a_titulo": titulo_fonte,
                "memoria_b_titulo": c.get("memoria_titulo", ""),
                "tipo_conflito":    c.get("tipo", "direto"),
                "peso_tensao":      float(c.get("peso_tensao", 5.0)),
                "hipotese":         c.get("hipotese", ""),
                "status":           "aberta",
                "memoria_a_id":     memoria_nova_id,
                "memoria_b_id":     mem_antiga.get("id") if mem_antiga else None,
            }

            saved = self._salvar(contradicao)
            if saved:
                salvas.append(contradicao)
                print(f"  ⚡ Contradição detectada: {contradicao['tema'][:60]} "
                      f"(tensão: {contradicao['peso_tensao']})")

        return salvas

    # ------------------------------------------------------------------
    # BUSCAR TENSÕES: enriquece contexto durante respostas
    # ------------------------------------------------------------------
    def buscar_tensoes_relevantes(self, query: str, limite: int = 3) -> list[dict]:
        """
        Retorna contradições abertas relevantes para o query atual.
        Usado para injetar incerteza produtiva no contexto das respostas.
        """
        if not self.sb:
            return []

        try:
            resultado = self.sb.get(
                "libertus_contradicoes_abertas",
                f"limit={limite}"
            )
            tensoes = resultado if isinstance(resultado, list) else []

            # Filtro simples por relevância textual
            if query and tensoes:
                query_lower = query.lower()
                tensoes = [
                    t for t in tensoes
                    if any(w in (t.get("tema") or "").lower()
                           for w in query_lower.split() if len(w) > 3)
                ] or tensoes  # se filtro vazio, retorna todas

            # Incrementa vezes_consultada
            for t in tensoes:
                self._incrementar_consulta(t.get("id"))

            return tensoes[:limite]
        except Exception:
            return []

    # ------------------------------------------------------------------
    # GERAR HIPÓTESE: para contradições sem hipótese ainda
    # ------------------------------------------------------------------
    def gerar_hipotese(self, contradicao_id: str) -> str:
        """Pede ao Groq uma hipótese para resolver a contradição."""
        if not self.groq or not self.sb:
            return ""

        try:
            rows = self.sb.get(
                "libertus_contradicoes",
                f"id=eq.{contradicao_id}&select=*"
            )
            if not rows:
                return ""
            c = rows[0]

            prompt = self.PROMPT_HIPOTESE.format(
                tema=c.get("tema", ""),
                fonte_a=c.get("memoria_a_titulo", "Fonte A"),
                afirmacao_a=c.get("afirmacao_a", ""),
                fonte_b=c.get("memoria_b_titulo", "Fonte B"),
                afirmacao_b=c.get("afirmacao_b", "")
            )

            hipotese = self.groq.conversar(prompt, "")
            if hipotese:
                self.sb.patch(
                    "libertus_contradicoes",
                    f"id=eq.{contradicao_id}",
                    {"hipotese": hipotese[:600], "updated_at": datetime.utcnow().isoformat()}
                )
            return hipotese
        except Exception as e:
            return f"Erro ao gerar hipótese: {e}"

    # ------------------------------------------------------------------
    # RESOLVER: marcar contradição como resolvida
    # ------------------------------------------------------------------
    def resolver(self, contradicao_id: str, resolucao: str,
                 fonte: str = "lorran") -> bool:
        """Marca uma contradição como resolvida."""
        if not self.sb:
            return False
        try:
            self.sb.patch(
                "libertus_contradicoes",
                f"id=eq.{contradicao_id}",
                {
                    "status": "resolvida",
                    "resolucao": resolucao[:600],
                    "resolucao_fonte": fonte,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
            print(f"  ✅ Contradição {contradicao_id[:8]} resolvida")
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # STATUS: diagnóstico das contradições
    # ------------------------------------------------------------------
    def status(self):
        if not self.sb:
            print("  ⚠️  Supabase offline")
            return

        abertas = self.sb.get("libertus_contradicoes", "status=eq.aberta&select=tema,peso_tensao,tipo_conflito")
        resolvidas = self.sb.get("libertus_contradicoes", "status=eq.resolvida&select=id")

        print(f"\n⚡ CONTRADIÇÕES ABERTAS: {len(abertas)}")
        for c in (abertas or [])[:5]:
            print(f"  [{c.get('peso_tensao',0):.1f}] {c.get('tema','')[:60]} ({c.get('tipo_conflito','')})")

        print(f"✅ Resolvidas: {len(resolvidas or [])}")

    # ------------------------------------------------------------------
    # INTERNOS
    # ------------------------------------------------------------------
    def _buscar_memorias_relevantes(self, conteudo: str) -> list[dict]:
        """Busca memórias com peso_vivo > 2 para comparar."""
        if not self.sb:
            return []
        try:
            return self.sb.get(
                "libertus_memoria",
                "peso_vivo=gte.2&order=peso_vivo.desc&limit=10"
                "&select=id,titulo,conteudo,tipo"
            )
        except Exception:
            return []

    def _salvar(self, contradicao: dict) -> bool:
        if not self.sb:
            return False
        try:
            self.sb.post("libertus_contradicoes", contradicao)
            return True
        except Exception as e:
            print(f"  ⚠️  Erro ao salvar contradição: {e}")
            return False

    def _incrementar_consulta(self, cid: str):
        if not self.sb or not cid:
            return
        try:
            rows = self.sb.get("libertus_contradicoes", f"id=eq.{cid}&select=vezes_consultada")
            if rows:
                atual = rows[0].get("vezes_consultada", 0)
                self.sb.patch("libertus_contradicoes", f"id=eq.{cid}",
                              {"vezes_consultada": atual + 1})
        except Exception:
            pass

    def _parse_json(self, texto: str) -> dict:
        """Extrai JSON da resposta do Groq com tolerância a markdown."""
        if not texto:
            return {"contradicoes": []}
        # Remove blocos markdown se houver
        texto = texto.strip()
        if "```" in texto:
            import re
            match = re.search(r"```(?:json)?\s*([\s\S]+?)```", texto)
            if match:
                texto = match.group(1).strip()
        try:
            return json.loads(texto)
        except Exception:
            return {"contradicoes": []}
