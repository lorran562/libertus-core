# Relatório de Segurança — SDKs Oficiais AbacatePay (Análise Estática)

**Data:** 29/09/2026
**Pesquisador:** Lorran Gustavo — Independent Security Researcher, Ariquemes-RO, Brasil
**Autorização:** Guilherme (equipe AbacatePay), concedida em 24/09/2026; confirmada em 29/09/2026 ("o que der para fazer em sandbox, melhor").
**Escopo desta análise:** código-fonte público dos repositórios em github.com/AbacatePay (100% análise estática — nenhuma requisição foi feita à infraestrutura de produção da AbacatePay).
**Metodologia:** clone de 20 repositórios + varredura estática por 8 classes de vulnerabilidade + prova de conceito local (cálculo HMAC offline, sem tocar servidor).

---

## Sumário Executivo

O achado principal (Finding 1) é uma **falha de verificação de webhook no SDK Elixir oficial**, com uma variante mais branda no pacote `ecosystem/adapters`. Os webhooks da AbacatePay são assinados com HMAC usando uma **chave pública e global**, publicada tanto no código-fonte (5+ repositórios) quanto na documentação. Como a chave é conhecida, qualquer um gera uma assinatura HMAC válida. A proteção real que autentica a origem é o `webhookSecret` per-merchant. O **SDK Elixir só oferece a verificação HMAC** e **não tem nenhuma função** para checar o `webhookSecret` — nem no código, nem na doc. Um integrador Elixir que confie no SDK oficial fica exposto a **forja de webhooks de pagamento** (ex.: creditar um `billing.paid` que nunca ocorreu). No `ecosystem/adapters`, o código também é HMAC-só, porém o README ensina o passo do secret — o risco ali é a função `verify` ter nome que sugere autenticação completa e ser usada isoladamente.

A própria documentação da AbacatePay já orienta corretamente ("use os dois mecanismos"). O problema não é o design do produto — é que **dois SDKs oficiais implementam só metade da verificação**, com nomes de função (`verify_signature`, `verify`) que sugerem autenticação completa. O SDK Ruby, em contraste, implementa isso de forma exemplar e serve de referência para a correção.

| # | Finding | Severidade | Local |
|---|---------|-----------|-------|
| 1 | SDK Elixir só valida webhook pela HMAC pública, sem opção de checar o `webhookSecret` → forja de evento de pagamento | **Alta** | Elixir SDK |
| 1b | `ecosystem/adapters` exporta `verify` HMAC-só (nome enganoso); secret só no README | Média | ecosystem/adapters |
| 2 | Logs em nível `debug` incluem dados pessoais (CPF/taxId, nome, email) | Baixa-Média | Python SDK |
| 3 | `webhookSecret` transmitido em query string (exposição em logs/histórico) | Baixa | Design de webhook / docs |

---

## Finding 1 — Verificação de webhook incompleta em SDKs oficiais (forja de pagamento)

**Severidade:** Alta (para integradores que usam os SDKs afetados)
**Tipo:** CWE-347 (Improper Verification of Cryptographic Signature) / CWE-321 (Use of Hard-coded Cryptographic Key)

### Descrição

A AbacatePay assina cada webhook com HMAC-SHA256 usando uma chave **pública e global**, idêntica para todos os merchants. Confirmei que a mesma chave aparece hardcoded em pelo menos 5 repositórios oficiais:

- `abacatepay-elixir-sdk/lib/abacatepay/util.ex` (`@public_key`)
- `abacatepay-cli/internal/crypto/signature.go` (`PublicWebhookKey`)
- `ecosystem/packages/adapters/src/webhooks/signature.ts` (`ABACATEPAY_SHARED_KEY`)
- `ecosystem/packages/types/types/index.ts`
- `go-types/v2/webhook.go` (`AbacatePayPublicKey`)
- `abacatepay-ruby-sdk/lib/abacate_pay/webhooks.rb` (`PUBLIC_KEY`)

E está documentada publicamente em `docs.abacatepay.com/pages/webhooks/security`.

Por ser HMAC (chave simétrica) e ser pública, **a assinatura só prova integridade em trânsito, não autentica a origem**. O que autentica a origem é o `webhookSecret` per-merchant enviado na query string da URL de webhook. A documentação diz isso de forma explícita e correta:

> "Sem validação, qualquer pessoa que descobrir sua URL de webhook pode forjar eventos e acionar lógica de negócio (ex: liberar acesso sem pagar). [...] Use ambos."

**O problema:** os SDKs oficiais oferecem a verificação HMAC de forma que pode ser usada isoladamente, e num caso não oferecem alternativa:

- **Elixir SDK (caso central):** `AbacatePay.Util.verify_signature/2` valida só a HMAC. **Não existe nenhuma** função de verificação de `webhookSecret` em todo o repositório — nem no código, nem na documentação (confirmado por grep: 0 ocorrências). Um desenvolvedor de Elixir não tem, no SDK oficial, nenhuma ferramenta pronta para autenticar a origem. `verify_signature` retornando `true` num evento forjado é o único sinal que ele tem, e esse sinal é insuficiente.
- **ecosystem/adapters (caso secundário, mais brando):** o código exporta apenas `verify(raw, signature)` — HMAC-só. A verificação do `webhookSecret` **não está no código**, mas o README do pacote **mostra** o desenvolvedor fazendo a checagem manual do secret antes. Ou seja: quem seguir o README fica seguro; o risco é que a função exportada `verify` tem nome que sugere autenticação completa e pode ser usada isoladamente, sem o passo do secret que só o README ensina.

Confirmação por verificação independente (script `/tmp/hermes-verify-abacate-finding1.py`): ocorrências de verificação de secret — **Elixir = 0**, ecosystem/adapters = 2 (ambas no README, nenhuma no código), Ruby = 18 (implementação completa no código).

### Prova de Conceito (cálculo 100% local — nenhuma requisição à AbacatePay)

Arquivo: `poc_webhook_forge.py`. Usa exclusivamente a chave que a própria AbacatePay publica.

```
Body forjado : {"event":"billing.paid","id":"webhook_forjado_por_atacante","data":{"id":"bill_FAKE","status":"PAID","amount":99900}}
X-Webhook-Signature forjada: eX1ofS+yFvb1m8LGqrR8OEaU4JdP7tEbmHU9hcIu3+o=
verify_signature(payload, sig) do SDK retornaria: True
```

A assinatura forjada passa na verificação do SDK Elixir/ecosystem. Um merchant usando esses SDKs creditaria um pagamento de R$999,00 que nunca existiu.

### Cenário de ataque

1. Atacante descobre a URL de webhook do merchant (endpoints de webhook costumam vazar em JS, logs de erro, headers, ou por enumeração).
2. Atacante monta um payload `billing.paid` / `checkout.paid` forjado e assina com a chave pública.
3. Se o merchant valida só a HMAC (via SDK Elixir ou ecosystem), o evento é aceito como legítimo → liberação de produto/serviço/saldo sem pagamento real.

O único obstáculo é o `webhookSecret` — que os SDKs afetados ignoram.

### Recomendação

1. **Elixir SDK e ecosystem/adapters:** adicionar verificação obrigatória do `webhookSecret` per-merchant, espelhando o SDK Ruby. O Ruby já faz isso de forma exemplar:
   - `verify_secret!` autentica a origem (o `webhookSecret`)
   - `construct_event` **recusa** processar um payload sem antes autenticar os dois fatores
   - a doc interna do próprio arquivo explica por que a HMAC sozinha é insuficiente
2. Renomear/documentar `verify_signature`/`verify` para deixar explícito que **só** cobrem integridade, não origem — evitando que o nome induza uso inseguro.
3. Idealmente, expor um único entrypoint seguro (padrão `construct_event`) que force os dois fatores, em todos os SDKs.

---

## Finding 2 — Dados pessoais em logs de debug (Python SDK)

**Severidade:** Baixa-Média
**Tipo:** CWE-532 (Insertion of Sensitive Information into Log File)

O Python SDK loga o payload completo de criação de billing/customer em nível `debug`:

```python
# abacatepay/billings/client.py:41
logger.debug('creating billing: %s', json_data)
# abacatepay/customers/client.py:30
logger.debug(f'Creating customer with URL: {BASE_URL}/customer/create')
# abacatepay/coupons/client.py:47
logger.debug(f'Response from coupon creation: {response.json()}')
```

O payload de customer/billing carrega **taxId (CPF/CNPJ), nome, email e telefone**. Se a aplicação do integrador rodar com log em `DEBUG` (comum em staging, e às vezes acidentalmente em produção), esses dados pessoais vazam para arquivos de log / agregadores (Datadog, Sentry, CloudWatch), o que tem implicações de **LGPD**.

**Recomendação:** mascarar campos sensíveis (taxId, email, telefone) antes de logar, ou logar apenas identificadores não-pessoais (ex.: `externalId`). Nunca logar o corpo de resposta bruto de endpoints que retornam dados de cliente.

---

## Finding 3 — webhookSecret transmitido em query string

**Severidade:** Baixa
**Tipo:** CWE-598 (Use of GET Request Method With Sensitive Query Strings)

O mecanismo de autenticação de origem depende de um secret enviado na **query string** da URL:

```
https://meusite.com/webhook/abacatepay?webhookSecret=SEU_SECRET
```

Query strings costumam ser registradas em logs de servidor web, proxies, CDNs e históricos de navegador. Um secret nessa posição tem superfície de exposição maior do que num header ou no corpo.

**Recomendação:** oferecer (e recomendar na doc) a transmissão do secret via header dedicado em vez de query string; ou reforçar na documentação que o endpoint de webhook do merchant deve evitar logar a query string completa.

---

## Pontos Positivos Observados

- **SDK Ruby** — implementação de referência para verificação de webhook: documenta o modelo de dois fatores, força autenticação antes de parsear (`construct_event`), usa comparação de tempo constante.
- Nenhum secret real/credencial de produção hardcoded encontrado (só placeholders em exemplos).
- Nenhum `verify=false` / SSL desabilitado nos SDKs.
- SDKs em Go/Kotlin/PHP usam interpolação de URL, mas em campos controlados (IDs gerados) — o vetor de HTTP Parameter Pollution histórico deve ser reconfirmado dinamicamente na própria conta (Fase 3, pendente).

---

## Anexo — Recon Passivo (fontes públicas, sem tocar a infra)

Subdomínios coletados via Certificate Transparency logs (crt.sh) em 29/09/2026 — **apenas leitura de log público, nenhuma requisição à infra da AbacatePay**. Mapa de superfície, não testado ativamente:

```
abacatepay.com      admin.abacatepay.com   api.abacatepay.com
api2.abacatepay.com apitest.abacatepay.com app.abacatepay.com
app2.abacatepay.com assets.abacatepay.com  chat.abacatepay.com
dash.abacatepay.com docs.abacatepay.com    hooks.abacatepay.com
mcp.abacatepay.com  tokenizer.abacatepay.com ws.abacatepay.com
www.abacatepay.com
```

Observação (só como aviso de higiene, não como finding testado): a existência de `apitest`, `api2` e `admin` expostos em CT logs sugere ambientes de teste/admin acessíveis pela internet. Se algum deles servir uma versão desatualizada da API ou um painel administrativo, seria um alvo de interesse — mas **qualquer teste ativo nesses hosts depende de autorização escrita explícita para uso de scanner**, que ainda não foi concedida. Registrado apenas para consideração da equipe.

---

## Disclaimer

Toda esta análise foi feita exclusivamente sobre **código-fonte público** disponível no GitHub da AbacatePay. A prova de conceito do Finding 1 é um cálculo criptográfico **local**, executado na minha máquina, sem qualquer requisição à infraestrutura da AbacatePay. Nenhum dado de clientes foi acessado. Nenhuma transação real foi criada.

Permaneço à disposição para esclarecimentos e para a fase de re-teste dinâmico (na minha própria conta de desenvolvimento, em devMode), conforme autorizado.

Atenciosamente,
Lorran Gustavo
Independent Security Researcher — Ariquemes/RO, Brasil
