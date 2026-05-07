"""
absorvedor.py — Absorção de Conhecimento
Processa PDFs, TXTs e documentos.
Extrai conhecimento útil e salva no vault.
"""

import re
from pathlib import Path
from typing import Optional


class Absorvedor:
    """Processa documentos e extrai conhecimento para o vault."""

    def __init__(self, root: Path):
        self.root = root

    def processar(self, caminho: str) -> str:
        """
        Processa um arquivo e salva conhecimento no vault.
        Suporta: .txt, .md, .pdf (com pdfplumber), .py
        """
        p = Path(caminho)
        if not p.exists():
            return f"Arquivo não encontrado: {caminho}"

        extensao = p.suffix.lower()

        if extensao in (".txt", ".md"):
            texto = p.read_text(encoding="utf-8", errors="replace")
            return self._absorver_texto(texto, p.stem)

        elif extensao == ".pdf":
            return self._absorver_pdf(p)

        elif extensao == ".py":
            texto = p.read_text(encoding="utf-8", errors="replace")
            return self._absorver_codigo(texto, p.stem)

        else:
            return f"Formato não suportado: {extensao}"

    def _absorver_texto(self, texto: str, nome: str) -> str:
        """Extrai conhecimento de texto simples."""
        from memoria_local import MemoriaLocal
        mem = MemoriaLocal(self.root)

        # Limpa o texto
        linhas = [l.strip() for l in texto.splitlines() if l.strip()]
        conteudo_limpo = "\n".join(linhas)

        # Classifica automaticamente
        c = conteudo_limpo.lower()
        if any(w in c for w in ["projeto","cliente","site"]):
            pasta = "projetos"
        elif any(w in c for w in ["erro","bug","problema"]):
            pasta = "erros"
        elif any(w in c for w in ["aprend","padrão","melhoria"]):
            pasta = "evolucao"
        else:
            pasta = "memoria"

        # Resume (primeiras 2000 chars como knowledge)
        resumo = (
            f"## Fonte\n{nome}\n\n"
            f"## Conteúdo absorvido\n{conteudo_limpo[:2000]}\n\n"
            f"## Absorvido em\n{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        )

        caminho = mem.salvar(pasta, f"absorvido_{nome}", resumo, ["absorvido", pasta])
        return f"Absorvido em {pasta}: {caminho}"

    def _absorver_pdf(self, p: Path) -> str:
        """Extrai texto de PDF com pdfplumber."""
        try:
            import pdfplumber
            texto = ""
            with pdfplumber.open(str(p)) as pdf:
                for pagina in pdf.pages[:20]:  # max 20 páginas
                    txt = pagina.extract_text()
                    if txt:
                        texto += txt + "\n"
            return self._absorver_texto(texto, p.stem)
        except ImportError:
            return "pdfplumber não instalado. Execute: pip install pdfplumber"
        except Exception as e:
            return f"Erro ao processar PDF: {e}"

    def _absorver_codigo(self, codigo: str, nome: str) -> str:
        """Extrai docstrings e funções de código Python."""
        from memoria_local import MemoriaLocal
        mem = MemoriaLocal(self.root)

        # Extrai docstrings
        docs = re.findall(r'"""(.*?)"""', codigo, re.DOTALL)
        funcoes = re.findall(r"def (\w+)\s*\(", codigo)

        resumo = (
            f"## Arquivo\n{nome}.py\n\n"
            f"## Funções detectadas\n" +
            "\n".join(f"- {f}()" for f in funcoes[:20]) +
            "\n\n## Documentação\n" +
            "\n\n".join(d.strip()[:300] for d in docs[:5]) +
            f"\n\n## Absorvido em\n{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        )

        caminho = mem.salvar("skills", f"codigo_{nome}", resumo,
                             ["codigo", "python", "absorvido"])
        return f"Código absorvido em skills: {caminho}"
