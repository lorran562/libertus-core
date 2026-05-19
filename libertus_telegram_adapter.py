#!/usr/bin/env python3
"""
LIBERTUS TELEGRAM ADAPTER
Adaptador REAL que conecta Telegram Bot ao cérebro completo LIBERTUS VPS
"""

import os
import sys
from pathlib import Path

# Configurar paths
LIBERTUS_ROOT = Path("/root/LIBERTUS")
sys.path.insert(0, str(LIBERTUS_ROOT / "core"))
sys.path.insert(0, str(LIBERTUS_ROOT))

# Configurar variáveis de ambiente necessárias
os.environ.setdefault("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
os.environ.setdefault("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY", ""))

class LibertusTelegramAdapter:
    """
    Adaptador que conecta Telegram Bot ao Libertus VPS completo
    """
    
    def __init__(self):
        """Inicializa conexão com LIBERTUS VPS"""
        self.libertus = None
        self._inicializar()
    
    def _inicializar(self):
        """Inicializa cérebro LIBERTUS"""
        try:
            # Importar Orquestrador (cérebro completo)
            from libertus import Orquestrador
            
            # Criar instância
            self.libertus = Orquestrador()
            
            print("✅ LIBERTUS VPS Cérebro inicializado com sucesso!")
            print(f"   - MemoriaViva: {'OK' if self.libertus.mv else 'OFF'}")
            print(f"   - LivroErros: {'OK' if self.libertus.le else 'OFF'}")
            print(f"   - AutoCuriosidade: {'OK' if self.libertus.ac else 'OFF'}")
            print(f"   - IdentidadeCognitiva: {'OK' if self.libertus.ic else 'OFF'}")
            print(f"   - Scanner: {'OK' if self.libertus.scanner else 'OFF'}")
            print(f"   - Groq: {'OK' if self.libertus.groq else 'OFF'}")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar LIBERTUS VPS: {e}")
            self.libertus = None
            raise
    
    def processar(self, mensagem: str) -> str:
        """
        Processa mensagem através do cérebro completo LIBERTUS
        
        Args:
            mensagem: Mensagem do usuário
            
        Returns:
            Resposta processada pelo LIBERTUS completo
        """
        if not self.libertus:
            return "❌ Cérebro LIBERTUS não inicializado"
        
        try:
            # Processar através do cérebro completo
            resposta = self.libertus.processar(mensagem)
            
            return resposta if resposta else "Processado, mas sem resposta gerada."
            
        except Exception as e:
            return f"❌ Erro ao processar: {e}"
    
    def esta_disponivel(self) -> bool:
        """Verifica se LIBERTUS está disponível"""
        return self.libertus is not None
    
    def get_stats(self) -> dict:
        """Retorna estatísticas do sistema"""
        if not self.libertus:
            return {}
        
        return {
            'memoria_viva': self.libertus.mv is not None,
            'livro_erros': self.libertus.le is not None,
            'auto_curiosidade': self.libertus.ac is not None,
            'identidade_cognitiva': self.libertus.ic is not None,
            'scanner': self.libertus.scanner is not None,
            'groq': self.libertus.groq is not None,
            'claude': self.libertus.claude is not None,
            'stats': getattr(self.libertus, '_stats', {})
        }


# Singleton global
_adapter = None

def get_libertus_adapter():
    """Retorna instância singleton do adaptador"""
    global _adapter
    if _adapter is None:
        _adapter = LibertusTelegramAdapter()
    return _adapter
