"""
LIBERTUS — Auto-Curiosidade
============================
O LIBERTUS detecta o que não sabe e quer aprender.
Ele para de ser reativo e começa a querer.

Três fontes de curiosidade:
  1. LACUNA: respondeu mal algo → detecta o que faltava saber
  2. CONTRADIÇÃO: dois documentos conflitam → quer saber qual está certo
  3. SESSÃO: durante conversa detecta conceito desconhecido → registra pra estudar

Fluxo:
  - A cada sessão: gerar_de_sessao() analisa o que foi discutido
  - A cada erro registrado: gerar_de_erro() detecta lacuna de conhecimento
  - A cada contradição: gerar_de_contradicao() quer resolver a tensão
  - periodicamente: proxima_a_estudar() retorna a pergunta mais urgente
  - Quando absorve PDF relevante: responder() marca a curiosidade como respondida

Uso:
    from auto_curiosidade import AutoCuriosidade
    ac = AutoCuriosidade(groq_client, supabase_client)

    ac.gerar_de_erro(entrada, resultado, dominio)
    ac.gerar_de_contradicao(contradicao_dict)
    ac.gerar_de_sessao(historico_sessao)

    proxima = ac.proxima_a_estudar()
    ac.responder(curiosidade_id, resposta, fonte)
"""

import json
from datetime import datetime
from typing import Optional


class AutoCuriosidade:

    PROMPT_LACUNA = """Você é o sistema de auto-curiosidade do LIBERTUS.

O LIBERTUS tentou responder algo e falhou ou foi parcial.
Detecte qual conhecimento estava faltando e formule UMA pergunta de estudo.

TAREFA QUE FALHOU: {entrada}
RESPOSTA GERADA: {resultado}
DOMÍNIO: {dominio}
CAUSA DO ERRO: {causa}

Responda APENAS em JSON:
{{
  "pergunta": "pergunta específica que o LIBERTUS deveria estudar para resolver isso melhor",
  "dominio": "{dominio}",
  "urgencia": 7.5
}}

A pergunta deve ser específica e técnica. Ex: "Como funciona o bypass de WAF com double encoding em SQL injection?"
NÃO faça perguntas genéricas como "como melhorar pentest"."""

    PROMPT_SESSAO = """Você é o sistema de auto-curiosidade do LIBERTUS.

Analise esta sessão e detecte conceitos, técnicas ou ferramentas
que foram mencionados mas que o LIBERTUS provavelmente não domina profundamente.

RESUMO DA SESSÃO:
{sessao}

DOMÍNIOS JÁ CONHECIDOS PELO LIBERTUS:
{dominios_conhecidos}

Gere de 1 a 3 perguntas de estudo. Responda APENAS em JSON:
{{
  "curiosidades": [
    {{
      "pergunta": "pergunta técnica específica",
      "dominio": "area (pentest|crypto|web|sistema|negocio|ia)",
      "urgencia": 6.0,
      "origem": "sessao"
    }}
  ]
}}

Só gere perguntas sobre coisas que aparecem na sessão mas que
o LIBERTUS claramente não explorou em profundidade.
Se tudo foi coberto, retorne: {{"curiosidades": []}}"""

    PROMPT_CONTRADICAO = """O LIBERTUS encontrou uma contradição entre dois documentos.
Formule a pergunta de pesquisa que resolveria essa tensão.

TEMA DA CONTRADIÇÃO: {tema}
DOC A AFIRMA: {afirmacao_a}
DOC B AFIRMA: {afirmacao_b}

Responda APENAS em JSON:
{{
  "pergunta": "pergunta que, se respondida, resolveria essa contradição",
  "urgencia": 7.0
}}"""

    def __init__(self, groq_client=None, supabase_client=None):
        self.groq = groq_client
        self.sb   = supabase_client

    # ------------------------------------------------------------------
    # FONTE 1: Lacuna detectada após erro
    # ------------------------------------------------------------------
    def gerar_de_erro(self, entrada: str, resultado: str,
                      dominio: str, causa: str = "",
                      erro_id: str = None) -> Optional[dict]:
        """Detecta o que faltou saber e registra como curiosidade."""
        if not self.groq:
            return None

        # Evita duplicatas — já tem pergunta pendente nesse domínio?
        if self._ja_tem_pendente(dominio, entrada):
            return None

        try:
            prompt = self.PROMPT_LACUNA.format(
                entrada=entrada[:300],
                resultado=str(resultado)[:300],
                dominio=dominio,
                causa=causa[:200]
            )
            resp = self.groq.conversar(prompt, "")
            dados = self._parse_json(resp)

            if not dados.get("pergunta"):
                return None

            curiosidade = {
                "pergunta":     dados["pergunta"][:400],
                "dominio":      dados.get("dominio", dominio),
                "origem":       "lacuna",
                "contexto_id":  erro_id,
                "contexto_tipo":"erro",
                "urgencia":     float(dados.get("urgencia", 6.0)),
                "status":       "pendente",
            }
            self._salvar(curiosidade)
            print(f"  🤔 Curiosidade gerada [{dominio}]: {curiosidade['pergunta'][:70]}")
            return curiosidade

        except Exception as e:
            print(f"  ⚠️  AutoCuriosidade erro: {e}")
            return None

    # ------------------------------------------------------------------
    # FONTE 2: Contradição entre documentos
    # ------------------------------------------------------------------
    def gerar_de_contradicao(self, contradicao: dict) -> Optional[dict]:
        """Gera pergunta de estudo a partir de uma contradição aberta."""
        if not self.groq or not contradicao:
            return None

        tema = contradicao.get("tema", "")
        if self._ja_tem_pendente("contradicao", tema):
            return None

        try:
            prompt = self.PROMPT_CONTRADICAO.format(
                tema=tema,
                afirmacao_a=contradicao.get("afirmacao_a", "")[:200],
                afirmacao_b=contradicao.get("afirmacao_b", "")[:200]
            )
            resp = self.groq.conversar(prompt, "")
            dados = self._parse_json(resp)

            if not dados.get("pergunta"):
                return None

            curiosidade = {
                "pergunta":     dados["pergunta"][:400],
                "dominio":      contradicao.get("tipo_conflito", "geral"),
                "origem":       "contradicao",
                "contexto_id":  contradicao.get("id"),
                "contexto_tipo":"contradicao",
                "urgencia":     float(dados.get("urgencia", 7.0)),
                "status":       "pendente",
            }
            self._salvar(curiosidade)
            print(f"  🤔 Curiosidade de contradição: {curiosidade['pergunta'][:70]}")
            return curiosidade

        except Exception as e:
            print(f"  ⚠️  AutoCuriosidade contradição: {e}")
            return None

    # ------------------------------------------------------------------
    # FONTE 3: Análise da sessão atual
    # ------------------------------------------------------------------
    def gerar_de_sessao(self, historico_sessao: str,
                        dominios_conhecidos: list = None) -> list[dict]:
        """
        Analisa a sessão e detecta conceitos que o LIBERTUS
        mencionou mas não domina. Chame ao final de cada sessão.
        """
        if not self.groq or not historico_sessao:
            return []

        dominios_fmt = ", ".join(dominios_conhecidos or [
            "pentest básico", "nmap", "SQL injection", "Python",
            "Supabase", "Next.js", "SHIELD vendas", "Groq API"
        ])

        try:
            prompt = self.PROMPT_SESSAO.format(
                sessao=historico_sessao[:1500],
                dominios_conhecidos=dominios_fmt
            )
            resp = self.groq.conversar(prompt, "")
            dados = self._parse_json(resp)
            curiosidades_raw = dados.get("curiosidades", [])

        except Exception as e:
            print(f"  ⚠️  AutoCuriosidade sessão: {e}")
            return []

        salvas = []
        for c in curiosidades_raw:
            if not c.get("pergunta"):
                continue
            if self._ja_tem_pendente(c.get("dominio", ""), c.get("pergunta", "")):
                continue

            curiosidade = {
                "pergunta":     c["pergunta"][:400],
                "dominio":      c.get("dominio", "geral"),
                "origem":       "sessao",
                "contexto_tipo":"sessao",
                "urgencia":     float(c.get("urgencia", 5.0)),
                "status":       "pendente",
            }
            self._salvar(curiosidade)
            salvas.append(curiosidade)
            print(f"  🤔 Curiosidade de sessão: {curiosidade['pergunta'][:70]}")

        return salvas

    # ------------------------------------------------------------------
    # PRÓXIMA A ESTUDAR: retorna a curiosidade mais urgente
    # ------------------------------------------------------------------
    def proxima_a_estudar(self) -> Optional[dict]:
        """
        Retorna a pergunta mais urgente da fila de estudo.
        O LIBERTUS pode usar isso para pedir PDFs ao Lorran
        ou buscar na web automaticamente.
        """
        if not self.sb:
            return None
        try:
            rows = self.sb.get(
                "libertus_fila_estudo",
                "limit=1"
            )
            if rows:
                c = rows[0]
                print(f"\n📚 PRÓXIMO ESTUDO [{c.get('urgencia',0):.1f}/10]:")
                print(f"   {c.get('pergunta','?')}")
                print(f"   Domínio: {c.get('dominio','?')} | "
                      f"Origem: {c.get('origem','?')} | "
                      f"Bloqueou {c.get('vezes_bloqueou',0)}x")
                return c
            return None
        except Exception:
            return None

    # ------------------------------------------------------------------
    # REGISTRAR BLOQUEIO: curiosidade impediu uma resposta boa
    # ------------------------------------------------------------------
    def registrar_bloqueio(self, dominio: str, entrada: str):
        """
        Chamado quando o LIBERTUS não consegue responder algo.
        Aumenta urgência de curiosidades pendentes no mesmo domínio.
        """
        if not self.sb:
            return
        try:
            pendentes = self.sb.get(
                "libertus_curiosidades",
                f"dominio=eq.{dominio}&status=eq.pendente&select=id,urgencia,vezes_bloqueou"
            ) or []
            for c in pendentes:
                nova_urgencia = min(10.0, float(c.get("urgencia", 5.0)) + 0.5)
                novos_bloqueios = c.get("vezes_bloqueou", 0) + 1
                self.sb.patch(
                    "libertus_curiosidades",
                    f"id=eq.{c['id']}",
                    {
                        "urgencia": nova_urgencia,
                        "vezes_bloqueou": novos_bloqueios,
                        "updated_at": datetime.utcnow().isoformat()
                    }
                )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # RESPONDER: marca curiosidade como respondida
    # ------------------------------------------------------------------
    def responder(self, curiosidade_id: str, resposta: str,
                  fonte: str = "groq") -> bool:
        """Marca uma curiosidade como respondida após aprender."""
        if not self.sb:
            return False
        try:
            self.sb.patch(
                "libertus_curiosidades",
                f"id=eq.{curiosidade_id}",
                {
                    "status":        "respondida",
                    "resposta":      resposta[:800],
                    "fonte_resposta": fonte,
                    "updated_at":    datetime.utcnow().isoformat()
                }
            )
            print(f"  ✅ Curiosidade respondida via {fonte}")
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # STATUS: fila de estudo completa
    # ------------------------------------------------------------------
    def status(self):
        if not self.sb:
            return
        fila = self.sb.get("libertus_fila_estudo", "limit=8") or []
        total = len(fila)
        print(f"\n🤔 FILA DE ESTUDO: {total} perguntas pendentes")
        for c in fila[:5]:
            print(f"  [{c.get('urgencia',0):.1f}] ({c.get('origem','?')}) "
                  f"{c.get('pergunta','?')[:70]}")

    # ------------------------------------------------------------------
    # INTERNOS
    # ------------------------------------------------------------------
    def _ja_tem_pendente(self, dominio: str, texto: str) -> bool:
        """Evita duplicatas verificando se já existe pergunta similar."""
        if not self.sb:
            return False
        try:
            pendentes = self.sb.get(
                "libertus_curiosidades",
                f"dominio=eq.{dominio}&status=eq.pendente"
                "&select=pergunta&limit=10"
            ) or []
            texto_lower = texto.lower()[:50]
            return any(
                texto_lower in (p.get("pergunta") or "").lower()
                for p in pendentes
            )
        except Exception:
            return False

    def _salvar(self, curiosidade: dict) -> bool:
        if not self.sb:
            return False
        try:
            self.sb.post("libertus_curiosidades", curiosidade)
            return True
        except Exception as e:
            print(f"  ⚠️  Erro ao salvar curiosidade: {e}")
            return False

    def _parse_json(self, texto: str) -> dict:
        if not texto:
            return {}
        texto = texto.strip()
        if "```" in texto:
            import re
            match = re.search(r"```(?:json)?\s*([\s\S]+?)```", texto)
            if match:
                texto = match.group(1).strip()
        try:
            return json.loads(texto)
        except Exception:
            return {}
