"""
memoria_local.py — Módulo de Memória Estratégica
Lê /memoria, /evolucao, /skills, /projetos como contexto.
Escreve aprendizados estruturados em markdown.
"""

import datetime, re, json
from pathlib import Path
from typing import List, Dict, Optional


class MemoriaLocal:
    """Interface com os arquivos markdown do vault Obsidian/LIBERTUS."""

    PASTAS = {"memoria", "evolucao", "skills", "projetos", "erros", "execucoes"}

    def __init__(self, root: Path):
        self.root = root
        for p in self.PASTAS:
            (self.root / p).mkdir(parents=True, exist_ok=True)

    # ── Leitura ───────────────────────────────────────────────────────────

    def buscar_contexto(self, query: str, limite: int = 5) -> str:
        """
        Busca query em todos os arquivos .md do vault.
        Prioriza /memoria e /evolucao.
        Retorna texto concatenado dos trechos relevantes.
        """
        resultados = []
        query_l = query.lower()
        palavras = [w for w in query_l.split() if len(w) > 3]

        prioridade = {"memoria": 10, "evolucao": 8, "projetos": 6,
                      "skills": 5, "erros": 7, "execucoes": 3}

        for pasta in self.PASTAS:
            dir_pasta = self.root / pasta
            if not dir_pasta.exists():
                continue
            for arquivo in sorted(dir_pasta.glob("*.md"),
                                  key=lambda f: f.stat().st_mtime, reverse=True):
                try:
                    txt = arquivo.read_text(encoding="utf-8")
                    # Verifica relevância
                    score = sum(1 for p in palavras if p in txt.lower())
                    if score == 0:
                        continue
                    # Extrai trecho relevante
                    idx = txt.lower().find(palavras[0]) if palavras else 0
                    trecho = txt[max(0, idx-50): idx+300].strip()
                    resultados.append({
                        "pasta": pasta,
                        "arquivo": arquivo.stem,
                        "trecho": trecho,
                        "score": score * prioridade.get(pasta, 1),
                    })
                except Exception:
                    continue

        resultados.sort(key=lambda x: x["score"], reverse=True)
        if not resultados:
            return ""

        partes = []
        for r in resultados[:limite]:
            partes.append(f"[{r['pasta']}/{r['arquivo']}]\n{r['trecho']}")
        return "\n\n".join(partes)

    def ler_recentes(self, pasta: str, limite: int = 3) -> List[Dict]:
        """Lê os arquivos mais recentes de uma pasta."""
        dir_pasta = self.root / pasta
        if not dir_pasta.exists():
            return []
        arquivos = sorted(dir_pasta.glob("*.md"),
                          key=lambda f: f.stat().st_mtime, reverse=True)
        resultado = []
        for arq in arquivos[:limite]:
            try:
                txt = arq.read_text(encoding="utf-8")
                body = txt.split("---", 2)[-1].strip() if txt.startswith("---") else txt
                resultado.append({"arquivo": arq.stem, "conteudo": body[:500]})
            except Exception:
                continue
        return resultado

    def ler_arquivo(self, pasta: str, nome: str) -> Optional[str]:
        """Lê um arquivo específico do vault."""
        p = self.root / pasta / f"{nome}.md"
        if not p.exists():
            return None
        try:
            return p.read_text(encoding="utf-8")
        except Exception:
            return None

    # ── Escrita ───────────────────────────────────────────────────────────

    def salvar(self, pasta: str, titulo: str, conteudo: str,
               tags: List[str] = None) -> str:
        """
        Salva conhecimento estruturado no vault.
        Pasta deve ser: memoria | evolucao | skills | projetos | erros
        Retorna caminho do arquivo criado.
        """
        if pasta not in self.PASTAS:
            pasta = self._classificar(conteudo, pasta)

        dir_pasta = self.root / pasta
        dir_pasta.mkdir(parents=True, exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_seguro = re.sub(r"[^\w\s-]", "", titulo).replace(" ", "_")[:40]
        nome_arquivo = f"{ts}_{nome_seguro}.md"
        caminho = dir_pasta / nome_arquivo

        frontmatter = (
            f"---\ntitulo: {titulo}\n"
            f"data: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"pasta: {pasta}\n"
            f"tags: {json.dumps(tags or [], ensure_ascii=False)}\n"
            f"---\n\n"
        )
        caminho.write_text(frontmatter + conteudo, encoding="utf-8")
        return str(caminho)

    def salvar_decisao(self, titulo: str, decisao: str, contexto: str = "") -> str:
        conteudo = (
            f"## Decisão\n{decisao}\n\n"
            f"## Contexto\n{contexto or 'Não informado'}\n\n"
            f"## Data\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        )
        return self.salvar("memoria", titulo, conteudo, ["decisao"])

    def salvar_aprendizado(self, titulo: str, aprendizado: str,
                           padrao: str = "", skill: str = "") -> str:
        conteudo = (
            f"## Aprendizado\n{aprendizado}\n\n"
            f"## Padrão\n{padrao or 'Nenhum específico'}\n\n"
            f"## Skill relacionada\n{skill or 'Nenhuma'}\n\n"
            f"## Data\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        )
        return self.salvar("evolucao", titulo, conteudo, ["aprendizado"])

    def salvar_erro(self, tarefa: str, erro: str, solucao: str = "") -> str:
        conteudo = (
            f"## Tarefa\n{tarefa}\n\n"
            f"## Erro\n```\n{erro}\n```\n\n"
            f"## Solução\n{solucao or 'Não resolvido'}\n\n"
            f"## Data\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        )
        return self.salvar("erros", f"erro_{tarefa[:30]}", conteudo, ["erro"])

    def atualizar_projeto(self, nome_projeto: str, atualizacao: str) -> str:
        """Atualiza ou cria arquivo de projeto."""
        conteudo = (
            f"## Atualização\n{atualizacao}\n\n"
            f"## Data\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        )
        return self.salvar("projetos", nome_projeto, conteudo, ["projeto"])

    # ── Classificação automática ──────────────────────────────────────────

    def _classificar(self, conteudo: str, tipo: str = "") -> str:
        c = (conteudo + tipo).lower()
        if any(w in c for w in ["decisão","decisao","regra","importante"]):
            return "memoria"
        if any(w in c for w in ["projeto","cliente","site","app"]):
            return "projetos"
        if any(w in c for w in ["aprend","padrão","padrao","melhoria"]):
            return "evolucao"
        if any(w in c for w in ["skill","função","automação","script"]):
            return "skills"
        if any(w in c for w in ["erro","bug","falhou"]):
            return "erros"
        return "execucoes"
