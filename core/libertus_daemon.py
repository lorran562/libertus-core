#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
libertus_daemon.py — Núcleo Cognitivo Contínuo

Roda 24/7 como systemd service.
A cada tick executa ciclos de cognição:
- Observação de eventos
- Consolidação de memória
- Detecção de padrões
- Autoevolução
- Resumo de atividade

Escreve heartbeat em /LIBERTUS/memory/heartbeat.json
"""

import os, sys, json, time, signal, traceback, threading
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

LIBERTUS_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(LIBERTUS_ROOT / "core"))

from supabase_client   import Supabase
from memoria_local     import MemoriaLocal
from motor_decisao     import MotorDecisao
from sistema_objetivos import SistemaObjetivos, Prazo
from auto_evolucao     import AutoEvolucao
from avaliador         import Avaliador
from git_sync          import GitSync
from auto_refatoracao  import AutoRefatoracao
from absorcao_docling  import AbsorcaoDocling
try:
    from buscador_autonomo import BuscadorAutonomo
    BUSCADOR_OK = True
except Exception:
    BUSCADOR_OK = False




# ── Configuração de ticks ────────────────────────────────────────────────
CICLO_OBSERVACAO   = 60       # 1 minuto — registra heartbeat
CICLO_CONSOLIDACAO = 1800     # 30 minutos — consolida memória
CICLO_BUSCA_WEB    = 3600     # 1 hora — busca e aprende da web
CICLO_REFLEXAO     = 7200     # 2 horas — reflexão sobre si mesmo
CICLO_AUTONOMIA    = 10800    # 3 horas — ciclo de autonomia livre
CICLO_PIPELINE     = 1800     # 30 min — processa fila de evolução
CICLO_PROATIVO     = 14400    # 4 horas — LIBERTUS inicia conversa
CICLO_BUGBOUNTY    = 21600    # 6 horas — treino em bug bounty
CICLO_SER_VIVO     = 3600     # 1 hora — iniciativas, lacunas, padrões
CICLO_EVOLUCAO     = 3600     # 1 hora — ciclo de autoevolução
CICLO_MANUTENCAO   = 86400    # 24 horas — reorganização profunda
CICLO_GIT_SYNC     = 14400    # 4 horas — commit automático

CICLO_AUTO_REFATORACAO = 43200   # 12 horas — auto-correção de bugs
CICLO_ABSORCAO_DOCLING = 21600   # 6 horas — aprendizado via Docling
CICLO_SECURITY_SCAN    = 10800   # 3 horas — security scanning automático

HEARTBEAT = LIBERTUS_ROOT / "memory" / "heartbeat.json"
DAEMON_LOG = LIBERTUS_ROOT / "evolution_logs" / "daemon.log"


class NucleoCognitivo:
    """
    Núcleo que roda continuamente analisando, consolidando e evoluindo.
    Não depende de input humano para agir.
    """

    def __init__(self):
        self.root = LIBERTUS_ROOT
        self.rodando = True
        self.inicio = datetime.now()
        self.ticks_total = 0

        # Componentes
        self.sb  = Supabase()
        self.mem = MemoriaLocal(self.root)
        self.dec = MotorDecisao(self.root)
        self.obj = SistemaObjetivos(self.root)
        self.evo = AutoEvolucao(self.root)
        self.ava = Avaliador(self.root)
        self.git = GitSync(self.root)

        # v10: Auto-refatoração + Docling
        self.refactor = AutoRefatoracao(self.root)
        self.docling = AbsorcaoDocling(self.root)
        
        # v5.0: Security Scanning 24/7
        self.scan_targets = self._carregar_targets_scan()

        # Timestamps dos últimos ciclos
        self.last = {
            "observacao":   0,
            "consolidacao": 0,
                "busca_web": 0,
                "reflexao": 0,
                "autonomia": 0,
                "pipeline": 0,
                "proativo": 0,
                "bugbounty": 0,
                "ser_vivo": 0,
            "evolucao":     0,
            "manutencao":   0,
            "git_sync":     0,
            "auto_refatoracao": 0,
            "absorcao_docling": 0,
            "security_scan": 0,
        }

        # Estatísticas da sessão do daemon
        self.stats = {
            "memorias_consolidadas": 0,
            "ciclos_evolucao":       0,
            "padroes_detectados":    0,
            "skills_melhoradas":     0,
            "commits_feitos":        0,
            "bugs_corrigidos":       0,
            "documentos_absorvidos": 0,
            "scans_realizados":      0,
            "vulnerabilidades_encontradas": 0,
            "erros":                 0,
        }

        # Garante pastas
        HEARTBEAT.parent.mkdir(parents=True, exist_ok=True)
        DAEMON_LOG.parent.mkdir(parents=True, exist_ok=True)

        # Signal handlers
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT,  self._shutdown)

        self._log("INICIO", "Núcleo cognitivo iniciado")

    # ── Loop principal ────────────────────────────────────────────────────

    def rodar(self):
        """Loop eterno do daemon."""
        self._log("LOOP", "Entrando em loop cognitivo contínuo")

        while self.rodando:
            try:
                agora = time.time()
                self.ticks_total += 1

                # Cada ciclo tem sua frequência
                if agora - self.last["observacao"] >= CICLO_OBSERVACAO:
                    self._tick_observacao()
                    self.last["observacao"] = agora

                if agora - self.last["consolidacao"] >= CICLO_CONSOLIDACAO:
                    self._tick_consolidacao()
                    self._salvar_briefing()
                    self.last["consolidacao"] = agora

                if agora - self.last.get("busca_web", 0) >= CICLO_BUSCA_WEB:
                    self._tick_busca_web()
                    self.last["busca_web"] = agora

                if agora - self.last.get("reflexao", 0) >= CICLO_REFLEXAO:
                    self._tick_reflexao()
                    self.last["reflexao"] = agora

                if agora - self.last.get("autonomia", 0) >= CICLO_AUTONOMIA:
                    self._tick_autonomia()
                    self.last["autonomia"] = agora

                if agora - self.last.get("pipeline", 0) >= CICLO_PIPELINE:
                    self._tick_pipeline()
                    self.last["pipeline"] = agora

                if agora - self.last.get("proativo", 0) >= CICLO_PROATIVO:
                    self._tick_proativo()
                    self.last["proativo"] = agora

                if agora - self.last.get("bugbounty", 0) >= CICLO_BUGBOUNTY:
                    self._tick_bugbounty()
                    self.last["bugbounty"] = agora

                if agora - self.last.get("ser_vivo", 0) >= CICLO_SER_VIVO:
                    self._tick_ser_vivo()
                    self.last["ser_vivo"] = agora

                if agora - self.last["evolucao"] >= CICLO_EVOLUCAO:
                    self._tick_evolucao()
                    self.last["evolucao"] = agora

                if agora - self.last["git_sync"] >= CICLO_GIT_SYNC:
                    self._tick_git_sync()
                    self.last["git_sync"] = agora

                if agora - self.last["manutencao"] >= CICLO_MANUTENCAO:
                    self._tick_manutencao()
                    self.last["manutencao"] = agora


                if agora - self.last["auto_refatoracao"] >= CICLO_AUTO_REFATORACAO:
                    self._tick_auto_refatoracao()
                    self.last["auto_refatoracao"] = agora

                if agora - self.last["absorcao_docling"] >= CICLO_ABSORCAO_DOCLING:
                    self._tick_absorcao_docling()
                    self.last["absorcao_docling"] = agora
                
                if agora - self.last["security_scan"] >= CICLO_SECURITY_SCAN:
                    self._tick_security_scan()
                    self.last["security_scan"] = agora

                # Dorme pelo menor intervalo
                time.sleep(30)

            except Exception as e:
                self.stats["erros"] += 1
                self._log("ERRO", f"{e}\n{traceback.format_exc()[-300:]}")
                time.sleep(60)  # espera antes de tentar de novo

        self._log("FIM", f"Encerrando após {self.ticks_total} ticks")

    # ── Ciclos ────────────────────────────────────────────────────────────

    def _tick_observacao(self):
        """
        Registra heartbeat com estado atual do sistema.
        É o sinal de vida do Libertus.
        """
        estado = {
            "timestamp":    datetime.now().isoformat(),
            "uptime_horas": round((datetime.now() - self.inicio).total_seconds() / 3600, 2),
            "ticks":        self.ticks_total,
            "stats":        self.stats,
            "proximo_evolucao_em":  int(CICLO_EVOLUCAO - (time.time() - self.last["evolucao"])),
            "proximo_git_em":       int(CICLO_GIT_SYNC - (time.time() - self.last["git_sync"])),
        }
        HEARTBEAT.write_text(
            json.dumps(estado, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def _tick_consolidacao(self):
        """
        Consolida memória: relê /memoria e /evolucao, detecta padrões,
        gera síntese de tópicos recorrentes.
        """
        self._log("CONSOLIDACAO", "Iniciando consolidação de memória")

        # 1. Busca memórias recentes do Supabase
        recentes = self.sb.get(
            "libertus_memoria",
            "order=created_at.desc&limit=20"
        )
        if not recentes:
            return

        # 2. Detecta padrões (tags recorrentes)
        contagem_tags = {}
        for mem in recentes:
            for tag in (mem.get("tags") or []):
                contagem_tags[tag] = contagem_tags.get(tag, 0) + 1

        # 3. Tags que aparecem 3+ vezes viram padrão
        padroes = {t: c for t, c in contagem_tags.items() if c >= 3}
        if padroes:
            self.stats["padroes_detectados"] += len(padroes)

            # Salva síntese no Obsidian
            conteudo = (
                f"## Padrões detectados em {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                + "\n".join(f"- **{t}**: {c} ocorrências" for t, c in
                            sorted(padroes.items(), key=lambda x: x[1], reverse=True))
                + f"\n\n## Contexto\n{len(recentes)} memórias recentes analisadas"
            )
            self.mem.salvar(
                "evolucao", f"padroes_consolidados",
                conteudo, ["padrao", "consolidacao", "autonomo"]
            )
            self.stats["memorias_consolidadas"] += 1

        self._log("CONSOLIDACAO",
                  f"Consolidados {len(recentes)} itens, {len(padroes)} padrões")

    def _salvar_briefing(self):
        """Salva estado atual do daemon no Supabase para injeção no contexto."""
        try:
            # Últimas atividades
            logs = []
            import os
            log_path = self.root / "evolution_logs" / "daemon.log"
            if log_path.exists():
                linhas = log_path.read_text().splitlines()[-20:]
                logs = [l for l in linhas if l.strip()]

            # Últimas pesquisas
            memorias_recentes = self.sb.get(
                "libertus_memoria",
                "tipo=eq.auto_aprendizado&order=created_at.desc&limit=5&select=titulo,created_at"
            ) or []

            # Reflexões recentes
            insights = self.sb.get(
                "libertus_memoria",
                "tipo=eq.insight_proprio&order=created_at.desc&limit=3&select=titulo,conteudo"
            ) or []

            briefing = {
                "timestamp": datetime.now().isoformat(),
                "daemon_ativo": True,
                "uptime_horas": round((time.time() - self._inicio) / 3600, 1) if hasattr(self, '_inicio') else 0,
                "ultimas_pesquisas": [m.get('titulo','?') for m in memorias_recentes],
                "insights_recentes": [i.get('titulo','?') for i in insights],
                "ciclos_completados": self.stats.get("ciclos", 0),
                "memorias_consolidadas": self.stats.get("memorias_consolidadas", 0),
            }

            # Salvar como memória especial
            existente = self.sb.get(
                "libertus_memoria",
                "tipo=eq.briefing_daemon&select=id&limit=1"
            ) or []

            briefing_txt = (
                f"Daemon ativo há {briefing['uptime_horas']}h. "
                f"Ciclos: {briefing['ciclos_completados']}. "
                f"Últimas pesquisas: {', '.join(briefing['ultimas_pesquisas'][:3])}. "
                f"Insights: {', '.join(briefing['insights_recentes'][:2])}."
            )

            if existente:
                self.sb.patch(
                    "libertus_memoria",
                    f"tipo=eq.briefing_daemon",
                    {
                        "conteudo": briefing_txt,
                        "titulo": f"Estado do Daemon — {datetime.now().strftime('%H:%M')}",
                        "updated_at": datetime.now().isoformat()
                    }
                )
            else:
                self.sb.post("libertus_memoria", {
                    "tipo": "briefing_daemon",
                    "titulo": f"Estado do Daemon — {datetime.now().strftime('%H:%M')}",
                    "conteudo": briefing_txt,
                    "tags": ["daemon", "estado", "briefing"],
                    "projeto": "LIBERTUS",
                    "peso_vivo": 9.0,
                    "decaimento_ativo": False
                })

        except Exception as e:
            self._log("BRIEFING", f"Erro: {e}")

    def _tick_ser_vivo(self):
        """Ciclo de ser vivo — iniciativas, lacunas, padrões."""
        try:
            from ser_vivo import SerVivo
            from buscador_autonomo import BuscadorAutonomo
            from groq_client import Groq
            import os

            groq = Groq(os.environ.get("GROQ_API_KEY", ""))
            ba = BuscadorAutonomo(groq_client=groq, supabase_client=self.sb)
            sv = SerVivo(supabase_client=self.sb, groq_client=groq)

            token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
            chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

            resultado = sv.ciclo(
                telegram_token=token,
                chat_id=chat_id,
                buscador=ba
            )
            self._log("SER_VIVO",
                f"Lacunas: {resultado.get('lacunas_resolvidas',0)}, "
                f"Iniciativas: {resultado.get('iniciativas_geradas',0)} geradas, "
                f"{resultado.get('iniciativas_enviadas',0)} enviadas")
        except Exception as e:
            self._log("SER_VIVO", f"Erro: {e}")

    def _tick_bugbounty(self):
        """Treino autônomo em bug bounty — a cada 6 horas."""
        try:
            from agente_bugbounty import AgenteBugBounty
            from buscador_autonomo import BuscadorAutonomo
            from groq_client import Groq
            import os

            groq = Groq(os.environ.get("GROQ_API_KEY", ""))
            ba   = BuscadorAutonomo(groq_client=groq, supabase_client=self.sb)
            ag   = AgenteBugBounty(supabase_client=self.sb, groq_client=groq, buscador=ba)

            resultado = ag.ciclo_treino()
            self._log("BUGBOUNTY",
                f"Tópicos: {resultado.get('topicos_estudados',0)}, "
                f"Scans: {resultado.get('scans_realizados',0)}, "
                f"Vulns: {resultado.get('vulnerabilidades_encontradas',0)}")
        except Exception as e:
            self._log("BUGBOUNTY", f"Erro: {e}")

    def _tick_proativo(self):
        """LIBERTUS decide enviar mensagem para Lorran por iniciativa própria."""
        try:
            from ser_vivo import SerVivo
            from groq_client import Groq
            import os, urllib.request, json

            groq = Groq(os.environ.get("GROQ_API_KEY", ""))
            sv = SerVivo(supabase_client=self.sb, groq_client=groq)

            # Gerar mensagem proativa
            msg = sv.gerar_mensagem_proativa()

            if msg:
                # Enviar via Telegram
                token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
                chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

                if token and chat_id:
                    texto = f"\U0001f916 *LIBERTUS*\n\n{msg}"
                    payload = json.dumps({
                        "chat_id": chat_id,
                        "text": texto,
                        "parse_mode": "Markdown"
                    }).encode()
                    req = urllib.request.Request(
                        f"https://api.telegram.org/bot{token}/sendMessage",
                        data=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    urllib.request.urlopen(req, timeout=10)
                    self._log("PROATIVO", f"Mensagem enviada: {msg[:60]}")
                else:
                    self._log("PROATIVO", f"Gerado mas sem TELEGRAM_CHAT_ID: {msg[:60]}")

        except Exception as e:
            self._log("PROATIVO", f"Erro: {e}")

    def _tick_pipeline(self):
        """Processa fila de evolução — extrai aprendizados de tudo que aconteceu."""
        try:
            from pipeline_evolucao import PipelineEvolucao
            from groq_client import Groq
            import os
            groq = Groq(os.environ.get("GROQ_API_KEY", ""))
            pe = PipelineEvolucao(supabase_client=self.sb, groq_client=groq)
            resultado = pe.processar_fila(limite=10)
            self._log("PIPELINE", f"Processados: {resultado.get('processados',0)}, Insights: {resultado.get('insights',0)}")
        except Exception as e:
            self._log("PIPELINE", f"Erro: {e}")

    def _tick_autonomia(self):
        """Ciclo de autonomia livre — LIBERTUS decide o que fazer sozinho."""
        try:
            from executor_livre import ExecutorLivre
            from groq_client import Groq
            import os

            groq = Groq(os.environ.get("GROQ_API_KEY", ""))
            el = ExecutorLivre(supabase_client=self.sb, groq_client=groq)
            resultado = el.ciclo_autonomo()
            self._log("AUTONOMIA",
                f"Explorações: {resultado.get('exploracoes',0)}, "
                f"Ferramentas: {resultado.get('ferramentas_criadas',0)}, "
                f"Objetivos: {resultado.get('objetivos_criados',0)}")
        except Exception as e:
            self._log("AUTONOMIA", f"Erro: {e}")

    def _tick_reflexao(self):
        """Reflexão própria — LIBERTUS pensa sobre si mesmo a cada 2 horas."""
        try:
            from reflexao_propria import ReflexaoPropria
            from buscador_autonomo import BuscadorAutonomo
            from groq_client import Groq
            import os

            groq = Groq(os.environ.get("GROQ_API_KEY", ""))
            ba = BuscadorAutonomo(groq_client=groq, supabase_client=self.sb)
            rp = ReflexaoPropria(groq_client=groq, supabase_client=self.sb, buscador=ba)

            # Buscar traços e erros atuais
            tracos = self.sb.get("libertus_eu", "limit=8") or []
            erros = self.sb.get(
                "libertus_livro_erros",
                "foi_corrigido=eq.false&order=created_at.desc&limit=3&select=causa_provavel,licao"
            ) or []

            sessao = f"Ciclo autônomo do daemon — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            resultado = rp.ciclo(sessao, tracos, erros)

            self._log("REFLEXAO", f"Ciclo: {resultado.get('perguntas_geradas',0)} perguntas, {resultado.get('tracos_novos',0)} traços novos")
        except Exception as e:
            self._log("REFLEXAO", f"Erro: {e}")

    def _tick_busca_web(self):
        """Busca na web e aprende tópicos pendentes da fila de Auto-Curiosidade."""
        try:
            if not BUSCADOR_OK:
                return
            from buscador_autonomo import BuscadorAutonomo
            from groq_client import Groq
            groq = Groq(os.environ.get("GROQ_API_KEY", ""))
            ba = BuscadorAutonomo(groq_client=groq, supabase_client=self.sb)
            respondidas = ba.ciclo(limite=2)
            for r in respondidas:
                self.stats["memorias_consolidadas"] += 1
                self._log("BUSCA_WEB", f"Aprendi: {r.get('pergunta','?')[:60]}")
        except Exception as e:
            self._log("BUSCA_WEB", f"Erro: {e}")

    def _tick_evolucao(self):
        """
        Executa ciclo de autoevolução sem intervenção humana.
        Detecta skills com baixa performance e aciona melhoria.
        """
        self._log("EVOLUCAO", "Iniciando ciclo autônomo")

        # 1. Roda análise padrão
        plano = self.evo.ciclo(self.sb, self.mem)
        self.stats["ciclos_evolucao"] += 1

        # 2. Detecta skills com falha recorrente
        skills = self.sb.get_skills()
        for skill in skills[:20]:
            nome = skill.get("name", "")
            tem_falha, count = self.ava.detectar_falha_recorrente(nome)
            if tem_falha:
                self._log("FALHA_RECORRENTE",
                          f"Skill '{nome}' falhou {count} vezes — marcando para revisão")
                # Marca skill como precisando revisão
                self.sb.patch(
                    "libertus_skills",
                    f"name=eq.{nome}",
                    {"ativo": False, "observacao": f"Desativada por {count} falhas em {datetime.now():%Y-%m-%d}"}
                )
                self.stats["skills_melhoradas"] += 1

        # 3. Verifica progresso dos objetivos
        objetivos_ativos = self.obj.listar()
        for objetivo in objetivos_ativos:
            # Auto-incrementa progresso se há memórias relacionadas
            tags_obj = objetivo.get("tags", [])
            if tags_obj:
                relevantes = self.sb.get(
                    "libertus_memoria",
                    f"tags=cs.{{{tags_obj[0]}}}"
                )
                if len(relevantes) > 5 and objetivo.get("progresso", 0) < 50:
                    self.obj.atualizar_progresso(
                        objetivo["id"], 25,
                        f"Auto-detectado: {len(relevantes)} memórias relacionadas"
                    )

        self._log("EVOLUCAO",
                  f"Ciclo: {len(plano.get('oportunidades',[]))} oportunidades detectadas")

    def _tick_git_sync(self):
        """Commit automático de mudanças se houver."""
        if not self.git.git_ok:
            return

        resultado = self.git.commit_evolucao(
            f"autocommit daemon — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            tipo="chore"
        )
        if "Nada para commitar" not in resultado:
            self.stats["commits_feitos"] += 1
            self._log("GIT", f"Commit automático: {resultado[:80]}")

            # Tenta push silencioso
            try:
                self.git.push()
            except Exception:
                pass

    def _tick_manutencao(self):
        """
        Manutenção profunda diária.
        Reorganiza estrutura, limpa logs antigos, gera relatório.
        """
        self._log("MANUTENCAO", "Manutenção profunda iniciada")

        # 1. Remove logs de feedback muito antigos (> 30 dias)
        dir_feedback = self.root / "memory" / "feedback"
        if dir_feedback.exists():
            limite = datetime.now() - timedelta(days=30)
            removidos = 0
            for arq in dir_feedback.glob("*.json"):
                try:
                    mtime = datetime.fromtimestamp(arq.stat().st_mtime)
                    if mtime < limite:
                        arq.unlink()
                        removidos += 1
                except Exception:
                    continue
            self._log("MANUTENCAO", f"Removidos {removidos} logs antigos")

        # 2. Gera relatório diário
        relatorio = self.gerar_relatorio_diario()
        self.mem.salvar(
            "evolucao", "relatorio_diario_daemon",
            relatorio, ["daemon", "relatorio", "diario"]
        )

    # ── Relatórios ────────────────────────────────────────────────────────

    def gerar_relatorio_diario(self) -> str:
        """Gera relatório do que o daemon fez nas últimas 24h."""
        uptime = datetime.now() - self.inicio
        skills = self.sb.get_skills()
        mems = self.sb.get("libertus_memoria", "select=id&limit=500")

        return f"""## Relatório do Núcleo Cognitivo

**Período:** {self.inicio.strftime('%Y-%m-%d %H:%M')} até {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Uptime:** {int(uptime.total_seconds() / 3600)} horas
**Ticks totais:** {self.ticks_total}

## Atividade autônoma
- Memórias consolidadas: {self.stats['memorias_consolidadas']}
- Ciclos de evolução: {self.stats['ciclos_evolucao']}
- Padrões detectados: {self.stats['padroes_detectados']}
- Skills revisadas: {self.stats['skills_melhoradas']}
- Commits feitos: {self.stats['commits_feitos']}
- Erros recuperados: {self.stats['erros']}

## Estado atual do sistema
- Skills ativas: {len(skills)}
- Memórias totais: {len(mems)}
- Objetivos ativos: {len(self.obj.listar())}

## Próximos ciclos agendados
- Consolidação: em {int((CICLO_CONSOLIDACAO - (time.time() - self.last['consolidacao'])) / 60)} min
- Evolução: em {int((CICLO_EVOLUCAO - (time.time() - self.last['evolucao'])) / 60)} min
- Git sync: em {int((CICLO_GIT_SYNC - (time.time() - self.last['git_sync'])) / 60)} min
"""

    def resumo_ao_acordar(self) -> str:
        """
        Retorna resumo do que o daemon fez enquanto o usuário estava ausente.
        Chamado quando usuário abre o libertus.py.
        """
        if not HEARTBEAT.exists():
            return "Daemon não está rodando. Execute: sudo systemctl start libertus"

        try:
            estado = json.loads(HEARTBEAT.read_text(encoding="utf-8"))
        except Exception:
            return "Heartbeat corrompido"

        ultimo = datetime.fromisoformat(estado["timestamp"])
        delta = datetime.now() - ultimo

        if delta.total_seconds() > 300:  # > 5 min
            return f"⚠️ Daemon offline há {int(delta.total_seconds()/60)} minutos"

        stats = estado.get("stats", {})
        return (
            f"🧬 Enquanto você esteve fora ({estado['uptime_horas']}h de uptime):\n"
            f"  • {stats.get('memorias_consolidadas',0)} consolidações de memória\n"
            f"  • {stats.get('ciclos_evolucao',0)} ciclos de evolução\n"
            f"  • {stats.get('padroes_detectados',0)} padrões detectados\n"
            f"  • {stats.get('commits_feitos',0)} commits automáticos\n"
            f"  • Próxima evolução em {estado['proximo_evolucao_em']//60} min"
        )

    # ── Internos ──────────────────────────────────────────────────────────

    def _log(self, tipo: str, msg: str):
        """Log do daemon."""
        linha = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {tipo}: {msg}\n"
        try:
            with open(DAEMON_LOG, "a", encoding="utf-8") as f:
                f.write(linha)
        except Exception:
            pass
        print(linha.strip())

    def _shutdown(self, signum, frame):
        """Handler de shutdown gracioso."""
        self._log("SHUTDOWN", f"Sinal {signum} recebido")
        self.rodando = False
        # Gera último heartbeat indicando shutdown limpo
        final = {
            "timestamp": datetime.now().isoformat(),
            "status":    "shutdown_limpo",
            "stats":     self.stats,
            "uptime_horas": round((datetime.now() - self.inicio).total_seconds() / 3600, 2),
        }
        HEARTBEAT.write_text(
            json.dumps(final, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        sys.exit(0)


    def _carregar_targets_scan(self) -> list:
        """
        Carrega targets de scan do Supabase.
        Usa o cliente httpx local (self.sb) — sem dependência do pacote PyPI 'supabase'.
        """
        try:
            rows = self.sb.get(
                "libertus_scan_targets",
                "ativo=eq.true&select=url"
            ) or []
            targets = [row["url"] for row in rows if row.get("url")]
            self._log("INIT", f"Carregados {len(targets)} targets de scan")
            return targets
        except Exception as e:
            self._log("ERRO", f"Falha ao carregar targets: {e}")
            return []
    
    def _tick_security_scan(self):
        """
        Executa security scanning profissional nos targets configurados.
        Usa Libertus Professional Scanner v5.0 com Brain + Crypto + Reverse.
        """
        self._log("SECURITY_SCAN", "Iniciando ciclo de scanning profissional")
        
        if not self.scan_targets:
            self._log("SECURITY_SCAN", "Nenhum target configurado - pulando")
            return
        
        try:
            from libertus_professional_scanner import LibertusProfessionalScanner
            import asyncio
            from datetime import datetime
            
            for target_url in self.scan_targets:
                self._log("SECURITY_SCAN", f"Scanning: {target_url}")
                
                # Executa scanner profissional v5.0
                scanner = LibertusProfessionalScanner(target_url)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                report = loop.run_until_complete(scanner.full_scan())
                loop.close()
                
                # Salva relatório
                report_path = self.root / "reports" / f"scan_{datetime.now():%Y%m%d_%H%M%S}.json"
                report_path.parent.mkdir(exist_ok=True)
                report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
                
                # Atualiza estatísticas
                self.stats["scans_realizados"] += 1
                self.stats["vulnerabilidades_encontradas"] += report["summary"]["total_vulnerabilities"]
                
                # Atualiza Supabase
                try:
                    self.sb.patch(
                        "libertus_scan_targets",
                        f"url=eq.{target_url}",
                        {
                            "ultima_scan": datetime.now().isoformat(),
                            "vulnerabilidades_encontradas": report["summary"]["total_vulnerabilities"],
                            "severidade_maxima": report["summary"]["risk_level"]
                        }
                    )
                except Exception as e:
                    self._log("ERRO", f"Falha ao atualizar Supabase: {e}")
                
                self._log("SECURITY_SCAN", 
                          f"✅ Scan completo: {report['summary']['total_vulnerabilities']} vulns, "
                          f"risk score {report['summary']['risk_score']}/100")
                
        except Exception as e:
            self._log("ERRO_SECURITY_SCAN", f"{e}")
            self.stats["erros"] += 1


    def _tick_auto_refatoracao(self):
        """
        Auto-correção de bugs detectados nos logs.
        """
        self._log("AUTO_REFATORACAO", "Iniciando ciclo de auto-correção")
        
        try:
            resultado = self.refactor.ciclo_auto_refatoracao()
            self.stats["bugs_corrigidos"] += len(resultado.get("bugs_corrigidos", []))
            
            self._log("AUTO_REFATORACAO",
                      f"Bugs: {resultado['bugs_detectados']}, "
                      f"Patches: {resultado['patches_aplicados']}/{resultado['patches_gerados']}")
        except Exception as e:
            self._log("ERRO_REFATORACAO", f"{e}")
    
    def _tick_absorcao_docling(self):
        """
        Absorção automática de conhecimento via Docling.
        """
        self._log("ABSORCAO_DOCLING", "Iniciando absorção de conhecimento")
        
        try:
            # Pega objetivos de aprendizado
            objetivos = self.obj.listar()
            for obj in objetivos:
                descricao_lower = obj.get("descricao", "").lower()
                if "aprender" in descricao_lower or "estudar" in descricao_lower:
                    tags = obj.get("tags", [])
                    if tags:
                        resultado = self.docling.ciclo_absorcao(tags[:3])
                        self.stats["documentos_absorvidos"] += resultado.get("documentos_processados", 0)
                        
                        self._log("ABSORCAO_DOCLING",
                                  f"Tags: {tags[:3]}, Docs: {resultado['documentos_processados']}, "
                                  f"Memórias: {resultado['memorias_criadas']}")
                        break  # Apenas 1 objetivo por ciclo
        except Exception as e:
            self._log("ERRO_DOCLING", f"{e}")


def main():
    """Ponto de entrada do daemon."""
    try:
        print(f"LIBERTUS Daemon — iniciando em {LIBERTUS_ROOT}")
        nucleo = NucleoCognitivo()
        nucleo.rodar()
    except Exception as e:
        import traceback
        erro = f"ERRO FATAL: {e}\n{traceback.format_exc()}"
        print(erro)
        Path(LIBERTUS_ROOT / "evolution_logs" / "daemon_crash.log").write_text(erro)
        raise


if __name__ == "__main__":
    main()
