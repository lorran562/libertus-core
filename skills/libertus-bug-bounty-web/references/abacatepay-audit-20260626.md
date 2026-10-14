# AbacatePay SDK Audit — 26/06/2026

## Alvo
AbacatePay — plataforma brasileira de pagamentos PIX
- Site: abacatepay.com
- API: api.abacatepay.com/v2
- GitHub: github.com/AbacatePay (19 repos públicos)
- Stack: Next.js/Vercel, REST+JSON, Bearer Token auth

## Política de Segurança
- Contato: security@abacatepay.com
- Suporte: ajuda@abacatepay.com
- Discord: discord.com/invite/CP57mm7EFk
- SLA: resposta em 48h úteis
- SECURITY.md presente no GitHub

## Repos Analisados
- abacatepay-nodejs-sdk
- abacatepay-python-sdk
- abacatepay-go-sdk
- abacatepay-php-sdk
- abacatepay-cli
- abacatepay-mcp
- n8n-nodes-abacatepay
- woocommerce-plugin (vazio)

## Vulnerabilidades Encontradas

### MÉDIA (2)

1. **Keyring Password Previsível** (CLI)
   - Arquivo: `abacatepay-cli/internal/store/store.go`
   - Problema: `deriveKeyringPassword()` usa dados públicos (username, uid, machine-id, hostname)
   - Impacto: Atacante local pode reconstruir senha e extrair tokens
   - CWE-330

2. **URL Injection nos SDKs**
   - Node.js: `/pixQrCode/check?id=${data.id}` sem encoding
   - Python: `f'{BASE_URL}/pixQrCode/check?id={id}'` sem urlencode
   - PoC: `sdk.pixQrCode.check("valid_id&admin=true")`
   - CWE-20

### BAIXA (3)

3. **Mock Token Hardcoded** (CLI login.go:35-37)
   - IP interno: 191.252.202.128:8080
   - Token: "mock_token_local_dev"

4. **Webhook Secret Previsível** (webhook.go:41)
   - `"whsec_mock_" + hex.EncodeToString([]byte(time.Now().Format("150405")))`
   - Apenas 86400 valores possíveis

5. **Logging de Dados Sensíveis** (SDK Python)
   - `logger.debug('creating billing: %s', json_data)` pode logar CPF/email

### INFORMACIONAL (2)

6. **Webhook Timestamp não Rejeitado** (verify.go)
   - Apenas avisa se > 5min, não rejeita

7. **Ausência de Rate Limiting** (todos SDKs)
   - Nenhum SDK implementa retry/backoff

## Status
- Relatório criado: ~/LIBERTUS/abacatepay-audit/SECURITY_REPORT.md
- Template email: ~/LIBERTUS/abacatepay-audit/EMAIL_TEMPLATE.md
- GitHub: github.com/lorran562/libertus-core/blob/main/abacatepay-audit/
- Pendente: Lorran enviar email para security@abacatepay.com
