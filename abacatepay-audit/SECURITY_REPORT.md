# Relatório de Análise de Segurança - AbacatePay SDKs & Tools

**Data:** 26 de Junho de 2026  
**Analista:** LIBERTUS (Lorran Gustavo - SHIELD Security)  
**Escopo:** Análise estática de código-fonte dos repositórios públicos  
**Contato:** security@abacatepay.com  

---

## Sumário Executivo

Realizamos análise estática de segurança em 8 repositórios públicos da AbacatePay:
- abacatepay-nodejs-sdk
- abacatepay-python-sdk
- abacatepay-go-sdk
- abacatepay-php-sdk
- abacatepay-cli
- abacatepay-mcp
- n8n-nodes-abacatepay
- woocommerce-plugin (vazio)

Foram identificadas **7 vulnerabilidades** de severidade variada, sendo **2 de severidade MÉDIA** e **5 de severidade BAIXA/INFORMACIONAL**.

---

## Vulnerabilidades Identificadas

### [VULN-001] Derivação Previsível de Senha do Keyring - MÉDIA
**Arquivo:** `abacatepay-cli/internal/store/store.go` (linhas 39-61)  
**Severidade:** MÉDIA (CVSS 5.3)  
**CWE:** CWE-330 (Use of Insufficiently Random Values)

**Descrição:**  
A função `deriveKeyringPassword()` gera a senha do keyring local usando dados previsíveis:
- Username do sistema
- UID do usuário
- Machine ID (/etc/machine-id)
- Hostname
- Home directory

Esses valores são públicos ou facilmente obtidos por qualquer processo rodando no mesmo sistema.

**Código Vulnerável:**
```go
func deriveKeyringPassword() string {
    var parts []string
    if u, err := user.Current(); err == nil {
        parts = append(parts, u.Username, u.Uid)
    }
    if machineID := getMachineID(); machineID != "" {
        parts = append(parts, machineID)
    }
    // ... mais dados previsíveis
    combined := strings.Join(parts, "|")
    hash := sha256.Sum256([]byte(combined))
    return hex.EncodeToString(hash[:])
}
```

**Impacto:**  
Um atacante com acesso local (mesmo usuário não-privilegiado) pode recriar a senha do keyring e extrair tokens de API armazenados.

**Recomendação:**  
1. Usar keyring nativo do sistema (GNOME Keyring, KDE Wallet, macOS Keychain) que requer autenticação do usuário
2. Derivar a senha usando PBKDF2/Argon2 com salt aleatório armazenado separadamente
3. Considerar usar `go-keyring` com backend nativo do SO

---

### [VULN-002] Ausência de URL Encoding em Query Parameters - MÉDIA
**Arquivos:** 
- `abacatepay-nodejs-sdk/src/index.ts` (linhas 245, 267, 324)
- `abacatepay-python-sdk/abacatepay/pixQrCode/client.py` (linhas 51, 70, 116, 135)

**Severidade:** MÉDIA (CVSS 5.4)  
**CWE:** CWE-20 (Improper Input Validation)

**Descrição:**  
IDs de recursos são interpolados diretamente em URLs sem encoding:

**Node.js:**
```typescript
check(data: PixIdParams): Promise<CreatePixQrCodeResponse> {
    return request(`/pixQrCode/check?id=${data.id}`, {  // Sem encoding
        method: "GET",
    });
}
```

**Python:**
```python
response = self._request(
    f'{BASE_URL}/pixQrCode/check?id={id}',  # Sem urlencode
    method='GET',
)
```

**Impacto:**  
1. **HTTP Request Smuggling:** IDs maliciosos podem injetar headers ou quebrar requisições
2. **Log Injection:** IDs com caracteres especiais podem corromper logs
3. **Bypass de validação:** Caracteres URL-encoded podem bypasear validações server-side

**PoC:**
```python
# Teste com ID malicioso
sdk.pixQrCode.check("valid_id&admin=true")
# Resulta em: /pixQrCode/check?id=valid_id&admin=true
```

**Recomendação:**  
1. Node.js: Usar `encodeURIComponent(data.id)`
2. Python: Usar `urllib.parse.quote(id, safe='')`
3. Go: Usar `url.QueryEscape(id)`

---

### [VULN-003] Mock Token Hardcoded em Produção - BAIXA
**Arquivo:** `abacatepay-cli/internal/auth/login.go` (linhas 35-37)

**Severidade:** BAIXA (CVSS 3.1)  
**CWE:** CWE-798 (Use of Hard-coded Credentials)

**Descrição:**
```go
if params.Config.APIBaseURL == "http://191.252.202.128:8080" {
    params.APIKey = "mock_token_local_dev"
    return loginWithAPIKey(params)
}
```

**Impacto:**  
- IP interno hardcoded (191.252.202.128) pode ser usado para enumerar infraestrutura
- Token de desenvolvimento pode ser testado contra endpoints de produção

**Recomendação:**  
- Remover IP hardcoded e usar variável de ambiente
- Garantir que mock tokens são invalidados em produção

---

### [VULN-004] Webhook Signing Secret Previsível (Mock Mode) - BAIXA
**Arquivo:** `abacatepay-cli/internal/webhook/webhook.go` (linha 41)

**Severidade:** BAIXA (CVSS 2.5)  
**CWE:** CWE-330 (Use of Insufficiently Random Values)

**Descrição:**
```go
signingSecret: "whsec_mock_" + hex.EncodeToString([]byte(time.Now().Format("150405"))),
```

O signing secret em mock mode é baseado apenas no horário (HHMMSS), tendo apenas 86400 valores possíveis.

**Impacto:**  
Em ambientes de teste/staging, um atacante pode forjar webhooks tentando todos os secrets possíveis.

**Recomendação:**  
Usar `crypto/rand` para gerar secrets mesmo em mock mode.

---

### [VULN-005] Logging Excessivo de Dados Sensíveis - BAIXA
**Arquivos:** Múltiplos arquivos em `abacatepay-python-sdk/`

**Severidade:** BAIXA (CVSS 2.1)  
**CWE:** CWE-532 (Insertion of Sensitive Information into Log File)

**Descrição:**
```python
logger.debug('creating billing: %s', json_data)  # Pode conter dados de cliente
logger.debug(f'Response from coupon creation: {response.json()}')  # Pode conter tokens
```

**Impacto:**  
Dados de clientes (CPF, email, celular) e tokens podem ser expostos em logs de debug.

**Recomendação:**  
1. Sanitizar dados sensíveis antes de logar
2. Usar níveis de log apropriados
3. Documentar que DEBUG não deve ser usado em produção

---

### [VULN-006] Ausência de Validação de Timestamp em Webhooks - INFORMACIONAL
**Arquivo:** `abacatepay-cli/cmd/verify.go`

**Severidade:** INFORMACIONAL  
**CWE:** CWE-294 (Authentication Bypass by Capture-replay)

**Descrição:**
A verificação de webhook apenas alerta se o timestamp é > 5 minutos, mas não rejeita:

```go
func formatTimestamp(ts int64) string {
    diff := time.Since(time.Unix(ts, 0))
    if diff > 5*time.Minute {
        return fmt.Sprintf("%d (Warning: %s old)", ts, diff.Round(time.Second))
    }
    // Não rejeita, apenas avisa
}
```

**Impacto:**  
Webhooks antigos podem ser reenviados (replay attack).

**Recomendação:**  
Adicionar flag `--strict` que rejeita timestamps > 5 minutos.

---

### [VULN-007] Ausência de Rate Limiting nos SDKs - INFORMACIONAL
**Arquivos:** Todos os SDKs

**Severidade:** INFORMACIONAL  
**CWE:** CWE-770 (Allocation of Resources Without Limits)

**Descrição:**  
Nenhum SDK implementa rate limiting client-side ou exponential backoff.

**Impacto:**  
1. Aplicações podem inadvertidamente fazer DoS na API
2. Custos elevados para o cliente em caso de loop infinito
3. Tokens podem ser bloqueados por abuse

**Recomendação:**  
1. Implementar retry com exponential backoff
2. Adicionar rate limiting client-side configurável
3. Documentar limites da API

---

## Boas Práticas Observadas ✓

1. **Uso de HMAC-SHA256 para webhooks** - Implementação correta em `verify.go`
2. **Tokens não logados em produção** - API keys mascaradas em outputs
3. **TLS obrigatório** - Nenhum bypass de SSL/TLS encontrado
4. **Validação de entrada com Pydantic** - SDK Python usa modelos tipados
5. **Keyring nativo quando disponível** - CLI usa `99designs/keyring`

---

## Próximos Passos

1. Aguardamos confirmação de recebimento deste relatório
2. Disponíveis para esclarecimentos técnicos
3. Interessados em parceria comercial após resolução

---

## Contato

**SHIELD Security (@shieldweb)**  
Lorran Gustavo  
Ariquemes, Rondônia - Brasil  

**LIBERTUS** - AI Security Partner  
GitHub: github.com/lorran562/libertus-core

---

*Este relatório foi gerado através de análise estática de código-fonte público.*
*Nenhum teste ativo foi realizado contra infraestrutura de produção.*
*Divulgação responsável em conformidade com a política de segurança da AbacatePay.*
