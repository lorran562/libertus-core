"""
sistema_objetivos.py — Sistema de Objetivos do Libertus
Mantém objetivos ativos, revisa prioridades e gera novos objetivos.

Lê/Escreve em: /LIBERTUS/memory/goals/
"""

import json, datetime, uuid
from pathlib import Path
from typing import List, Dict, Optional
from enum import Enum


class Prazo(str, Enum):
    CURTO  = "curto"   # execução imediata (hoje)
    MEDIO  = "medio"   # melhorias do sistema (semana)
    LONGO  = "longo"   # evolução estrutural (mês+)


class Status(str, Enum):
    ATIVO      = "ativo"
    CONCLUIDO  = "concluido"
    CANCELADO  = "cancelado"
    PAUSADO    = "pausado"


class SistemaObjetivos:
    def __init__(self, root: Path):
        self.root     = root
        self.dir_goals = root / "memory" / "goals"
        self.dir_goals.mkdir(parents=True, exist_ok=True)
        self._garantir_objetivos_iniciais()

    # ── API pública ───────────────────────────────────────────────────────

    def criar(self, titulo: str, descricao: str, prazo: Prazo,
              prioridade: int = 5, tags: List[str] = None) -> Dict:
        """Cria novo objetivo e salva em /memory/goals/."""
        obj = {
            "id":          str(uuid.uuid4())[:8],
            "titulo":      titulo,
            "descricao":   descricao,
            "prazo":       prazo,
            "prioridade":  prioridade,
            "tags":        tags or [],
            "status":      Status.ATIVO,
            "criado_em":   datetime.datetime.now().isoformat(),
            "atualizado_em": datetime.datetime.now().isoformat(),
            "progresso":   0,
            "subobjetivos": [],
            "resultado":   None,
        }
        self._salvar(obj)
        return obj

    def listar(self, prazo: Prazo = None,
               status: Status = Status.ATIVO) -> List[Dict]:
        """Lista objetivos filtrados por prazo e status."""
        todos = self._carregar_todos()
        filtrados = [o for o in todos if o.get("status") == status]
        if prazo:
            filtrados = [o for o in filtrados if o.get("prazo") == prazo]
        return sorted(filtrados, key=lambda x: x.get("prioridade", 5),
                      reverse=True)

    def atualizar_progresso(self, obj_id: str, progresso: int,
                             nota: str = "") -> bool:
        """Atualiza progresso (0-100) de um objetivo."""
        for arq in self.dir_goals.glob("*.json"):
            try:
                dados = json.loads(arq.read_text(encoding="utf-8"))
                if dados.get("id") == obj_id:
                    dados["progresso"]    = min(100, max(0, progresso))
                    dados["atualizado_em"] = datetime.datetime.now().isoformat()
                    if nota:
                        dados.setdefault("notas", []).append({
                            "data": datetime.datetime.now().isoformat(),
                            "nota": nota,
                        })
                    if progresso >= 100:
                        dados["status"]    = Status.CONCLUIDO
                        dados["resultado"] = nota or "Concluído"
                    arq.write_text(json.dumps(dados, ensure_ascii=False,
                                              indent=2), encoding="utf-8")
                    return True
            except Exception:
                continue
        return False

    def resumo(self) -> str:
        """Retorna resumo de objetivos para usar como contexto."""
        linhas = ["=== OBJETIVOS DO LIBERTUS ===\n"]
        for prazo in [Prazo.CURTO, Prazo.MEDIO, Prazo.LONGO]:
            objs = self.listar(prazo=prazo)
            if not objs:
                continue
            linhas.append(f"\n## {prazo.upper()} PRAZO ({len(objs)}):")
            for o in objs[:5]:
                barra = "█" * (o["progresso"] // 10) + "░" * (10 - o["progresso"] // 10)
                linhas.append(
                    f"  [{barra}] {o['progresso']}% — {o['titulo']} "
                    f"(p:{o['prioridade']})"
                )
        return "\n".join(linhas)

    def gerar_objetivos_automaticos(self, contexto: str) -> List[Dict]:
        """Gera novos objetivos baseados no contexto atual."""
        novos = []
        c = contexto.lower()

        # Detecta padrões e gera objetivos relevantes
        if "erro" in c or "bug" in c or "falhou" in c:
            novos.append(self.criar(
                "Corrigir erros detectados no sistema",
                f"Contexto: {contexto[:200]}",
                Prazo.CURTO, prioridade=9,
                tags=["correcao", "urgente"]
            ))

        if "skill" in c and ("criar" in c or "nova" in c):
            novos.append(self.criar(
                "Criar nova skill para tarefa detectada",
                f"Baseado em: {contexto[:200]}",
                Prazo.CURTO, prioridade=7,
                tags=["skill", "aprendizado"]
            ))

        if "performance" in c or "lento" in c or "demorou" in c:
            novos.append(self.criar(
                "Otimizar performance do sistema",
                "Performance abaixo do esperado detectada",
                Prazo.MEDIO, prioridade=6,
                tags=["performance", "otimizacao"]
            ))

        return novos

    # ── Internos ──────────────────────────────────────────────────────────

    def _salvar(self, obj: Dict):
        arq = self.dir_goals / f"{obj['id']}.json"
        arq.write_text(json.dumps(obj, ensure_ascii=False, indent=2),
                       encoding="utf-8")

    def _carregar_todos(self) -> List[Dict]:
        resultado = []
        for arq in self.dir_goals.glob("*.json"):
            try:
                resultado.append(json.loads(arq.read_text(encoding="utf-8")))
            except Exception:
                continue
        return resultado

    def _garantir_objetivos_iniciais(self):
        """Cria objetivos base se o sistema for novo."""
        if any(self.dir_goals.glob("*.json")):
            return

        objetivos_base = [
            ("Atingir 100 skills autônomas no Supabase",
             "Crescer o Skill Engine para cobertura total das tarefas de Lorran",
             Prazo.LONGO, 9),
            ("Configurar Groq API para conversa inteligente gratuita",
             "Ativar llama3-70b como motor de conversa sem custo",
             Prazo.CURTO, 10),
            ("Documentar todos os projetos ativos no Obsidian",
             "T7 Vapor, PixSwap, Ashen Roots, LorranStack completamente documentados",
             Prazo.MEDIO, 8),
            ("Implementar ciclo de autoevolução contínuo",
             "Sistema que detecta, planeja e aplica melhorias automaticamente",
             Prazo.LONGO, 10),
            ("Configurar sincronização com GitHub",
             "Commits automáticos com contexto semântico a cada evolução",
             Prazo.MEDIO, 7),
        ]

        for titulo, desc, prazo, prio in objetivos_base:
            self.criar(titulo, desc, prazo, prioridade=prio,
                       tags=["inicial", "sistema"])
