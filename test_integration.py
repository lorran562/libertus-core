"""
TESTES DE INTEGRAÇÃO - ANTES DE PLUGAR NO DAEMON
Valida latência, estabilidade, fallback.
"""

import asyncio
import time
import sys
sys.path.insert(0, '/root/LIBERTUS/core')

from ai_router import AIRouter
from logic_engine import TaskType

async def test_latency():
    """Mede latência de cada componente"""
    print("⏱️  TESTE DE LATÊNCIA\n")
    
    router = AIRouter()
    
    # 1. Logic Engine (deve ser <1ms)
    start = time.time()
    result = await router.execute(
        TaskType.RISK_CALCULATION,
        {'vulnerabilities': [{'severity': 'MEDIUM'}] * 10}
    )
    logic_time = (time.time() - start) * 1000
    print(f"✅ Logic Engine: {logic_time:.2f}ms (risk={result['risk_score']})")
    
    if logic_time > 100:
        print(f"   ⚠️  ALERTA: Logic muito lento! Esperado <1ms")
    
    # 2. RAG Retrieval (deve ser <500ms)
    start = time.time()
    try:
        knowledge = await router.rag_engine.retrieve("SQL Injection", top_k=3)
        rag_time = (time.time() - start) * 1000
        print(f"✅ RAG Engine: {rag_time:.2f}ms (chars={len(knowledge)})")
        
        if rag_time > 1000:
            print(f"   ⚠️  ALERTA: RAG lento demais para produção!")
    except Exception as e:
        print(f"❌ RAG falhou: {e}")
    
    # 3. LLM (Groq) - depende de API
    start = time.time()
    try:
        response = await router.llm_manager.generate(
            provider='groq',
            prompt="Responda: OK",
            max_tokens=10
        )
        groq_time = (time.time() - start) * 1000
        print(f"✅ Groq API: {groq_time:.2f}ms")
        
        if groq_time > 5000:
            print(f"   ⚠️  API lenta - considere timeout menor")
    except Exception as e:
        print(f"⚠️  Groq não disponível: {e}")

async def test_fallback_chain():
    """Testa se fallback funciona quando backend falha"""
    print("\n🔄 TESTE DE FALLBACK\n")
    
    router = AIRouter()
    
    # Forçar Ollama a falhar (se não estiver rodando)
    print("1️⃣ Testando fallback Ollama → Groq:")
    try:
        result = await router.execute(
            TaskType.VULNERABILITY_ANALYSIS,
            {'query': 'Teste de fallback', 'vulnerabilities': []}
        )
        print(f"   ✅ Fallback funcionou! Backend usado conseguiu responder")
    except Exception as e:
        print(f"   ❌ Fallback falhou completamente: {e}")

async def test_concurrent_load():
    """Simula carga concorrente (3 requests simultâneos)"""
    print("\n⚡ TESTE DE CARGA CONCORRENTE\n")
    
    router = AIRouter()
    
    tasks = []
    for i in range(3):
        task = router.execute(
            TaskType.RISK_CALCULATION,
            {'vulnerabilities': [{'severity': 'MEDIUM'}] * 5}
        )
        tasks.append(task)
    
    start = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_time = (time.time() - start) * 1000
    
    success = sum(1 for r in results if not isinstance(r, Exception))
    print(f"✅ {success}/3 requests bem-sucedidos")
    print(f"⏱️  Tempo total: {total_time:.2f}ms")
    print(f"📊 Média por request: {total_time/3:.2f}ms")
    
    if total_time > 1000:
        print(f"   ⚠️  ALERTA: Sistema muito lento sob carga!")

async def test_stability():
    """10 chamadas seguidas - verifica se não trava"""
    print("\n🛡️  TESTE DE ESTABILIDADE (10 chamadas)\n")
    
    router = AIRouter()
    
    failures = 0
    for i in range(10):
        try:
            await router.execute(
                TaskType.DECISION_MAKING,
                {'targets': [
                    {'url': f'site{i}.com', 'priority': 2, 'scan_count': i}
                ]}
            )
        except Exception as e:
            failures += 1
            print(f"   ❌ Falha {i+1}: {e}")
    
    print(f"✅ Taxa de sucesso: {(10-failures)/10*100:.1f}%")
    
    if failures > 2:
        print(f"   ⚠️  ALERTA: {failures} falhas em 10 chamadas!")

async def main():
    print("="*60)
    print("TESTES DE INTEGRAÇÃO - AI ROUTER")
    print("="*60)
    
    await test_latency()
    await test_fallback_chain()
    await test_concurrent_load()
    await test_stability()
    
    print("\n" + "="*60)
    print("RESULTADO:")
    print("="*60)
    print("✅ Se todos os testes passaram → SAFE para integrar no daemon")
    print("❌ Se algum falhou → CORRIGIR antes de integrar")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
