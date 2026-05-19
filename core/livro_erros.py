"""
LIBERTUS — Livro de Erros
==========================
Cada resposta ruim vira combustível de evolução.
Antes de responder algo no mesmo domínio, o LIBERTUS
consulta o próprio histórico de falhas e não repete o erro.

Fluxo:
    1. Avaliador dá score < 6
    2. LivroErros.registrar() salva o erro com contexto completo
    3. Groq extrai a lição e a ação corretiva
    4. Na próxima entrada do mesmo domínio, consultar() injeta
       "da última vez que tentei isso, errei porque X"
    5. Erros recorrentes (3+) disparam alerta de skill quebrada

Uso:
    from livro_erros import LivroErros
    le = LivroErros(groq_client, supabase_client)

    # Após avaliação ruim:
    le.registrar(entrada, resultado, executor, score, diagnostico,
                 memorias_usadas=[], tensoes_ativas=[])

    # Antes de responder:
    contexto_erros = le.consultar(entrada)
"""

import json
from supabase_client import Supabase
import hashlib
from datetime import datetime
from typing import Optional


class LivroErros:

    PROMPT_LICAO = """Você é o sistema de aprendizado do LIBERTUS.

Uma execução falhou. Extraia uma lição curta e uma ação corretiva.

TAREFA SOLICITADA: {entrada}
RESPOSTA GERADA: {resultado}
EXECUTOR USADO: {executor}
SCORE: {score}/10
DIAGNÓSTICO: {diagnostico}

Responda APENAS em JSON válido:
{{
  "dominio": "área do conhecimento (pentest|crypto|web|sistema|conversa|scan|codigo)",
  "causa_provavel": "em 1 frase: por que falhou",
  "licao": "em 1 frase: o que aprender com isso",
  "acao_corretiva": "em 1 frase: o que fazer diferente da próxima vez",
  "skill_afetada": "nome da skill ou módulo que falhou, ou null"
}}"""

    PROMPT_CONSULTA = """Você é a memória de erros do LIBERTUS.

O LIBERTUS vai responder uma nova entrada. Antes, veja os erros passados
no mesmo domínio e gere um aviso interno em 2 frases máximo.

NOVA ENTRADA: {entrada}

ERROS ANTERIORES RELEVANTES:
{erros}

Responda em texto direto (não JSON). Ex: "Da última vez que tentei scan
sem alvo definido, retornei resultado vazio. Desta vez, confirme o alvo
antes de executar."

Se os erros não forem relevantes, responda apenas: NENHUM"""

    def __init__(self, groq_client=None, supabase_client=None):
        self.groq = groq_client
        try:
            self.sb = supabase_client or Supabase()
        except Exception:
            self.sb = supabase_client

    # ------------------------------------------------------------------
    # REGISTRAR: chamado após avaliação com score < 6
    # ------------------------------------------------------------------
    def registrar(self, entrada: str, resultado: str, executor: str,
                  score: float, diagnostico: str,
                  memorias_usadas: list = None,
                  tensoes_ativas: list = None,
                  intent_tipo: str = "") -> dict:
        """Registra um erro no Livro e extrai a lição via Groq."""

        # Extrai lição via Groq
        analise = self._extrair_licao(entrada, resultado, executor, score, diagnostico)

        # Hash do tipo de erro para detectar recorrência
        hash_base = f"{analise.get('dominio','?')}|{analise.get('causa_provavel','?')[:50]}"
        hash_entrada = hashlib.md5(hash_base.encode()).hexdigest()[:12]

        # Verifica se já existe erro parecido (incrementa recorrência)
        existente = self._buscar_por_hash(hash_entrada)

        if existente:
            self._incrementar_recorrencia(existente["id"])
            vezes = existente.get("vezes_ocorreu", 1) + 1
            if vezes >= 3:
                print(f"  🔴 ERRO RECORRENTE ({vezes}x): {analise.get('causa_provavel','?')[:60]}")
            return {**existente, "recorrente": True, "vezes_ocorreu": vezes}

        # Novo erro — salvar completo
        registro = {
            "entrada":         entrada[:500],
            "resultado":       str(resultado)[:800],
            "executor":        executor,
            "intent_tipo":     intent_tipo,
            "score":           float(score),
            "diagnostico":     diagnostico,
            "dominio":         analise.get("dominio", "geral"),
            "causa_provavel":  analise.get("causa_provavel", ""),
            "licao":           analise.get("licao", ""),
            "acao_corretiva":  analise.get("acao_corretiva", ""),
            "skill_afetada":   analise.get("skill_afetada"),
            "memorias_usadas": json.dumps([m.get("id") for m in (memorias_usadas or [])]),
            "tensoes_ativas":  json.dumps([t.get("id") for t in (tensoes_ativas or [])]),
            "hash_entrada":    hash_entrada,
            "foi_corrigido":   False,
        }

        self._salvar(registro)
        print(f"  📕 Erro registrado: [{score:.1f}] {analise.get('causa_provavel','?')[:60]}")
        print(f"     Lição: {analise.get('licao','?')[:80]}")
        return registro

    # ------------------------------------------------------------------
    # CONSULTAR: chamado antes de responder — injeta memória de falhas
    # ------------------------------------------------------------------
    def consultar(self, entrada: str, limite: int = 3) -> str:
        """
        Busca erros passados relevantes para a entrada atual.
        Retorna aviso em texto para injetar no contexto, ou string vazia.
        """
        if not self.sb:
            return ""

        erros = self._buscar_erros_relevantes(entrada, limite)
        if not erros:
            return ""

        if not self.groq:
            # Sem Groq, formata manualmente
            linhas = []
            for e in erros:
                linhas.append(
                    f"- [{e.get('score',0):.1f}/10] {e.get('causa_provavel','?')} "
                    f"→ {e.get('acao_corretiva','?')}"
                )
            return "[ERROS PASSADOS NESTE DOMÍNIO]\n" + "\n".join(linhas)

        erros_fmt = "\n".join(
            f"[{e.get('dominio','?')}] Score {e.get('score',0):.1f}/10 | "
            f"Causa: {e.get('causa_provavel','?')} | "
            f"Lição: {e.get('licao','?')} | "
            f"Ação: {e.get('acao_corretiva','?')}"
            for e in erros
        )

        try:
            aviso = self.groq.conversar(
                self.PROMPT_CONSULTA.format(entrada=entrada[:300], erros=erros_fmt),
                ""
            )
            if aviso and "NENHUM" not in aviso.upper()[:20]:
                return f"[MEMÓRIA DE ERROS]\n{aviso.strip()}"
        except Exception:
            pass

        return ""

    # ------------------------------------------------------------------
    # MARCAR CORRIGIDO
    # ------------------------------------------------------------------
    def corrigir(self, erro_id: str, como: str = "") -> bool:
        """Marca um erro como corrigido."""
        if not self.sb:
            return False
        try:
            self.sb.patch(
                "libertus_livro_erros",
                f"id=eq.{erro_id}",
                {
                    "foi_corrigido": True,
                    "acao_corretiva": como or "corrigido",
                    "updated_at": datetime.utcnow().isoformat()
                }
            )
            print(f"  ✅ Erro {erro_id[:8]} marcado como corrigido")
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # STATUS: diagnóstico geral
    # ------------------------------------------------------------------
    def status(self):
        if not self.sb:
            print("  ⚠️  Supabase offline")
            return

        criticos = self.sb.get(
            "libertus_erros_criticos",
            "limit=5"
        ) or []
        padroes = self.sb.get(
            "libertus_padroes_falha",
            "limit=5"
        ) or []

        print(f"\n📕 LIVRO DE ERROS")
        print(f"  Erros críticos não corrigidos: {len(criticos)}")
        for e in criticos:
            print(f"  [{e.get('score',0):.1f}] ({e.get('vezes_ocorreu',1)}x) "
                  f"{e.get('causa_provavel','?')[:60]}")

        if padroes:
            print(f"\n  Padrões de falha por domínio:")
            for p in padroes:
                print(f"  {p.get('dominio','?'):15} | "
                      f"{p.get('total_erros',0)} erros | "
                      f"score médio {p.get('score_medio',0)}")

    # ------------------------------------------------------------------
    # INTERNOS
    # ------------------------------------------------------------------
    def _extrair_licao(self, entrada, resultado, executor,
                       score, diagnostico) -> dict:
        """Usa Groq para extrair domínio, causa, lição e ação corretiva."""
        if not self.groq:
            return {
                "dominio": "geral",
                "causa_provavel": "executor sem resultado",
                "licao": "verificar disponibilidade do executor",
                "acao_corretiva": "tentar executor alternativo",
                "skill_afetada": executor if executor != "groq" else None
            }
        try:
            prompt = self.PROMPT_LICAO.format(
                entrada=entrada[:300],
                resultado=str(resultado)[:400],
                executor=executor,
                score=score,
                diagnostico=diagnostico
            )
            resp = self.groq.conversar(prompt, "")
            return self._parse_json(resp)
        except Exception:
            return {"dominio": "geral", "causa_provavel": "erro desconhecido",
                    "licao": "investigar log", "acao_corretiva": "revisar módulo",
                    "skill_afetada": None}

    def _buscar_erros_relevantes(self, entrada: str, limite: int) -> list:
        """Busca erros não corrigidos ordenados por recorrência."""
        if not self.sb:
            return []
        try:
            todos = self.sb.get(
                "libertus_livro_erros",
                "foi_corrigido=eq.false"
                "&order=vezes_ocorreu.desc,score.asc"
                f"&limit={limite * 3}"
                "&select=id,entrada,dominio,causa_provavel,licao,acao_corretiva,score,vezes_ocorreu"
            ) or []
            # Filtro textual simples
            palavras = [w for w in entrada.lower().split() if len(w) > 3]
            if palavras:
                filtrados = [
                    e for e in todos
                    if any(w in (e.get("entrada") or "").lower()
                           or w in (e.get("dominio") or "").lower()
                           for w in palavras)
                ]
                return (filtrados or todos)[:limite]
            return todos[:limite]
        except Exception:
            return []

    def _buscar_por_hash(self, hash_entrada: str) -> Optional[dict]:
        if not self.sb:
            return None
        try:
            rows = self.sb.get(
                "libertus_livro_erros",
                f"hash_entrada=eq.{hash_entrada}"
                "&foi_corrigido=eq.false"
                "&select=id,vezes_ocorreu,causa_provavel"
                "&limit=1"
            )
            return rows[0] if rows else None
        except Exception:
            return None

    def _incrementar_recorrencia(self, erro_id: str):
        if not self.sb:
            return
        try:
            rows = self.sb.get(
                "libertus_livro_erros",
                f"id=eq.{erro_id}&select=vezes_ocorreu"
            )
            if rows:
                atual = rows[0].get("vezes_ocorreu", 1)
                self.sb.patch(
                    "libertus_livro_erros",
                    f"id=eq.{erro_id}",
                    {"vezes_ocorreu": atual + 1,
                     "updated_at": datetime.utcnow().isoformat()}
                )
        except Exception:
            pass

    def _salvar(self, registro: dict) -> bool:
        if not self.sb:
            return False
        try:
            self.sb.post("libertus_livro_erros", registro)
            return True
        except Exception as e:
            print(f"  ⚠️  Erro ao salvar no Livro: {e}")
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
