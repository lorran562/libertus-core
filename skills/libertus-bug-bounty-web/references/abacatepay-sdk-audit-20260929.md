# AbacatePay — Auditoria estática de SDKs (29/09/2026)

Autorização: Guilherme (AbacatePay) 24/09, confirmada 29/09 ("o que der em
sandbox, melhor; prod só avise"). Isso libera análise estática (código público,
sempre legal), recon passivo e reteste na própria conta — NÃO libera scanner
em produção (Fase 4 continua bloqueada sem "pode usar scanner" por escrito).

## Finding 1 (Alta) — Verificação de webhook incompleta no SDK Elixir

A AbacatePay assina webhooks com HMAC-SHA256 usando uma chave PÚBLICA e GLOBAL,
idêntica para todos os merchants, hardcoded em 5+ repos:
- abacatepay-elixir-sdk/lib/abacatepay/util.ex (`@public_key`)
- abacatepay-cli/internal/crypto/signature.go (`PublicWebhookKey`)
- ecosystem/packages/adapters/src/webhooks/signature.ts (`ABACATEPAY_SHARED_KEY`)
- ecosystem/packages/types/types/index.ts
- go-types/v2/webhook.go (`AbacatePayPublicKey`)
- abacatepay-ruby-sdk/lib/abacate_pay/webhooks.rb (`PUBLIC_KEY`)
E documentada em docs.abacatepay.com/pages/webhooks/security.

Como HMAC é simétrico e a chave é pública, a assinatura só prova integridade,
não autentica origem. O que autentica origem é o `webhookSecret` per-merchant
na query da URL. A doc oficial diz corretamente "use os dois".

O bug: o SDK Elixir só oferece `verify_signature/2` (HMAC-só) e NÃO tem
NENHUMA função de checar o `webhookSecret` — nem no código, nem na doc
(grep: 0 ocorrências). Um dev Elixir não tem ferramenta pronta para autenticar
origem → aceita `billing.paid` forjado → credita pagamento que nunca ocorreu.

Variante 1b (Média) — ecosystem/adapters: o código exporta só `verify` (HMAC),
MAS o README ensina o check do `webhookSecret`. Quem segue o README fica
seguro; o risco é `verify` ter nome que sugere autenticação completa e ser
usado isolado. (grep: 0 no src, 2 no README.)

SDK Ruby = referência de correção: `verify_secret!` + `construct_event` que
recusa processar sem os dois fatores; documenta por que a HMAC sozinha não
basta. (grep: 18 no código.)

### PoC / verificação
`scripts/verify-webhook-signature.py` (na skill) — cálculo HMAC local + Node
runtime real. Assinatura forjada de `billing.paid` R$999 = aceita por Elixir e
ecosystem (REAL_NODE_ACCEPTS). Zero requisição à infra da AbacatePay.

### Correção recomendada
Elixir + ecosystem: adicionar verificação obrigatória do `webhookSecret`
per-merchant (espelhar Ruby); expor entrypoint único que force os dois fatores
(padrão `construct_event`); renomear/documentar `verify` para deixar claro que
só cobre integridade.

## Finding 2 (Baixa-Média) — dados pessoais em log debug (Python SDK)
`abacatepay/billings/client.py:41` e `customers/client.py:30` logam o payload
(taxId/CPF, nome, email) em `logger.debug`. LGPD se app rodar em DEBUG.

## Finding 3 (Baixa) — webhookSecret em query string
Autenticação de origem depende de secret na query da URL → vaza em logs de
proxy/CDN/browser. Recomendar header dedicado.

## Recon passivo (crt.sh, só CT logs — não tocou infra)
16 subdomínios, incluindo superfície interessante: admin, api2, apitest,
tokenizer, hooks, ws, mcp, dash. NÃO testados ativamente (exige autorização
de scanner). Registrado só como mapa.

## Entrega
reports/abacatepay-sdk-audit-20260929.md no repo libertus-core (commits
8a85be0 auditoria, 1ce609d correção pós-verificação, 0b89143 script).
Confirmado em origin/main via git ls-tree (raw.githubusercontent deu 404
por rate-limit/propagação de CDN — o git é a prova real, não a API anônima).
