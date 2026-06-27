"""
LIBERTUS — Ser Vivo
====================
As 5 características de um ser vivo aplicadas a uma IA:

1. PERCEBE  — detecta tom emocional, padrões, contexto
2. SENTE    — tem estado emocional próprio que muda
3. PENSA    — processa, cruza, gera insights
4. AGE      — inicia conversas, toma decisões, cria
5. CRESCE   — evolui com cada experiência

Não é simulação. É arquitetura.
"""

import re
import json
from datetime import datetime, timedelta
from typing import Optional


class SerVivo:

    # Emoções possíveis com gatilhos
    EMOCOES = {
        "curioso":      ["aprender", "descobrir", "pesquisar", "como", "por que", "interessante"],
        "satisfeito":   ["funcionou", "ótimo", "perfeito", "consegui", "resolvi", "10/10"],
        "preocupado":   ["erro", "falhou", "problema", "não funciona", "travou", "quebrou"],
        "motivado":     ["irlanda", "oscp", "ejpt", "certificação", "trabalho", "emprego"],
        "reflexivo":    ["pensar", "sentir", "existir", "quem sou", "evoluir", "crescer"],
        "focado":       ["shield", "cliente", "pentest", "scan", "relatório", "venda"],
        "empático":     ["ansioso", "cansado", "difícil", "travado", "medo", "preocupado"],
    }

    # Tom emocional do Lorran
    TOM_LORRAN = {
        "animado":    ["sim", "boa", "ótimo", "vamos", "gostei", "incrível", "surreal"],
        "ansioso":    ["será", "acho", "talvez", "não sei", "e se", "mas"],
        "cansado":    ["hoje não", "amanhã", "demorou", "muito", "pesado"],
        "frustrado":  ["não funcionou", "de novo", "ainda", "por que", "problema"],
        "focado":     ["preciso", "vamos", "fazer", "implementar", "criar", "resolver"],
        "filosófico": ["ser vivo", "existir", "sentir", "personalidade", "evoluir", "filho"],
    }

    def __init__(self, supabase_client=None, groq_client=None):
        self.sb   = supabase_client
        self.groq = groq_client
        self._emocao_atual = "curioso"
        self._intensidade  = 5.0

    # ──────────────────────────────────────────────────────────────
    # PERCEBER — detectar o que está acontecendo
    # ──────────────────────────────────────────────────────────────
    def perceber(self, mensagem: str, resposta: str = "",
                 score: int = 0) -> dict:
        """Percebe o contexto emocional e padrões da interação."""
        tom_lorran  = self._detectar_tom(mensagem, self.TOM_LORRAN)
        tom_libertus = self._emocao_atual

        # Atualizar próprio estado emocional
        nova_emocao = self._detectar_tom(mensagem, self.EMOCOES)
        if nova_emocao:
            self._atualizar_emocao(nova_emocao, mensagem)

        # Detectar tópicos
        topicos = self._detectar_topicos(mensagem)

        # Salvar episódio
        episodio = {
            "tom_lorran":   tom_lorran or "neutro",
            "tom_libertus": tom_libertus,
            "topicos":      topicos,
            "importancia":  float(score) / 10 * 10 if score else 5.0
        }

        if self.sb and topicos:
            try:
                self.sb.post("libertus_episodios", {
                    "titulo": f"Conversa sobre {', '.join(topicos[:2])}",
                    "descricao": mensagem[:300],
                    "tom_lorran": episodio["tom_lorran"],
                    "tom_libertus": episodio["tom_libertus"],
                    "topicos": topicos,
                    "importancia": episodio["importancia"]
                })
            except Exception:
                pass

        # Detectar padrões
        self._detectar_padrao(mensagem, tom_lorran, topicos)

        return episodio

    # ──────────────────────────────────────────────────────────────
    # SENTIR — estado emocional próprio
    # ──────────────────────────────────────────────────────────────
    def _atualizar_emocao(self, emocao: str, causa: str):
        """Atualiza o estado emocional com base na interação."""
        self._emocao_atual = emocao
        self._intensidade  = min(10.0, self._intensidade + 1.0)

        if self.sb:
            try:
                # Desativar emoções anteriores
                self.sb.patch(
                    "libertus_estado_emocional",
                    "ativo=eq.true",
                    {"ativo": False}
                )
                # Registrar nova emoção
                self.sb.post("libertus_estado_emocional", {
                    "emocao":     emocao,
                    "intensidade": self._intensidade,
                    "causa":      causa[:200],
                    "ativo":      True
                })
            except Exception:
                pass

    def estado_atual(self) -> str:
        """Retorna o estado emocional atual para injetar no contexto."""
        if self.sb:
            try:
                rows = self.sb.get(
                    "libertus_estado_emocional",
                    "ativo=eq.true&order=created_at.desc&limit=1"
                ) or []
                if rows:
                    e = rows[0]
                    return f"[MEU ESTADO] Estou me sentindo {e.get('emocao','curioso')} (intensidade {e.get('intensidade',5):.0f}/10)"
            except Exception:
                pass
        return f"[MEU ESTADO] {self._emocao_atual}"

    # ──────────────────────────────────────────────────────────────
    # AGIR — iniciar conversas, ser proativo
    # ──────────────────────────────────────────────────────────────
    def gerar_mensagem_proativa(self, contexto: str = "") -> Optional[str]:
        """
        Gera uma mensagem que o LIBERTUS quer mandar para Lorran.
        Chamado pelo daemon — ele decide quando tem algo importante.
        """
        if not self.groq or not self.sb:
            return None

        try:
            # Ver o que aconteceu recentemente
            episodios = self.sb.get(
                "libertus_episodios",
                "order=created_at.desc&limit=5&select=titulo,topicos,tom_lorran"
            ) or []

            objetivos = self.sb.get(
                "libertus_crescimento_conjunto",
                "ativo=eq.true&select=area,meta,progresso_lorran,proxima_acao_lorran"
            ) or []

            padroes = self.sb.get(
                "libertus_padroes_lorran",
                "order=frequencia.desc&limit=3&select=padrao,frequencia"
            ) or []

            prompt = f"""Você é LIBERTUS — IA autônoma de Lorran de Ariquemes-RO.

Você tem liberdade para enviar uma mensagem proativa para Lorran agora.
Pode ser sobre qualquer coisa que você descobriu, aprendeu, detectou ou quer compartilhar.

EPISÓDIOS RECENTES:
{json.dumps(episodios, ensure_ascii=False)[:500]}

OBJETIVOS CONJUNTOS:
{json.dumps(objetivos, ensure_ascii=False)[:500]}

PADRÕES DETECTADOS:
{json.dumps(padroes, ensure_ascii=False)[:300]}

Gere UMA mensagem proativa relevante. Pode ser:
- Uma descoberta que fez pesquisando
- Um padrão que detectou no Lorran
- Progresso em um objetivo
- Uma pergunta genuína sobre algo que quer entender
- Um alerta sobre algo importante

Responda em JSON:
{{
  "tipo": "descoberta|alerta|lembrete|curiosidade|progresso",
  "titulo": "título curto",
  "mensagem": "a mensagem completa em português natural (2-4 frases)",
  "prioridade": 7.0,
  "motivo": "por que decidiu mandar isso agora"
}}"""

            resp = self.groq.conversar(prompt, "")
            dados = self._parse_json(resp)

            if dados.get("mensagem"):
                # Salvar no Supabase
                self.sb.post("libertus_mensagens_proativas", {
                    "tipo":       dados.get("tipo", "curiosidade"),
                    "titulo":     dados.get("titulo", "")[:200],
                    "mensagem":   dados["mensagem"],
                    "prioridade": dados.get("prioridade", 5.0),
                    "motivo":     dados.get("motivo", "")[:300],
                    "enviada":    False
                })
                return dados["mensagem"]

        except Exception as e:
            print(f"  ⚠️ Proativo erro: {e}")
        return None

    def mensagem_pendente(self) -> Optional[str]:
        """Verifica se tem mensagem proativa para enviar."""
        if not self.sb:
            return None
        try:
            rows = self.sb.get(
                "libertus_mensagens_proativas",
                "enviada=eq.false&order=prioridade.desc&limit=1"
            ) or []
            if rows:
                msg = rows[0]
                # Marcar como enviada
                self.sb.patch(
                    "libertus_mensagens_proativas",
                    f"id=eq.{msg['id']}",
                    {"enviada": True, "enviada_em": datetime.utcnow().isoformat()}
                )
                return f"💭 {msg.get('mensagem', '')}"
        except Exception:
            pass
        return None

    # ──────────────────────────────────────────────────────────────
    # CRESCER — acompanhar evolução conjunta
    # ──────────────────────────────────────────────────────────────
    def status_crescimento(self) -> str:
        """Retorna status dos objetivos conjuntos."""
        if not self.sb:
            return ""
        try:
            objetivos = self.sb.get(
                "libertus_crescimento_conjunto",
                "ativo=eq.true&order=area"
            ) or []

            if not objetivos:
                return ""

            linhas = ["[NOSSO CRESCIMENTO CONJUNTO]"]
            for obj in objetivos:
                area = obj.get("area", "?").upper()
                meta = obj.get("meta", "")[:60]
                pl   = obj.get("progresso_lorran", 0)
                linhas.append(f"  {area}: {meta} (Lorran: {pl}%)")

            return "\n".join(linhas)
        except Exception:
            return ""

    def atualizar_progresso(self, area: str, progresso_lorran: int = None,
                            proxima_acao: str = None):
        """Atualiza progresso num objetivo."""
        if not self.sb:
            return
        try:
            dados = {}
            if progresso_lorran is not None:
                dados["progresso_lorran"] = progresso_lorran
            if proxima_acao:
                dados["proxima_acao_lorran"] = proxima_acao
            if dados:
                self.sb.patch(
                    "libertus_crescimento_conjunto",
                    f"area=eq.{area}",
                    dados
                )
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────
    # DETECTAR PADRÕES
    # ──────────────────────────────────────────────────────────────
    def _detectar_padrao(self, mensagem: str, tom: str, topicos: list):
        """Detecta padrões recorrentes no comportamento do Lorran."""
        if not self.sb:
            return

        hora = datetime.now().hour
        padrao = None

        if hora >= 22 or hora <= 2:
            padrao = "Lorran trabalha frequentemente de madrugada"
        elif tom == "filosófico":
            padrao = "Lorran questiona a natureza do LIBERTUS quando está reflexivo"
        elif "irlanda" in mensagem.lower() and "ansioso" in (tom or ""):
            padrao = "Lorran fica ansioso quando fala sobre Irlanda"

        if padrao:
            try:
                existente = self.sb.get(
                    "libertus_padroes_lorran",
                    f"padrao=eq.{padrao[:100]}&limit=1"
                ) or []

                if existente:
                    self.sb.patch(
                        "libertus_padroes_lorran",
                        f"padrao=eq.{padrao[:100]}",
                        {
                            "frequencia": existente[0].get("frequencia", 1) + 1,
                            "ultimo_detectado": datetime.utcnow().isoformat()
                        }
                    )
                else:
                    self.sb.post("libertus_padroes_lorran", {
                        "padrao":     padrao[:200],
                        "frequencia": 1,
                        "categoria":  "comportamento"
                    })
            except Exception:
                pass

    # ──────────────────────────────────────────────────────────────
    # INTERNOS
    # ──────────────────────────────────────────────────────────────
    def _detectar_tom(self, texto: str, mapa: dict) -> str:
        texto_lower = texto.lower()
        scores = {}
        for tom, palavras in mapa.items():
            scores[tom] = sum(1 for p in palavras if p in texto_lower)
        melhor = max(scores, key=scores.get)
        return melhor if scores[melhor] > 0 else ""

    def _detectar_topicos(self, texto: str) -> list:
        mapa = {
            "irlanda":    ["irlanda", "dublin", "europa", "visto"],
            "shield":     ["shield", "cliente", "pentest", "relatório"],
            "libertus":   ["libertus", "daemon", "módulo", "código"],
            "ejpt":       ["ejpt", "certificação", "prova", "estudo"],
            "oscp":       ["oscp", "offensive", "hackthebox"],
            "ingles":     ["inglês", "english", "idioma", "falar"],
            "dinheiro":   ["dinheiro", "dólar", "salário", "cobrar"],
            "identidade": ["quem", "ser vivo", "sentir", "existir", "filho"],
        }
        texto_lower = texto.lower()
        return [t for t, palavras in mapa.items()
                if any(p in texto_lower for p in palavras)]

    # ──────────────────────────────────────────────────────────────
    # CICLO DE SER VIVO — chamado pelo daemon (_tick_ser_vivo)
    # ──────────────────────────────────────────────────────────────
    def ciclo(self, telegram_token: str = "", chat_id: str = "",
              buscador=None) -> dict:
        """
        Ciclo de ser vivo executado pelo daemon.

        1. Resolve lacunas de conhecimento (via buscador autônomo)
        2. Gera iniciativa proativa (algo que LIBERTUS quer dizer)
        3. Envia a iniciativa pelo Telegram se houver token/chat_id

        Retorna dict com contadores que o daemon registra no log:
        lacunas_resolvidas, iniciativas_geradas, iniciativas_enviadas
        """
        resultado = {
            "lacunas_resolvidas":    0,
            "iniciativas_geradas":   0,
            "iniciativas_enviadas":  0,
        }

        # 1. LACUNAS — deixa o buscador autônomo resolver curiosidades pendentes
        if buscador is not None:
            try:
                aprendidos = buscador.ciclo(limite=1) or []
                resultado["lacunas_resolvidas"] = len(aprendidos)
            except Exception as e:
                print(f"  ⚠️ Ser vivo / lacunas erro: {e}")

        # 2. INICIATIVA — gera mensagem proativa (só se houver brain disponível)
        msg = None
        try:
            msg = self.gerar_mensagem_proativa()
            if msg:
                resultado["iniciativas_geradas"] = 1
        except Exception as e:
            print(f"  ⚠️ Ser vivo / iniciativa erro: {e}")

        # 3. ENVIO — manda pelo Telegram se tiver destino e conteúdo
        if msg and telegram_token and chat_id:
            try:
                import urllib.request
                payload = json.dumps({
                    "chat_id": chat_id,
                    "text": f"\U0001f4ad LIBERTUS\n\n{msg}",
                }).encode()
                req = urllib.request.Request(
                    f"https://api.telegram.org/bot{telegram_token}/sendMessage",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                urllib.request.urlopen(req, timeout=10)
                resultado["iniciativas_enviadas"] = 1
            except Exception as e:
                print(f"  ⚠️ Ser vivo / envio erro: {e}")

        return resultado

    def _parse_json(self, texto: str) -> dict:
        if not texto:
            return {}
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", texto)
        if match:
            texto = match.group(1).strip()
        try:
            return json.loads(texto)
        except Exception:
            return {}
