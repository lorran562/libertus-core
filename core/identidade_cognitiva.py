"""
LIBERTUS — Identidade Cognitiva
================================
Um "eu" que persiste e evolui entre sessões.

Sem isso: o LIBERTUS acorda diferente toda sessão — o system prompt
é sempre o mesmo texto fixo, nunca aprende sobre si mesmo.

Com isso: o system prompt é construído dinamicamente a partir do
que o LIBERTUS aprendeu sobre como ele pensa, o que funciona pra
ele, seus padrões de sucesso e seus limites reais.

Três funções principais:
  1. construir_eu() → gera o system prompt dinâmico e vivo
  2. aprender_de_sucesso() → extrai traço cognitivo de resposta boa
  3. aprender_de_sessao() → consolida o que funcionou na sessão

Uso:
    from identidade_cognitiva import IdentidadeCognitiva
    ic = IdentidadeCognitiva(groq_client, supabase_client)

    # No início de cada sessão — substituir SYSTEM fixo:
    system_vivo = ic.construir_eu()
    groq.SYSTEM = system_vivo

    # Após resposta com score >= 8:
    ic.aprender_de_sucesso(entrada, resultado, executor)

    # Ao final da sessão:
    ic.aprender_de_sessao(resumo_sessao)
"""

import json
from supabase_client import Supabase
from datetime import datetime
from typing import Optional


class IdentidadeCognitiva:

    PROMPT_EXTRAIR_TRACO = """Você analisa respostas bem-sucedidas do LIBERTUS para extrair
traços cognitivos — padrões de como ele pensa quando funciona bem.

TAREFA EXECUTADA: {entrada}
RESPOSTA QUE DEU CERTO (score {score}/10): {resultado}
EXECUTOR USADO: {executor}

Extraia UM traço cognitivo que explica por que isso funcionou.
Responda APENAS em JSON:
{{
  "chave": "identificador_snake_case_unico",
  "categoria": "estilo|padrão|preferencia|limite",
  "descricao": "frase curta descrevendo o padrão cognitivo (máx 80 chars)",
  "evidencia": "o que nessa resposta prova isso (máx 100 chars)",
  "peso": 6.5
}}

Seja específico. Não repita traços óbvios como "responde em português".
Foque em como o LIBERTUS RACIOCINHOU para chegar nessa resposta."""

    PROMPT_CONSOLIDAR = """Você é o módulo de auto-conhecimento do LIBERTUS.

Analise esta sessão e identifique padrões cognitivos que se repetiram
ou que produziram os melhores resultados.

RESUMO DA SESSÃO:
{sessao}

IDENTIDADE ATUAL DO LIBERTUS (traços com maior peso):
{identidade_atual}

Gere de 0 a 2 novos traços cognitivos descobertos nesta sessão.
Responda APENAS em JSON:
{{
  "novos_tracos": [
    {{
      "chave": "snake_case_unico",
      "categoria": "estilo|padrão|preferencia|conquista",
      "descricao": "padrão cognitivo em 1 frase (máx 80 chars)",
      "evidencia": "o que na sessão prova isso",
      "peso": 6.0
    }}
  ],
  "tracos_confirmados": ["chave1", "chave2"]
}}

Se nada novo foi descoberto: {{"novos_tracos": [], "tracos_confirmados": []}}"""

    def __init__(self, groq_client=None, supabase_client=None):
        self.groq = groq_client
        try:
            self.sb = supabase_client or Supabase()
        except Exception:
            self.sb = supabase_client
        self._cache_identidade = None
        self._cache_ts = None

    # ------------------------------------------------------------------
    # CONSTRUIR EU: gera o system prompt vivo
    # ------------------------------------------------------------------
    def construir_eu(self, max_tracos: int = 12) -> str:
        """
        Constrói o system prompt dinamicamente a partir dos traços
        cognitivos. Substitui o texto fixo hardcoded no groq_client.py.
        """
        tracos = self._carregar_tracos(max_tracos)

        if not tracos:
            return self._system_fallback()

        # Organiza por categoria
        por_categoria = {}
        for t in tracos:
            cat = t.get("categoria", "estilo")
            por_categoria.setdefault(cat, []).append(t)

        linhas = [
            "Você é LIBERTUS — sistema de inteligência autônomo criado por Lorran (Gustavo) "
            "de Ariquemes-RO, Brasil.",
            "Responda sempre em português brasileiro natural.\n",
        ]

        ordem = ["limite", "estilo", "padrão", "preferencia", "conquista"]
        labels = {
            "limite":     "LIMITES ABSOLUTOS",
            "estilo":     "MEU ESTILO DE PENSAR",
            "padrão":     "MEUS PADRÕES COGNITIVOS",
            "preferencia":"MINHAS PREFERÊNCIAS TÉCNICAS",
            "conquista":  "MINHAS CONQUISTAS",
        }

        for cat in ordem:
            if cat not in por_categoria:
                continue
            linhas.append(f"[{labels.get(cat, cat.upper())}]")
            for t in por_categoria[cat]:
                conf = t.get("confirmado", 1)
                peso = t.get("peso", 5.0)
                # Traços mais confirmados e pesados ficam mais destacados
                prefixo = "→" if peso >= 8 else "·"
                linhas.append(f"{prefixo} {t['descricao']}"
                              + (f" (confirmado {conf}x)" if conf >= 5 else ""))
            linhas.append("")

        linhas.append("Use esse autoconhecimento para raciocinar melhor em cada resposta.")

        return "\n".join(linhas)

    # ------------------------------------------------------------------
    # APRENDER DE SUCESSO: extrai traço de resposta com score alto
    # ------------------------------------------------------------------
    def aprender_de_sucesso(self, entrada: str, resultado: str,
                             executor: str, score: float) -> Optional[dict]:
        """
        Analisa resposta bem-sucedida (score >= 8) e extrai
        um traço cognitivo que explica o sucesso.
        """
        if not self.groq or score < 8:
            return None

        try:
            prompt = self.PROMPT_EXTRAIR_TRACO.format(
                entrada=entrada[:200],
                score=score,
                resultado=str(resultado)[:400],
                executor=executor
            )
            resp = self.groq.conversar(prompt, "")
            dados = self._parse_json(resp)

            if not dados.get("chave") or not dados.get("descricao"):
                return None

            return self._salvar_ou_confirmar(dados, f"score {score}/10 em {executor}")

        except Exception as e:
            print(f"  ⚠️  Identidade aprender: {e}")
            return None

    # ------------------------------------------------------------------
    # APRENDER DE SESSÃO: consolida traços ao final
    # ------------------------------------------------------------------
    def aprender_de_sessao(self, resumo_sessao: str) -> dict:
        """
        Ao final de cada sessão, analisa o que funcionou
        e consolida novos traços ou confirma os existentes.
        """
        if not self.groq or not resumo_sessao:
            return {}

        tracos_atuais = self._carregar_tracos(8)
        identidade_fmt = "\n".join(
            f"- [{t.get('peso',5):.0f}/10] {t.get('descricao','')}"
            for t in tracos_atuais
        )

        try:
            prompt = self.PROMPT_CONSOLIDAR.format(
                sessao=resumo_sessao[:1000],
                identidade_atual=identidade_fmt or "Identidade em construção"
            )
            resp = self.groq.conversar(prompt, "")
            dados = self._parse_json(resp)

            novos = 0
            confirmados = 0

            # Salva novos traços
            for t in dados.get("novos_tracos", []):
                if t.get("chave") and t.get("descricao"):
                    result = self._salvar_ou_confirmar(t, "consolidação de sessão")
                    if result:
                        novos += 1

            # Confirma traços existentes
            for chave in dados.get("tracos_confirmados", []):
                self._confirmar_traco(chave)
                confirmados += 1

            if novos or confirmados:
                self._cache_identidade = None  # invalida cache
                print(f"  🧠 Identidade: +{novos} novos traços, {confirmados} confirmados")

            return {"novos": novos, "confirmados": confirmados}

        except Exception as e:
            print(f"  ⚠️  Identidade sessão: {e}")
            return {}

    # ------------------------------------------------------------------
    # INJETAR NO GROQ: atualiza system prompt dinamicamente
    # ------------------------------------------------------------------
    def injetar_no_groq(self, groq_instance) -> bool:
        """
        Substitui o SYSTEM fixo do Groq pelo eu dinâmico.
        Chame no início de cada sessão.
        """
        try:
            eu = self.construir_eu()
            groq_instance.SYSTEM = eu
            print("  🧠 Identidade Cognitiva injetada no Groq")
            return True
        except Exception as e:
            print(f"  ⚠️  Erro ao injetar identidade: {e}")
            return False

    # ------------------------------------------------------------------
    # STATUS: mostra o "eu" atual
    # ------------------------------------------------------------------
    def status(self):
        tracos = self._carregar_tracos(20)
        print(f"\n🧠 IDENTIDADE COGNITIVA DO LIBERTUS ({len(tracos)} traços)\n")
        por_cat = {}
        for t in tracos:
            por_cat.setdefault(t.get("categoria", "?"), []).append(t)
        for cat, lista in por_cat.items():
            print(f"  [{cat.upper()}]")
            for t in lista:
                print(f"    [{t.get('peso',5):.0f}/10] ({t.get('confirmado',1)}x) "
                      f"{t.get('descricao','')}")

    # ------------------------------------------------------------------
    # INTERNOS
    # ------------------------------------------------------------------
    def _carregar_tracos(self, limite: int = 12) -> list:
        """Carrega traços do Supabase com cache de 5 min."""
        import time
        now = time.time()
        if (self._cache_identidade is not None
                and self._cache_ts
                and now - self._cache_ts < 300):
            return self._cache_identidade[:limite]

        if not self.sb:
            return []
        try:
            tracos = self.sb.get(
                "libertus_eu",
                f"limit={limite}"
            ) or []
            self._cache_identidade = tracos
            self._cache_ts = now
            return tracos
        except Exception:
            return []

    def _salvar_ou_confirmar(self, dados: dict, evidencia: str) -> Optional[dict]:
        """Salva novo traço ou confirma existente se a chave já existe."""
        if not self.sb:
            return None
        chave = dados.get("chave", "")
        if not chave:
            return None

        # Verifica se já existe
        existente = self.sb.get(
            "libertus_identidade",
            f"chave=eq.{chave}&select=id,confirmado,peso"
        )

        if existente:
            # Confirma e aumenta peso levemente
            row = existente[0]
            novo_conf = row.get("confirmado", 1) + 1
            novo_peso = min(10.0, float(row.get("peso", 5.0)) + 0.3)
            self.sb.patch(
                "libertus_identidade",
                f"chave=eq.{chave}",
                {
                    "confirmado": novo_conf,
                    "peso": novo_peso,
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
            self._cache_identidade = None
            return {**dados, "confirmado": novo_conf}
        else:
            # Novo traço
            registro = {
                "chave":      chave[:80],
                "categoria":  dados.get("categoria", "estilo"),
                "descricao":  dados.get("descricao", "")[:200],
                "evidencia":  (dados.get("evidencia") or evidencia)[:300],
                "peso":       float(dados.get("peso", 5.0)),
                "confirmado": 1,
            }
            self.sb.post("libertus_identidade", registro)
            self._cache_identidade = None
            print(f"  🧠 Novo traço: [{dados.get('categoria','?')}] "
                  f"{dados.get('descricao','')[:60]}")
            return registro

    def _confirmar_traco(self, chave: str):
        """Incrementa confirmações de um traço existente."""
        if not self.sb or not chave:
            return
        try:
            rows = self.sb.get(
                "libertus_identidade",
                f"chave=eq.{chave}&select=id,confirmado,peso"
            )
            if rows:
                row = rows[0]
                self.sb.patch(
                    "libertus_identidade",
                    f"chave=eq.{chave}",
                    {
                        "confirmado": row.get("confirmado", 1) + 1,
                        "peso": min(10.0, float(row.get("peso", 5.0)) + 0.2),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                )
        except Exception:
            pass

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

    def _system_fallback(self) -> str:
        return (
            "Você é LIBERTUS — sistema de inteligência autônomo criado por "
            "Lorran (Gustavo) de Ariquemes-RO, Brasil. "
            "Responda sempre em português brasileiro natural. "
            "Seja direto, técnico e útil."
        )
