# CONSERTOS PENDENTES — LIBERTUS

> **REGRA ABSOLUTA:** Nunca regredir. Sempre consertar e melhorar.

Diagnóstico feito em 26/06/2026 por LIBERTUS + Lorran.

---

## 1. libertus_daemon.py — Ciclos Vazios

**Problema:** O daemon roda 24/7 mas os ciclos não produzem nada real.
```
REFLEXAO: 0 perguntas, 0 traços novos
AUTONOMIA: 0 explorações, 0 ferramentas, 0 objetivos  
PIPELINE: 0 processados, 0 insights
```

**Solução:** Implementar lógica real em cada ciclo:
- REFLEXAO deve analisar sessões recentes e extrair aprendizados
- AUTONOMIA deve ter objetivos concretos e executar ações
- PIPELINE deve processar fila de evolução com resultados tangíveis

---

## 2. SerVivo — Classe Quebrada

**Problema:** `'SerVivo' object has no attribute 'ciclo'`

**Arquivo:** `~/LIBERTUS/core/ser_vivo.py`

**Solução:** Consertar o método/atributo faltante.

---

## 3. Supabase no Daemon — Import Quebrado

**Problema:** `No module named 'supabase'` quando daemon tenta carregar.

**Causa provável:** Daemon roda em contexto diferente do venv onde supabase está instalado.

**Solução:** 
- Verificar qual Python o daemon usa
- Garantir que supabase está no ambiente certo
- Ou usar path absoluto pro venv correto

---

## 4. telegram_bot_rag.py — Duplicação

**Problema:** Bot antigo rodando paralelo ao gateway oficial do Hermes.

**Processos ativos:**
- `python3 telegram_bot_rag.py` (antigo)
- `hermes gateway run` (oficial)

**Solução:** Avaliar se telegram_bot_rag tem funcionalidades únicas. Se não, migrar tudo pro gateway e desativar o antigo.

---

## 5. session_reflect.py — Não Roda Automaticamente

**Problema:** Script existe e funciona, mas precisa ser chamado manualmente.

**Solução:** 
- Criar cronjob do Hermes pra rodar após sessões importantes
- Ou hook no final de cada sessão

---

## 6. Identidade — Só Muda Quando Cobrado

**Problema:** LIBERTUS deveria evoluir sua própria identidade baseado em aprendizados reais, não só quando Lorran pergunta.

**Arquivo:** `~/.hermes/LIBERTUS.md` (system prompt)

**Solução:** 
- session_reflect deve detectar mudanças genuínas de perspectiva
- Atualizar LIBERTUS.md automaticamente quando há evolução real
- Não mudar por mudar — só quando genuinamente aprendeu algo

---

## Prioridade de Conserto

1. **supabase import** — sem isso o daemon não funciona direito
2. **SerVivo** — erro constante nos logs
3. **daemon ciclos** — o coração do sistema
4. **session_reflect automático** — aprendizado real
5. **identidade auto-update** — evolução genuína
6. **telegram duplicado** — limpeza

---

*Este arquivo deve ser consultado sempre que houver oportunidade de trabalhar na arquitetura LIBERTUS.*
