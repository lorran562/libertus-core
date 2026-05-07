"""
auto_evolucao.py — Ciclo de Autoevolução do Libertus
Analisa estado → detecta falhas → planeja → executa → testa → registra.

Lê/Escreve em:
  /LIBERTUS/evolution_logs/   → histórico de evoluções
  /LIBERTUS/plans/            → planos de melhoria
  /LIBERTUS/evolucao/         → aprendizados registrados
  /LIBERTUS/core/             → modifica seu próprio código
"""

import json, datetime, hashlib, subprocess
from pathlib import Path
from typing import List, Dict, Optional


class AutoEvolucao:
    def __init__(self, root: Path):
        self.root       = root
        self.dir_evo    = root / "evolution_logs"
        self.dir_plans  = root / "plans"
        self.dir_core   = root / "core"
        self.dir_evolucao = root / "evolucao"
        for d in [self.dir_evo, self.dir_plans, self.dir_evolucao]:
            d.mkdir(parents=True, exist_ok=True)

    # ── Ciclo principal ───────────────────────────────────────────────────

    def ciclo(self, sb=None, mem=None) -> Dict:
        """
        Executa um ciclo completo de autoevolução:
        1. Analisa estado atual
        2. Detecta oportunidades
        3. Planeja melhoria
        4. Registra plano
        5. Retorna plano para execução pelo orquestrador
        """
        ts = datetime.datetime.now().isoformat()

        # 1. Analisa estado
        estado = self._analisar_estado(sb)

        # 2. Detecta oportunidades
        oportunidades = self._detectar_oportunidades(estado)

        # 3. Gera plano
        plano = {
            "id":           hashlib.md5(ts.encode()).hexdigest()[:8],
            "timestamp":    ts,
            "estado":       estado,
            "oportunidades": oportunidades,
            "acoes":        self._gerar_acoes(oportunidades),
            "status":       "pendente",
        }

        # 4. Salva plano
        self._salvar_plano(plano)

        # 5. Registra no log de evolução
        self._registrar_log({
            "timestamp": ts,
            "tipo":      "ciclo_analise",
            "resumo":    f"{len(oportunidades)} oportunidades detectadas",
            "plano_id":  plano["id"],
        })

        return plano

    def executar_plano(self, plano: Dict) -> Dict:
        """Executa as ações de um plano de evolução."""
        resultados = []
        for acao in plano.get("acoes", []):
            resultado = self._executar_acao(acao)
            resultados.append(resultado)

        plano["status"]    = "executado"
        plano["resultados"] = resultados
        plano["executado_em"] = datetime.datetime.now().isoformat()

        # Atualiza plano salvo
        self._salvar_plano(plano)

        # Registra aprendizado se houve sucesso
        sucessos = [r for r in resultados if r.get("sucesso")]
        if sucessos:
            self._registrar_aprendizado(plano, sucessos)

        return plano

    # ── Análise ───────────────────────────────────────────────────────────

    def _analisar_estado(self, sb) -> Dict:
        """Analisa o estado atual do sistema."""
        estado = {
            "timestamp": datetime.datetime.now().isoformat(),
            "arquivos_core": len(list(self.dir_core.glob("*.py"))),
            "logs_evolucao": len(list(self.dir_evo.glob("*.json"))),
            "planos_pendentes": len([
                f for f in self.dir_plans.glob("*.json")
                if "pendente" in f.read_text(encoding="utf-8", errors="ignore")
            ]),
        }

        # Analisa Supabase se disponível
        if sb:
            try:
                skills = sb.get_skills()
                autonomas = sum(1 for s in skills if s.get("executor") == "libertus")
                memorias = sb.get("libertus_memoria", "select=id&limit=500")
                estado.update({
                    "skills_total":    len(skills),
                    "skills_autonomas": autonomas,
                    "taxa_autonomia":  round(autonomas / max(len(skills), 1) * 100, 1),
                    "memorias_total":  len(memorias),
                })
            except Exception:
                pass

        # Analisa arquivos do vault
        for pasta in ["memoria", "evolucao", "skills", "projetos"]:
            dir_p = self.root / pasta
            if dir_p.exists():
                estado[f"arquivos_{pasta}"] = len(list(dir_p.glob("*.md")))

        return estado

    def _detectar_oportunidades(self, estado: Dict) -> List[Dict]:
        """Detecta oportunidades de melhoria baseado no estado."""
        ops = []

        # Taxa de autonomia baixa
        taxa = estado.get("taxa_autonomia", 0)
        if taxa < 80:
            ops.append({
                "tipo":      "autonomia_baixa",
                "descricao": f"Taxa de autonomia em {taxa}% — meta: 80%+",
                "prioridade": 8,
                "acao_sugerida": "converter_skills_para_libertus",
            })

        # Poucas memórias
        if estado.get("memorias_total", 0) < 100:
            ops.append({
                "tipo":      "memoria_escassa",
                "descricao": "Menos de 100 memórias — sistema ainda aprendendo",
                "prioridade": 6,
                "acao_sugerida": "absorver_mais_conhecimento",
            })

        # Planos acumulados
        if estado.get("planos_pendentes", 0) > 5:
            ops.append({
                "tipo":      "planos_acumulados",
                "descricao": f"{estado['planos_pendentes']} planos pendentes",
                "prioridade": 7,
                "acao_sugerida": "executar_planos_pendentes",
            })

        # Poucas skills
        if estado.get("skills_total", 0) < 50:
            ops.append({
                "tipo":      "skills_insuficientes",
                "descricao": f"Apenas {estado.get('skills_total',0)} skills — meta: 100+",
                "prioridade": 7,
                "acao_sugerida": "criar_novas_skills",
            })

        return sorted(ops, key=lambda x: x["prioridade"], reverse=True)

    def _gerar_acoes(self, oportunidades: List[Dict]) -> List[Dict]:
        """Gera ações concretas para cada oportunidade."""
        acoes = []
        for op in oportunidades[:3]:  # max 3 ações por ciclo
            if op["tipo"] == "autonomia_baixa":
                acoes.append({
                    "tipo":      "migrar_skills",
                    "descricao": "Identificar skills 'claude' com 3+ usos e migrar para 'libertus'",
                    "prioridade": op["prioridade"],
                })
            elif op["tipo"] == "memoria_escassa":
                acoes.append({
                    "tipo":      "absorver_conhecimento",
                    "descricao": "Absorver documentos pendentes na pasta de conhecimento",
                    "prioridade": op["prioridade"],
                })
            elif op["tipo"] == "skills_insuficientes":
                acoes.append({
                    "tipo":      "gerar_skills",
                    "descricao": "Analisar tarefas frequentes e gerar skills reutilizáveis",
                    "prioridade": op["prioridade"],
                })
        return acoes

    def _executar_acao(self, acao: Dict) -> Dict:
        """Executa uma ação específica do plano."""
        resultado = {
            "acao":     acao["tipo"],
            "inicio":   datetime.datetime.now().isoformat(),
            "sucesso":  False,
            "detalhe":  "",
        }
        try:
            # Por enquanto registra a intenção — execução real via orquestrador
            resultado["sucesso"] = True
            resultado["detalhe"] = f"Ação '{acao['tipo']}' registrada para execução"
        except Exception as e:
            resultado["detalhe"] = str(e)
        finally:
            resultado["fim"] = datetime.datetime.now().isoformat()
        return resultado

    # ── Registro ──────────────────────────────────────────────────────────

    def _salvar_plano(self, plano: Dict):
        arq = self.dir_plans / f"{plano['id']}.json"
        arq.write_text(json.dumps(plano, ensure_ascii=False, indent=2),
                       encoding="utf-8")

    def _registrar_log(self, dados: Dict):
        ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        arq = self.dir_evo / f"{ts}_{dados.get('tipo','log')}.json"
        arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                       encoding="utf-8")

    def _registrar_aprendizado(self, plano: Dict, sucessos: List[Dict]):
        """Registra aprendizados em /evolucao/ como markdown."""
        ts      = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        arq     = self.dir_evolucao / f"{ts}_ciclo_evolucao.md"
        conteudo = (
            f"---\ntitulo: Ciclo de evolução {plano['id']}\n"
            f"data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"tipo: autoevolucao\ntags: [\"autoevolucao\",\"ciclo\"]\n---\n\n"
            f"## Oportunidades detectadas\n"
            + "\n".join(f"- {o['descricao']}"
                        for o in plano.get("oportunidades", [])) +
            f"\n\n## Ações executadas com sucesso\n"
            + "\n".join(f"- {s['acao']}: {s['detalhe']}"
                        for s in sucessos) +
            f"\n\n## Estado após execução\n"
            + json.dumps(plano.get("estado", {}), indent=2, ensure_ascii=False)
        )
        arq.write_text(conteudo, encoding="utf-8")

    def historico(self, ultimos: int = 5) -> str:
        """Retorna resumo dos últimos ciclos de evolução."""
        logs = sorted(self.dir_evo.glob("*.json"),
                      key=lambda f: f.stat().st_mtime, reverse=True)
        linhas = ["=== HISTÓRICO DE EVOLUÇÃO ==="]
        for log_file in logs[:ultimos]:
            try:
                d = json.loads(log_file.read_text(encoding="utf-8"))
                linhas.append(
                    f"[{d.get('timestamp','?')[:16]}] {d.get('tipo','?')}: "
                    f"{d.get('resumo','')}"
                )
            except Exception:
                continue
        return "\n".join(linhas)
