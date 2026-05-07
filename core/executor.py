"""
executor.py — Executor de Ações Reais do Libertus
Executa scripts, APIs, arquivos com validação e rollback.

Registra em: /LIBERTUS/memory/feedback/
"""

import subprocess, datetime, json, shutil, hashlib
from pathlib import Path
from typing import Dict, Optional, List, Callable


class Executor:
    def __init__(self, root: Path, seguranca=None):
        self.root        = root
        self.seguranca   = seguranca
        self.dir_feedback = root / "memory" / "feedback"
        self.dir_backup  = root / "memory" / ".backups"
        for d in [self.dir_feedback, self.dir_backup]:
            d.mkdir(parents=True, exist_ok=True)

    # ── Execução de código Python ─────────────────────────────────────────

    def executar_python(self, codigo: str, contexto: Dict = None,
                        timeout: int = 30) -> Dict:
        """
        Executa código Python com análise de segurança prévia.
        Registra resultado em /memory/feedback/.
        """
        inicio = datetime.datetime.now().isoformat()

        # Análise de segurança
        if self.seguranca:
            ok, alertas = self.seguranca.analisar(codigo)
            if not ok:
                resultado = {
                    "status":    "bloqueado",
                    "inicio":    inicio,
                    "alertas":   alertas,
                    "resultado": "Bloqueado por segurança: " + "; ".join(alertas[:3]),
                }
                self._registrar_feedback(resultado, "execucao_python")
                return resultado

        import time as _time
        t0 = _time.time()
        try:
            import re as _re
            from pathlib import Path as _Path
            import subprocess as _sp

            ctx = {
                "resultado": None,
                "tarefa":    (contexto or {}).get("tarefa", ""),
                "params":    (contexto or {}).get("params", {}),
                "Path":      _Path, "json": json,
                "subprocess": _sp, "datetime": datetime,
                "time":      _time, "re": _re,
            }
            exec(compile(codigo, "<libertus_exec>", "exec"), ctx)
            duracao = int((_time.time() - t0) * 1000)

            resultado = {
                "status":     "ok",
                "inicio":     inicio,
                "fim":        datetime.datetime.now().isoformat(),
                "duracao_ms": duracao,
                "resultado":  str(ctx.get("resultado", ""))[:1000],
                "sucesso":    True,
            }
        except Exception as e:
            resultado = {
                "status":    "erro",
                "inicio":    inicio,
                "fim":       datetime.datetime.now().isoformat(),
                "erro":      str(e)[:500],
                "sucesso":   False,
                "resultado": f"Erro: {e}",
            }

        self._registrar_feedback(resultado, "execucao_python")
        return resultado

    # ── Execução de scripts externos ──────────────────────────────────────

    def executar_script(self, caminho: str, args: List[str] = None,
                        timeout: int = 60) -> Dict:
        """Executa script externo (.py, .sh, .bat) com timeout."""
        inicio = datetime.datetime.now().isoformat()
        p = Path(caminho)

        if not p.exists():
            return {"status": "erro", "resultado": f"Script não encontrado: {caminho}"}

        cmd = []
        if p.suffix == ".py":
            cmd = ["python3" if shutil.which("python3") else "python", str(p)]
        elif p.suffix == ".sh":
            cmd = ["bash", str(p)]
        elif p.suffix == ".bat":
            cmd = [str(p)]
        else:
            cmd = [str(p)]

        if args:
            cmd.extend(args)

        try:
            r = subprocess.run(
                cmd, capture_output=True, text=True,
                timeout=timeout, cwd=str(self.root)
            )
            resultado = {
                "status":    "ok" if r.returncode == 0 else "erro",
                "inicio":    inicio,
                "fim":       datetime.datetime.now().isoformat(),
                "returncode": r.returncode,
                "stdout":    r.stdout[:1000],
                "stderr":    r.stderr[:500],
                "sucesso":   r.returncode == 0,
                "resultado": r.stdout[:500] if r.returncode == 0 else r.stderr[:500],
            }
        except subprocess.TimeoutExpired:
            resultado = {"status": "timeout", "sucesso": False,
                         "resultado": f"Timeout após {timeout}s"}
        except Exception as e:
            resultado = {"status": "erro", "sucesso": False,
                         "resultado": str(e)}

        self._registrar_feedback(resultado, "execucao_script")
        return resultado

    # ── Manipulação de arquivos com backup ────────────────────────────────

    def escrever_arquivo(self, caminho: str, conteudo: str,
                         modo: str = "w") -> Dict:
        """
        Escreve em arquivo com backup automático antes de sobrescrever.
        Permite rollback em caso de falha.
        """
        p = Path(caminho)
        backup_id = None

        # Cria backup se arquivo existe
        if p.exists() and modo == "w":
            backup_id = self._criar_backup(p)

        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, modo, encoding="utf-8") as f:
                f.write(conteudo)

            resultado = {
                "status":    "ok",
                "caminho":   str(p),
                "backup_id": backup_id,
                "sucesso":   True,
                "resultado": f"Arquivo escrito: {p.name} ({len(conteudo)} chars)",
            }
        except Exception as e:
            # Tenta rollback
            if backup_id:
                self._restaurar_backup(backup_id, p)
            resultado = {
                "status":  "erro",
                "sucesso": False,
                "resultado": f"Erro ao escrever {p}: {e}",
                "rollback": backup_id is not None,
            }

        self._registrar_feedback(resultado, "escrita_arquivo")
        return resultado

    def rollback(self, backup_id: str, caminho: str) -> bool:
        """Restaura arquivo a partir de um backup."""
        return self._restaurar_backup(backup_id, Path(caminho))

    # ── Feedback e métricas ───────────────────────────────────────────────

    def resumo_feedback(self, ultimos: int = 10) -> str:
        """Retorna resumo das últimas execuções."""
        arquivos = sorted(self.dir_feedback.glob("*.json"),
                          key=lambda f: f.stat().st_mtime, reverse=True)
        linhas   = ["=== FEEDBACK DE EXECUÇÕES ==="]
        ok_count = err_count = 0

        for arq in arquivos[:ultimos]:
            try:
                d = json.loads(arq.read_text(encoding="utf-8"))
                status = "✓" if d.get("sucesso") else "✗"
                if d.get("sucesso"):
                    ok_count += 1
                else:
                    err_count += 1
                linhas.append(
                    f"[{status}] {d.get('inicio','?')[:16]} — "
                    f"{d.get('resultado','')[:60]}"
                )
            except Exception:
                continue

        total = ok_count + err_count
        if total:
            taxa = round(ok_count / total * 100, 1)
            linhas.append(f"\nTaxa de sucesso: {taxa}% ({ok_count}/{total})")

        return "\n".join(linhas)

    # ── Internos ──────────────────────────────────────────────────────────

    def _registrar_feedback(self, dados: Dict, tipo: str):
        ts  = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        arq = self.dir_feedback / f"{ts}_{tipo}.json"
        dados["tipo"] = tipo
        arq.write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                       encoding="utf-8")

    def _criar_backup(self, arquivo: Path) -> str:
        backup_id = hashlib.md5(
            (str(arquivo) + datetime.datetime.now().isoformat()).encode()
        ).hexdigest()[:8]
        backup_dir = self.dir_backup / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(arquivo), str(backup_dir / arquivo.name))
        return backup_id

    def _restaurar_backup(self, backup_id: str, destino: Path) -> bool:
        backup_dir = self.dir_backup / backup_id
        if not backup_dir.exists():
            return False
        arquivos = list(backup_dir.iterdir())
        if not arquivos:
            return False
        try:
            shutil.copy2(str(arquivos[0]), str(destino))
            return True
        except Exception:
            return False
