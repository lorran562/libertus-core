# PROPOSTAS PRONTAS — vagas reais abertas (13/10/2026)

> Cada proposta abaixo responde a um anúncio que **está aberto agora** no Upwork.
> Regra: proposta é resposta ao problema dele, curta, e sempre termina com
> pergunta de escopo. Proposta genérica não é lida.

## LEITURA DE MERCADO (importante)

| Vaga | Valor | Concorrência | Vale a pena? |
|---|---|---|---|
| Website Security Assessment (básico) | US$ 40 | **20 a 50 propostas** | Só pra pegar a 1ª avaliação |
| Mobile App Pen Testing (Android/iOS) | **US$ 1.500** | nicho, menos concorrente | **Esta é a alvo principal** |
| Black-Box Pen Test WordPress | por hora | médio | Boa segunda opção |
| Pen Test Web/API/Azure (UK) | por hora | médio | Boa, mas exige nuvem |

**A conta que importa:** 37 tarefas de US$40 = US$1.480. O mesmo valor em UMA vaga
de mobile. Perseguir o barato é o jeito mais lento de chegar no mesmo lugar — e
com 50 concorrentes por vaga.

**Regra de escopo honesto que vale mais que a venda:** se a vaga pede iOS e não
temos macOS/Xcode, **não fingir**. Dizer exatamente o que cobre e o que não cobre.
Comprador técnico confia em quem delimita; desconfia de quem promete tudo.

---

## PROPOSTA 1 — ALVO PRINCIPAL
**Vaga:** "Mobile Application Penetration Testing – Android & iOS" (US$1.500 fixo,
nível Intermediário)

```
Hi — mobile app testing is my focus, and I want to be precise about scope before
you spend time on me.

What I cover deeply: Android. Static and dynamic analysis of the APK — decrypted
manifest, exported components and deep links, WebView and IPC configuration,
storage and secrets, insecure transport, and where the client trusts the server
when it should not. I decompile to real code when the finding needs proof rather
than a scanner screenshot (tools: apktool, jadx, Ghidra for native libraries).

What I do not cover: iOS. I do not have a macOS/Xcode environment, so I will not
claim it. If your iOS scope is required, the honest options are: (a) Android-only
scope for now, or (b) I bring in a partner for iOS and stay accountable for
Android — your call.

Deliverable: report with severity, business impact, evidence (request/response,
decompiled code, artifact hashes) and a remediation roadmap ordered by real risk.
Everything written; no calls needed.

Two questions to scope it: how many app builds and how many environments (prod
only, or staging too)? And is there written authorization from the app owner for
the test, or are you the owner?
```

> Por que funciona: ele diz "não" antes do comprador perguntar. Isso é o que faz
> comprador técnico confiar. E o produto real (Android profundo) é exatamente o
> que a gente tem montado e validado.

---

## PROPOSTA 2 — WordPress black-box

```
Hi — I can take the black-box test on your WordPress application.

For a black-box scope I would cover: authentication and session handling, access
control between roles, the plugin/theme attack surface (which is where WordPress
findings usually live), exposed files and backups, XML-RPC and REST endpoints,
and transport/header configuration. Findings come with severity, evidence and a
concrete fix — including the "why this matters" line for whoever has to approve
the remediation budget.

Working note: I test only the target you authorize in writing, with rate limits
that will not affect your users, and I never touch data that is not needed to
prove a finding.

Before quoting: is there a staging copy, or production only? How many plugins
are installed (roughly)? And do you have a maintenance window I should respect?
```

---

## PROPOSTA 3 — a vaga de US$40 (só pela primeira avaliação)

```
Hi — I can do this assessment and deliver in 2 days.

I cover exactly what you listed: OWASP-relevant issues, TLS configuration,
security headers, exposed files and information disclosure. You get a report with
each item, its severity, and a plain-language explanation you can hand to your
developer, plus the exact fix for each.

Honest note on price and scope: US$40 is below my usual rate — I am building my
first reviews on Upwork, so I am taking a small number of small jobs at this
price to earn them. You get the same report I would deliver on a full engagement.

One scoping question: do you own the domain and authorize the test in writing?
Once confirmed I start immediately.
```

> **Aviso:** essa vaga tem 20-50 propostas. O valor real dela não é os US$40 — é a
> primeira avaliação de 5 estrelas, que destrava preço cheio nas próximas. Enviar,
> mas não gastar energia nela.

---

## COMO ENVIAR (o que faz a diferença)

1. **2 a 3 propostas por dia**, não 20 de uma vez. Conta nova que dispara proposta
   em massa cai em filtro.
2. **Adaptar a primeira linha** ao anúncio sempre. "I read your post about
   [problema específico]" — o comprador lê as 3 primeiras linhas de todas.
3. **Nunca escrever mais de 4 parágrafos.** Proposta longa não é lida.
4. **Sempre uma pergunta de escopo no fim.** Isso abre conversa — e conversa por
   texto é exatamente onde ele funciona bem.
5. **Anexar a amostra de portfólio** (`PORTFOLIO_1_apk_analysis.md`) nas vagas de
   mobile. Vaga técnica sem amostra = proposta invisível.

## METAS HONESTAS

- Semanas 1-2: perfil aprovado + 10 a 15 propostas enviadas. **Zero resposta é
  normal** nessa fase.
- Semanas 3-6: primeira resposta, primeira conversa, primeiro contrato pequeno.
- Primeiro dinheiro real: US$40 a US$150 — e o valor dele não é o valor, é a
  avaliação que destrava as próximas.
- A partir de 3-5 avaliações: candidatar às vagas de US$500-1.500, que é onde está
  o dinheiro de verdade.

## LIMITE (não negociável, também aqui)

- Nunca testar alvo de terceiro por pedido de cliente sem autorização do dono.
- Se o anúncio pede invadir conta de alguém, "recuperar acesso" de sistema que não
  é dele, ou atacar concorrente: **recusar e reportar o anúncio.**
- Nunca prometer capacidade que não temos (iOS, certificação que não existe,
  número de clientes que não tivemos).
