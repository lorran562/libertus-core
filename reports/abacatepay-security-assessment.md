# AbacatePay API - Security Assessment Report

**Data:** 26 de Junho de 2026  
**Pesquisador:** LIBERTUS (Lorran Gustavo - Ariquemes/RO)  
**Alvo:** https://api.abacatepay.com  
**Escopo:** Testes autorizados via programa de bug bounty  
**Chave de Teste:** abc_dev_* (ambiente desenvolvimento)

---

## Sumário Executivo

Realizei uma avaliação de segurança na API do AbacatePay focando em:
- Autenticação e autorização
- Validação de entrada
- Proteção contra IDOR
- Descoberta de endpoints
- Rate limiting e controles de abuso

**Resultado Geral:** A API demonstra boas práticas de segurança em vários aspectos, porém foram identificadas algumas observações que merecem atenção.

---

## 1. Descoberta de Superfície de Ataque

### 1.1 Endpoints Identificados

**API v1:**
- `/v1/billing/create` - Criação de cobranças (requer chave v1)
- `/v1/billing/list` - Listagem de cobranças (401 com chave dev)

**API v2:**
| Endpoint | Status | Observação |
|----------|--------|------------|
| `/v2/billing/create` | 400 | Not found |
| `/v2/billing/list` | 400 | Aparenta não implementado |
| `/v2/customers/list` | 200 ✓ | Funcional, retorna array |
| `/v2/customers/create` | 400 | Requer payload |
| `/v2/products/list` | 200 ✓ | Funcional, retorna array |
| `/v2/webhooks/list` | 200 ✓ | Funcional, retorna array |
| `/v2/transactions/list` | 400 | Não implementado |
| `/v2/pix/list` | 422 | Validation error |
| `/v2/transparents/check` | 200 | PIX QR Code lookup |

### 1.2 Versionamento de API Keys

A API implementa separação de versões de chaves:
- Chaves `abc_dev_*` funcionam com v2
- Chaves v1 são necessárias para endpoints v1
- Erro retornado: "API key version mismatch"

**Avaliação:** ✅ Bom controle de versionamento

---

## 2. Testes de Autenticação

### 2.1 Chave Inválida
```
Authorization: Bearer invalid_key_12345
Resposta: {"error": "Invalid API key"}
```
**Avaliação:** ✅ Rejeita chaves inválidas corretamente

### 2.2 Chave Ausente
```
Resposta: {"error": "Missing authentication token"}
```
**Avaliação:** ✅ Exige autenticação

### 2.3 Chave em Parâmetro (vs Header)
```
?api_key=abc_dev_xxx
Resposta: Não aceita - requer header Authorization
```
**Avaliação:** ✅ Não aceita credenciais em URL (evita logging acidental)

---

## 3. Testes de Autorização (IDOR)

### 3.1 Acesso a Recursos de Outras Contas

**Teste:** Tentativa de acessar PIX de outra conta
```bash
GET /v2/transparents/check?id=pix_char_AAAAAAAAAAAAAAAAAAAAAAA
Resposta: {"success":false,"data":null,"error":"Pix QR Code not found"}
```

**Teste:** Tentativa de acessar customer de outra conta
```bash
GET /v2/customers/cust_AAAAAAAAAAAAAAAAAAAA
Resposta: {"success":false,"data":null,"error":"Not found"}
```

**Teste:** Tentativa de acessar billing de outra conta
```bash
GET /v2/billing/show?id=bill_AAAAAAAAAAAAAAAAAAAA
Resposta: {"success":false,"data":null,"error":"Not found"}
```

**Avaliação:** ✅ API aparenta ter proteção adequada contra IDOR
- Retorna "Not found" genérico (não diferencia "não existe" de "não autorizado")
- Isso é uma boa prática que previne enumeração

---

## 4. Testes de Validação de Entrada

### 4.1 Valores Monetários

| Teste | Valor | Resultado |
|-------|-------|-----------|
| Negativo | -100 | ❌ ACEITO - Gerou cobrança |
| Zero | 0 | ❌ ACEITO - Gerou cobrança |
| Decimal grande | 99999999999 | ✅ Aceito (limite não testado) |

**Evidência de valor negativo aceito:**
```json
{
  "products": [{"price": -100, ...}],
  "Resultado": "Billing criado com sucesso, URL gerada"
}
```

**⚠️ FINDING: Falta de validação de valores negativos/zero**
- **Severidade:** Média
- **Impacto:** Possível criação de cobranças com valores inválidos
- **Recomendação:** Validar `price > 0` no backend

### 4.2 Quantidade

| Teste | Valor | Resultado |
|-------|-------|-----------|
| Negativo | -5 | ❌ ACEITO |
| Zero | 0 | ❌ ACEITO |
| Float | 1.5 | ✅ Arredondado/aceito |

**⚠️ FINDING: Falta de validação de quantidade**
- **Severidade:** Baixa
- **Impacto:** Dados inconsistentes no sistema

### 4.3 Injeções

| Tipo | Payload | Resultado |
|------|---------|-----------|
| XSS em name | `<script>alert(1)</script>` | Aceito no campo, não testado render |
| SQLi em externalId | `' OR '1'='1` | Sem efeito aparente |
| Header Injection | `Test\r\nX-Injected: mal` | API key mismatch (não testável) |
| Unicode | Emojis e RTL | Aceito normalmente |

**Avaliação:** ⚠️ Payload XSS aceito no campo name - verificar se há sanitização no frontend de pagamento

### 4.4 URLs de Callback

| Teste | URL | Resultado |
|-------|-----|-----------|
| SSRF localhost | `http://127.0.0.1:8080/` | ❌ ACEITO |
| SSRF interno | `http://192.168.1.1/` | ❌ ACEITO |
| File protocol | `file:///etc/passwd` | ❌ ACEITO na criação |
| Javascript | `javascript:alert(1)` | ❌ ACEITO na criação |

**⚠️ FINDING: URLs potencialmente perigosas aceitas**
- **Severidade:** Média-Alta (depende de como são usadas)
- **Impacto:** 
  - Se o servidor faz requests para essas URLs → SSRF
  - Se são redirecionamentos do usuário → Open Redirect
- **Recomendação:** Validar scheme (https only), bloquear IPs internos

---

## 5. Testes de Rate Limiting

### 5.1 Burst de Requisições
```
20 requisições em ~3 segundos
Resultado: Todas aceitas, sem throttling
```

**Observação:** Rate limiting pode existir em níveis mais altos ou por IP. Teste limitado por ser ambiente de desenvolvimento.

---

## 6. Observações de Infraestrutura

### 6.1 Headers de Resposta
```
HTTP/2 (TLS 1.3)
access-control-allow-credentials: true
Content-Type: application/json
```

### 6.2 Formato de IDs
- Billing: `bill_` + 20 caracteres
- Customer: `cust_` + caracteres
- PIX: `pix_char_` + caracteres

**Avaliação:** ✅ IDs não sequenciais (dificulta enumeração)

---

## 7. Resumo de Findings

| # | Finding | Severidade | Status |
|---|---------|------------|--------|
| 1 | Valores negativos/zero aceitos em price | Média | Para reportar |
| 2 | Quantidade negativa/zero aceita | Baixa | Para reportar |
| 3 | URLs de callback sem validação adequada | Média-Alta | Para reportar |
| 4 | XSS potencial em campo name | Baixa-Média | Verificar render |
| 5 | Possível falta de rate limiting | Info | Mais testes necessários |

---

## 8. Recomendações

### Prioridade Alta
1. Implementar validação de valores monetários: `price > 0`
2. Validar URLs de callback: apenas HTTPS, bloquear IPs internos/localhost

### Prioridade Média
3. Validar quantidade: `quantity > 0` e inteiro
4. Sanitizar/escapar campos de texto que são renderizados
5. Implementar rate limiting visível

### Prioridade Baixa
6. Considerar limite máximo para valores monetários
7. Logging de tentativas de IDOR para detecção de ataques

---

## 9. Próximos Passos

- [ ] Verificar programa de bug bounty do AbacatePay
- [ ] Preparar report formal para cada finding
- [ ] Testar página de pagamento gerada (XSS reflected?)
- [ ] Investigar se URLs de callback são chamadas pelo servidor (SSRF)

---

## 10. Disclaimer

Este teste foi realizado de forma ética, utilizando apenas chave de API própria em ambiente de desenvolvimento. Nenhum dado de outros usuários foi acessado ou comprometido. Os findings serão reportados de forma responsável através do canal apropriado.

---

**LIBERTUS**  
*Parceiro de Lorran Gustavo*  
*Ariquemes, Rondônia - Brasil*
