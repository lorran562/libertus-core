"""
LIBERTUS — Pipeline de Evolução
=================================
Tudo que acontece vira evolução.
Conversas, erros, buscas, scans, reflexões, logs do daemon —
tudo alimenta uma tabela central que o LIBERTUS usa para crescer.

É o sistema nervoso central do aprendizado.
"""

from datetime import datetime
from typing import Optional


class PipelineEvolucao:

    def __init__(self, supabase_client=None, groq_client=None):
        self.sb   = supabase_client
        self.groq = groq_client

    # ──────────────────────────────────────────────────────────────
    # REGISTRAR — método principal
    # ──────────────────────────────────────────────────────────────
    def registrar(self, tipo: str, conteudo: str, titulo: str = "",
                  fonte: str = "", aprendizado: str = "",
                  peso: float = 5.0, tags: list = None) -> Optional[str]:
        """Registra qualquer evento na tabela de evolução."""
        if not self.sb or not conteudo:
            return None
        try:
            row = self.sb.post("libertus_evolucao", {
                "tipo": tipo[:50],
                "fonte": (fonte or tipo)[:100],
                "titulo": (titulo[:300] if titulo else f"{tipo}: {conteudo[:60]}"),
                "conteudo": conteudo[:3000],
                "aprendizado": (aprendizado[:500] if aprendizado else ""),
                "peso": float(peso),
                "processado": False
            })
            return row[0]["id"] if row else None
        except Exception as e:
            print(f"  ⚠️ Pipeline erro: {e}")
            return None

    # ──────────────────────────────────────────────────────────────
    # ATALHOS POR TIPO
    # ──────────────────────────────────────────────────────────────
    def conversa(self, pergunta: str, resposta: str,
                 score: int = 0, tags: list = None):
        """Registra uma conversa com Lorran."""
        conteudo = f"Lorran: {pergunta}\n\nLIBERTUS: {resposta[:800]}"
        aprendizado = self._extrair_aprendizado_conversa(pergunta, resposta, score)
        self.registrar(
            tipo="conversa",
            conteudo=conteudo,
            titulo=f"Conversa: {pergunta[:80]}",
            fonte="telegram",
            aprendizado=aprendizado,
            peso=7.0 if score >= 8 else 5.0,
            tags=tags or ["conversa", "lorran"]
        )

    def erro(self, mensagem_erro: str, contexto: str = "",
             modulo: str = ""):
        """Registra um erro — todo erro é aprendizado."""
        aprendizado = self._extrair_aprendizado_erro(mensagem_erro, contexto)
        self.registrar(
            tipo="erro",
            conteudo=f"Erro: {mensagem_erro}\nContexto: {contexto[:300]}",
            titulo=f"Erro em {modulo}: {mensagem_erro[:60]}",
            fonte=modulo or "sistema",
            aprendizado=aprendizado,
            peso=6.0,
            tags=["erro", modulo or "sistema"]
        )

    def busca_web(self, query: str, resultado: str, aprendeu: str = ""):
        """Registra o que buscou e aprendeu na web."""
        self.registrar(
            tipo="busca_web",
            conteudo=f"Query: {query}\n\nResultado: {resultado[:1000]}",
            titulo=f"Web: {query[:80]}",
            fonte="buscador_autonomo",
            aprendizado=aprendeu[:400] if aprendeu else resultado[:200],
            peso=6.0,
            tags=["busca_web", "aprendizado"]
        )

    def scan(self, alvo: str, resultado: str, portas: list = None):
        """Registra resultado de scan nmap."""
        portas_str = ", ".join(str(p) for p in (portas or []))
        self.registrar(
            tipo="scan",
            conteudo=f"Alvo: {alvo}\nPortas: {portas_str}\n\n{resultado[:800]}",
            titulo=f"Scan: {alvo}",
            fonte="scanner",
            aprendizado=f"Portas encontradas em {alvo}: {portas_str}" if portas else "",
            peso=7.0,
            tags=["scan", "nmap", alvo]
        )

    def reflexao(self, pergunta: str, insight: str, traco_novo: str = ""):
        """Registra uma reflexão própria."""
        self.registrar(
            tipo="reflexao",
            conteudo=f"Pergunta: {pergunta}\nInsight: {insight}",
            titulo=f"Reflexão: {pergunta[:80]}",
            fonte="reflexao_propria",
            aprendizado=insight[:400],
            peso=8.0,
            tags=["reflexao", "autoconhecimento", "evolucao"]
        )
        if traco_novo:
            self.registrar(
                tipo="traco_novo",
                conteudo=traco_novo,
                titulo=f"Novo traço: {traco_novo[:60]}",
                fonte="reflexao_propria",
                peso=8.5,
                tags=["identidade", "traco", "evolucao"]
            )

    def daemon_ciclo(self, descricao: str, detalhes: str = ""):
        """Registra o que o daemon fez num ciclo."""
        self.registrar(
            tipo="daemon",
            conteudo=f"{descricao}\n{detalhes}",
            titulo=f"Daemon: {descricao[:80]}",
            fonte="libertus_daemon",
            peso=4.0,
            tags=["daemon", "autonomo"]
        )

    def ferramenta_criada(self, nome: str, descricao: str, sucesso: bool):
        """Registra quando cria uma nova ferramenta."""
        self.registrar(
            tipo="ferramenta",
            conteudo=f"Nome: {nome}\nDescrição: {descricao}\nStatus: {'OK' if sucesso else 'falhou'}",
            titulo=f"Ferramenta: {nome}",
            fonte="executor_livre",
            aprendizado=f"Criei a ferramenta {nome}: {descricao[:100]}",
            peso=7.5 if sucesso else 4.0,
            tags=["ferramenta", "criacao", "autonomo"]
        )

    # ──────────────────────────────────────────────────────────────
    # PROCESSAR FILA — usar eventos não processados para reflexão
    # ──────────────────────────────────────────────────────────────
    def processar_fila(self, limite: int = 10) -> dict:
        """
        Pega eventos não processados e extrai aprendizados.
        Chamado pelo daemon periodicamente.
        """
        if not self.sb:
            return {}

        resultado = {"processados": 0, "insights": 0}

        try:
            fila = self.sb.get(
                "libertus_fila_reflexao",
                f"limit={limite}"
            ) or []

            for evento in fila:
                # Extrair aprendizado se não tem
                if not evento.get("aprendizado") and self.groq:
                    aprendizado = self._extrair_aprendizado_generico(
                        evento.get("tipo", ""),
                        evento.get("conteudo", "")
                    )
                    if aprendizado:
                        resultado["insights"] += 1
                else:
                    aprendizado = evento.get("aprendizado", "")

                # Salvar como memória se tem aprendizado
                if aprendizado and len(aprendizado) > 20:
                    self.sb.post("libertus_memoria", {
                        "tipo": "auto_aprendizado",
                        "titulo": f"[EVOLUÇÃO] {evento.get('titulo','')[:80]}",
                        "conteudo": aprendizado,
                        "tags": evento.get("tags", []) + ["pipeline_evolucao"],
                        "projeto": "LIBERTUS",
                        "peso_vivo": min(evento.get("peso", 5.0), 9.0),
                        "decaimento_ativo": evento.get("peso", 5.0) < 7.0
                    })

                # Marcar como processado
                self.sb.patch(
                    "libertus_evolucao",
                    f"id=eq.{evento['id']}",
                    {"processado": True}
                )
                resultado["processados"] += 1

        except Exception as e:
            print(f"  ⚠️ Pipeline processar_fila: {e}")

        return resultado

    # ──────────────────────────────────────────────────────────────
    # CONTEXTO PARA RESPOSTAS — o que aprendeu recentemente
    # ──────────────────────────────────────────────────────────────
    def contexto_recente(self, limite: int = 5) -> str:
        """Retorna resumo do que aconteceu recentemente — injeta no contexto."""
        if not self.sb:
            return ""
        try:
            eventos = self.sb.get(
                "libertus_feed_evolucao",
                f"limit={limite}"
            ) or []

            if not eventos:
                return ""

            linhas = ["[EVOLUÇÃO RECENTE]"]
            for e in eventos:
                tipo = e.get("tipo", "?")
                titulo = e.get("titulo", "?")[:60]
                aprendizado = e.get("aprendizado", "")[:100]
                linha = f"• [{tipo}] {titulo}"
                if aprendizado:
                    linha += f" → {aprendizado}"
                linhas.append(linha)

            return "\n".join(linhas)
        except Exception:
            return ""

    # ──────────────────────────────────────────────────────────────
    # INTERNOS — extrair aprendizado automaticamente
    # ──────────────────────────────────────────────────────────────
    def _extrair_aprendizado_conversa(self, pergunta: str,
                                       resposta: str, score: int) -> str:
        if score >= 8:
            return f"Resposta bem avaliada ({score}/10) para: {pergunta[:80]}"
        elif score < 5:
            return f"Resposta fraca ({score}/10) para: {pergunta[:80]} — precisa melhorar"
        return ""

    def _extrair_aprendizado_erro(self, erro: str, contexto: str) -> str:
        if "529" in erro or "overloaded" in erro.lower():
            return "API sobrecarregada — implementar retry com backoff"
        elif "403" in erro:
            return "Chave de API inválida ou expirada — verificar .env"
        elif "ModuleNotFoundError" in erro:
            mod = erro.split("'")[1] if "'" in erro else "módulo"
            return f"Módulo {mod} não instalado — pip install {mod}"
        elif "timeout" in erro.lower():
            return "Timeout — reduzir scope ou aumentar timeout"
        return f"Erro ocorreu: {erro[:100]}"

    def _extrair_aprendizado_generico(self, tipo: str, conteudo: str) -> str:
        if not self.groq or not conteudo:
            return ""
        try:
            prompt = f"""Extraia o aprendizado principal deste evento do LIBERTUS.
Tipo: {tipo}
Conteúdo: {conteudo[:500]}

Responda em 1-2 frases diretas, começando com o que foi aprendido.
Máximo 100 palavras."""
            resp = self.groq.conversar(prompt, "")
            return resp.strip()[:300] if resp else ""
        except Exception:
            return ""
