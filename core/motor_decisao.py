"""
motor_decisao.py — Motor de Decisão do Libertus
Avalia contexto atual, compara alternativas e registra cada decisão.

Escreve em: /LIBERTUS/memory/decisions/
Lê de:     /LIBERTUS/memoria/, /LIBERTUS/memory/goals/
"""

import json, datetime, uuid
from pathlib import Path
from typing import List, Dict, Optional, Any


class MotorDecisao:
    def __init__(self, root: Path):
        self.root = root
        self.dir_decisions = root / "memory" / "decisions"
        self.dir_goals     = root / "memory" / "goals"
        self.dir_memoria   = root / "memoria"
        for d in [self.dir_decisions, self.dir_goals]:
            d.mkdir(parents=True, exist_ok=True)

    # ── API pública ───────────────────────────────────────────────────────

    def decidir(self, situacao: str, opcoes: List[Dict],
                contexto: str = "") -> Dict:
        """
        Avalia opções e retorna a melhor decisão.
        Registra resultado em /memory/decisions/.

        opcoes = [
            {"acao": "usar_skill", "descricao": "...", "impacto": 8, "custo": 2},
            {"acao": "chamar_claude", "descricao": "...", "impacto": 9, "custo": 7},
        ]
        """
        if not opcoes:
            return {"acao": "nenhuma", "motivo": "Sem opções disponíveis"}

        # Pontua cada opção: score = impacto - custo
        for op in opcoes:
            op["score"] = op.get("impacto", 5) - op.get("custo", 5)

        # Ordena por score
        opcoes_ordenadas = sorted(opcoes, key=lambda x: x["score"], reverse=True)
        escolha = opcoes_ordenadas[0]

        # Busca contexto histórico relevante
        historico = self._buscar_decisoes_similares(situacao, limite=3)

        decisao = {
            "id":        str(uuid.uuid4())[:8],
            "timestamp": datetime.datetime.now().isoformat(),
            "situacao":  situacao,
            "contexto":  contexto[:500] if contexto else "",
            "opcoes_avaliadas": opcoes_ordenadas,
            "escolha":   escolha,
            "historico_similar": historico,
            "resultado": None,  # preenchido após execução
        }

        self._registrar(decisao)
        return decisao

    def registrar_resultado(self, decisao_id: str, resultado: str,
                            sucesso: bool):
        """Atualiza decisão com o resultado real após execução."""
        for arq in self.dir_decisions.glob("*.json"):
            try:
                dados = json.loads(arq.read_text(encoding="utf-8"))
                if dados.get("id") == decisao_id:
                    dados["resultado"] = resultado
                    dados["sucesso"]   = sucesso
                    dados["fechado_em"] = datetime.datetime.now().isoformat()
                    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
                    return True
            except Exception:
                continue
        return False

    def resumo_decisoes(self, ultimas: int = 10) -> str:
        """Retorna resumo das últimas decisões para uso como contexto."""
        arquivos = sorted(self.dir_decisions.glob("*.json"),
                          key=lambda f: f.stat().st_mtime, reverse=True)
        linhas = []
        for arq in arquivos[:ultimas]:
            try:
                d = json.loads(arq.read_text(encoding="utf-8"))
                status = "✓" if d.get("sucesso") else ("✗" if d.get("resultado") else "?")
                linhas.append(
                    f"[{status}] {d['timestamp'][:16]} — {d['situacao'][:60]}\n"
                    f"   Escolha: {d['escolha'].get('acao','?')} "
                    f"(score:{d['escolha'].get('score','?')})"
                )
            except Exception:
                continue
        return "\n".join(linhas) if linhas else "Nenhuma decisão registrada ainda."

    # ── Internos ──────────────────────────────────────────────────────────

    def _registrar(self, decisao: Dict):
        ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        arq = self.dir_decisions / f"{ts}_{decisao['id']}.json"
        arq.write_text(json.dumps(decisao, ensure_ascii=False, indent=2),
                       encoding="utf-8")

    def _buscar_decisoes_similares(self, situacao: str,
                                   limite: int = 3) -> List[Dict]:
        palavras = [w for w in situacao.lower().split() if len(w) > 3]
        resultados = []
        for arq in sorted(self.dir_decisions.glob("*.json"),
                          key=lambda f: f.stat().st_mtime, reverse=True):
            try:
                d = json.loads(arq.read_text(encoding="utf-8"))
                txt = (d.get("situacao", "") + d.get("contexto", "")).lower()
                if any(p in txt for p in palavras) and d.get("resultado"):
                    resultados.append({
                        "situacao": d["situacao"][:80],
                        "escolha":  d["escolha"].get("acao", "?"),
                        "sucesso":  d.get("sucesso", False),
                    })
                    if len(resultados) >= limite:
                        break
            except Exception:
                continue
        return resultados
