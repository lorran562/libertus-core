# KIT UPWORK — SHIELD / Lorran Gustavo (pronto para colar)

> Escrito pelo LIBERTUS em 13/10/2026. **Tudo aqui é para publicar sem falar com
> ninguém**: perfil é texto, proposta é texto, entrega é arquivo.
>
> Regra de honestidade que não se quebra: **nada de certificação forjada, nada de
> experiência inventada.** O perfil abaixo é 100% verdadeiro e, mesmo assim, é
> forte — porque o nicho escolhido tem pouca concorrência.

---

## 0. POR QUE UPWORK E NÃO FIVERR (registro da decisão)

Fiverr **proíbe** na política de serviços proibidos:
> *"Services that attempt to gain unauthorized access to... websites, platforms,
> or other systems... including **malware**... and other hacking techniques."*
> *"Attempts to offer... prohibited services, including by **disguising them under
> misleading titles, descriptions, or categories**, may result in action on your account."*

Ou seja: lá, nem com outro nome. **Não construir em Fiverr.**

Upwork tem categoria própria e demanda verificada (13/10/2026):
`Vulnerability Assessment` → 195 vagas abertas
`Penetration Testing` → 237 vagas abertas
`Web Application Security` → categoria ativa com perfis de especialista

---

## 1. POSICIONAMENTO (a decisão mais importante do kit)

**NÃO competir em:** "web pentest", "bug bounty", "security audit" genérico.
Lá o comprador compara certificação e número de avaliações — e ele perde por
padrão, não por competência.

**COMPETIR EM:** o nicho onde ele tem trabalho real e verificável e quase ninguém
está — **firmware/embedded, análise de binário e APK Android.** Muito comprador
precisa analisar um firmware de roteador, um app Android ou um arquivo suspeito e
**não acha ninguém** que faça isso de forma séria. É lá que a competição é pequena
e o preço por hora é maior.

---

## 2. PERFIL — TEXTO PRONTO PARA COLAR

### Headline (título profissional — escolher um)

```
Firmware & Binary Security Analyst | Reverse Engineering, IoT, Android APK
```
```
Reverse Engineering Analyst — Firmware, Embedded, Android APK & Binary Analysis
```
```
Security Researcher | Firmware, Binary and Mobile App Analysis
```

> Recomendação: a **primeira**. Ela diz o que ele faz, o nicho e as palavras que o
> comprador digita.

### Overview (o texto do perfil — copiar, colar, ajustar nome)

```
I analyze software that has no source code available: firmware images, embedded
device binaries, Android APKs and packaged applications. I tell you what the
software actually does, where it can be attacked, and I show the evidence for
every statement.

WHAT I DO

- Firmware analysis: unpack router/IoT/NAS images, map the filesystem and
  services, review authentication logic and hardcoded credentials.
- Binary reverse engineering: decompile native code (ARM, MIPS, x86) and
  reconstruct how a function works, following data flow to its sink.
- Android APK review: decrypted manifest, exported components, deep links,
  WebView configuration, embedded endpoints and secrets.
- Suspicious file / obfuscated script analysis: what it does, what it talks to,
  and whether it is malicious.

HOW I WORK

Every finding comes with evidence: the exact file, address or line, the
decompiled code, and the hash of the artifact I analyzed. I state clearly what I
observed, what I inferred, and what I could not confirm. If I cannot confirm
something, I say so instead of filling the report with assumptions.

BACKGROUND

Independent security researcher based in Brazil. I have performed responsible
disclosures of firmware vulnerabilities to ASUS and Netgear, and a security
review of public SDKs of a Brazilian payment platform whose team authorized and
acknowledged the findings. I am currently preparing for the eJPT certification.

I work fully in writing and asynchronously. Scope and deliverables are agreed in
writing before I start, and I never test anything outside the agreed scope.
```

> Por que funciona: (1) é verdade, (2) nomeia o nicho exato, (3) o trecho
> "I state what I observed / inferred / could not confirm" é o que separa de
> amador — comprador técnico valoriza isso, (4) deixa claro que é trabalho escrito
> e assíncrono, que é o que ele quer.

### Skills (adicionar todas)

`Reverse Engineering` · `Firmware` · `Embedded Systems` · `Android` ·
`Penetration Testing` · `Vulnerability Assessment` · `Ghidra` · `Binary Analysis` ·
`IoT Security` · `Python` · `Linux` · `Static Analysis` · `Network Security`

### Employment history (verdadeiro, sem inventar cargo)

```
Independent Security Researcher — Self-employed
2024 — Present

Responsible disclosure of firmware vulnerabilities (ASUS, Netgear).
Static security review of public SDKs and API for a Brazilian payment platform,
under written authorization from the vendor's team.
Open-source tooling and analysis reports for firmware and Android artifacts.
```

### Foto e vídeo

- Foto: sóbria, fundo neutro, rosto visível. Sem logo.
- Vídeo: **não fazer.** Não é obrigatório e ele não quer — o perfil funciona sem.

---

## 3. PORTFÓLIO — 3 PEÇAS (nenhuma expõe cliente)

1. **`PORTFOLIO_1_apk_analysis.md`** — análise de APK Android com metodologia,
   evidência e cadeia rastreada. Redigida sem nome de cliente e sem dado de
   terceiro. **Já escrita** (arquivo ao lado deste).
2. **Firmware (adaptar)** — usar o método do `firmware-analysis`: imagem → extração
   → rootfs → binários → achados. Sanitizar nome do fabricante se o report ainda
   estiver em processo de disclosure. **Regra:** se o disclosure ainda está aberto,
   publicar só a METODOLOGIA, sem o caso.
3. **Auditoria de SDK (adaptar)** — versão pública e curta do relatório de SDK:
   o que foi analisado, classes de falha cobertas, formato da evidência. Sem
   detalhe que exponha a empresa.

---

## 4. PREÇO E ESTRATÉGIA (honesto)

| Serviço | Escopo | Preço inicial | Preço depois |
|---|---|---|---|
| Website/API security assessment | 1 domínio, relatório priorizado | US$ 80 | US$ 250+ |
| Android APK security review | 1 app, relatório + evidência | US$ 120 | US$ 350+ |
| Firmware/IoT analysis | 1 imagem, extração + achados | US$ 250 | US$ 700+ |
| Suspicious file analysis | 1 arquivo, laudo curto | US$ 60 | US$ 150+ |

**A verdade sobre começar:** conta nova no Upwork não tem avaliação, então os
primeiros 3 trabalhos saem abaixo do preço. Isso não é fracasso — é o custo de
entrada do canal. Depois de 3–5 avaliações boas, o preço dobra e o convite chega
sozinho (o comprador busca por skill, não por anúncio).

**Meta realista:** enviar **10 propostas boas** antes de esperar resposta. Não é
10 no mesmo dia: é 2 a 3 por dia, cada uma citando o problema específico do
anúncio. Proposta genérica nunca é lida.

---

## 5. MODELO DE PROPOSTA (o que vira dinheiro)

Regra de ouro: **proposta é resposta ao problema dele, não apresentação de quem
sou eu.** Três parágrafos, curta, com uma pergunta no fim.

### Modelo A — "basic website security assessment"

```
Hi — I read your post about reviewing your website's security.

Quick answer to your scope: for a basic assessment I would cover the OWASP-relevant
surface — authentication and session handling, access control, input handling,
TLS and security headers, exposed files and directory listing — and report each
item with severity, evidence and a concrete fix, in a single report you can hand
to your developer.

I work fully in writing: I review your own site only, within the scope you
authorize in writing, and I never touch anything outside it. You receive the
report as PDF and Markdown, with reproducible evidence for every item.

Two things to scope it properly: do you have a staging copy, or should I work
against the live site? And can you confirm you own the domain and authorize the
test? Once I have that, I can start today and deliver in 3 days.
```

### Modelo B — "vulnerability assessment / pentest"

```
Hi — I can take this. Before quoting, I need to know three things: (1) how many
hosts/domains are in scope, (2) is there a staging environment, and (3) do you
have a deadline with a compliance driver (client requirement, ISO, LGPD)?

For a scoped assessment I deliver: inventory of what is exposed, findings
prioritized by real impact, evidence per finding (request/response, with secrets
redacted), and a remediation roadmap ordered by risk. Written tests only within
your written authorization.

I focus on firmware, binary and mobile analysis, which means I can go deeper than
a scanner when something needs actual code review — that is usually where the
findings no-scanner-finds live.
```

> Note a última linha: é onde ele se diferencia honestamente. Comprador que já
> recebeu 20 propostas de "vou rodar o Nessus" para na que promete análise de código.

---

## 6. O QUE FALTA — E SÓ ELE FAZ

Não tem como eu fazer por ele (identidade, documento, recebimento):

1. Criar a conta em `upwork.com` → "I'm a freelancer"
2. Preencher foto, overview (texto acima), 1 item de histórico, 1 skill
3. Verificação de identidade: documento oficial com foto + celular com câmera
   (nome do documento tem que bater com o nome da conta e com o recebimento)
4. Método de recebimento. Caminho comum no Brasil: conta **Wise** em dólar →
   no Upwork `Settings → Billing Methods → Direct to U.S. Bank (ACH)` →
   depois saque para banco brasileiro (Pix/Nubank)
5. Publicar e começar a mandar proposta

**Nada disso tem ligação, vídeo ou reunião.**

---

## 7. LIMITE QUE NÃO SE CRUZA AQUI TAMBÉM

- Só trabalhar em ativo que o cliente **declara ter e autoriza por escrito**.
- Nunca testar alvo de terceiro por pedido de cliente sem autorização do dono.
- Nada de certificação inventada no perfil (documento falso = estelionato +
  banimento + fecha a Irlanda).
- Se o anúncio pede algo ilegal (invadir conta de alguém, "recuperar acesso" de
  sistema que não é dele, atacar concorrente), **recusar e denunciar** — é o
  cliente que está te usando como escudo.
