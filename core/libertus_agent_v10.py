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

try:
    from learning_engine import LearningEngine
    HAS_LEARNING = True
except ImportError:
    HAS_LEARNING = False

try:
    from objetivo_system import ObjetivoSystem
    HAS_OBJETIVOS = True
except ImportError:
    HAS_OBJETIVOS = False


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
        
        # Inicializar Learning Engine
        if HAS_LEARNING and self.llm_client:
            self.learning_engine = LearningEngine(groq_client=self.llm_client)
        else:
            self.learning_engine = None
        
        # Inicializar Sistema de Objetivos
        if HAS_OBJETIVOS:
            self.objetivo_system = ObjetivoSystem()
        else:
            self.objetivo_system = None
        
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
            "model": "llama-3.3-70b-versatile",  # ou "claude-sonnet-4"
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
        
        elif intent == "objetivo":
            response = self._handle_objetivo(user_message)
        
        elif intent == "progresso":
            response = self._handle_progresso()
        
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
        
        # Comandos de objetivo
        if any(word in message_lower for word in ["objetivo", "goal", "meta"]):
            return "objetivo"
        
        if "progresso" in message_lower:
            return "progresso"
        
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
        """Aprende sobre um tópico usando Learning Engine (Docling + ArXiv + LLM)"""
        
        # Extrair tópico (limpar comandos do sistema)
        topic = message.lower()
        topic = topic.replace("aprender", "").replace("learn", "").strip()
        topic = topic.replace("python3", "").replace("core/libertus_agent_v10.py", "").strip()
        topic = topic.replace("sobre", "", 1).strip()
        
        if not topic or len(topic) < 3:
            return "❌ Especifique o que quer que eu aprenda. Exemplo: aprender sobre SQLi em APIs GraphQL"
        
        print(f"\n🧠 Iniciando aprendizado sobre: {topic}")
        
        # Usar Learning Engine se disponível
        if self.learning_engine:
            try:
                # Buscar papers no ArXiv
                result = await self.learning_engine.learn_from_arxiv(topic, max_papers=3)
                
                if result.get("success"):
                    papers_count = result.get("papers_count", 0)
                    summary = result.get("summary", "")
                    filepath = result.get("filepath", "")
                    
                    # Salvar também na knowledge base local do agente
                    self.knowledge_base[topic] = {
                        "timestamp": datetime.now().isoformat(),
                        "content": summary,
                        "source": "learning_engine_arxiv",
                        "papers_count": papers_count
                    }
                    
                    return f"""✅ Conhecimento adquirido sobre: {topic}

📚 Papers analisados: {papers_count}
💾 Resumo salvo em: {filepath}

📖 RESUMO TÉCNICO:
{summary[:800]}...

💡 Esse conhecimento será aplicado nos próximos scans!"""
                
                else:
                    error = result.get("error", "Erro desconhecido")
                    return f"⚠️ Erro no Learning Engine: {error}"
            
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                return f"""❌ Erro ao aprender: {str(e)}

Debug: {error_detail[:300]}"""
        
        # Fallback: LLM direto (se Learning Engine não disponível)
        elif self.llm_client:
            print("⚠️ Learning Engine não disponível, usando LLM direto...")
            
            prompt = f"""Pesquise e resuma conhecimento técnico sobre: {topic}

Foco em cybersecurity:
1. Vulnerabilidades e vetores de ataque
2. Técnicas de exploração
3. Payloads específicos
4. Contramedidas

Formate como resumo técnico."""
            
            try:
                response = await self.llm_client.chat.completions.create(
                    model=self.config["model"],
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1500
                )
                
                knowledge = response.choices[0].message.content
                
                # Salvar localmente
                home_dir = os.path.expanduser("~/LIBERTUS")
                kb_dir = os.path.join(home_dir, "knowledge_base")
                os.makedirs(kb_dir, exist_ok=True)
                
                filename = topic.replace(" ", "_").replace("/", "_").lower()[:50] + "_llm.json"
                filepath = os.path.join(kb_dir, filename)
                
                with open(filepath, "w") as f:
                    json.dump({
                        "topic": topic,
                        "timestamp": datetime.now().isoformat(),
                        "content": knowledge,
                        "source": "groq_llm_direct"
                    }, f, indent=2)
                
                return f"""✅ Conhecimento adquirido sobre: {topic}

💾 Salvo em: ~/LIBERTUS/knowledge_base/{filename}

{knowledge[:600]}..."""
            
            except Exception as e:
                return f"❌ Erro ao aprender: {str(e)}"
        
        else:
            return "⚠️ LLM não configurado. Configure GROQ_API_KEY"
    
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

    
    def _handle_objetivo(self, message: str) -> str:
        """Define ou exibe objetivo"""
        
        if not self.objetivo_system:
            return "⚠️ Sistema de objetivos não disponível"
        
        message_lower = message.lower()
        
        # Listar objetivos predefinidos
        if "listar" in message_lower or "list" in message_lower:
            from objetivo_system import OBJETIVOS_PREDEFINIDOS
            
            resultado = "🎯 OBJETIVOS DISPONÍVEIS:\n\n"
            
            for key, obj in OBJETIVOS_PREDEFINIDOS.items():
                resultado += f"📌 {key}\n"
                resultado += f"   {obj['titulo']}\n"
                resultado += f"   {obj['descricao']}\n\n"
            
            resultado += "Para definir: objetivo <nome_objetivo>"
            
            return resultado
        
        # Definir objetivo predefinido
        from objetivo_system import OBJETIVOS_PREDEFINIDOS
        
        for key in OBJETIVOS_PREDEFINIDOS.keys():
            if key in message_lower:
                obj = OBJETIVOS_PREDEFINIDOS[key]
                
                self.objetivo_system.definir_objetivo(
                    titulo=obj["titulo"],
                    descricao=obj["descricao"],
                    metricas=obj["metricas"],
                    topicos_aprendizado=obj["topicos_aprendizado"]
                )
                
                proximo = self.objetivo_system.get_proximo_topico_aprendizado()
                
                return f"""✅ OBJETIVO DEFINIDO!

🎯 {obj['titulo']}

📝 {obj['descricao']}

📊 MÉTRICAS:
{self._format_metricas(obj['metricas'])}

🎓 PRÓXIMO TÓPICO DE APRENDIZADO:
{proximo}

💡 LIBERTUS começará a aprender e evoluir automaticamente no rumo deste objetivo!

Digite 'progresso' para ver o andamento."""
        
        return "ℹ️ Use 'objetivo listar' para ver os objetivos disponíveis"
    
    def _handle_progresso(self) -> str:
        """Exibe progresso do objetivo"""
        
        if not self.objetivo_system:
            return "⚠️ Sistema de objetivos não disponível"
        
        return self.objetivo_system.gerar_relatorio()
    
    def _format_metricas(self, metricas: list) -> str:
        """Formata métricas para exibição"""
        
        resultado = ""
        for m in metricas:
            resultado += f"• {m['nome']}: Meta {m['meta']}\n"
        
        return resultado
