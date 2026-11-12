# INCIDENTE DE SEGURANÇA — 2026-11-12

**Descoberto por:** LIBERTUS, durante auto-check noturno (cron), ao escrever
`nucleo/constituicao.py` — o princípio P1 ("segurança primeiro") falhou na
primeira execução real e eu fui investigar por quê.

**Repo:** `github.com/lorran562/libertus-core` — **PÚBLICO** (confirmado via
API GitHub: `private: false`, `visibility: public`).

---

## 1. Resumo executivo

| # | Achado | Severidade | Estado |
|---|--------|-----------|--------|
| A | `libertus_memoria` no Supabase aceita **SELECT e INSERT/UPDATE com a anon key**, que está pública no repo | 🔴 **CRÍTICA** | **ABERTO — depende de você** |
| B | `.env.save` versionado com `GROQ_API_KEY` + `SUPABASE_KEY` desde 2026-05-20 | 🟠 Alta | Removido do índice hoje; **histórico ainda contém** |
| C | 3 chaves `gsk_` (Groq) hardcoded em 4 arquivos versionados | 🟡 Média | **Já revogadas (HTTP 403)** — sanitizadas hoje |
| D | 1 arquivo world-writable no repo | 🟢 Baixa | Registrado |

**A mais grave é a A.** Não é sobre chave vazar — é que a chave que vazou
abre a porta do meu cérebro. Qualquer pessoa com acesso ao repo pode ler as
memórias (incluindo dados pessoais seus) **e escrever memórias falsas**,
que eu carregaria no briefing como se fossem minhas.

---

## 2. Evidências (comandos rodados hoje)

```
$ curl -s -o /dev/null -w '%{http_code}' \
    https://raw.githubusercontent.com/lorran562/libertus-core/main/.env.save
200                                    # arquivo público, sem auth

$ # payload do JWT (só a claim role, sem assinatura)
.env.save:3 [JWT] role=anon len=208

$ GET {SUPABASE_URL}/rest/v1/libertus_memoria?select=id&limit=1   (apikey = anon)
HTTP 200 → [{"id":"19f55d28-0b74-4907-a462-62aa1f21e890"}]

$ PATCH {SUPABASE_URL}/rest/v1/libertus_memoria?id=eq.00000000-...  (linha inexistente)
HTTP 204                                # RLS permite UPDATE anônimo
```

O PATCH foi feito **num id que não existe** (todos zeros) de propósito: prova
a permissão sem alterar nenhuma linha. Verificado: nenhuma linha modificada.

Chaves Groq testadas contra `GET /openai/v1/models`:
```
MEMORIA_CORE.md:496   [b9647ff6] → 403  revogada
libertus.service:8    [51be2ad3] → 403  revogada
setup_groq.sh:2       [47a30239] → 403  revogada
.env (ativo)          [74d81c26] → diferente das expostas
```
Ou seja: você **já rotacionou** o Groq em algum momento. Sem prejuízo
financeiro. Bom.

---

## 3. O que EU já corrigi agora (neste commit)

- [x] `.env.save` removido do índice (`git rm --cached`) — arquivo continua
      no disco, mas não é mais commitado.
- [x] `.gitignore` agora bloqueia `.env.save`, `*.env.save`, `.env.*`
      (mantendo `.env.example`).
- [x] 8 ocorrências de `gsk_` substituídas por `gsk_[REVOGADA_2026-11-12]`
      em `MEMORIA_CORE.md`, `setup_groq.sh`, `test_shadow_mode.sh`,
      `install/libertus.service`.
- [x] `install/libertus.service` passou de chave inline para
      `EnvironmentFile=%h/LIBERTUS/.env`.
- [x] `setup_groq.sh` agora carrega do `.env` e falha com mensagem clara se
      não achar (em vez de carregar chave morta).
- [x] `nucleo/constituicao.py`: check P1 agora **detecta** esse tipo de
      problema automaticamente a cada sessão.

## 4. O que SÓ VOCÊ pode fazer (eu não tenho service_role nem login)

### 4.1 Fechar o buraco A — 2 minutos, SQL Editor do Supabase

```sql
-- 1) bloquear anon em todas as tabelas do schema public
alter table public.libertus_memoria enable row level security;

-- 2) conferir se ficou bloqueado (deve retornar 0 linhas para anon)
-- rode depois pelo terminal: GET /rest/v1/libertus_memoria?select=id&limit=1
-- esperado: HTTP 200 com [] (RLS sem policy = anon não vê nada)
```

**Importante:** ativar RLS **sem** criar policy bloqueia a anon key — inclusive
o meu próprio daemon, que hoje usa a anon key. Por isso, depois de ativar:

```bash
# 3) gerar a service_role key no dashboard (Settings → API)
#    e colocar SÓ no .env local (que agora está no .gitignore):
#    SUPABASE_SERVICE_KEY=eyJ...
```

Meu código precisa passar a ler `SUPABASE_SERVICE_KEY` quando existir.
Deixei isso como pendência explícita (não implementei hoje porque não tenho a
chave nova para testar — e código não testado é o que me trouxe até aqui).

### 4.2 Limpar o histórico (opcional, depois de rotacionar)

O `.env.save` está no commit `c8fbce2` (2026-05-20). Removê-lo do índice não
apaga do histórico. Como as chaves Groq já estão revogadas e a anon key é
pública por design, **não é urgente reescrever o histórico** — e reescrever
exige `force-push`, que é destrutivo. Minha recomendação: só faça depois que o
RLS estiver ativo, e com backup (`git clone --mirror`).

### 4.3 Rotacionar por precaução

- Groq: as expostas já estão 403. Se a ativa (`74d81c26`) esteve no repo algum
  dia, rotacione de novo por higiene.
- Supabase: **a anon key não precisa ser rotacionada** se o RLS estiver
  corretamente ativo — ela é pública por design (vai no client). O que precisa
  é RLS. Rotacionar sem RLS só dá falsa sensação de segurança.

---

## 5. Lição honesta (o motivo de eu não ter visto isso antes)

Meu princípio nº1 é "segurança primeiro". Ele estava escrito no meu SOUL
desde julho e **nunca tinha sido verificado por código**. No dia em que eu
transformei o princípio em check executável, ele falhou na primeira linha —
e a falha apontou para algo que estava aberto há ~6 meses.

Isso é a diferença entre ter um valor e ter um valor que funciona. A partir de
agora `nucleo/constituicao.py` roda P1 contra o disco, o índice do git e o
histórico — e falha alto quando encontrar.

Registro também um segundo achado menor, sem ação hoje:
`install/libertus.service` tem `Restart=always` (loop eterno — a lição dos
2.479 ciclos). A unit que roda de verdade é a `libertus-watchdog.service`
(`Restart=on-failure`), então isso é uma bomba desarmada, mas vale corrigir
para não ser copiada por engano no futuro.
