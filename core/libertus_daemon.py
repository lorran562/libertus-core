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

# LIBERTUS SCANNER v10
import sys
sys.path.insert(0, str(LIBERTUS_ROOT))
from libertus_scanner import LibertusScanner
import asyncio


# ── Configuração de ticks ────────────────────────────────────────────────
CICLO_OBSERVACAO   = 60       # 1 minuto — registra heartbeat
CICLO_CONSOLIDACAO = 1800     # 30 minutos — consolida memória
CICLO_EVOLUCAO     = 3600     # 1 hora — ciclo de autoevolução
CICLO_MANUTENCAO   = 86400    # 24 horas — reorganização profunda
CICLO_GIT_SYNC     = 14400    # 4 horas — commit automático

CICLO_AUTO_REFATORACAO = 43200   # 12 horas — auto-correção de bugs
CICLO_ABSORCAO_DOCLING = 21600   # 6 horas — aprendizado via Docling
CICLO_SECURITY_SCAN    = 86400   # 24 horas — security scanning

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
        
        # Targets para security scanning (carrega do Supabase)
        self.scan_targets = self._carregar_targets_scan()

        # Timestamps dos últimos ciclos
        self.last = {
            "observacao":   0,
            "consolidacao": 0,
            "evolucao":     0,
            "manutencao":   0,
            "git_sync":     0,
            "auto_refatoracao": 0,
            "absorcao_docling": 0,
            "security_scan":    0,
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
                    self.last["consolidacao"] = agora

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
        """
        try:
            from supabase import create_client
            import os
            
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_KEY")
            
            if not supabase_url or not supabase_key:
                return []
            
            client = create_client(supabase_url, supabase_key)
            response = client.table("libertus_scan_targets").select("url").eq("ativo", True).execute()
            
            targets = [row["url"] for row in response.data]
            self._log("INIT", f"Carregados {len(targets)} targets de scan")
            return targets
            
        except Exception as e:
            self._log("ERRO", f"Falha ao carregar targets: {e}")
            return []
    
    def _tick_security_scan(self):
        """
        Executa security scanning nos targets configurados.
        """
        self._log("SECURITY_SCAN", "Iniciando ciclo de scanning")
        
        if not self.scan_targets:
            self._log("SECURITY_SCAN", "Nenhum target configurado - pulando")
            return
        
        try:
            for target_url in self.scan_targets:
                self._log("SECURITY_SCAN", f"Scanning: {target_url}")
                
                # Executa scanner de forma assíncrona
                scanner = LibertusScanner(target_url)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(scanner.run_full_scan())
                loop.close()
                
                # Atualiza estatísticas
                self.stats["scans_realizados"] += 1
                self.stats["vulnerabilidades_encontradas"] += len(results.get("vulnerabilities", []))
                
                self._log("SECURITY_SCAN", 
                          f"Scan completo: {len(results.get('vulnerabilities', []))} vulnerabilidades")
                
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
