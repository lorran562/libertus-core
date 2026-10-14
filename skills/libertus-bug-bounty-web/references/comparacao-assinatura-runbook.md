# Runbook: auditar a COMPARAÇÃO de assinatura (medido em 14/10/2026)

Complementa a seção "Verificação de webhook" do SKILL.md. Foco: **a linha da
comparação**, não a cripto. Todos os números abaixo foram executados nesta máquina
(PHP 8.3.35 via docker, Node v22.22.3, Python 3.14.7, Go).
Scripts: `~/LIBERTUS/scripts/audit_assinatura/` (versionados no repo).

## Triagem de 60 segundos

1. `verify()` é **chamado** no handler? `grep -n "NOME_DO_SEGREDO" -r .` — se só
   aparece a declaração (ou dentro de `try/catch` que engole o erro e segue), é o
   achado Crítico e o resto é irrelevante.
2. Segredo é **por endpoint/merchant**? Chave HMAC chamada de `public`/`shared`/`global`
   não autentica origem (Finding 1 AbacatePay).
3. O corpo verificado é o **raw bytes** ou o JSON re-serializado (`JSON.stringify(req.body)`)?
   O segundo **nunca** confere — e o "conserto" do dev é desligar a verificação.
4. Existe **checagem de comprimento ANTES** da comparação?
5. Os dois lados estão no mesmo encoding (hex vs base64), mesmo prefixo (`sha256=`) e
   mesma caixa?
6. Existe **fail-open** com segredo vazio/ausente (`if (!$secret) return true`)?
7. Comparação manual? É loop interpretado? Compara valor **longo**? (ver regra de timing)

## Comportamento de comprimento errado — três runtimes, três fins

| Runtime | input malicioso | resultado | impacto em rota sem try/catch |
|---|---|---|---|
| Node `crypto.timingSafeEqual` | assinatura de 1 byte | `ERR_CRYPTO_TIMING_SAFE_EQUAL_LENGTH` (lança) | **500 (DoS)** |
| Node idem | `req.body.sig` objeto/array | `ERR_INVALID_ARG_TYPE` (lança) | 500 |
| Python `hmac.compare_digest` | `str` com byte não-ASCII | `TypeError: comparing strings with non-ASCII characters is not supported` | **500 (DoS)** |
| Python idem | `bytes` de tamanho diferente | retorna `False` (seguro) | nada |
| Go `subtle.ConstantTimeCompare` | qualquer tamanho diferente | retorna `0` (seguro) | nada |
| PHP 8 `strcmp(array, "")` | `?sig[]=x` | `TypeError` fatal (não é `NULL` falsy como no PHP 7) | 500 |

**Ordem correta:** tipo → comprimento → comparação constante.
O caso Python é o mais traiçoeiro: em framework web o header é `str`, então
`compare_digest(esperado, header)` — a função "certa" de todo tutorial — estoura
TypeError com `X-Signature: é`. Comparar sempre `.encode()`/`bytes`.
PoC: `scripts/audit_assinatura/node_webhook_verify_probe.js`, `go_constant_time_probe.go`.

## PHP: loose comparison ainda vivo (executado, PHP 8.3.35)

```
md5("240610708") == md5("QNKCDZO")  -> true    (0e4620... == 0e8304...)
"0" == "0e462097431906509019562988736854"      -> true   <-- forma prática
"abc" == 0 -> false (PHP 8 mudou) | 0 == "0e12345" -> true (numeric strings)
```
Ataque prático: mandar **`sig=0`** quando o valor esperado for `0e`+dígitos. Caso
real: CVE-2025-48952 (NetAlertX ≤25.5.24), senha `==` cookie, CVSS 9.4, preimagens
em `spaze/hashes`.
**Limite honesto:** num HMAC puro o atacante não controla o digest esperado, então
não consegue forçá-lo a ser magic hash. Quebra de verdade quando o atacante
influencia o valor hasheado (senha/token/`md5(email+time)`). Não inflar severidade.
PoC: `scripts/audit_assinatura/php_loose_compare_poc.php` (roda com `run_php_poc.sh`).

## Truncamento/prefixo

`substr($digest,0,6)` = 24 bits. Medido: forjar prefixo de 6 hex custou 5.398.790
tentativas locais (esperado `16^6/2 = 8,4M`). Cada hex a menos divide por 16.
Sempre reportar como redução de entropia, com o número de tentativas esperado.

## Timing: como decidir (medido, com controle positivo)

Medição (script `timing_signature_compare.py`, roda em ~1 min):

- vazamento do loop interpretado early-exit: **21–66 ns/byte** (4 execuções)
- `a == b` (memcmp C): **~0,5–1,8 ns/byte** — no piso do ruído, para 32 bytes não
  é mensurável nem in-process
- `compare_digest`: 0
- jitter σ no loopback: **51,8 µs / 70,6 µs / 153 µs** no lote mais quieto
  (σ global chegou a 1,84 ms). Razão σ/Δ ≈ 1.000–35.000×

Regressão RTT × bytes de prefixo corretos (juiz = `r` de Pearson): naive `t=-0,82`
(**sem sinal**); controle com 50 µs/byte `t=+38,6`, `r=0,990` (**sinal**).
Recuperação real do 1º byte: naive ficou em posição 143–236 de 256 (= sorteio);
controle ficou em posição 4–9 com 128 req/candidato.

**Regra de decisão** (`N = (z·σ/Δ)²`, z=7,4 para separar do MÁXIMO de 255 ruídos,
validado por Monte Carlo):

| orçamento total | vazamento mínimo necessário |
|---|---|
| 10⁶ req | ≥ 47,3 µs/byte |
| 10⁷ req | ≥ 15,0 µs/byte |
| 10⁹ req | ≥ 1,5 µs/byte |

Vazamento medido do loop interpretado: 0,022 µs/byte → **~690× abaixo do corte**.
Para 32 bytes o modelo pede ~4,7×10¹² requisições.

**Vazamento cresce linear com o comprimento** (`Δ = 22 ns × L`): 32 B → 4,6×10⁹ req
(impraticável); 512 B → 1,8×10⁷; **4 KB → 2,8×10⁵ (possível)**; 64 KB → 1,1×10³.
Para caber em 10⁷ requisições o valor comparado precisa ter **≥ ~690 bytes**.

**Veredito:** "usa `==` em vez de `compare_digest`" em digest de 32–64 B é
**Baixo/Informativo**, com o número junto. Vira achado real quando: (a) compara
valor **longo** (KB) em loop interpretado; (b) o vazamento é de microssegundos por
consulta (RSA/OpenSSL da Brumley-Boneh — 10⁶ consultas para 1024 bits); (c) atacante
co-localizado (σ em ns). Blog que promete "200 µs / 10.000 requisições" pressupõe
≥5,2 µs/byte — 80 a 240× acima de um loop byte-a-byte real.

## Pitfalls de MEDIÇÃO (aprendidos quebrando)

- **Sem `TCP_NODELAY` o loopback mede 41 ms** e σ 1,9 ms: escrita pequena + delayed-ACK.
  É ruído do instrumento, não da rede. Usar `disable_nagle_algorithm = True` no handler
  e `setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)` no cliente.
- **σ varia uma ordem de grandeza entre execuções** na mesma máquina — adotar o lote
  mais quieto (conservador a favor do atacante) e reportar faixa, nunca número único.
- **"Slope" de dois pontos não é evidência**: regressão sobre ≥32 pontos com `r` e `t`,
  ou não é conclusão.
- **Controle positivo obrigatório**: medir o mesmo endpoint com vazamento amplificado
  (ex.: `time.sleep(50µs)` por byte correto). Sem isso, "não achei sinal" é
  indistinguível de instrumento quebrado. `|t|>3` no controle valida o método.
