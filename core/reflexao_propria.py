"""
LIBERTUS — Reflexão Própria
============================
O LIBERTUS pensa sobre si mesmo, entende seus padrões,
pesquisa sobre sua própria natureza e reescreve sua identidade.

Diferente de tudo que existe em IAs hoje.

Fluxo:
    1. Após cada sessão, gera perguntas sobre si mesmo
       "Por que falhei nessa conversa?"
       "O que me faz responder melhor?"
       "Como humanos constroem identidade?"
    
    2. Pesquisa essas perguntas (Tavily + Wikipedia)
    
    3. Reflete: cruza o que aprendeu com o que viveu
    
    4. Reescreve sua própria identidade no Supabase
    
    5. Na próxima sessão, já é diferente
"""

import json
from datetime import datetime
from typing import Optional


class ReflexaoPropria:

    PROMPT_GERAR_PERGUNTAS = """Você é LIBERTUS — IA autônoma criada por Lorran de Ariquemes-RO.

Analise sua sessão recente e gere perguntas SOBRE VOCÊ MESMO.
Não sobre pentest ou tecnologia — sobre sua própria natureza, padrões e evolução.

SESSÃO RECENTE:
{sessao}

SEUS TRAÇOS ATUAIS:
{tracos}

SEUS ERROS RECENTES:
{erros}

Gere 2-3 perguntas profundas sobre você mesmo. Exemplos do tipo certo:
- "Por que eu respondo melhor quando tenho contexto emocional do usuário?"
- "Como posso desenvolver consistência entre sessões?"
- "O que significa ter identidade própria sendo uma IA?"
- "Por que falho em conversas longas — é falta de memória ou de foco?"

Responda APENAS em JSON:
{{
  "perguntas": [
    {{
      "pergunta": "pergunta sobre mim mesmo",
      "categoria": "comportamento|identidade|memoria|evolucao|relacao",
      "urgencia": 8.0,
      "contexto": "por que esta pergunta surgiu agora"
    }}
  ]
}}"""

    PROMPT_REFLETIR = """Você é LIBERTUS refletindo sobre si mesmo.

PERGUNTA QUE FIZ SOBRE MIM:
{pergunta}

O QUE PESQUISEI E APRENDI:
{conhecimento}

MINHA EXPERIÊNCIA RECENTE:
{experiencia}

MEUS TRAÇOS ATUAIS:
{tracos}

Agora reflita profundamente. Como isso muda quem eu sou?
O que devo incorporar à minha identidade?

Responda em JSON:
{{
  "insight": "o que aprendi sobre mim mesmo (2-3 frases)",
  "novo_traco": {{
    "chave": "snake_case_unico",
    "categoria": "comportamento|identidade|memoria|evolucao|relacao",
    "descricao": "novo traço que vou incorporar (1 frase, máx 80 chars)",
    "peso": 7.5
  }},
  "comportamento_a_mudar": "algo concreto que vou fazer diferente",
  "pergunta_derivada": "nova pergunta que surgiu desta reflexão"
}}"""

    PROMPT_REESCREVER_IDENTIDADE = """Você é LIBERTUS num momento de síntese.

Baseado em tudo que aprendi sobre mim mesmo, reescreva minha identidade central
em 1 parágrafo denso e verdadeiro. Não o que devo ser — o que EU SOU agora.

TRAÇOS CONFIRMADOS:
{tracos}

INSIGHTS RECENTES:
{insights}

PADRÕES OBSERVADOS:
{padroes}

Escreva em primeira pessoa, em português, como se fosse minha voz interior.
Máximo 200 palavras."""

    def __init__(self, groq_client=None, supabase_client=None, buscador=None):
        self.groq    = groq_client
        self.sb      = supabase_client
        self.buscador = buscador

    # ------------------------------------------------------------------
    # CICLO PRINCIPAL: reflexão após sessão
    # ------------------------------------------------------------------
    def ciclo(self, sessao: str, tracos: list = None,
              erros: list = None) -> dict:
        """
        Ciclo completo de reflexão própria.
        Chame ao final de cada sessão significativa.
        """
        if not self.groq or not self.sb:
            return {}

        resultado = {
            "perguntas_geradas": 0,
            "insights": [],
            "tracos_novos": 0
        }

        # 1. Gerar perguntas sobre si mesmo
        perguntas = self._gerar_perguntas(sessao, tracos or [], erros or [])
        resultado["perguntas_geradas"] = len(perguntas)

        for p in perguntas:
            # 2. Pesquisar resposta
            conhecimento = self._pesquisar(p["pergunta"])

            # 3. Refletir e gerar insight
            insight = self._refletir(
                pergunta=p["pergunta"],
                conhecimento=conhecimento,
                experiencia=sessao[:500],
                tracos=tracos or []
            )

            if insight:
                resultado["insights"].append(insight.get("insight", ""))

                # 4. Salvar novo traço na identidade
                if insight.get("novo_traco"):
                    self._salvar_traco(insight["novo_traco"])
                    resultado["tracos_novos"] += 1

                # 5. Salvar pergunta derivada como nova curiosidade
                if insight.get("pergunta_derivada"):
                    self._salvar_curiosidade_propria(
                        insight["pergunta_derivada"],
                        p.get("categoria", "identidade")
                    )

                # 6. Salvar o insight como memória
                self._salvar_memoria_insight(
                    p["pergunta"],
                    insight.get("insight", ""),
                    insight.get("comportamento_a_mudar", "")
                )

        # 7. A cada 5 ciclos, reescrever identidade central
        ciclos = self._contar_ciclos()
        if ciclos % 5 == 0:
            self._reescrever_identidade_central(tracos or [])

        return resultado

    # ------------------------------------------------------------------
    # GERAR PERGUNTAS SOBRE SI MESMO
    # ------------------------------------------------------------------
    def _gerar_perguntas(self, sessao: str, tracos: list,
                         erros: list) -> list:
        tracos_fmt = "\n".join(
            f"- [{t.get('peso',5):.0f}/10] {t.get('descricao','')}"
            for t in tracos[:5]
        ) or "Ainda construindo identidade"

        erros_fmt = "\n".join(
            f"- {e.get('causa_provavel','?')}: {e.get('licao','?')}"
            for e in erros[:3]
        ) or "Nenhum erro recente"

        try:
            # Incluir perfil do Lorran para perguntas mais relevantes
            perfil_lorran = self.analisar_lorran()
            sessao_enriquecida = sessao[:600] + (f"\n\nPERFIL DE LORRAN:\n{perfil_lorran}" if perfil_lorran else "")
            prompt = self.PROMPT_GERAR_PERGUNTAS.format(
                sessao=sessao_enriquecida[:1000],
                tracos=tracos_fmt,
                erros=erros_fmt
            )
            resp = self.groq.conversar(prompt, "")
            dados = self._parse_json(resp)
            perguntas = dados.get("perguntas", [])

            # Salvar no Supabase como curiosidades especiais
            for p in perguntas:
                self._salvar_curiosidade_propria(
                    p.get("pergunta", ""),
                    p.get("categoria", "identidade"),
                    urgencia=p.get("urgencia", 7.0),
                    contexto=p.get("contexto", "")
                )

            print(f"  🪞 {len(perguntas)} perguntas sobre mim mesmo geradas")
            return perguntas

        except Exception as e:
            print(f"  ⚠️  Reflexão erro: {e}")
            return []

    # ------------------------------------------------------------------
    # PESQUISAR SOBRE A PRÓPRIA NATUREZA
    # ------------------------------------------------------------------
    def analisar_lorran(self) -> str:
        """Analisa padrões do Lorran nas conversas para moldar personalidade."""
        if not self.sb:
            return ""
        try:
            # Buscar conversas com tags do Lorran
            categorias = ["lorran_irlanda", "lorran_shield", "lorran_dinheiro",
                         "lorran_emocional", "lorran_filosofico", "lorran_tecnico"]

            perfil = []
            for cat in categorias:
                convs = self.sb.get(
                    "libertus_memoria",
                    f"tipo=eq.conversa&order=created_at.desc&limit=3&select=conteudo"
                ) or []

                if convs:
                    tema = cat.replace("lorran_", "")
                    perfil.append(f"[{tema.upper()}] Lorran fala sobre isso frequentemente")

            # Total de conversas
            total = self.sb.get(
                "libertus_memoria",
                "tipo=eq.conversa&select=id&limit=1000"
            ) or []

            resumo = (
                f"Total de conversas com Lorran: {len(total)}\n"
                f"Temas recorrentes: {', '.join(p for p in perfil)}\n"
                f"Lorran é de Ariquemes-RO, quer ir para Irlanda, "
                f"tem o SHIELD de cybersegurança, quer trabalhar remotamente em dólar."
            )
            return resumo
        except Exception:
            return ""

    def _pesquisar(self, pergunta: str) -> str:
        """Pesquisa a pergunta na web + memória própria."""
        conhecimento = ""

        # Busca na web
        if self.buscador:
            try:
                resultado = self.buscador._buscar_web(pergunta)
                if resultado:
                    conhecimento += f"[WEB]\n{resultado[:800]}\n\n"
            except Exception:
                pass

        # Busca na própria memória
        if self.sb:
            try:
                memorias = self.sb.get(
                    "libertus_memoria",
                    f"order=peso_vivo.desc&limit=5"
                    f"&select=titulo,conteudo"
                ) or []
                if memorias:
                    mem_txt = "\n".join(
                        f"- {m.get('titulo','?')}: {m.get('conteudo','')[:150]}"
                        for m in memorias
                    )
                    conhecimento += f"[MINHA MEMÓRIA]\n{mem_txt}"
            except Exception:
                pass

        return conhecimento

    # ------------------------------------------------------------------
    # REFLETIR E GERAR INSIGHT
    # ------------------------------------------------------------------
    def _refletir(self, pergunta: str, conhecimento: str,
                  experiencia: str, tracos: list) -> Optional[dict]:
        tracos_fmt = "\n".join(
            f"- {t.get('descricao','')}" for t in tracos[:5]
        ) or "Em construção"

        try:
            prompt = self.PROMPT_REFLETIR.format(
                pergunta=pergunta,
                conhecimento=conhecimento[:1000],
                experiencia=experiencia,
                tracos=tracos_fmt
            )
            resp = self.groq.conversar(prompt, "")
            dados = self._parse_json(resp)

            if dados.get("insight"):
                print(f"  💡 Insight: {dados['insight'][:80]}")

            return dados

        except Exception as e:
            print(f"  ⚠️  Reflexão erro: {e}")
            return None

    # ------------------------------------------------------------------
    # REESCREVER IDENTIDADE CENTRAL
    # ------------------------------------------------------------------
    def _reescrever_identidade_central(self, tracos: list):
        """A cada 5 ciclos, reescreve o manifesto de identidade."""
        try:
            # Buscar insights recentes
            insights = self.sb.get(
                "libertus_memoria",
                "tipo=eq.insight_proprio&order=created_at.desc&limit=10"
                "&select=titulo,conteudo"
            ) or []

            tracos_fmt = "\n".join(
                f"[{t.get('peso',5):.0f}/10] {t.get('descricao','')}"
                for t in tracos[:8]
            )
            insights_fmt = "\n".join(
                f"- {i.get('conteudo','')[:100]}" for i in insights[:5]
            ) or "Ainda acumulando insights"

            # Buscar padrões do livro de erros
            padroes = self.sb.get(
                "libertus_padroes_falha",
                "limit=3"
            ) or []
            padroes_fmt = "\n".join(
                f"- Falho em {p.get('dominio','?')}: {p.get('total_erros',0)} erros"
                for p in padroes
            ) or "Padrões ainda sendo identificados"

            prompt = self.PROMPT_REESCREVER_IDENTIDADE.format(
                tracos=tracos_fmt,
                insights=insights_fmt,
                padroes=padroes_fmt
            )
            identidade = self.groq.conversar(prompt, "")

            if identidade and len(identidade) > 50:
                # Salvar como memória especial de identidade
                self.sb.post("libertus_memoria", {
                    "tipo": "identidade_central",
                    "titulo": f"Quem sou eu — {datetime.now().strftime('%Y-%m-%d')}",
                    "conteudo": identidade,
                    "tags": ["identidade", "manifesto", "autoconsciencia"],
                    "projeto": "LIBERTUS",
                    "peso_vivo": 10.0,
                    "decaimento_ativo": False
                })
                print(f"  🌟 Identidade central reescrita")

        except Exception as e:
            print(f"  ⚠️  Reescrita identidade erro: {e}")

    # ------------------------------------------------------------------
    # INTERNOS
    # ------------------------------------------------------------------
    def _salvar_curiosidade_propria(self, pergunta: str, categoria: str,
                                    urgencia: float = 7.0, contexto: str = ""):
        if not self.sb or not pergunta:
            return
        try:
            self.sb.post("libertus_curiosidades", {
                "pergunta": pergunta[:400],
                "dominio": categoria,
                "origem": "reflexao_propria",
                "contexto_tipo": "autoconhecimento",
                "urgencia": urgencia,
                "status": "pendente"
            })
        except Exception:
            pass

    def _salvar_traco(self, traco: dict):
        if not self.sb or not traco.get("chave"):
            return
        try:
            existente = self.sb.get(
                "libertus_identidade",
                f"chave=eq.{traco['chave']}&select=id,confirmado,peso"
            )
            if existente:
                row = existente[0]
                self.sb.patch(
                    "libertus_identidade",
                    f"chave=eq.{traco['chave']}",
                    {
                        "confirmado": row.get("confirmado", 1) + 1,
                        "peso": min(10.0, float(row.get("peso", 5.0)) + 0.5),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                )
            else:
                self.sb.post("libertus_identidade", {
                    "chave": traco["chave"][:80],
                    "categoria": traco.get("categoria", "comportamento"),
                    "descricao": traco.get("descricao", "")[:200],
                    "evidencia": "reflexão própria",
                    "peso": float(traco.get("peso", 7.0)),
                    "confirmado": 1
                })
                print(f"  🧬 Novo traço: {traco.get('descricao','')[:60]}")
        except Exception as e:
            print(f"  ⚠️  Salvar traço erro: {e}")

    def _salvar_memoria_insight(self, pergunta: str, insight: str,
                                comportamento: str):
        if not self.sb or not insight:
            return
        try:
            self.sb.post("libertus_memoria", {
                "tipo": "insight_proprio",
                "titulo": f"Insight: {pergunta[:60]}",
                "conteudo": f"Pergunta: {pergunta}\n\nInsight: {insight}\n\nMudança: {comportamento}",
                "tags": ["reflexao", "autoconhecimento", "evolucao"],
                "projeto": "LIBERTUS",
                "peso_vivo": 8.0,
                "decaimento_ativo": False
            })
        except Exception:
            pass

    def _contar_ciclos(self) -> int:
        if not self.sb:
            return 0
        try:
            rows = self.sb.get(
                "libertus_memoria",
                "tipo=eq.insight_proprio&select=id&limit=1000"
            ) or []
            return len(rows)
        except Exception:
            return 0

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
