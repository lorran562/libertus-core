# Relatório de Segurança - AbacatePay API

**Data:** 26/06/2026  
**Pesquisador:** Lorran Gustavo  
**Contato:** [SEU_EMAIL_AQUI]

---

## Resumo

Durante testes na API v2 do AbacatePay utilizando minha própria chave de desenvolvimento, identifiquei falhas de validação de entrada que podem impactar a integridade dos dados e potencialmente a segurança da plataforma.

---

## Finding 1: Valores Monetários Negativos/Zero Aceitos

**Severidade:** Média  
**Endpoint:** `POST /v2/billing/create`

**Descrição:**  
A API aceita valores negativos e zero no campo `price` dos produtos, gerando cobranças com valores inválidos.

**Reprodução:**
```bash
curl -X POST "https://api.abacatepay.com/v2/billing/create" \
  -H "Authorization: Bearer [API_KEY]" \
  -H "Content-Type: application/json" \
  -d '{
    "frequency": "ONE_TIME",
    "methods": ["PIX"],
    "products": [{"externalId": "test", "name": "Produto", "quantity": 1, "price": -100}],
    "returnUrl": "https://exemplo.com",
    "completionUrl": "https://exemplo.com"
  }'
```

**Resultado:** Billing criado com sucesso, URL de pagamento gerada.

**Impacto:**  
- Cobranças com valores inválidos no sistema
- Possível manipulação de saldo/créditos dependendo da lógica de negócio

**Recomendação:** Validar `price > 0` no backend.

---

## Finding 2: Quantidade Negativa/Zero Aceita

**Severidade:** Baixa  
**Endpoint:** `POST /v2/billing/create`

**Descrição:**  
O campo `quantity` aceita valores negativos e zero.

**Reprodução:**  
Mesmo request acima com `"quantity": -5` ou `"quantity": 0`.

**Impacto:** Dados inconsistentes no sistema.

**Recomendação:** Validar `quantity > 0` e tipo inteiro.

---

## Finding 3: URLs de Callback Sem Validação

**Severidade:** Média-Alta  
**Endpoint:** `POST /v2/billing/create`

**Descrição:**  
Os campos `returnUrl` e `completionUrl` aceitam URLs potencialmente perigosas.

**URLs aceitas em testes:**
- `http://127.0.0.1:8080/` (localhost)
- `http://192.168.1.1/` (rede interna)
- `file:///etc/passwd` (protocolo file)
- `javascript:alert(1)` (javascript)

**Impacto:**  
- Se o servidor faz requests para essas URLs → SSRF (Server-Side Request Forgery)
- Se são redirecionamentos do usuário → Open Redirect

**Recomendação:**  
- Validar scheme (aceitar apenas `https://`)
- Bloquear IPs internos/localhost
- Whitelist de domínios se possível

---

## Pontos Positivos Observados

- Proteção adequada contra IDOR (não consegui acessar recursos de outras contas)
- IDs não sequenciais (dificulta enumeração)
- Autenticação obrigatória via header
- Separação de versões de API keys

---

## Disclaimer

Todos os testes foram realizados utilizando exclusivamente minha própria conta e chave de API em ambiente de desenvolvimento. Nenhum dado de outros usuários foi acessado ou comprometido.

Fico à disposição para esclarecer qualquer dúvida.

Atenciosamente,  
Lorran Gustavo
