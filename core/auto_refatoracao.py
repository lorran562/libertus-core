#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
auto_refatoracao.py — Auto-Refatoração com Rollback Seguro

Detecta bugs no próprio código, gera patches via Claude API,
valida, testa em sandbox e aplica com rollback automático.
"""

import os, sys, json, subprocess, tempfile, shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Importa cliente Anthropic
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None


class AutoRefatoracao:
    """
    Sistema de auto-correção de bugs com validação multi-camada.
    """
    
    def __init__(self, root: Path):
        self.root = root
        self.logs = root / "evolution_logs"
        self.daemon_log = self.logs / "daemon.log"
        self.refactor_log = self.logs / "refatoracao.log"
        self.tentativas_file = root / "memory" / "tentativas_fix.json"
        
        # Cliente Claude
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.claude = Anthropic(api_key=api_key) if (Anthropic and api_key) else None
        
        # Carrega histórico de tentativas
        self.tentativas = self._carregar_tentativas()
        
        # Limite de tentativas por bug
        self.MAX_TENTATIVAS = 3
    
    # ── Detecção de Bugs ──────────────────────────────────────────────
    
    def detectar_bugs_recorrentes(self) -> List[Dict]:
        """
        Analisa logs do daemon e detecta erros recorrentes.
        
        Returns:
            Lista de bugs detectados com contexto
        """
        if not self.daemon_log.exists():
            return []
        
        # Lê últimas 1000 linhas do log
        linhas = self.daemon_log.read_text(encoding="utf-8").split("\n")[-1000:]
        
        # Detecta padrões de erro
        bugs = []
        erros_contados = {}
        
        for linha in linhas:
            # EOF error pattern
            if "EOF when reading a line" in linha:
                erros_contados["EOF_bug"] = erros_contados.get("EOF_bug", 0) + 1
                if erros_contados["EOF_bug"] == 3:  # 3+ ocorrências
                    bugs.append({
                        "id": "EOF_bug",
                        "tipo": "input_pipe_incompativel",
                        "arquivo": "libertus.py",
                        "descricao": "input() não funciona com pipe/redirect",
                        "ocorrencias": erros_contados["EOF_bug"],
                        "gravidade": "media"
                    })
            
            # ModuleNotFoundError pattern
            if "ModuleNotFoundError" in linha:
                modulo = linha.split("No module named ")[-1].strip("'\"")
                bug_id = f"missing_module_{modulo}"
                erros_contados[bug_id] = erros_contados.get(bug_id, 0) + 1
                if erros_contados[bug_id] == 2:
                    bugs.append({
                        "id": bug_id,
                        "tipo": "dependencia_faltando",
                        "arquivo": "requirements.txt",
                        "descricao": f"Módulo {modulo} não instalado",
                        "modulo": modulo,
                        "ocorrencias": erros_contados[bug_id],
                        "gravidade": "alta"
                    })
        
        return bugs
    
    # ── Geração de Patches ────────────────────────────────────────────
    
    def gerar_patch_claude(self, bug: Dict) -> Optional[str]:
        """
        Usa Claude API para gerar patch de correção.
        
        Args:
            bug: Dicionário com informações do bug
            
        Returns:
            Código do patch ou None se falhar
        """
        if not self.claude:
            self._log("ERRO", "Claude API não disponível")
            return None
        
        # Lê código atual
        arquivo_path = self.root / "core" / bug["arquivo"]
        if not arquivo_path.exists():
            return None
        
        codigo_atual = arquivo_path.read_text(encoding="utf-8")
        
        # Prompt especializado por tipo de bug
        if bug["tipo"] == "input_pipe_incompativel":
            prompt = f"""
Arquivo: {bug['arquivo']}
Erro: {bug['descricao']}

Código atual (primeiras 100 linhas):
```python
{chr(10).join(codigo_atual.split(chr(10))[:100])}
```

TAREFA: Gere um patch que:
1. Detecte se stdin está conectado a um pipe usando sys.stdin.isatty()
2. Se for pipe (isatty() == False), use modo não-interativo
3. Se for terminal normal, use input() normalmente
4. Mantenha toda a lógica existente intacta

IMPORTANTE: 
- Retorne APENAS o código Python completo
- NÃO inclua ```python ou markdown
- Mantenha imports e estrutura originais
"""
        
        elif bug["tipo"] == "dependencia_faltando":
            prompt = f"""
Falta módulo: {bug.get('modulo', 'desconhecido')}

TAREFA: Adicione "{bug.get('modulo')}" ao requirements.txt
Retorne APENAS o conteúdo completo do requirements.txt atualizado.
"""
        
        else:
            return None
        
        # Chama Claude API
        try:
            response = self.claude.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            patch = response.content[0].text
            return patch
            
        except Exception as e:
            self._log("ERRO_API", f"Claude API falhou: {e}")
            return None
    
    # ── Validação de Patches ──────────────────────────────────────────
    
    def validar_patch(self, patch: str, arquivo: str) -> Tuple[bool, str]:
        """
        Valida patch em 3 camadas: sintaxe, sandbox, compatibilidade.
        
        Returns:
            (válido: bool, motivo: str)
        """
        # CAMADA 1: Validação sintática
        if arquivo.endswith(".py"):
            try:
                compile(patch, '<patch>', 'exec')
            except SyntaxError as e:
                return False, f"Erro de sintaxe: {e}"
        
        # CAMADA 2: Sandbox test
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
            tmp.write(patch)
            tmp_path = tmp.name
        
        try:
            # Tenta importar o módulo patcheado
            result = subprocess.run(
                [sys.executable, '-c', f'import py_compile; py_compile.compile("{tmp_path}")'],
                capture_output=True,
                timeout=5,
                text=True
            )
            
            if result.returncode != 0:
                return False, f"Falha na compilação: {result.stderr[:200]}"
        
        finally:
            Path(tmp_path).unlink(missing_ok=True)
        
        # CAMADA 3: Tamanho razoável (não pode deletar 90% do código)
        arquivo_path = self.root / "core" / arquivo
        if arquivo_path.exists():
            linhas_originais = len(arquivo_path.read_text().split("\n"))
            linhas_patch = len(patch.split("\n"))
            
            if linhas_patch < linhas_originais * 0.5:
                return False, f"Patch muito curto: {linhas_patch} vs {linhas_originais} linhas"
        
        return True, "Patch válido"
    
    # ── Aplicação com Rollback ────────────────────────────────────────
    
    def aplicar_patch_seguro(self, patch: str, arquivo: str) -> Tuple[bool, str]:
        """
        Aplica patch com backup automático e rollback se quebrar.
        
        Returns:
            (sucesso: bool, mensagem: str)
        """
        arquivo_path = self.root / "core" / arquivo
        backup_path = arquivo_path.with_suffix(arquivo_path.suffix + ".backup")
        
        # 1. Backup
        if arquivo_path.exists():
            shutil.copy2(arquivo_path, backup_path)
            self._log("BACKUP", f"Backup criado: {backup_path}")
        
        try:
            # 2. Aplica patch
            arquivo_path.write_text(patch, encoding="utf-8")
            self._log("PATCH_APLICADO", f"Patch aplicado em {arquivo}")
            
            # 3. Testa funcionamento básico
            if not self._testar_funcionamento(arquivo):
                raise Exception("Teste de funcionamento falhou")
            
            # 4. Sucesso! Remove backup
            backup_path.unlink(missing_ok=True)
            return True, "Patch aplicado com sucesso"
        
        except Exception as e:
            # ROLLBACK: Restaura backup
            if backup_path.exists():
                shutil.copy2(backup_path, arquivo_path)
                backup_path.unlink()
                self._log("ROLLBACK", f"Patch revertido devido a: {e}")
            
            return False, f"Patch falhou e foi revertido: {e}"
    
    def _testar_funcionamento(self, arquivo: str) -> bool:
        """Testa se o arquivo patcheado ainda funciona."""
        if not arquivo.endswith(".py"):
            return True  # Não-Python, assume OK
        
        arquivo_path = self.root / "core" / arquivo
        
        # Testa import
        try:
            result = subprocess.run(
                [sys.executable, '-c', f'import sys; sys.path.insert(0, "{self.root}/core"); import {arquivo[:-3]}'],
                capture_output=True,
                timeout=10,
                text=True,
                cwd=str(self.root)
            )
            
            return result.returncode == 0
            
        except Exception:
            return False
    
    # ── Controle de Tentativas ───────────────────────────────────────
    
    def _carregar_tentativas(self) -> Dict:
        """Carrega histórico de tentativas de fix."""
        if self.tentativas_file.exists():
            return json.loads(self.tentativas_file.read_text())
        return {}
    
    def _salvar_tentativas(self):
        """Salva histórico de tentativas."""
        self.tentativas_file.parent.mkdir(exist_ok=True)
        self.tentativas_file.write_text(
            json.dumps(self.tentativas, indent=2),
            encoding="utf-8"
        )
    
    def pode_tentar_fix(self, bug_id: str) -> bool:
        """Verifica se ainda pode tentar corrigir o bug."""
        return self.tentativas.get(bug_id, 0) < self.MAX_TENTATIVAS
    
    def registrar_tentativa(self, bug_id: str, sucesso: bool):
        """Registra tentativa de correção."""
        if bug_id not in self.tentativas:
            self.tentativas[bug_id] = 0
        
        self.tentativas[bug_id] += 1
        self._salvar_tentativas()
        
        if not sucesso and self.tentativas[bug_id] >= self.MAX_TENTATIVAS:
            self._alertar_humano(bug_id)
    
    def _alertar_humano(self, bug_id: str):
        """Registra bug persistente para análise humana."""
        alerta = {
            "timestamp": datetime.now().isoformat(),
            "bug_id": bug_id,
            "tentativas": self.tentativas[bug_id],
            "status": "requer_intervencao_humana"
        }
        
        alerta_file = self.root / "memory" / "bugs_persistentes.json"
        alertas = []
        if alerta_file.exists():
            alertas = json.loads(alerta_file.read_text())
        
        alertas.append(alerta)
        alerta_file.write_text(json.dumps(alertas, indent=2))
        
        self._log("ALERTA_HUMANO", f"Bug {bug_id} não resolvido após {self.MAX_TENTATIVAS} tentativas")
    
    # ── Ciclo Completo ────────────────────────────────────────────────
    
    def ciclo_auto_refatoracao(self) -> Dict:
        """
        Executa ciclo completo de detecção → geração → validação → aplicação.
        
        Returns:
            Relatório do ciclo
        """
        relatorio = {
            "timestamp": datetime.now().isoformat(),
            "bugs_detectados": 0,
            "patches_gerados": 0,
            "patches_aplicados": 0,
            "patches_falharam": 0,
            "bugs_corrigidos": []
        }
        
        # 1. Detecta bugs
        bugs = self.detectar_bugs_recorrentes()
        relatorio["bugs_detectados"] = len(bugs)
        
        for bug in bugs:
            # Verifica limite de tentativas
            if not self.pode_tentar_fix(bug["id"]):
                self._log("LIMITE", f"Bug {bug['id']} atingiu limite de tentativas")
                continue
            
            # 2. Gera patch
            patch = self.gerar_patch_claude(bug)
            if not patch:
                self.registrar_tentativa(bug["id"], False)
                continue
            
            relatorio["patches_gerados"] += 1
            
            # 3. Valida patch
            valido, motivo = self.validar_patch(patch, bug["arquivo"])
            if not valido:
                self._log("VALIDACAO_FALHOU", f"{bug['id']}: {motivo}")
                self.registrar_tentativa(bug["id"], False)
                relatorio["patches_falharam"] += 1
                continue
            
            # 4. Aplica patch com rollback
            sucesso, msg = self.aplicar_patch_seguro(patch, bug["arquivo"])
            
            if sucesso:
                relatorio["patches_aplicados"] += 1
                relatorio["bugs_corrigidos"].append(bug["id"])
                self.registrar_tentativa(bug["id"], True)
                self._log("SUCESSO", f"Bug {bug['id']} corrigido!")
            else:
                relatorio["patches_falharam"] += 1
                self.registrar_tentativa(bug["id"], False)
                self._log("FALHA", f"{bug['id']}: {msg}")
        
        return relatorio
    
    def _log(self, tipo: str, msg: str):
        """Log de auto-refatoração."""
        linha = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {tipo}: {msg}\n"
        self.refactor_log.parent.mkdir(exist_ok=True)
        with open(self.refactor_log, "a", encoding="utf-8") as f:
            f.write(linha)
        print(linha.strip())
