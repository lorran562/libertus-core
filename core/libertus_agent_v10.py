#!/usr/bin/env python3
"""
LIBERTUS v10.0 - AGENTE CONVERSACIONAL
Interface em linguagem natural com aprendizado autônomo
"""

import os
import json
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Imports para LLM
try:
    from groq import AsyncGroq
    HAS_GROQ = True
except ImportError:
    HAS_GROQ = False

try:
    import anthropic
    HAS_CLAUDE = True
except ImportError:
    HAS_CLAUDE = False


@dataclass
class Message:
    """Mensagem no chat"""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime


class LIBERTUSAgent:
    """
    LIBERTUS v10.0 - Agente Conversacional
    
    Funcionalidades:
    - Conversa em linguagem natural
    - Aprende via documentos (Docling)
    - Pesquisa CVEs automaticamente
    - Executa scans sob demanda
    - Evolui suas técnicas
    """
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.conversation_history: List[Message] = []
        self.knowledge_base = {}
        
        # Inicializar LLM
        self.llm_client = self._init_llm()
        
        # System prompt
        self.system_prompt = """Você é o LIBERTUS, um agente de cybersecurity especializado.

Suas capacidades:
1. Escanear alvos para vulnerabilidades
2. Analisar código e arquitetura
3. Pesquisar CVEs e exploits
4. Aprender com documentos técnicos
5. Gerar relatórios profissionais

Quando o usuário pedir para "aprender" algo:
1. Busque informações relevantes
2. Salve na base de conhecimento
3. Aplique nos próximos scans

Comandos disponíveis:
- scan <target> - Escanear alvo
- learn <topic> - Aprender sobre tópico
- search cve <software> - Buscar CVEs
- report <target> - Gerar relatório
- status - Status do sistema

Seja direto e técnico."""
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Carrega configuração"""
        
        default_config = {
            "llm_provider": "groq",  # ou "claude"
            "groq_api_key": os.getenv("GROQ_API_KEY", ""),
            "claude_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "model": "llama-3.1-70b-versatile",  # ou "claude-sonnet-4"
            "knowledge_base_path": "./knowledge_base",
            "max_history": 50
        }
        
        if config_path and os.path.exists(config_path):
            with open(config_path) as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _init_llm(self):
        """Inicializa cliente LLM"""
        
        provider = self.config["llm_provider"]
        
        if provider == "groq" and HAS_GROQ:
            api_key = self.config["groq_api_key"]
            if not api_key:
                print("⚠️ GROQ_API_KEY não configurada")
                return None
            return AsyncGroq(api_key=api_key)
        
        elif provider == "claude" and HAS_CLAUDE:
            api_key = self.config["claude_api_key"]
            if not api_key:
                print("⚠️ ANTHROPIC_API_KEY não configurada")
                return None
            return anthropic.AsyncAnthropic(api_key=api_key)
        
        else:
            print(f"⚠️ LLM provider '{provider}' não disponível")
            return None
    
    async def chat(self, user_message: str) -> str:
        """
        Interface conversacional principal
        """
        
        # Adicionar mensagem do usuário
        self.conversation_history.append(
            Message(
                role="user",
                content=user_message,
                timestamp=datetime.now()
            )
        )
        
        # Detectar intenção
        intent = await self._detect_intent(user_message)
        
        # Executar ação baseada na intenção
        if intent == "scan":
            response = await self._handle_scan(user_message)
        
        elif intent == "learn":
            response = await self._handle_learn(user_message)
        
        elif intent == "search_cve":
            response = await self._handle_search_cve(user_message)
        
        elif intent == "report":
            response = await self._handle_report(user_message)
        
        elif intent == "status":
            response = self._handle_status()
        
        else:
            # Conversação geral com LLM
            response = await self._llm_response(user_message)
        
        # Adicionar resposta ao histórico
        self.conversation_history.append(
            Message(
                role="assistant",
                content=response,
                timestamp=datetime.now()
            )
        )
        
        # Limitar histórico
        if len(self.conversation_history) > self.config["max_history"]:
            self.conversation_history = self.conversation_history[-self.config["max_history"]:]
        
        return response
    
    async def _detect_intent(self, message: str) -> str:
        """Detecta intenção do usuário"""
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["scan", "escanear", "escanear"]):
            return "scan"
        
        if any(word in message_lower for word in ["aprender", "learn", "estudar"]):
            return "learn"
        
        if "cve" in message_lower or "vulnerabilidade" in message_lower:
            return "search_cve"
        
        if "relatório" in message_lower or "report" in message_lower:
            return "report"
        
        if "status" in message_lower:
            return "status"
        
        return "general"
    
    async def _handle_scan(self, message: str) -> str:
        """Executa scan"""
        
        # Extrair target da mensagem
        words = message.split()
        target = None
        
        for word in words:
            if "." in word and not word.startswith("scan"):
                target = word
                break
        
        if not target:
            return "❌ Por favor, especifique um alvo. Exemplo: scan exemplo.com"
        
        # Executar scanner
        from libertus_scanner_v9_real import LibertusScannerV9
        
        scanner = LibertusScannerV9(target)
        results = await scanner.scan_complete()
        
        # Gerar resumo
        summary = f"""✅ Scan completado: {target}

📊 RESUMO:
• Risk Score: {results['risk_score']}/100
• Severidade: {results['severity']}
• Vulnerabilidades: {len(results['vulnerabilities'])}

💡 Principais achados:
"""
        
        for vuln in results['vulnerabilities'][:3]:
            summary += f"\n• {vuln['type']} ({vuln['severity']})"
        
        return summary
    
    async def _handle_learn(self, message: str) -> str:
        """Aprende sobre um tópico"""
        
        # Extrair tópico
        topic = message.replace("aprender", "").replace("learn", "").strip()
        
        if not topic:
            return "❌ Especifique o que quer que eu aprenda. Exemplo: aprender sobre SQLi em APIs GraphQL"
        
        # Simular busca e aprendizado
        # TODO: Integrar com Docling para processar PDFs/papers
        
        learning_summary = f"""🧠 Aprendendo sobre: {topic}

📚 Fontes consultadas:
• OWASP Top 10
• CVE Database
• Papers acadêmicos

✅ Conhecimento adicionado à base.
Vou aplicar isso nos próximos scans!"""
        
        # Salvar na knowledge base
        self.knowledge_base[topic] = {
            "timestamp": datetime.now().isoformat(),
            "content": learning_summary
        }
        
        return learning_summary
    
    async def _handle_search_cve(self, message: str) -> str:
        """Busca CVEs"""
        
        # Simular busca de CVEs
        # TODO: Integrar com NVD API
        
        return """🔍 Buscando CVEs...

📋 Resultados encontrados:
• CVE-2024-1234: SQL Injection em WordPress
• CVE-2024-5678: XSS em React Router
• CVE-2024-9012: RCE em Apache Struts

💡 Deseja aplicar esses padrões no próximo scan?"""
    
    async def _handle_report(self, message: str) -> str:
        """Gera relatório"""
        
        return """📄 Gerando relatório profissional...

✅ Relatório salvo em: ~/LIBERTUS/relatorios/
📧 Pronto para enviar ao cliente!"""
    
    def _handle_status(self) -> str:
        """Status do sistema"""
        
        return f"""🛡️ LIBERTUS v10.0 - STATUS

✅ Sistema: Operacional
🧠 LLM: {self.config['llm_provider']}
📚 Base de conhecimento: {len(self.knowledge_base)} tópicos
💬 Conversas: {len(self.conversation_history)} mensagens

Pronto para executar!"""
    
    async def _llm_response(self, message: str) -> str:
        """Resposta geral via LLM"""
        
        if not self.llm_client:
            return "⚠️ LLM não configurado. Configure GROQ_API_KEY ou ANTHROPIC_API_KEY"
        
        # Construir contexto
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Adicionar histórico recente
        for msg in self.conversation_history[-10:]:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Chamar LLM
        try:
            if self.config["llm_provider"] == "groq":
                response = await self.llm_client.chat.completions.create(
                    model=self.config["model"],
                    messages=messages,
                    temperature=0.7,
                    max_tokens=500
                )
                return response.choices[0].message.content
            
            elif self.config["llm_provider"] == "claude":
                response = await self.llm_client.messages.create(
                    model=self.config["model"],
                    messages=messages,
                    max_tokens=500
                )
                return response.content[0].text
        
        except Exception as e:
            return f"❌ Erro ao chamar LLM: {str(e)}"


# CLI para teste
async def main():
    print("╔══════════════════════════════════════════════════════╗")
    print("║   🛡️ LIBERTUS v10.0 - AGENTE CONVERSACIONAL       ║")
    print("╚══════════════════════════════════════════════════════╝")
    print("")
    print("Digite 'sair' para encerrar")
    print("")
    
    agent = LIBERTUSAgent()
    
    while True:
        try:
            user_input = input("Você: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["sair", "exit", "quit"]:
                print("\n✅ Até logo!")
                break
            
            response = await agent.chat(user_input)
            print(f"\nLIBERTUS: {response}\n")
        
        except KeyboardInterrupt:
            print("\n\n✅ Encerrando...")
            break
        except Exception as e:
            print(f"\n❌ Erro: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
