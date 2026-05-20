"""
git_sync.py — Sincronização Git do Libertus
Commits automáticos com contexto semântico a cada evolução.

Opera em: /LIBERTUS/ (que deve ser um repositório git)
"""

import subprocess, datetime, json
from pathlib import Path
from typing import Optional, List


class GitSync:
    def __init__(self, root: Path):
        self.root   = root
        self.git_ok = self._verificar_git()

    # ── Setup ─────────────────────────────────────────────────────────────

    def inicializar(self, remote_url: str = "") -> str:
        """Inicializa repositório git no root do Libertus."""
        if (self.root / ".git").exists():
            return "Repositório já inicializado"

        cmds = [
            ["git", "init"],
            ["git", "add", ".gitignore"],
        ]

        # Cria .gitignore
        gitignore = self.root / ".gitignore"
        gitignore.write_text(
            "__pycache__/\n*.pyc\n*.pyo\n.env\n*.key\n"
            "*.secret\nvenv/\n.venv/\n*.log\n.DS_Store\n"
            "Thumbs.db\n*.tmp\n",
            encoding="utf-8"
        )

        resultados = []
        for cmd in cmds:
            r = self._git(cmd)
            resultados.append(r)

        if remote_url:
            self._git(["git", "remote", "add", "origin", remote_url])

        return "\n".join(resultados)

    # ── Commit automático ─────────────────────────────────────────────────

    def commit_evolucao(self, descricao: str, arquivos: List[str] = None,
                        tipo: str = "feat") -> str:
        """
        Faz commit semântico de uma evolução do sistema.
        tipos: feat, fix, docs, refactor, chore, learn
        """
        if not self.git_ok:
            return "Git não disponível"

        # Garantir identidade git configurada
        self._git(["git", "config", "user.email", "libertus@shield.ai"])
        self._git(["git", "config", "user.name", "LIBERTUS"])

        # Adiciona arquivos
        if arquivos:
            for arq in arquivos:
                self._git(["git", "add", arq])
        else:
            self._git(["git", "add", "-A"])

        # Verifica se há algo para commitar
        status = self._git(["git", "status", "--porcelain"])
        if not status.strip():
            return "Nada para commitar"

        # Mensagem semântica
        ts      = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        msg     = f"{tipo}(libertus): {descricao[:72]}\n\n[{ts}] Autocommit do Libertus v6"
        resultado = self._git(["git", "commit", "-m", msg])

        return resultado

    def commit_skill(self, skill_name: str, descricao: str) -> str:
        """Commit específico para nova skill criada."""
        return self.commit_evolucao(
            f"adiciona skill: {skill_name} — {descricao[:50]}",
            arquivos=[str(self.root / "skills")],
            tipo="learn"
        )

    def commit_memoria(self, titulo: str) -> str:
        """Commit de novo conhecimento absorvido."""
        return self.commit_evolucao(
            f"absorve conhecimento: {titulo[:60]}",
            arquivos=[str(self.root / "memoria"),
                      str(self.root / "evolucao")],
            tipo="docs"
        )

    def push(self, branch: str = "main") -> str:
        """Envia commits para o GitHub."""
        if not self.git_ok:
            return "Git não disponível"
        return self._git(["git", "push", "origin", branch])

    def pull(self) -> str:
        """Busca atualizações do GitHub."""
        if not self.git_ok:
            return "Git não disponível"
        return self._git(["git", "pull"])

    def status(self) -> str:
        """Retorna status do repositório."""
        if not self.git_ok:
            return "Git não disponível ou não inicializado"
        s = self._git(["git", "status", "--short"])
        log = self._git(["git", "log", "--oneline", "-5"])
        return f"Status:\n{s}\n\nÚltimos commits:\n{log}"

    def log_evolucao(self, ultimos: int = 10) -> str:
        """Retorna log de commits do Libertus."""
        if not self.git_ok:
            return ""
        return self._git([
            "git", "log", f"-{ultimos}",
            "--pretty=format:%ai | %s",
            "--grep=libertus"
        ])

    def sincronizar(self) -> str:
        """Pull + add + commit automático + push."""
        if not self.git_ok:
            return "Git não disponível"
        resultados = []
        resultados.append(self.pull())
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        resultados.append(self.commit_evolucao(
            f"sincronização automática do sistema",
            tipo="chore"
        ))
        resultados.append(self.push())
        return "\n".join(r for r in resultados if r.strip())

    # ── Configuração do repositório ───────────────────────────────────────

    def configurar_repositorio(self, nome: str, email: str,
                               remote_url: str = "") -> str:
        """Configura identidade git e remote."""
        resultados = [
            self._git(["git", "config", "user.name", nome]),
            self._git(["git", "config", "user.email", email]),
        ]
        if remote_url:
            # Verifica se remote já existe
            remotes = self._git(["git", "remote"])
            if "origin" not in remotes:
                resultados.append(
                    self._git(["git", "remote", "add", "origin", remote_url])
                )
            else:
                resultados.append(
                    self._git(["git", "remote", "set-url", "origin", remote_url])
                )
        return "\n".join(r for r in resultados if r.strip())

    # ── Internos ──────────────────────────────────────────────────────────

    def _git(self, cmd: List[str]) -> str:
        try:
            r = subprocess.run(
                cmd, cwd=str(self.root),
                capture_output=True, text=True, timeout=30
            )
            return (r.stdout + r.stderr).strip()
        except subprocess.TimeoutExpired:
            return "Timeout no comando git"
        except FileNotFoundError:
            return "git não instalado"
        except Exception as e:
            return str(e)

    def _verificar_git(self) -> bool:
        try:
            r = subprocess.run(
                ["git", "--version"],
                capture_output=True, timeout=5
            )
            return r.returncode == 0
        except Exception:
            return False
