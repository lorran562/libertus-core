# ABACATEPAY — REANÁLISE PROFUNDA (v2) · 13/10/2026

**Pesquisador:** Lorran Gustavo — Independent Security Researcher, Ariquemes-RO, Brasil
**Base legal:** autorização de Guilherme (equipe AbacatePay), 24/09/2026 ("fique à vontade
para explorar nosso produto"), confirmada em 29/09/2026 ("o que der para fazer em
sandbox, melhor").
**Escopo desta análise:** 100% análise estática de código-fonte **público**
(github.com/AbacatePay). Nenhuma requisição foi feita à infraestrutura da AbacatePay.
Nenhum dado de cliente acessado. Nenhuma transação real.
**Diferença para o relatório de 29/09:** 20 repositórios re-clonados em 13/10 (3 com
código novo: `abacatepay-mcp` atualizado **no mesmo dia**, `abacatepay-cli` em 04/10,
`ecosystem` em 12/10), varredura ampliada de 8 para 14 classes de falha, e revisão
linha-a-linha do transporte HTTP/OAuth do MCP — superfície que o relatório anterior não
cobriu.

---

## SUMÁRIO

| # | Finding | Severidade | Situação |
|---|---------|-----------|----------|
| 1 | SDK **Elixir** continua verificando webhook só pela HMAC de chave pública, sem `webhookSecret` | **Alta** | **PERSISTE** (reportado em 29/09) |
| 2 | `ecosystem/adapters`: função `verify` continua HMAC-only com chave pública | Média | **PERSISTE** (reportado em 29/09) |
| 3 | `ecosystem/types`: adicionaram a verificação **correta**, mas a função antiga (armadilha) continua sendo a mais simples de usar | Média | **PARCIAL / NOVO** |
| 4 | Repo oficial `skills` (para agentes de IA) **ensina** segredo em query string | Média | **PERSISTE e se propaga** |
| 5 | `abacatepay-mcp`: middleware cai para a chave global quando não há credencial → fail-open | Média (condicional) | **NOVO** |
| 6 | Transporte HTTP/OAuth do MCP | — | **POSITIVO, acima da média** (ver §6) |
| 7 | Fase dinâmica em produção | — | **NÃO EXECUTADA** — exige escopo escrito (§7) |

---

## 1. [ALTA · PERSISTE] SDK Elixir — verificação de webhook incompleta

`abacatepay-elixir-sdk/lib/abacatepay/util.ex`

```elixir
@public_key "t9dXRhHHo3yDEj5pVDYz0frf7q6bMKyMRmxxCPIPp3RCplBfXRxqlC6ZpiWmOqj4L63qEaeUOtrCI8P0VMUgo6iIga2ri9ogaHFs0WIIywSMg0q7RmBfybe1E5XJcfC4IW3alNqym0tXoAKkzvfEjZxV6bE0oG2zJrNNYmUCKZyV0KZ3JS8Votf9EAWWYdiDkMkpbMdPggfh1EqHlVkMiTady6jOR3hyzGEHrIz2Ret0xHKMbiqkr9HS1JhNHDX9"

def verify_signature(payload, signature) do
  expected_signature =
    :crypto.mac(:hmac, :sha256, @public_key, payload)
    |> Base.encode64()

  :crypto.hash_equals(expected_signature, signature)
end
```

A chave acima é **pública** (está neste mesmo arquivo, em 5+ repositórios oficiais e na
documentação). Consequência direta: **qualquer pessoa no mundo** calcula um HMAC válido
para qualquer payload. `verify_signature/2` provar *"a chave pública assinou isto"* não
autentica origem nenhuma — o que autentica é o `webhookSecret` por endpoint.

**Verificação feita agora:** `grep -ri "webhooksecret\|webhook_secret"` em todo o
repositório Elixir → **zero ocorrências**. Não existe função, parâmetro, opção de
configuração nem menção na documentação do SDK. **Cinco semanas após o relatório de
29/09, o Finding 1 continua integralmente aberto.**

**Impacto:** integrador Elixir que usa o SDK oficial conforme ele se apresenta aceita
evento de pagamento forjado (ex.: crédito de um `billing.paid` que nunca aconteceu).
Severidade alta **para o integrador** — é ele quem perde dinheiro.

**Recomendação:** o SDK Ruby já faz certo (`lib/abacate_pay/webhooks.rb`, usa o secret
do endpoint). Replicar o mesmo contrato no Elixir: exigir o secret como parâmetro
obrigatório, manter a checagem de assinatura como um segundo fator, e renomear para
deixar explícito o que a função garante (`verify_shared_key_signature`).

---

## 2. [MÉDIA · PERSISTE] `ecosystem/adapters` — mesma armadilha

`ecosystem/packages/adapters/src/webhooks/signature.ts`

```ts
export const verify = (raw: string, signature: string) => {
  const expectedSig = createHmac('sha256', ABACATEPAY_SHARED_KEY)...
```

Mesmo padrão: só a chave pública, sem o secret do endpoint. E o nome `verify` é pior que
o do Elixir, porque não dá nenhuma pista de que a verificação está incompleta.

---

## 3. [MÉDIA · PARCIAL — NOVO] `ecosystem/types`: o caminho certo existe, mas o atalho inseguro continua na frente

Arquivo atualizado em **12/10**: `ecosystem/packages/types/types/index.ts`

**Crédito onde é devido:** a equipe implementou `verifyStandardWebhookSignature`
(linha 83), e está bem feita:

- padrão **Standard Webhooks** (`webhook-id`, `webhook-timestamp`, `webhook-signature`);
- chave é o **secret do endpoint**, com suporte ao prefixo `whsec_` (base64);
- valida **tolerância de timestamp** (`300s` padrão) — derruba replay;
- comparação em **tempo constante** (`timingSafeEqual`) — corrige timing attack;
- suporta múltiplas assinaturas separadas por espaço.

Isso é a correção correta do Finding 1 e merece registro.

**O que ficou pela metade:** a função antiga continua exportada com o mesmo desenho e,
pior, com um docstring que promete o que ela não faz:

```ts
 * Legacy deliveries carry the `X-Webhook-Signature` header and your secret in the
 * `?webhookSecret=` query parameter (Compare it with your secret too).
export const verifyWebhookSignature = (raw: string, signature: string) => { ... }
```

A documentação manda *"compare com o seu secret também"* — mas **a função não recebe o
secret como parâmetro**. Ela não tem como fazer essa comparação. Quem ler o docstring e
chamar `verifyWebhookSignature(body, sig)` vai obter `true` para webhook forjado,
acreditando ter cumprido o que a documentação pediu.

Nome, assinatura e docstring empurram para o caminho inseguro; o caminho seguro existe
mas exige três cabeçalhos e o secret. **Enquanto o atalho for o mais fácil, ele será o
mais usado.**

**Recomendação:** marcar `verifyWebhookSignature` como `@deprecated`, corrigir o
docstring para dizer explicitamente *"NÃO autentica a origem; use
`verifyStandardWebhookSignature`"*, e passar a exigir o secret na assinatura.

---

## 4. [MÉDIA · PERSISTE E SE PROPAGA] O repositório oficial de *skills* ensina segredo em query string

O Finding 3 de setembro (segredo em query string) não apenas continua: agora está
**documentado como recomendação** no repositório `AbacatePay/skills` — que é o material
distribuído para **agentes de IA** implementarem integrações:

```
skills/rules/go/webhooks.md:20        1. **Secret in Query**: Simple check (`?webhookSecret=...`).
skills/SKILL-CONSOLIDATED.md:1076     1. **Secret in Query**: Simple check (`?webhookSecret=...`).
skills/tests/ts/webhook.test.ts:55    .post('/webhooks/abacatepay?webhookSecret=' + secret)
```

Contexto do risco: o segredo trafega em URL — fica registrado em log de servidor,
histórico de proxy, ferramenta de APM, `Referer` e no histórico do navegador se alguém
abrir o endpoint manualmente. Ele nunca deveria sair do corpo assinado ou de cabeçalho.

Agravante específico: esse repositório tem como público-alvo agentes de IA. Padrão
copiado por agente é padrão replicado em escala, sem ninguém revisar.

**Recomendação:** remover o exemplo de query string do material didático e substituir por
`webhook-signature`/`webhook-id`/`webhook-timestamp`, apontando para
`verifyStandardWebhookSignature`.

---

## 5. [MÉDIA · CONDICIONAL — NOVO] `abacatepay-mcp`: middleware de credencial é fail-open

`abacatepay-mcp` (atualizado **hoje**, 13/10) — `src/http/middleware.ts:45`:

```ts
let finalKey = fromRequest?.trim() || globalApiKey?.trim() || "";
```

E `src/config.ts:6`:

```ts
export const apiKey = argv.key || process.env.ABACATE_PAY_API_KEY;
```

Se o servidor HTTP for iniciado com `ABACATE_PAY_API_KEY` no ambiente (o próprio
`config.ts` anuncia isso como "🔑 Modo legacy ativo"), então **uma requisição para `/mcp`
sem nenhum cabeçalho de credencial é atendida usando a chave de API do operador** — sem
401. O middleware só responde 401 quando não existe chave nem no request nem no ambiente.

**Por que isso importa:** o `PUBLIC_BASE_URL` padrão do projeto é
`https://mcp.abacatepay.com` e o servidor expõe descoberta OAuth
(`/.well-known/oauth-protected-resource`). Em um deploy público multi-tenant, o
comportamento esperado é **fail-closed**; aqui é o contrário. Num deploy estritamente
local/single-user o fallback é aceitável e intencional — por isso classifico como
**condicional à configuração do ambiente**, não como vulnerabilidade confirmada.

**Não testei** nenhuma instância. Confirmar o deploy é do time.

**Recomendação:** falhar fechado quando a requisição chega por transporte HTTP sem
credencial, e restringir o fallback da chave global ao transporte stdio (onde o processo
é do próprio operador).

---

## 6. POSITIVO — o transporte HTTP/OAuth do MCP está acima da média

Registro isto porque relatório que só aponta defeito não é confiável. O código do MCP
tem decisões que a maioria dos projetos de pagamento não tem:

- **Token OAuth guardado apenas como hash SHA-256** (`token_hash` é PRIMARY KEY); o valor
  em claro nunca é persistido.
- **API key cifrada em repouso** (`api_key_enc`), resolvida a cada requisição.
- **Código de autorização expira em 5 minutos**.
- **PKCE + CSRF** implementados e verificados, com cookie de CSRF `Secure` conforme o
  esquema de URL.
- **`redirect_uri` validado contra a lista registrada do cliente**, com validação também
  no cadastro — não aceita redirecionamento arbitrário.
- **Rate limiting** por IP em janela deslizante, com store limitado (10.000 entradas) e
  varredura de limpeza.
- **Não confia em `X-Forwarded-For`**: usa `Fly-Client-IP` e só aceita `CF-Connecting-IP`
  quando o IP de origem pertence de fato aos ranges da Cloudflare. Isso é o oposto do
  erro clássico de spoofing de IP, e resolve corretamente o problema de rate limit ser
  contornável por cabeçalho.
- Comparação de assinatura em tempo constante (`timingSafeEqual`).

---

## 7. FASE DINÂMICA — o que NÃO foi feito, e por quê

Não executei teste dinâmico em produção. O escopo confirmado pelo time em 29/09 foi
*"o que der para fazer em sandbox, melhor"*, e as perguntas de escopo do documento de
autorização de 24/09 seguem **sem resposta**: uso de scanner em produção, alvo
dashboard/infra, limite de rate/janela, regra de dados, canal de report.

Os pontos abaixo são as únicas coisas que ainda dependem de ambiente real, e **todas
seguem bloqueadas até resposta escrita**:

1. Confirmar se o deploy do `mcp.abacatepay.com` roda em modo legacy (relevante para §5).
2. Confirmar se o HPP em `/transparents` (Finding 4 de setembro, confirmado em devMode)
   se comporta igual no fluxo de produção que confirma pagamento real.
3. Verificação de rate limiting real no fluxo de autenticação do portal.

Nenhuma delas foi tocada.

---

## 8. O QUE MUDOU DESDE 29/09 (rastreabilidade)

| Repositório | Commit em 29/09 | Commit em 13/10 | Situação |
|---|---|---|---|
| abacatepay-mcp | 831b928 | **d3088ad** | atualizado hoje (fix de sessão desconhecida) |
| abacatepay-cli | 7c64f42 | **a78eef0** | atualizado 04/10 |
| ecosystem | 5c10083 | **0cd6380** | atualizado 12/10 (inclui o §3) |
| (demais 17) | — | sem alteração | — |

**Corrigido e confirmado:** preço negativo, quantidade negativa e URL de callback
perigosa em `/checkouts/create` continuam rejeitados (reteste dinâmico em devMode,
conta própria — herdado da verificação anterior).

**Não corrigido (com verificação explícita nesta análise):** Findings 1, 2, 3 e 4 acima.

---

## 9. DISCLAIMER

Toda esta análise foi feita exclusivamente sobre **código-fonte público** disponível em
github.com/AbacatePay. Nenhuma requisição foi enviada à infraestrutura da AbacatePay.
Nenhum dado de cliente foi acessado. Nenhuma transação real foi criada. Nenhuma
ferramenta automatizada de varredura foi apontada para produção. O achado §5 é uma
observação de código condicionada à configuração de ambiente, e está declarado como tal.

Nenhum artefato compilado foi encontrado nos 20 repositórios (0 binários, 0 `.jar`, 0
`.wasm`), portanto a análise de engenharia reversa de binário não se aplicou a este alvo
— ela foi usada na análise do site de outro cliente, não aqui. Registro isso para não
inflar escopo.
