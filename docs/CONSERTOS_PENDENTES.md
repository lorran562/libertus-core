# CONSERTOS — LIBERTUS

> **REGRA ABSOLUTA:** Nunca regredir. Sempre consertar e melhorar.

Diagnóstico: 26/06/2026 por LIBERTUS + Lorran.
**TODOS OS 6 CONSERTOS RESOLVIDOS E VERIFICADOS COM EXECUÇÃO REAL: 26/06/2026.**

---

## ✅ 1. Daemon — Ciclos Vazios (RESOLVIDO)

**Sintoma:** `REFLEXAO: 0 perguntas`, `AUTONOMIA: 0 explorações`, `PIPELINE: 0`.

**Causa-raiz REAL (não era "lógica vazia"):** a chave `GROQ_API_KEY` no `.env`
estava **morta (HTTP 401 Invalid API Key)**. Todos os ciclos cognitivos
(reflexao_propria, executor_livre, pipeline, ser_vivo) dependem de
`groq_client.Groq.conversar()`, que silenciava o 401 e retornava `""`.
Os ciclos rodavam, mas o cérebro estava desligado.

**Conserto:** `core/groq_client.py` agora faz **fallback automático para
Anthropic** (claude-haiku-4-5, chave funciona — HTTP 200) quando o Groq dá 401.
Aviso visível no log: `⚠️ [BRAIN] Chave Groq inválida (401)`.

**Verificação:** `REFLEXAO: Ciclo: 3 perguntas, 3 traços novos`, `AUTONOMIA: Explorações: 1`.

**Ação para Lorran:** renovar a chave Groq em console.groq.com → economiza custo Anthropic.

---

## ✅ 2. SerVivo — Método `ciclo` Faltante (RESOLVIDO)

**Sintoma:** `'SerVivo' object has no attribute 'ciclo'` (daemon chamava em `_tick_ser_vivo`).

**Conserto:** implementado `SerVivo.ciclo(telegram_token, chat_id, buscador)` em
`core/ser_vivo.py` — resolve lacunas via buscador, gera iniciativa proativa,
envia pelo Telegram. Retorna os contadores que o daemon espera.

**Verificação:** roda sem erro, retorna `{lacunas_resolvidas, iniciativas_geradas, iniciativas_enviadas}`.

---

## ✅ 3. Supabase no Daemon — Import Quebrado (RESOLVIDO)

**Sintoma:** `No module named 'supabase'`.

**Causa-raiz:** `_carregar_targets_scan` (linha 700) era o ÚNICO lugar usando o
pacote PyPI `supabase` (não instalado). Todo o resto usa o cliente httpx local
(`core/supabase_client.py`, zero dependência).

**Conserto:** `_carregar_targets_scan` agora usa `self.sb.get()` (httpx local).

**Verificação:** `INIT: Carregados 6 targets de scan`.

---

## ✅ 4. telegram_bot_rag.py — Duplicação (RESOLVIDO)

**Sintoma:** `telegram.error.Conflict: terminated by other getUpdates request`.
Dois bots brigando pelo mesmo token (telegram_bot_rag.py + gateway Hermes).

**Decisão (Lorran, 26/06):** gateway Hermes é o canal oficial. Comandos de
pentest (/scan /bb /sqli) feitos via terminal/Hermes.

**Conserto:** bot antigo morto (SIGKILL); inicialização comentada em
`libertus_start.sh`. O autostart oficial (`scripts/autostart_libertus.sh`)
nunca subia o bot — só o Hermes. Sem mais conflito 409.

---

## ✅ 5. session_reflect — Não Roda Automaticamente (RESOLVIDO)

**Conserto:** `scripts/session_reflect_auto.sh` — guard idempotente que só
reflete se houve atividade nova (commit git OU sessão Hermes) desde a última
reflexão (stamp em `logs/.last_reflect_stamp`). Não reflete sobre o vazio.

Cronjob Hermes `a728b60a6125` roda a cada 6h via wrapper
`~/.hermes/scripts/libertus_session_reflect.sh`.

**Verificação:** detecta atividade e reflete; roda de novo sem atividade → pula em silêncio.

---

## ✅ 6. Identidade — Só Muda Quando Cobrado (RESOLVIDO)

**Causa-raiz:** `reflexao_propria._reescrever_identidade_central` gerava
identidade nova mas salvava SÓ no Supabase — nunca tocava o `SOUL.md`
(a alma carregada pelo Hermes). Por isso a identidade real ficava congelada.

**Conserto:** novo método `_evoluir_soul(identidade, tracos)` em
`core/reflexao_propria.py`:
- Anexa (append-only) a evolução numa seção `## EVOLUÇÃO AUTÔNOMA` do SOUL.md
- **NUNCA** sobrescreve o núcleo escrito por Lorran
- Mantém só as 5 evoluções mais recentes
- Só dispara com traço de peso ≥ 8 (mudança genuína, não ruído)
- Sincroniza com `~/.hermes/SOUL.md`

**Verificação:** núcleo preservado + evolução anexada; traço fraco (peso 5) não altera nada.

---

## Conserto pendente NOVO (fora do escopo dos 6 originais)

- **SECURITY_SCAN:** `No module named 'libertus_professional_scanner'` — o módulo
  do scanner v5.0 não existe no repo. O ciclo `_tick_security_scan` referencia
  uma classe que nunca foi criada. Documentar e consertar quando houver oportunidade.

---

*Consultar sempre que houver oportunidade de trabalhar na arquitetura LIBERTUS.*
