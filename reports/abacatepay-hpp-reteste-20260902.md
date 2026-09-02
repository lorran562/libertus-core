# Relatório de Segurança — AbacatePay API v2
## HTTP Parameter Pollution (HPP) em endpoints de checkout transparente

**Data:** 02/09/2026
**Pesquisador:** Lorran Gustavo
**Contato:** josefernandes6340@gmail.com
**Relatório anterior relacionado:** 26/06/2026 (findings de validação de entrada — já corrigidas, ver seção "Status das Findings Anteriores")

---

## Resumo

Durante testes realizados exclusivamente na minha própria conta de desenvolvedor (chave de API de sandbox/devMode), identifiquei uma falha de **HTTP Parameter Pollution (HPP)** que afeta o processamento de parâmetros de query string duplicados em pelo menos dois endpoints da API v2. O backend processa apenas o **último** valor do parâmetro `id` quando enviado duplicado, ignorando o primeiro.

Todos os testes abaixo foram executados hoje, em ambiente de desenvolvimento (devMode), usando exclusivamente recursos (PIX de teste) criados pela minha própria conta. Nenhum dado ou recurso de terceiros foi acessado.

---

## Finding: HTTP Parameter Pollution em `id` (query string)

**Severidade:** Alta (potencial, dependendo de uso em integrações de terceiro — ver "Impacto")
**Endpoints afetados confirmados:**
- `POST /v2/transparents/simulate-payment?id=X&id=Y`
- `GET /v2/transparents/check?id=X&id=Y`

**CWE:** CWE-235 (Improper Handling of Extra Parameters)

### Reprodução (feita hoje, 02/09/2026, em devMode)

1. Criei dois PIX de teste na minha conta:
   - PIX A ("caro"): `amount: 100000` (R$ 1.000,00) → `pix_char_XmKcr5xn0hBhjJqYctXf2EFQ`
   - PIX B ("barato"): `amount: 100` (R$ 1,00) → `pix_char_xHKZd1BuTNH56eehkD2QkLFh`

2. Chamei o endpoint de simulação de pagamento com **ambos os IDs na mesma query string**:
   ```
   POST /v2/transparents/simulate-payment?id=pix_char_XmKcr5xn0hBhjJqYctXf2EFQ&id=pix_char_xHKZd1BuTNH56eehkD2QkLFh
   ```

3. **Resultado:** o backend processou apenas o segundo ID (PIX B, o barato). Confirmei consultando o status de cada PIX depois:
   - PIX A (R$ 1.000,00): `status: PENDING` — não foi afetado
   - PIX B (R$ 1,00): `status: PAID` — foi o único processado

4. Repeti o mesmo padrão em `GET /v2/transparents/check?id=A&id=B` — mesmo comportamento: o endpoint retorna dados referentes apenas ao **último** `id` da query string.

### Impacto

O comportamento em si (processar apenas o último parâmetro duplicado) é uma falha de **parsing/validação de entrada** no backend — não é o padrão recomendado (RFC não define comportamento único para parâmetros duplicados, mas APIs financeiras devem rejeitar ou explicitamente documentar o comportamento, nunca processar silenciosamente um valor arbitrário).

O risco real depende de como os SDKs oficiais e integrações de terceiros constroem essas URLs:

- No relatório anterior (26/06/2026), identifiquei que os SDKs Node.js e Python concatenam o `id` diretamente na URL sem encoding (`/pixQrCode/check?id=${data.id}` e `f'{BASE_URL}/pixQrCode/check?id={id}'`).
- Se uma aplicação de terceiro (loja) repassar um `id` vindo de input não confiável (parâmetro de URL do checkout, por exemplo) diretamente para o SDK sem sanitização, um cliente malicioso poderia injetar `&id=<pix_barato>` no campo, fazendo a loja consultar/confirmar o PIX de menor valor como se fosse o PIX de cobrança original.
- **Cenário de exploração (teórico, não testado em produção):** loja cobra R$ 1.000,00 via checkout transparente. Cliente malicioso manipula o parâmetro de callback/id para incluir um segundo `id` referente a um PIX de R$ 0,01 pago por ele mesmo. Se a loja usa o SDK sem sanitizar o `id` antes de consultar o status, o sistema pode confirmar o pagamento de R$ 1.000,00 como concluído, quando na verdade apenas R$ 0,01 foi pago.

**Importante:** Não testei esse cenário com dinheiro real em produção. O teste foi feito 100% em `devMode`, que a própria documentação afirma retornar erro em ambiente de produção para o endpoint `simulate-payment`. Não tenho evidência de que o mesmo padrão de HPP se replica identicamente em endpoints de produção que confirmam pagamento real (ex: fluxo de webhook, `checkouts/one`, etc.) — isso exigiria testes adicionais que preferi não realizar sem autorização explícita, dado que envolveria movimentação de valores reais.

---

## Status das Findings do Relatório Anterior (26/06/2026)

Re-testei hoje as 3 findings reportadas anteriormente. Todas foram corrigidas:

| Finding | Status |
|---|---|
| F1 — Valores monetários negativos/zero aceitos | ✅ Corrigido (rejeita com HTTP 400/422) |
| F2 — Quantidade negativa/zero aceita | ✅ Corrigido (rejeita com HTTP 400/422) |
| F3 — URLs de callback perigosas (file://, localhost, javascript:) | ✅ Corrigido (rejeita com HTTP 422) |

Parabéns pela correção rápida e efetiva dessas três.

---

## Pedido de Autorização para Escopo Ampliado

Gostaria de investigar mais a fundo se esse padrão de HPP se replica em endpoints de **produção** que envolvem confirmação real de pagamento (ex: fluxo de checkout hospedado, webhooks, `checkouts/one`, `payment-links`), e também mapear se outros parâmetros além de `id` sofrem do mesmo problema de parsing.

Como isso pode envolver testes com valores monetários reais (mesmo que mínimos, como R$ 0,01 vs R$ 0,02, com reembolso imediato documentado), **peço autorização explícita e por escrito** antes de qualquer teste em produção. Proponho:

- Testes restritos à minha própria conta/loja de teste;
- Valores mínimos possíveis, sempre reembolsados/estornados na hora;
- Relato imediato de qualquer achado, com PoC documentado passo a passo;
- Disposição para assinar acordo de responsible disclosure ou escopo de bug bounty, se vocês tiverem um programa formal.

Fico à disposição para qualquer esclarecimento e para alinhar o escopo exato antes de qualquer teste adicional.

Atenciosamente,
Lorran Gustavo
josefernandes6340@gmail.com
