import asyncio
import sys
sys.path.insert(0, '/root/LIBERTUS/core')

from ai_router import AIRouter
from logic_engine import TaskType

async def test_router():
    print("🧪 Testando AI Router...")
    
    router = AIRouter()
    
    # Teste 1: Logic Only (risk calculation)
    print("\n1️⃣ Teste Logic Engine (Risk Calculation):")
    result = await router.execute(
        TaskType.RISK_CALCULATION,
        {
            'vulnerabilities': [
                {'severity': 'MEDIUM'},
                {'severity': 'MEDIUM'},
                {'severity': 'LOW'},
            ]
        }
    )
    print(f"   Risk Score: {result['risk_score']}/100")
    print(f"   Classification: {result['classification']}")
    
    # Teste 2: Decision Making
    print("\n2️⃣ Teste Logic Engine (Decision Making):")
    decision = await router.execute(
        TaskType.DECISION_MAKING,
        {
            'targets': [
                {'url': 'site1.com', 'priority': 4, 'scan_count': 5, 'vulnerabilities_found': 0},
                {'url': 'site2.com', 'priority': 1, 'scan_count': 0, 'vulnerabilities_found': 0},  # Nunca testado = CRITICAL
                {'url': 'site3.com', 'priority': 2, 'scan_count': 3, 'vulnerabilities_found': 10},
            ]
        }
    )
    print(f"   Próximo target: {decision}")
    
    # Teste 3: RAG (se ChromaDB funcionar)
    print("\n3️⃣ Teste RAG Engine:")
    try:
        knowledge = await router.rag_engine.retrieve("SQL Injection", top_k=1)
        print(f"   Status RAG: ✅ Funcionando")
        print(f"   Tamanho do contexto: {len(knowledge)} caracteres")
    except Exception as e:
        print(f"   Status RAG: ⚠️ {e}")
    
    # Teste 4: LLM Manager (Groq)
    print("\n4️⃣ Teste LLM Manager (Groq):")
    try:
        response = await router.llm_manager.generate(
            provider='groq',
            prompt="Responda com apenas 'OK' se você está funcionando.",
            max_tokens=50
        )
        print(f"   Status Groq: ✅ {response.strip()[:50]}")
    except Exception as e:
        print(f"   Status Groq: ❌ {e}")
    
    # Teste 5: Ollama (se estiver rodando)
    print("\n5️⃣ Teste Ollama Local:")
    try:
        if await router.llm_manager._check_ollama_running():
            response = await router.llm_manager.generate(
                provider='ollama',
                prompt="Responda apenas: OK",
                max_tokens=10
            )
            print(f"   Status Ollama: ✅ {response.strip()[:50]}")
        else:
            print(f"   Status Ollama: ⚠️ Não está rodando (execute: ollama serve)")
    except Exception as e:
        print(f"   Status Ollama: ❌ {e}")
    
    print("\n✅ Testes completos!")

if __name__ == "__main__":
    asyncio.run(test_router())
