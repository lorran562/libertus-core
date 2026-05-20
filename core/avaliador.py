"""
avaliador.py — Avaliador de Qualidade de Execuções
Pontua resultados, detecta padrões de falha e aciona melhoria de skills.

Lê/Escreve em: /LIBERTUS/memory/feedback/
"""

import re, json, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class Avaliador:
    """
    Avalia cada execução e alimenta o loop de autoevolução.
    
    Fluxo:
        resultado = executor.executar(...)
        score = avaliador.avaliar(tarefa, resultado)
        if score < 5:
            avaliador.registrar_falha(tarefa, resultado)
            # Após 3 falhas: aciona Claude para reescrever skill
    """

    INDICADORES_SUCESSO = [
        r"✓|✅|sucesso|success|ok|done|completo|concluído|encontrado|detectado|salvo|criado",
        r"Score:\s*\d+",
        r"chunks?\s+salvos?",
        r"\d+\s+(porta|host|finding|vulnerabilidade)",
        r"Absorvido|Analisado|Escaneado|Reconhecido",
        # Indicadores de conversa natural
        r"posso ajudar|como posso|estou (pronto|aqui|funcionando|disponível)",
        r"lorran|libertus|ariquemes|shield|groq",
        r"sim|não|claro|certeza|entendi|compreendi|concordo",
        r"python|nmap|sqlmap|pentest|segurança|scan|vulnerabilidade",
        r"obrigado|agradeço|melhor|ótimo|perfeito|excelente",
    ]

    INDICADORES_FALHA = [
        r"erro|error|falhou|failed|exception|traceback|not found|não encontrado",
        r"timeout|timed out|connection refused|refused",
        r"nenhum|none|vazio|empty|sem resultado",
        r"bloqueado|blocked|denied|permission denied",
        r"módulo não encontrado|module not found|import error",
    ]

    def __init__(self, root: Path = None):
        self.root = root
        self.dir_feedback = (root / "memory" / "feedback") if root else None
        self.dir_evolucao = (root / "evolucao") if root else None
        if self.dir_feedback:
            self.dir_feedback.mkdir(parents=True, exist_ok=True)

    def avaliar(self, tarefa: str, resultado: str,
                executor: str = "", duracao_ms: int = 0) -> Dict:
        """
        Avalia um resultado e retorna score + diagnóstico.
        Score: 0-10
        """
        resultado_str = str(resultado).lower()

        # Conta indicadores
        pontos_sucesso = sum(
            1 for p in self.INDICADORES_SUCESSO
            if re.search(p, resultado_str, re.IGNORECASE)
        )
        pontos_falha = sum(
            1 for p in self.INDICADORES_FALHA
            if re.search(p, resultado_str, re.IGNORECASE)
        )

        # Score base
        if pontos_falha > pontos_sucesso:
            score = max(0, 3 - pontos_falha)
        elif pontos_sucesso > 0:
            score = min(10, 6 + pontos_sucesso * 2 - pontos_falha)
        else:
            # Resultado neutro — tem conteúdo mas sem indicadores claros
            score = 5 if len(resultado_str) > 100 else 3

        # Penaliza timeout
        if duracao_ms > 25000:
            score = max(0, score - 2)

        # Bônus por executor autônomo
        if executor == "skill":
            score = min(10, score + 1)

        avaliacao = {
            "tarefa":       tarefa[:100],
            "score":        score,
            "executor":     executor,
            "duracao_ms":   duracao_ms,
            "sucesso":      score >= 6,
            "timestamp":    datetime.datetime.now().isoformat(),
            "diagnostico":  self._diagnosticar(score, pontos_sucesso, pontos_falha),
            "acao":         self._recomendar_acao(score, executor),
        }

        self._salvar_avaliacao(avaliacao)
        return avaliacao

    def detectar_falha_recorrente(self, skill_name: str,
                                   ultimas: int = 5) -> Tuple[bool, int]:
        """
        Verifica se uma skill falhou repetidamente.
        Retorna (tem_falha_recorrente, count_falhas).
        """
        if not self.dir_feedback:
            return False, 0

        falhas = 0
        arquivos = sorted(
            self.dir_feedback.glob("*.json"),
            key=lambda f: f.stat().st_mtime, reverse=True
        )

        for arq in arquivos[:ultimas * 3]:
            try:
                dados = json.loads(arq.read_text(encoding="utf-8"))
                if (skill_name.lower() in dados.get("tarefa","").lower()
                        and not dados.get("sucesso", True)):
                    falhas += 1
            except Exception:
                continue

        return falhas >= 3, falhas

    def historico_score(self, ultimos: int = 10) -> Dict:
        """Retorna métricas de qualidade das últimas execuções."""
        if not self.dir_feedback:
            return {}

        scores = []
        por_executor = {}
        arquivos = sorted(
            self.dir_feedback.glob("*.json"),
            key=lambda f: f.stat().st_mtime, reverse=True
        )

        for arq in arquivos[:ultimos]:
            try:
                dados = json.loads(arq.read_text(encoding="utf-8"))
                if "score" in dados:
                    scores.append(dados["score"])
                    exe = dados.get("executor", "?")
                    por_executor.setdefault(exe, []).append(dados["score"])
            except Exception:
                continue

        if not scores:
            return {"sem_dados": True}

        return {
            "score_medio":    round(sum(scores) / len(scores), 1),
            "score_min":      min(scores),
            "score_max":      max(scores),
            "total":          len(scores),
            "taxa_sucesso":   round(sum(1 for s in scores if s >= 6) / len(scores) * 100, 1),
            "por_executor":   {k: round(sum(v)/len(v), 1) for k, v in por_executor.items()},
        }

    def _diagnosticar(self, score: int, sucessos: int, falhas: int) -> str:
        if score >= 8:
            return "Excelente — resultado claro e completo"
        if score >= 6:
            return "Bom — resultado satisfatório"
        if score >= 4:
            return "Parcial — resultado incompleto ou ambíguo"
        if score >= 2:
            return f"Fraco — {falhas} indicadores de falha detectados"
        return "Falha — resultado inválido ou erro crítico"

    def _recomendar_acao(self, score: int, executor: str) -> str:
        if score >= 8:
            if executor == "groq":
                return "converter_para_skill"  # resultado bom via Groq → vira skill
            return "nenhuma"
        if score >= 6:
            return "monitorar"
        if score >= 4:
            return "revisar_skill"
        return "reescrever_skill"  # aciona Claude para reescrever

    def _salvar_avaliacao(self, dados: Dict):
        if not self.dir_feedback:
            return
        ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        arq = self.dir_feedback / f"{ts}_avaliacao.json"
        arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                       encoding="utf-8")
