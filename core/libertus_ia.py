#!/usr/bin/env python3
"""
LIBERTUS IA - Cliente Groq
Responde perguntas usando conhecimento do RAG
"""

import os
from typing import List, Dict, Any
from groq import Groq

class LibertusIA:
    """Cliente inteligente com Groq API"""
    
    def __init__(self, api_key: str = None):
        """
        Inicializa cliente Groq
        
        Args:
            api_key: Chave API Groq (ou usa variável de ambiente)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        
        if not self.api_key:
            raise ValueError("❌ GROQ_API_KEY não configurada")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "llama-3.3-70b-versatile"  # Modelo rápido e poderoso
        
        print(f"✅ IA inicializada: {self.model}")
    
    def responder_com_contexto(
        self, 
        pergunta: str, 
        contexto: List[Dict[str, Any]] = None,
        area: str = "geral"
    ) -> str:
        """
        Responde pergunta usando contexto do RAG
        
        Args:
            pergunta: Pergunta do usuário
            contexto: Documentos relevantes do RAG
            area: Área de conhecimento (pentest, medicina, etc)
            
        Returns:
            Resposta da IA
        """
        # Construir prompt com contexto
        system_prompt = self._build_system_prompt(area)
        user_prompt = self._build_user_prompt(pergunta, contexto)
        
        try:
            # Chamar Groq
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=2048
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            return f"❌ Erro ao gerar resposta: {e}"
    
    def _build_system_prompt(self, area: str) -> str:
        """Constrói prompt do sistema baseado na área"""
        
        base = """Você é LIBERTUS, uma IA especializada que responde perguntas baseado em conhecimento técnico absorvido de documentos.

REGRAS:
1. Responda APENAS baseado no contexto fornecido
2. Se não souber, diga "não encontrei essa informação nos documentos"
3. Seja técnico, preciso e direto
4. Cite fontes quando relevante
5. Para pentest: foque em segurança e vulnerabilidades
6. Para medicina: seja cuidadoso e cite estudos
7. Para outras áreas: adapte ao contexto"""
        
        area_prompts = {
            "pentest": "\n\nESPECIALIZAÇÃO: Segurança da informação, hacking ético, vulnerabilidades web",
            "medicina": "\n\nESPECIALIZAÇÃO: Medicina, farmacologia, diagnósticos. SEMPRE indique: 'consulte um profissional'",
            "advocacia": "\n\nESPECIALIZAÇÃO: Direito brasileiro, leis, jurisprudência",
            "robotica": "\n\nESPECIALIZAÇÃO: Robótica, mecânica, eletrônica, programação de sistemas embarcados"
        }
        
        return base + area_prompts.get(area, "")
    
    def _build_user_prompt(self, pergunta: str, contexto: List[Dict[str, Any]]) -> str:
        """Constrói prompt do usuário com contexto"""
        
        if not contexto:
            return f"PERGUNTA: {pergunta}\n\nCONTEXTO: Nenhum documento relevante encontrado."
        
        # Formatar contexto
        contexto_formatado = "\n\n".join([
            f"DOCUMENTO {i+1} (fonte: {doc.get('metadata', {}).get('source', 'desconhecida')}):\n{doc['texto']}"
            for i, doc in enumerate(contexto[:5])  # Limite 5 documentos
        ])
        
        return f"""CONTEXTO DOS DOCUMENTOS:
{contexto_formatado}

PERGUNTA DO USUÁRIO:
{pergunta}

Responda baseado APENAS no contexto acima."""
    
    def analisar_e_criar(
        self,
        objetivo: str,
        contexto: List[Dict[str, Any]],
        area: str = "geral"
    ) -> str:
        """
        Analisa conhecimento e CRIA algo novo
        
        Args:
            objetivo: O que criar (fórmula, exploit, projeto, etc)
            contexto: Documentos relevantes
            area: Área de conhecimento
            
        Returns:
            Proposta de criação
        """
        system_prompt = f"""Você é LIBERTUS, uma IA que ANALISA conhecimento técnico e PROPÕE inovações.

MISSÃO: Combinar conhecimentos dos documentos para criar algo novo e útil.

PROCESSO:
1. Analisar padrões nos documentos
2. Identificar gaps e oportunidades
3. Combinar conhecimentos de forma inovadora
4. Propor solução detalhada e técnica

ÁREA: {area}

IMPORTANTE:
- Seja técnico e específico
- Explique o raciocínio
- Indique testes/validações necessárias
- Cite fontes dos documentos"""

        user_prompt = f"""DOCUMENTOS DISPONÍVEIS:
{self._format_context_for_creation(contexto)}

OBJETIVO:
{objetivo}

TAREFA:
Analise os documentos, combine conhecimentos e CRIE uma proposta detalhada e inovadora."""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.8,  # Mais criativo
                max_tokens=4096   # Resposta mais longa
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            return f"❌ Erro ao criar: {e}"
    
    def _format_context_for_creation(self, contexto: List[Dict[str, Any]]) -> str:
        """Formata contexto para criação"""
        return "\n\n".join([
            f"DOC {i+1} [{doc.get('metadata', {}).get('source', '?')}]:\n{doc['texto']}"
            for i, doc in enumerate(contexto[:10])  # Mais documentos para criação
        ])


# Teste rápido
if __name__ == "__main__":
    # Requer GROQ_API_KEY
    if os.getenv("GROQ_API_KEY"):
        ia = LibertusIA()
        
        # Teste simples
        contexto_teste = [{
            'texto': 'SQL Injection permite injetar comandos SQL maliciosos em aplicações web vulneráveis.',
            'metadata': {'source': 'owasp.pdf'}
        }]
        
        resposta = ia.responder_com_contexto(
            "Como funciona SQL injection?",
            contexto_teste,
            area="pentest"
        )
        
        print(f"\n🤖 Resposta:\n{resposta}")
    else:
        print("⚠️ Configure GROQ_API_KEY para testar")
