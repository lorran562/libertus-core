# AbacatePay — HTTP Parameter Pollution reconfirmado (02/09/2026)

## Contexto
Reteste de acompanhamento do finding "URL Injection nos SDKs" reportado em
26/06/2026 (ver `abacatepay-audit-20260626.md`). O finding original era sobre
SDKs (Node/Python) interpolando `id` sem encoding em `/pixQrCode/check?id=`.
Este reteste confirma que o mesmo padrão de HTTP Parameter Pollution (HPP)
ainda funciona no BACKEND, em endpoints renomeados da API v2 atual.

## Descoberta de schema atual (a API mudou desde jun/2026)

Os endpoints antigos (`/pixQrCode/*`) não existem mais. A rota atual é
`/v2/transparents/*`. Para descobrir o schema certo sem adivinhar, puxar:

```bash
curl -s https://docs.abacatepay.com/llms-full.txt > /tmp/abacate_full.txt
grep -n "transparents/create" /tmp/abacate_full.txt
```

Body correto para criar um PIX de teste:
```json
{
  "method": "PIX",
  "data": { "amount": 100000, "description": "opcional" }
}
```
(NÃO é `{"amount": ..., "method": ...}` direto — `amount`/`description` ficam
dentro de `data`. Erro comum: mandar sem o wrapper `data` dá 422 "Value should
be one of 'object', 'object'".)

## PoC (rodado ao vivo, ambiente devMode/sandbox, chave própria)

1. Criar dois PIX com valores bem diferentes:
   - PIX_CARO: `amount: 100000` (R$1000,00) → `pix_char_XmKcr...`
   - PIX_BARATO: `amount: 100` (R$1,00) → `pix_char_xHKZd...`

2. Disparar o endpoint de simulação de pagamento com **dois `id` na query
   string**, caro primeiro, barato depois:
   ```
   POST /v2/transparents/simulate-payment?id=PIX_CARO&id=PIX_BARATO
   ```

3. Resultado observado: a API processa o **último** `id` da query string.
   - PIX_CARO permanece `PENDING` (nunca foi tocado)
   - PIX_BARATO passa a `PAID`

4. Mesmo padrão confirmado em `GET /v2/transparents/check?id=X&id=Y` — retorna
   os dados do ÚLTIMO id, não do primeiro.

5. Tentativa alternativa de HPP via body (`{"id": [caro, barato]}`) FALHOU
   com 422 "Expected property 'id' to be string but found: undefined" — o
   parser de JSON body é mais rígido que o de query string. A vulnerabilidade
   é especificamente no parsing de query params duplicados, não no body.

## Por que isso importa (e o limite honesto do achado)

- `simulate-payment` só existe em `devMode`. A doc oficial diz explicitamente:
  "Em produção este endpoint retorna erro." Logo, essa PoC específica não
  movimenta dinheiro real e não prova exploração em produção.
- O que ELA prova: a lógica de parsing de parâmetros duplicados no backend
  aceita/prioriza o último valor de forma inconsistente. Se o MESMO padrão
  existir em algum endpoint de produção que confirma pagamento ou libera
  saldo, seria explorável (isso não foi testado — testar exigiria dinheiro
  real e autorização explícita, que não temos).
- Reportar como: "HTTP Parameter Pollution confirmado em endpoints
  transparents/simulate-payment e transparents/check — mesma classe do
  finding de URL Injection de 26/06 nos SDKs, ainda não mitigada no backend.
  Recomendação: rejeitar/normalizar parâmetros de query duplicados (usar
  `req.query.id` como array e recusar, ou validar length===1) em todos os
  endpoints que aceitam `id` via query string."

## Status das 3 findings do relatório oficial (26/06/2026), reconfirmado 02/09

Rodando `scripts/reteste_abacatepay.py` (que já existia no projeto, em
`~/LIBERTUS/scripts/`):

| Finding | Status 02/09 |
|---|---|
| F1: Preço negativo aceito | CORRIGIDO (400/422) |
| F2: Quantidade negativa aceita | CORRIGIDO (400/422) |
| F3: URLs de callback perigosas (file://, localhost, javascript:) | CORRIGIDO (422) |

Ou seja: a AbacatePay corrigiu tudo que foi reportado formalmente. O HPP é um
achado NOVO, não coberto pelo relatório original — vale reportar separado.
