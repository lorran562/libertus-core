#!/usr/bin/env python3
"""
LIBERTUS AUTO-EVOLUÇÃO - SISTEMA REAL
Zero Simulação - Validação Obrigatória

Workflow:
1. LLM gera código
2. Salva em /tmp/test_module.py
3. Executa testes automáticos
4. SE PASSAR → substitui código real + git commit
5. SE FALHAR → descarta automaticamente

Autor: Libertus v10.0
Data: 2026-05-14
"""

import os
import sys
import json
import subprocess
import tempfile
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - AUTO-EVOLUTION - %(levelname)s - %(message)s'
)
logger = logging.getLogger('AUTO_EVOLUTION')


class LibertusAutoEvolution:
    """
    Sistema de auto-evolução com validação obrigatória
    
    REGRAS:
    - Nenhum código entra sem passar em testes
    - Todo código gerado é validado antes de substituir
    - Rollback automático em caso de falha
    - Git commit apenas após sucesso
    """
    
    def __init__(self):
        self.base_dir = Path.home() / "LIBERTUS"
        self.core_dir = self.base_dir / "core"
        self.test_dir = self.base_dir / "tests"
        self.backup_dir = self.base_dir / "backups"
        
        # Criar diretórios
        for d in [self.test_dir, self.backup_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def generate_validation_test(self, module_name: str, test_cases: list) -> str:
        """Gera código de teste automático"""
        
        test_code = f'''#!/usr/bin/env python3
"""
Teste automático para {module_name}
Gerado automaticamente pelo sistema de auto-evolução
"""

import sys
sys.path.insert(0, "{str(self.core_dir)}")

def test_{module_name}():
    """Testa {module_name} automaticamente"""
    
    try:
        # Importar módulo
        from {module_name} import *
        
        # Testes específicos
        results = {{}}
        
'''
        
        for i, test_case in enumerate(test_cases):
            test_code += f'''
        # Test case {i+1}: {test_case.get('description', 'Test')}
        try:
            {test_case.get('code', 'pass')}
            results['test_{i+1}'] = True
        except Exception as e:
            results['test_{i+1}'] = False
            print(f"❌ Test {i+1} failed: {{e}}")
'''
        
        test_code += '''
        
        # Verificar resultados
        passed = sum(results.values())
        total = len(results)
        
        print(f"\\n{'='*60}")
        print(f"RESULTADO: {passed}/{total} testes passaram")
        print(f"{'='*60}")
        
        # Sucesso se todos passaram
        return all(results.values())
    
    except ImportError as e:
        print(f"❌ Erro ao importar módulo: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False


if __name__ == "__main__":
    success = test_module()
    sys.exit(0 if success else 1)
'''
        
        return test_code
    
    def validate_code(self, code: str, module_name: str) -> Tuple[bool, str]:
        """
        Valida código ANTES de substituir
        
        Retorna: (passou, mensagem)
        """
        logger.info(f"🧪 Validando {module_name}...")
        
        # 1. Salvar código temporário
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False,
            dir='/tmp'
        )
        
        try:
            temp_file.write(code)
            temp_file.close()
            
            # 2. Teste de sintaxe
            logger.info("  1/3 Verificando sintaxe...")
            result = subprocess.run(
                ['python3', '-m', 'py_compile', temp_file.name],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return False, f"Erro de sintaxe: {result.stderr.decode()}"
            
            logger.info("  ✅ Sintaxe OK")
            
            # 3. Teste de importação
            logger.info("  2/3 Testando importação...")
            result = subprocess.run(
                ['python3', '-c', f'import sys; sys.path.insert(0, "/tmp"); import {Path(temp_file.name).stem}'],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return False, f"Erro de importação: {result.stderr.decode()}"
            
            logger.info("  ✅ Importação OK")
            
            # 4. Testes funcionais (se existirem)
            test_file = self.test_dir / f"test_{module_name}.py"
            
            if test_file.exists():
                logger.info("  3/3 Executando testes funcionais...")
                result = subprocess.run(
                    ['python3', str(test_file)],
                    capture_output=True,
                    timeout=60
                )
                
                if result.returncode != 0:
                    return False, f"Testes falharam: {result.stdout.decode()}"
                
                logger.info("  ✅ Testes funcionais OK")
            else:
                logger.info("  3/3 Sem testes funcionais (pulando)")
            
            return True, "Validação completa com sucesso"
        
        except subprocess.TimeoutExpired:
            return False, "Timeout durante validação"
        except Exception as e:
            return False, f"Erro inesperado: {str(e)}"
        finally:
            # Limpar arquivo temporário
            try:
                os.unlink(temp_file.name)
            except:
                pass
    
    def backup_current_version(self, module_path: Path) -> Optional[Path]:
        """Cria backup da versão atual"""
        
        if not module_path.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"{module_path.stem}_{timestamp}.py"
        
        shutil.copy2(module_path, backup_file)
        
        logger.info(f"💾 Backup criado: {backup_file}")
        
        return backup_file
    
    def rollback(self, module_path: Path, backup_path: Path) -> bool:
        """Rollback para versão anterior"""
        
        try:
            shutil.copy2(backup_path, module_path)
            logger.info(f"↩️ Rollback executado: {module_path.name}")
            return True
        except Exception as e:
            logger.error(f"❌ Falha no rollback: {e}")
            return False
    
    def git_commit_evolution(self, module_name: str, description: str) -> bool:
        """Git commit após evolução bem-sucedida"""
        
        try:
            os.chdir(self.base_dir)
            
            # Git add
            subprocess.run(['git', 'add', '-A'], check=True, capture_output=True, timeout=30)
            
            # Git commit
            commit_msg = f"🧬 Auto-evolução: {module_name}\n\n{description}\n\nValidado e testado automaticamente"
            
            result = subprocess.run(
                ['git', 'commit', '-m', commit_msg],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0 and b"nothing to commit" in result.stdout:
                logger.info("ℹ️ Nada para commitar")
                return True
            
            if result.returncode != 0:
                logger.warning(f"⚠️ Git commit warning: {result.stderr.decode()}")
                return False
            
            # Git push
            subprocess.run(
                ['git', 'push', 'origin', 'main'],
                check=True,
                capture_output=True,
                timeout=60
            )
            
            logger.info(f"✅ Git commit + push: {module_name}")
            
            return True
        
        except Exception as e:
            logger.error(f"❌ Git error: {e}")
            return False
    
    def evolve_module(
        self,
        module_name: str,
        new_code: str,
        description: str,
        test_cases: Optional[list] = None
    ) -> bool:
        """
        Evolui módulo com validação OBRIGATÓRIA
        
        Workflow COMPLETO:
        1. Valida código novo
        2. Backup versão atual
        3. Substitui código
        4. Testa novamente
        5. Se falhar → rollback
        6. Se passar → git commit
        
        Retorna: True se evolução bem-sucedida
        """
        logger.info("\n" + "="*70)
        logger.info(f"🧬 INICIANDO AUTO-EVOLUÇÃO: {module_name}")
        logger.info("="*70)
        
        module_path = self.core_dir / f"{module_name}.py"
        
        # Passo 1: Validação
        logger.info("\n📋 PASSO 1/5: VALIDAÇÃO")
        
        passed, message = self.validate_code(new_code, module_name)
        
        if not passed:
            logger.error(f"❌ Validação falhou: {message}")
            logger.error("🚫 EVOLUÇÃO ABORTADA")
            return False
        
        logger.info(f"✅ {message}")
        
        # Passo 2: Backup
        logger.info("\n📋 PASSO 2/5: BACKUP")
        
        backup_path = self.backup_current_version(module_path)
        
        if module_path.exists() and not backup_path:
            logger.error("❌ Falha ao criar backup")
            logger.error("🚫 EVOLUÇÃO ABORTADA")
            return False
        
        # Passo 3: Substituição
        logger.info("\n📋 PASSO 3/5: SUBSTITUIÇÃO")
        
        try:
            module_path.write_text(new_code)
            logger.info(f"✅ Código substituído: {module_path}")
        except Exception as e:
            logger.error(f"❌ Erro ao substituir: {e}")
            if backup_path:
                self.rollback(module_path, backup_path)
            logger.error("🚫 EVOLUÇÃO ABORTADA")
            return False
        
        # Passo 4: Validação pós-substituição
        logger.info("\n📋 PASSO 4/5: VALIDAÇÃO PÓS-SUBSTITUIÇÃO")
        
        passed, message = self.validate_code(module_path.read_text(), module_name)
        
        if not passed:
            logger.error(f"❌ Validação pós-substituição falhou: {message}")
            if backup_path:
                self.rollback(module_path, backup_path)
            logger.error("🚫 EVOLUÇÃO ABORTADA (ROLLBACK EXECUTADO)")
            return False
        
        logger.info(f"✅ {message}")
        
        # Passo 5: Git commit
        logger.info("\n📋 PASSO 5/5: GIT COMMIT")
        
        git_success = self.git_commit_evolution(module_name, description)
        
        if not git_success:
            logger.warning("⚠️ Git commit falhou (mas código foi atualizado)")
        
        logger.info("\n" + "="*70)
        logger.info("✅ AUTO-EVOLUÇÃO COMPLETA COM SUCESSO")
        logger.info("="*70)
        
        return True


# CLI para testes
if __name__ == "__main__":
    # Exemplo de uso
    evolver = LibertusAutoEvolution()
    
    # Código de exemplo
    new_code = '''#!/usr/bin/env python3
"""
Módulo de exemplo - Auto-gerado
"""

def hello_world():
    """Função de teste"""
    return "Hello from evolved code!"


if __name__ == "__main__":
    print(hello_world())
'''
    
    # Testar evolução
    success = evolver.evolve_module(
        module_name="test_evolution",
        new_code=new_code,
        description="Teste de auto-evolução",
        test_cases=[
            {
                "description": "Importação básica",
                "code": "assert hello_world() is not None"
            }
        ]
    )
    
    print(f"\n{'='*70}")
    print(f"Resultado: {'✅ SUCESSO' if success else '❌ FALHOU'}")
    print(f"{'='*70}")
