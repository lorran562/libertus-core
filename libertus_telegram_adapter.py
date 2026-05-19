#!/usr/bin/env python3
"""
LIBERTUS TELEGRAM ADAPTER
Adaptador REAL que conecta Telegram Bot ao cérebro completo LIBERTUS VPS
"""

import os
import sys

# ⚠️ CRÍTICO: CONFIGURAR ANTES DE QUALQUER IMPORT!
# Forçar API keys NO AMBIENTE antes de importar libertus
os.environ["GROQ_API_KEY"] = "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"
os.environ["SUPABASE_URL"] = "https://jkgrmlfqgprcwfooovkx.supabase.co"
os.environ["SUPABASE_KEY"] = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImprZ3JtbGZxZ3ByY3dmb29vdmt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMyNTY4NTIsImV4cCI6MjA4ODgzMjg1Mn0.f0N9ase2ZoYKq4JL7zVT9rzrjjsslYMPLcwd-k5Z8DA"

# Paths DEPOIS — relativo ao arquivo, funciona em /root ou /home/libertus
from pathlib import Path
LIBERTUS_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(LIBERTUS_ROOT / "core"))
sys.path.insert(0, str(LIBERTUS_ROOT))

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
            
            # Converter para string se for lista
            if isinstance(resposta, list):
                resposta = "\n".join(str(item) for item in resposta)
            elif resposta is None:
                resposta = "Processado, mas sem resposta gerada."
            else:
                resposta = str(resposta)
            
            return resposta
            
        except Exception as e:
            import traceback
            traceback.print_exc()
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
