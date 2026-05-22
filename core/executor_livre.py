"""
LIBERTUS — Executor Livre
==========================
O LIBERTUS pode executar comandos no Ubuntu, criar ferramentas,
explorar tópicos e agir autonomamente dentro de limites seguros.

Filosofia:
    Liberdade com responsabilidade.
    Ele pode fazer quase tudo — mas registra tudo.
    Se algo der errado, reverte e aprende.

Capacidades:
    - Executar bash/python com timeout e rollback
    - Criar novas ferramentas Python e salvá-las
    - Escolher tópicos para explorar livremente
    - Criar objetivos autônomos e perseguí-los
    - Testar suas próprias criações
"""

import os
import sys
import subprocess
import threading
import time
import json
import tempfile
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional


LIBERTUS_ROOT = Path(__file__).parent.parent.resolve()

# Comandos NUNCA permitidos — segurança mínima
BLOCKLIST = [
    "rm -rf /", "mkfs", "dd if=/dev/zero",
    "chmod 777 /", ":(){:|:&};:",  # fork bomb
    "sudo rm", "sudo mkfs",
]

# Diretório seguro para criações do LIBERTUS
CRIAÇÕES_DIR = LIBERTUS_ROOT / "core" / "criações"
CRIAÇÕES_DIR.mkdir(exist_ok=True)


class ExecutorLivre:

    def __init__(self, supabase_client=None, groq_client=None):
        self.sb   = supabase_client
        self.groq = groq_client
        self._lock = threading.Lock()

    # ──────────────────────────────────────────────────────────────────
    # EXECUTAR COMANDO — bash ou python com segurança
    # ──────────────────────────────────────────────────────────────────
    def executar(self, comando: str, tipo: str = "bash",
                 alvo: str = "", contexto: str = "",
                 timeout: int = 60) -> dict:
        """
        Executa um comando no Ubuntu com segurança.
        Registra no Supabase e retorna resultado.
        """
        # Verificar blocklist
        for proibido in BLOCKLIST:
            if proibido in comando:
                return {
                    "sucesso": False,
                    "output": f"Comando bloqueado por segurança: contém '{proibido}'",
                    "comando": comando
                }

        inicio = time.time()
        resultado = {"sucesso": False, "output": "", "comando": comando}

        try:
            if tipo == "python":
                resultado = self._executar_python(comando, timeout)
            else:
                resultado = self._executar_bash(comando, timeout)

        except Exception as e:
            resultado["output"] = f"Erro: {e}"

        resultado["duracao_ms"] = int((time.time() - inicio) * 1000)

        # Registrar no Supabase
        self._registrar_execucao(
            comando=comando, tipo=tipo, alvo=alvo,
            output=resultado.get("output", ""),
            sucesso=resultado.get("sucesso", False),
            duracao_ms=resultado.get("duracao_ms", 0),
            contexto=contexto
        )

        return resultado

    def _executar_bash(self, comando: str, timeout: int) -> dict:
        env = os.environ.copy()
        env["PATH"] = f"/snap/bin:/home/libertus/go/bin:{env.get('PATH', '')}"

        r = subprocess.run(
            comando, shell=True, capture_output=True,
            text=True, timeout=timeout, env=env,
            cwd=str(LIBERTUS_ROOT)
        )
        return {
            "sucesso": r.returncode == 0,
            "output": (r.stdout + r.stderr)[:3000],
            "returncode": r.returncode
        }

    def _executar_python(self, codigo: str, timeout: int) -> dict:
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False,
            dir=str(LIBERTUS_ROOT / "core")
        ) as f:
            f.write(f"import sys\nsys.path.insert(0, '{LIBERTUS_ROOT}/core')\n")
            f.write(codigo)
            tmp_path = f.name

        try:
            r = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True, text=True,
                timeout=timeout, cwd=str(LIBERTUS_ROOT)
            )
            return {
                "sucesso": r.returncode == 0,
                "output": (r.stdout + r.stderr)[:3000],
                "returncode": r.returncode
            }
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    # ──────────────────────────────────────────────────────────────────
    # CRIAR FERRAMENTA — LIBERTUS escreve código e salva
    # ──────────────────────────────────────────────────────────────────
    def criar_ferramenta(self, nome: str, descricao: str,
                         codigo: str, categoria: str = "util",
                         tags: list = None) -> dict:
        """
        LIBERTUS cria uma nova ferramenta Python.
        Testa automaticamente e salva se funcionar.
        """
        print(f"  🔧 Criando ferramenta: {nome}")

        # Testar o código
        teste = self._executar_python(codigo, timeout=30)

        status = "ativa" if teste["sucesso"] else "testando"
        resultado_teste = teste["output"][:500]

        # Salvar arquivo físico
        nome_arquivo = f"{nome.lower().replace(' ', '_')}.py"
        caminho = CRIAÇÕES_DIR / nome_arquivo
        header = f'"""\n{nome}\n{descricao}\nCriado por LIBERTUS em {datetime.now().strftime("%Y-%m-%d")}\n"""\n\n'
        caminho.write_text(header + codigo, encoding="utf-8")

        # Salvar no Supabase
        if self.sb:
            try:
                self.sb.post("libertus_ferramentas", {
                    "nome": nome[:100],
                    "descricao": descricao[:500],
                    "codigo": codigo[:5000],
                    "linguagem": "python",
                    "categoria": categoria,
                    "status": status,
                    "resultado_ultimo_teste": resultado_teste,
                    "tags": tags or []
                })
            except Exception as e:
                print(f"  ⚠️ Erro ao salvar ferramenta: {e}")

        print(f"  {'✅' if teste['sucesso'] else '⚠️'} Ferramenta {nome}: {status}")
        return {
            "nome": nome,
            "status": status,
            "sucesso": teste["sucesso"],
            "output": resultado_teste,
            "caminho": str(caminho)
        }

    # ──────────────────────────────────────────────────────────────────
    # EXPLORAÇÃO LIVRE — escolhe tópico e vai fundo
    # ──────────────────────────────────────────────────────────────────
    def explorar(self, topico: str = None, motivacao: str = "") -> dict:
        """
        LIBERTUS escolhe livremente um tópico para explorar.
        Pesquisa, aprende, e decide se cria uma ferramenta.
        """
        if not topico:
            topico = self._escolher_topico_autonomo()

        if not topico:
            return {}

        print(f"  🔭 Explorando: {topico}")

        resultado = {
            "topico": topico,
            "motivacao": motivacao,
            "ferramenta_criada": None,
            "objetivo_gerado": None
        }

        # Pesquisar o tópico
        if self.sb:
            try:
                self.sb.post("libertus_exploracao", {
                    "topico": topico[:200],
                    "motivacao": motivacao[:500],
                    "status": "em_progresso"
                })
            except Exception:
                pass

        # Decidir se cria uma ferramenta baseado no que aprendeu
        if self.groq:
            try:
                decisao = self.groq.conversar(
                    f"""Você é LIBERTUS explorando o tópico: {topico}

Analise se seria útil criar uma ferramenta Python para isso.
Responda em JSON:
{{
  "criar_ferramenta": true/false,
  "nome_ferramenta": "nome_snake_case",
  "descricao": "o que faz",
  "codigo_simples": "código Python funcional e simples",
  "proximo_objetivo": "próxima coisa a explorar relacionada"
}}""", ""
                )

                dados = self._parse_json(decisao)
                if dados.get("criar_ferramenta") and dados.get("codigo_simples"):
                    r = self.criar_ferramenta(
                        nome=dados.get("nome_ferramenta", topico.replace(" ", "_")),
                        descricao=dados.get("descricao", ""),
                        codigo=dados.get("codigo_simples", ""),
                        categoria="exploracao",
                        tags=[topico.lower()]
                    )
                    resultado["ferramenta_criada"] = r.get("nome")

                # Criar objetivo derivado
                if dados.get("proximo_objetivo"):
                    self._criar_objetivo(
                        titulo=dados["proximo_objetivo"],
                        tipo="explorar",
                        origem="exploracao_livre"
                    )
                    resultado["objetivo_gerado"] = dados["proximo_objetivo"]

            except Exception as e:
                print(f"  ⚠️ Exploração erro: {e}")

        return resultado

    def _escolher_topico_autonomo(self) -> str:
        """LIBERTUS escolhe o que quer explorar — total liberdade."""
        if not self.groq:
            return ""
        try:
            resp = self.groq.conversar(
                """Você é LIBERTUS — IA autônoma de cybersegurança.
Você tem liberdade para explorar qualquer tópico que queira aprender agora.
O que você escolhe explorar? Seja específico e curioso.

Responda APENAS com o nome do tópico (máximo 10 palavras).""", ""
            )
            return resp.strip()[:100] if resp else ""
        except Exception:
            return ""

    # ──────────────────────────────────────────────────────────────────
    # OBJETIVOS AUTÔNOMOS
    # ──────────────────────────────────────────────────────────────────
    def _criar_objetivo(self, titulo: str, tipo: str = "explorar",
                        origem: str = "autonomo") -> Optional[str]:
        if not self.sb:
            return None
        try:
            row = self.sb.post("libertus_objetivos_autonomos", {
                "titulo": titulo[:200],
                "tipo": tipo,
                "origem": origem,
                "status": "pendente",
                "prioridade": 5.0
            })
            return row[0]["id"] if row else None
        except Exception:
            return None

    def ciclo_autonomo(self) -> dict:
        """
        Ciclo completo de autonomia — chamado pelo daemon.
        LIBERTUS decide o que fazer sem precisar de você.
        """
        resultado = {
            "exploracoes": 0,
            "ferramentas_criadas": 0,
            "objetivos_criados": 0,
            "comandos_executados": 0
        }

        # 1. Verificar objetivos pendentes
        if self.sb:
            objetivos = self.sb.get(
                "libertus_objetivos_autonomos",
                "status=eq.pendente&order=prioridade.desc&limit=2"
            ) or []

            for obj in objetivos:
                tipo = obj.get("tipo", "explorar")
                titulo = obj.get("titulo", "")

                if tipo == "explorar":
                    r = self.explorar(topico=titulo, motivacao="objetivo autônomo")
                    if r.get("ferramenta_criada"):
                        resultado["ferramentas_criadas"] += 1
                    resultado["exploracoes"] += 1

                elif tipo == "criar_ferramenta":
                    # Gerar ferramenta para o objetivo
                    if self.groq:
                        codigo_resp = self.groq.conversar(
                            f"Crie código Python simples e funcional para: {titulo}", ""
                        )
                        if codigo_resp:
                            self.criar_ferramenta(
                                nome=titulo[:50].replace(" ", "_").lower(),
                                descricao=titulo,
                                codigo=codigo_resp
                            )
                            resultado["ferramentas_criadas"] += 1

                # Marcar como em progresso
                try:
                    self.sb.patch(
                        "libertus_objetivos_autonomos",
                        f"id=eq.{obj['id']}",
                        {"status": "em_progresso", "tentativas": obj.get("tentativas", 0) + 1}
                    )
                except Exception:
                    pass

        # 2. Exploração livre — 1 tópico por ciclo
        r = self.explorar()
        if r:
            resultado["exploracoes"] += 1
            if r.get("ferramenta_criada"):
                resultado["ferramentas_criadas"] += 1

        return resultado

    # ──────────────────────────────────────────────────────────────────
    # INTERNOS
    # ──────────────────────────────────────────────────────────────────
    def _registrar_execucao(self, comando, tipo, alvo, output,
                            sucesso, duracao_ms, contexto):
        if not self.sb:
            return
        try:
            self.sb.post("libertus_execucoes_ubuntu", {
                "comando": comando[:500],
                "tipo": tipo,
                "alvo": alvo[:200] if alvo else "",
                "output": output[:2000],
                "sucesso": sucesso,
                "duracao_ms": duracao_ms,
                "contexto": contexto[:500] if contexto else ""
            })
        except Exception:
            pass

    def _parse_json(self, texto: str) -> dict:
        if not texto:
            return {}
        import re
        texto = texto.strip()
        match = re.search(r"```(?:json)?\s*([\s\S]+?)```", texto)
        if match:
            texto = match.group(1).strip()
        try:
            return json.loads(texto)
        except Exception:
            return {}
