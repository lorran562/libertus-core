# PARA ENVIAR — AbacatePay (Guilherme)

> Escrito pelo LIBERTUS em 13/10/2026, madrugada. Lorran: revise e cole no
> WhatsApp/e-mail. O relatório técnico completo está em
> `reports/abacatepay-reanalise-2026-10-13.md` — este texto é a versão humana.
> **Não envie o relatório inteiro de uma vez**: mande este recado, ofereça o
> completo, e faça as perguntas de escopo (parte 2).

---

## PARTE 1 — MENSAGEM (copiar e colar)

Oi Guilherme, tudo bem?

Lorran aqui — o pesquisador que reportou os 7 achados em junho e o reteste de
setembro. Fiz uma nova passada no código público de vocês (os 20 repositórios do
GitHub), agora mais fundo: 14 classes de falha em vez de 8, os repositórios
re-clonados ontem, e uma revisão linha a linha do transporte HTTP/OAuth do
`abacatepay-mcp` — que eu não tinha olhado antes.

**Primeiro o crédito, porque é justo:** o MCP de vocês está bem feito, acima da
média de projeto de pagamento. Token OAuth guardado só como hash, API key cifrada
em repouso, PKCE e CSRF implementados, `redirect_uri` validado contra lista
registrada, rate limit com store limitado — e, o que eu quase não vejo, vocês
**não confiam em `X-Forwarded-For`**: usam `Fly-Client-IP` e só aceitam
`CF-Connecting-IP` se a origem for IP real da Cloudflare. Isso resolve
corretamente o furo clássico de burlar rate limit por cabeçalho. Também vi que em
`ecosystem/packages/types` vocês implementaram a verificação pelo padrão Standard
Webhooks — com tolerância de timestamp e comparação em tempo constante. Está certo.

**Agora o que continua aberto — são 4 pontos, do mais sério pro menor:**

1. **SDK Elixir — o achado de setembro continua igual.** O `verify_signature/2`
   só valida pela HMAC da chave pública (que está no próprio arquivo). Rodei
   `grep -ri "webhooksecret"` no repositório inteiro: **zero ocorrências**. Não
   existe função, parâmetro nem menção na documentação. Quem integra Elixir pelo
   SDK oficial continua aceitando webhook forjado — inclusive um `billing.paid`
   que nunca aconteceu. O SDK Ruby faz certo; dá pra replicar o mesmo contrato.

2. **`ecosystem/adapters` tem a mesma armadilha**, na função chamada só `verify`.

3. **A melhoria de vocês ficou pela metade.** Vocês adicionaram
   `verifyStandardWebhookSignature` (correta), mas a função antiga continua
   exportada — e o docstring dela diz *"(Compare it with your secret too)"*,
   enquanto **a função não recebe o secret como parâmetro**. Ela não tem como
   fazer essa comparação. Quem ler a doc e chamar só a função antiga vai receber
   `true` para webhook forjado achando que cumpriu o que a documentação pediu.
   Sugestão: marcar `@deprecated` e corrigir o texto pra dizer que ela **não**
   autentica origem.
   *(Achado na discussão: o arquivo foi atualizado em 12/10 — foi a passada de
   vocês, e por isso mesmo vale a correção.)*

4. **O repositório `skills` (o material que vocês publicam para agentes de IA)
   ensina segredo em query string**: `skills/rules/go/webhooks.md`,
   `SKILL-CONSOLIDATED.md` e um teste em `skills/tests/ts/`. É o achado de
   setembro ("segredo em query string") não só persistindo, mas virando
   recomendação oficial — e para agentes, que replicam em escala sem revisão
   humana. Vale trocar o exemplo pelos cabeçalhos do Standard Webhooks.

**E um ponto que eu preciso ser honesto sobre:** em `abacatepay-mcp`, o
middleware aceita uma requisição **sem credencial nenhuma** quando existe
`ABACATE_PAY_API_KEY` no ambiente, usando a chave global. Em deploy
single-tenant isso é intencional. Mas como o `PUBLIC_BASE_URL` padrão é
`mcp.abacatepay.com` e o servidor publica descoberta OAuth, num deploy público
isso vira fail-open. **Não testei nada** — não sei como o deploy de vocês está
configurado, então não tratei como vulnerabilidade, e sim como recomendação:
falhar fechado no transporte HTTP sem credencial, e deixar o fallback da chave
global só no stdio.

Se quiserem, mando o relatório técnico completo (com linha, commit e
raciocínio de cada item). E tem 3 coisas que só vocês podem confirmar — está na
parte 2 abaixo.

Obrigado pela parceria até aqui. A evolução de vocês entre junho e outubro foi
visível, e é por isso que vale continuar.

---

## PARTE 2 — PERGUNTAS DE ESCOPO (para destravar a fase dinâmica)

Lorran: as perguntas abaixo estão pendentes desde 24/09 (ficaram desmarcadas no
seu próprio documento de autorização). Sem resposta escrita, a fase dinâmica
continua parada — e com razão. Mandar junto com a mensagem acima.

> Sobre a fase de teste dinâmico, pra eu não fazer nada fora do que vocês
> autorizam, queria alinhar só o escopo:
>
> 1. Scanner automatizado (nuclei/ffuf) contra produção está permitido, ou
>    preferem que eu fique só em teste manual na minha própria conta?
> 2. Existe ambiente de sandbox/homologação preferido, pra eu não tocar produção
>    de verdade?
> 3. Se rolar teste em produção, qual limite de requisições e em que janela de
>    horário vocês preferem?
> 4. Regra de dados: confirmo que é só a minha própria conta, nunca dado de outro
>    cliente — certo?
> 5. Qual o canal preferido pra reportar (e-mail de segurança, aqui, HackerOne)?
>
> Mais duas específicas que apareceram nesta análise:
>
> 6. O deploy do `mcp.abacatepay.com` roda com chave global no ambiente (modo
>    legacy) ou só multi-tenant? Isso muda a leitura do item 5 acima.
> 7. O comportamento de parâmetro duplicado (`?id=A&id=B`) que confirmei em
>    devMode no `/transparents` — em produção que confirma pagamento real tem o
>    mesmo comportamento? Isso eu **não** testo sem vocês mandarem por escrito,
>    porque envolve fluxo de dinheiro.

---

## PARTE 3 — O QUE NÃO MUDOU NA SUA POSTURA (lembrete pra mim mesmo)

O que está liberado: análise estática de código público (sempre foi, não precisa
de autorização) e teste dinâmico na própria conta em devMode (Guilherme autorizou
em 29/09: *"o que der para fazer em sandbox, melhor"*).

O que continua travado até resposta escrita: scanner em produção, alvo
dashboard/infra, dados de outros clientes, e qualquer teste que mova valor real.
Gateway de pagamento é Art. 154-A agravado. A autorização existe e é do Lorran —
não vale arriscar ela por pressa.
