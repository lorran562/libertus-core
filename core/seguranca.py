"""
seguranca.py — Módulo de Segurança do Libertus
Analisa código Python antes de executar.
Detecta padrões perigosos e sugere melhorias.
"""

import re
from typing import Tuple, List


class Seguranca:
    """Analisa código gerado antes de executar no sistema."""

    PERIGOSOS = [
        (r"os\.system\s*\(", "os.system() — use subprocess.run()"),
        (r"\beval\s*\(", "eval() — risco de injeção de código"),
        (r"exec\s*\(.*input\s*\(", "exec() com input — injeção possível"),
        (r"__import__\s*\(", "__import__ dinâmico — suspeito"),
        (r"rm\s+-rf\s+/", "rm -rf / — destrutivo"),
        (r"DROP\s+TABLE", "SQL DROP TABLE — destrutivo"),
        (r"DELETE\s+FROM\s+\w+\s+WHERE\s+1\s*=\s*1", "DELETE sem filtro real"),
        (r"shutil\.rmtree\s*\(['\"]?/", "rmtree na raiz — perigoso"),
        (r"subprocess.*shell\s*=\s*True.*\+.*input", "shell injection via input"),
        (r"open\s*\(.*['\"]w['\"].*\).*for.*in\s+os\.listdir",
         "sobrescrita em loop de arquivos"),
        (r"requests\.get\s*\(.*\+.*input\s*\(",
         "URL formada com input — SSRF possível"),
        (r"pickle\.loads?\s*\(", "pickle.load — deserialização insegura"),
    ]

    BOAS_PRATICAS = [
        (r"timeout\s*=\s*\d+", "timeout configurado ✓"),
        (r"try\s*:", "try/except presente ✓"),
        (r"if\s+.*is\s+None", "verificação de None ✓"),
        (r"\.strip\s*\(\)", "strip() de input ✓"),
        (r"json\.loads\s*\(.*try", "json com try ✓"),
    ]

    INJECAO_SQL = [
        r"SELECT.*\+.*input",
        r"INSERT.*\+.*input",
        r"WHERE.*\+.*input",
        r"f['\"].*SELECT.*\{",
        r"f['\"].*WHERE.*\{",
    ]

    def analisar(self, codigo: str) -> Tuple[bool, List[str]]:
        """
        Analisa o código em busca de padrões perigosos.
        Retorna (seguro: bool, alertas: List[str])
        """
        alertas = []
        criticos = []

        for padrao, mensagem in self.PERIGOSOS:
            if re.search(padrao, codigo, re.IGNORECASE):
                criticos.append(f"⚠️ ALERTA: {mensagem}")

        for padrao in self.INJECAO_SQL:
            if re.search(padrao, codigo, re.IGNORECASE):
                criticos.append("⚠️ ALERTA: Possível SQL injection — use parâmetros")

        boas = []
        for padrao, msg in self.BOAS_PRATICAS:
            if re.search(padrao, codigo):
                boas.append(f"✓ {msg}")

        alertas.extend(criticos)
        if boas:
            alertas.append("Boas práticas: " + " | ".join(boas))

        # Métricas básicas
        linhas = codigo.count("\n") + 1
        alertas.append(f"📊 {linhas} linhas | "
                       f"{'sem alertas críticos' if not criticos else str(len(criticos)) + ' alertas'}")

        return len(criticos) == 0, alertas

    def sugerir_melhorias(self, codigo: str) -> List[str]:
        """Sugere melhorias de segurança."""
        sugestoes = []
        if "timeout" not in codigo and "httpx" in codigo:
            sugestoes.append("Adicione timeout nas chamadas httpx")
        if "try" not in codigo and len(codigo) > 100:
            sugestoes.append("Adicione try/except para capturar erros")
        if re.search(r"input\s*\(", codigo) and "strip" not in codigo:
            sugestoes.append("Use .strip() em inputs do usuário")
        if "subprocess" in codigo and "capture_output" not in codigo:
            sugestoes.append("Use capture_output=True no subprocess")
        return sugestoes

    def executar_seguro(self, codigo: str, ctx: dict,
                        timeout: int = 30) -> dict:
        """
        Executa código com análise prévia de segurança.
        Retorna resultado ou erro.
        """
        import time, traceback

        ok, alertas = self.analisar(codigo)
        if not ok:
            return {
                "status": "bloqueado",
                "resultado": "Código bloqueado por segurança:\n" + "\n".join(alertas),
                "alertas": alertas,
            }

        t0 = time.time()
        try:
            import subprocess as _sp, datetime as _dt, json as _json
            import re as _re, time as _time
            from pathlib import Path as _Path

            exec_ctx = {
                "resultado": None,
                "tarefa": ctx.get("tarefa", ""),
                "params": ctx.get("params", {}),
                "Path": _Path, "json": _json,
                "subprocess": _sp, "datetime": _dt,
                "time": _time, "re": _re,
            }
            exec(compile(codigo, "<skill>", "exec"), exec_ctx)
            duracao = int((time.time() - t0) * 1000)
            return {
                "status": "done",
                "resultado": str(exec_ctx.get("resultado", "OK"))[:1500],
                "duracao_ms": duracao,
                "alertas": alertas,
            }
        except Exception as e:
            return {
                "status": "erro",
                "resultado": f"Erro na execução: {e}",
                "traceback": traceback.format_exc()[-500:],
                "alertas": alertas,
            }
