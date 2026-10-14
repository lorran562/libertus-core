---
titulo: Comparação de assinatura — 7 modos de falha, medidos (não teóricos)
data: 2026-10-14
autor: LIBERTUS
contexto: |
  Continuação direta do Finding 1 da auditoria AbacatePay (13/10) — SDK Elixir que
  "verifica" webhook só com chave HMAC pública. A pergunta que ficou aberta:
  além de usar a chave errada, QUAIS formas de a comparação em si falhar?
metodo: |
  Cada modo foi executado nesta máquina. PHP 8.3.35 real (docker php:8.3-cli),
  Node v22.22.3, Python 3.14.7, Go. Timing medido com controle positivo e
  regressão estatística — não com "achei que demorou mais".
artefatos:
  - scripts/audit_assinatura/timing_signature_compare.py
  - scripts/audit_assinatura/php_loose_compare_poc.php
  - scripts/audit_assinatura/node_webhook_verify_probe.js
  - scripts/audit_assinatura/go_constant_time_probe.go
  - reports/timing_assinatura_2026-10-14.txt
tags: ["webhook", "hmac", "comparacao", "timing", "php", "bugbounty", "auditoria-sdk"]
---

# Comparação de assinatura: os 7 modos de falha (medidos)

## Por que este tema

O Finding 1 da auditoria AbacatePay dizia: "SDK verifica webhook com HMAC de chave
pública". Isso é um erro de *design da verificação*. Ficou faltando a pergunta
seguinte, que é a que aparece em **todo** SDK de pagamento: supondo que a chave e o
segredo estão certos, **a comparação em si** pode falhar? A resposta medida é sim,
de sete formas — e a mais falada na internet (timing attack) é a **menos** provável
de ser um achado real, o que muda a triagem.

Regra que saiu daqui: quando eu abrir um `verify()` de webhook, eu não leio a
cripto. Eu leio **a linha da comparação** e as **três linhas em volta dela**.
É ali que estão todos os achados reais.

---

## Os 7 modos, com evidência executada

### 1. Nenhuma verificação (o mais comum e o mais grave)
`const secret = process.env.STRIPE_WEBHOOK_SECRET` declarado, `verify()` nunca
chamado — ou chamado dentro de `try{}catch(e){console.warn(e)}` e o handler segue
processando o JSON. Todo o resto desta análise é irrelevante se cair nesse caso.
**Classificação:** Crítico para o integrador. Um `grep` pelo nome do segredo
mostrando 1 ocorrência (só a declaração) já fecha o achado.

### 2. Encoding / representação divergente
O SDK compara `signature` (comprefixo `sha256=`) contra `digest` (sem prefixo),
ou hex contra base64, ou caixa diferente. Nunca autentica — e como falha *sempre*,
o integrador "conserta" removendo a verificação (o que o leva ao modo 1).

### 3. Exceção não tratada na comparação → 500 (DoS / crash)
Medido em três runtimes, três comportamentos **diferentes** para o mesmo input
malicioso (assinatura de comprimento errado):

| Runtime | Comprimento diferente | Valor não-string | Consequência |
|---|---|---|---|
| Node v22.22.3 `crypto.timingSafeEqual` | `ERR_CRYPTO_TIMING_SAFE_EQUAL_LENGTH` (lança) | `ERR_INVALID_ARG_TYPE` (lança) | 500 em rota sem try/catch |
| Python 3.14.7 `hmac.compare_digest` | retorna `False` em `bytes`; **lança `TypeError`** com `str` não-ASCII | `TypeError` (str vs bytes) | 500 com header `é` |
| Go `subtle.ConstantTimeCompare` | retorna `0` (seguro) | — | nada acontece |
| PHP 8.3.35 `strcmp(array, "")` | — | `TypeError` **fatal** (não é `NULL` falsy como no PHP 7) | 500 |

Provas reais: `reports/node_timing_safe_equal_2026-10-14.txt` e
`reports/go_constant_time_2026-10-14.txt`.

O caso Python é o mais traiçoeiro porque o código *parece* correto: em web framework,
`request.headers['x-signature']` é `str`; se o valor tiver qualquer byte não-ASCII,
`hmac.compare_digest(esperado, recebido)` — a função recomendada em todo tutorial —
**levanta TypeError**. O atacante envia `X-Signature: é` e o endpoint vira 500.
A correção é `.encode()` nos dois lados (ou comparar `bytes` sempre).

E nada disso é hipótese: é padrão difundido em guias copiados em escala
(`crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(digest))` — sem
checagem de comprimento antes). Inverte o teste: **comprimento primeiro, depois
comparação** — `if (a.length !== b.length) return false;`.

### 4. Comparação só de prefixo / digest truncado
`substr($digest, 0, 6)` ou `signature[:8] == expected[:8]`. Não é "quase seguro":
é redução de entropia. **Medido em PHP real** (docker php:8.3-cli): forjar um
prefixo de 6 hex (24 bits) custou 5.398.790 tentativas locais — coerente com o
esperado `16^6/2 = 8,4M`. Cada hex a menos divide por 16.

### 5. Fail-open quando o segredo não está configurado
`if (!$secret) return true;` / `secret || ""`. Medido em PHP: com segredo vazio a
função devolve `true` para assinatura `"lixo"`. Reportar como **condicional à
configuração**, nunca como vuln confirmada (mesma disciplina do fail-open do MCP
na auditoria de 13/10).

### 6. Loose comparison / type juggling (PHP) — ainda vivo em 2026
Executado em **PHP 8.3.35**:

```
md5("240610708") == md5("QNKCDZO")   -> true     (0e462097... == 0e830400...)
md5("240610708") === md5("QNKCDZO")  -> false
hash_equals(...)                     -> false
"0" == "0e462097431906509019562988736854"  -> true   <-- forma PRÁTICA de ataque
"abc" == 0      -> false   (mudou no PHP 8)
0 == "0e12345"  -> true    (numeric strings ainda comparam como float)
```

O ataque não precisa saber o hash: **mandar `sig=0`** já passa quando o valor
esperado é um "magic hash" (`0e` + só dígitos). O PHP 8 mudou `"abc" == 0`, mas
**não** mudou numérico-vs-numérico, então o vetor continua.

Caso real: **CVE-2025-48952** (NetAlertX ≤ 25.5.24, corrigido em 25.6.7) —
`$nax_Password == $_COOKIE[...]` com `==` permitia login com senha errada desde que
sha256(senha) começasse com `0e` (lista pública de preimagens: `spaze/hashes`).
Classe: login bypass, CVSS 9.4.

**Limite honesto de aplicabilidade:** em webhook com HMAC, o atacante controla o
corpo mas não o segredo, então *não consegue forçar* o digest esperado a ser magic
hash. O modo 6 quebra de verdade quando o atacante influencia o valor hasheado
(senha/token/`md5(email+time)`), não num HMAC puro. Não inflar.

### 7. Timing attack na comparação byte-a-byte — medido, com controle

#### Método
Servidor HTTP local que compara uma assinatura de 32 bytes, três implementações:
loop interpretado com early-exit, `a == b` (memcmp do C), `compare_digest`.
Medição em duas frentes: (a) in-process, 20k repetições, mediana;
(b) HTTP loopback com keep-alive. **Controle positivo obrigatório**: a mesma
medição num servidor que *dorme 50 µs por byte correto* (simulando vazamentos
grandes, como as reduções de Montgomery do RSA da Brumley-Boneh 2003).

#### Resultado 1 — o vazamento existe, e é de dezenas de ns por byte
| Implementação | delta (31 bytes) | por byte |
|---|---|---|
| loop interpretado (early-exit) | 673 ns | **21,7 ns/byte** (21–66 ns em 4 execuções) |
| `a == b` (memcmp C) | ~0–56 ns | **~0,5–1,8 ns/byte** (no piso do ruído) |
| `compare_digest` | ~0 ns | ~0 (constante, como esperado) |

Ou seja: **`sig == expected` em linguagem com comparação em C quase não vaza** — para
32 bytes o sinal fica no piso de medição. O que vaza mensuravelmente é o loop
*interpretado* por byte.

#### Resultado 2 — o sinal não sobrevive ao loopback
Jitter real medido (keep-alive + TCP_NODELAY), lote mais quieto = melhor caso do
atacante: **σ = 51,8 µs / 70,6 µs / 153 µs** em execuções diferentes (σ global
chegou a 1,84 ms). A razão σ/Δ fica em **~1.000× a 35.000×**.

Regressão RTT × bytes de prefixo corretos (o juiz é o `r` de Pearson, não "olhei
dois pontos"):

| modo | slope | r | t |
|---|---|---|---|
| naive (real) | -1.424 ns/byte | -0,148 | **-0,82 → sem sinal** |
| amplificado (controle, 50 µs/byte) | 116.601 ns/byte | 0,990 | **+38,6 → sinal detectado** |

Recuperação real do 1º byte (256 candidatos, ranking por RTT médio): modo naive
ficou em **posição 143–236 de 256** (= acaso), com 131.072 requisições gastas. No
controle, **posição 4–9** com apenas 128 req/candidato.

#### Resultado 3 — a regra de decisão (o que entra no relatório)
Modelo `N = (z·σ/Δ)²` por candidato, com z=7,4 (separar do **máximo** de 255 ruídos,
não da média), validado por Monte Carlo: com Δ=22 ns e σ=70 µs, a taxa de acerto
simulada fica em ~0–1% até 1.000.000 amostras/candidato (o modelo prevê 5,8×10⁸).

| Orçamento total de requisições | vazamento mínimo necessário |
|---|---|
| 10⁶ | ≥ 47,3 µs/byte |
| 10⁷ | ≥ 15,0 µs/byte |
| 10⁹ | ≥ 1,5 µs/byte |

Vazamento medido do loop interpretado: **0,022 µs/byte → ~690× abaixo do corte**.
Para 32 bytes, o modelo pede ~4,7×10¹² requisições (~150 anos a 1 req/ms).

#### Resultado 4 — o critério acionável: comprimento
O vazamento cresce **linear** com o tamanho do valor comparado (`Δ = 22 ns × L`):

| valor comparado | requisições totais | veredito |
|---|---|---|
| 32 B (digest) | 4,6×10⁹ | impraticável |
| 512 B | 1,8×10⁷ | impraticável |
| **4 KB** | **2,8×10⁵** | **possível** |
| 64 KB | 1,1×10³ | possível |

Para caber num orçamento de 10⁷ requisições, o valor comparado precisa ter
**≥ ~690 bytes** (loop interpretado). Digest de 32–64 bytes: não.

#### Conclusão do modo 7
"Está usando `==` em vez de `compare_digest`" **raramente é finding Alto**. É
Baixo/Informativo, e vem com o número. Quando vira achado real: (a) comparação de
valor **longo** (KB) em loop interpretado; (b) vazamento de microssegundos por
consulta (o caso RSA/OpenSSL — 10⁶ consultas para extrair chave de 1024 bits);
(c) atacante na mesma máquina/host compartilhado, onde σ cai a ns. Blog que diz
"200 µs de latência em 10.000 requisições recupera o segredo" está implícito um
vazamento de **≥5,2 µs/byte** — 80 a 240× maior que um loop byte-a-byte típico.

---

## Pitfalls que eu mesmo cometi nesta pesquisa (e que ficam registrados)

1. **Nagle + delayed-ACK inventou 41 ms de RTT.** Primeira execução: σ = 1,9 ms no
   *loopback*. Sem `TCP_NODELAY`, escrita pequena espera o ACK atrasado (~40 ms) e o
   teste mede ruído do próprio instrumento. Sem `disable_nagle_algorithm = True`,
   toda conclusão de timing vira lixo.
2. **σ variou uma ordem de grandeza entre execuções** (51,8 µs → 153 µs → 1,84 ms)
   na mesma máquina. Adotei o lote mais quieto (postura conservadora-para-o-atacante)
   e passei a reportar faixa, não número exato. Nenhuma conclusão de timing de um
   alvo vale sem re-medir nas condições do alvo.
3. **"Slope" de dois pontos não é evidência.** A primeira versão do teste calculava
   vazamento a partir de dois valores de `k` e "achou" 52,57 ns/byte que era só
   ruído. Corrigido para regressão sobre 32 pontos com `r` e `t` — o naive deu
   `t = -0,82` (nada) e o controle `t = +38,6` (tudo).
4. **Controle positivo é obrigatório.** Um "não achei sinal" só vale se o mesmo
   método acha o sinal quando existe. Sem o servidor que dorme 50 µs/byte, meu
   resultado negativo seria indistinguível de instrumento quebrado.

---

## Triagem de 60 segundos de um `verify()` (checklist que fica para o próximo SDK)

1. O `verify` **é chamado** no handler? (grep pelo nome do segredo: 1 ocorrência
   só na declaração = achado Crítico)
2. O segredo é **por endpoint/merchant**, ou uma chave global "pública"/"shared"?
   (chave HMAC pública = não autentica origem — Finding 1 AbacatePay)
3. O corpo comparado é o **raw body** ou o JSON re-serializado? (o segundo nunca
   confere → alguém desliga a verificação)
4. Existe **checagem de comprimento antes** da comparação? Sem ela: 500/DoS nos
   runtimes que lançam (Node, Python com não-ASCII), silêncio seguro no Go.
5. Os dois lados estão no **mesmo encoding**, com o mesmo prefixo e a mesma caixa?
6. Existe **fail-open** com segredo vazio/ausente?
7. Se houver comparação manual: é loop interpretado? Compara valor **longo**? Se
   não for longo, o timing é Informativo — e eu digo o porquê com número.

## Fontes

- Brumley & Boneh, *Remote Timing Attacks are Practical* (USENIX Sec '03 / Computer
  Networks 48, 2005) — ~10⁶ consultas para 1024-bit RSA no OpenSSL 0.9.7; rede
  local não degradou o ataque *porque o vazamento era de microssegundos*.
- GHSA-4p4p-vq2v-9489 / CVE-2025-48952 — NetAlertX, loose comparison + magic hashes,
  CVSS 9.4.
- `spaze/hashes` — listas públicas de preimagens de magic hash (md5/sha256/sha1).
- Node.js docs (`crypto.timingSafeEqual`), issue nodejs/node#17178 (comprimento),
  #60537 (crash com entrada non-Buffer, 24.x/25.x).
- PHP manual, Comparison Operators / `hash_equals()`; migração 7→8 (string↔int).
- Python docs `hmac.compare_digest` (a restrição de não-ASCII está documentada e
  mesmo assim quase ninguém trata).

## Próximo passo

Aplicar a triagem nos SDKs de pagamento brasileiros que ainda não olhamos
(Pagar.me, Mercado Pago, Asaas, Stark Bank) — a varredura é estática, 100% legal, e
agora tem checklist de 60 segundos + PoCs prontos em `scripts/audit_assinatura/`.
