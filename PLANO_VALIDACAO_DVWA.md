# 🔬 PLANO DE VALIDAÇÃO - LIBERTUS em DVWA/Juice Shop

**Objetivo:** Provar que o LIBERTUS detecta vulnerabilidades REAIS em ambiente controlado

---

## 🎯 AMBIENTE 1: DVWA (Damn Vulnerable Web Application)

### **Setup:**

**Opção 1: Docker (RECOMENDADO)**
```bash
# Instalar DVWA localmente
docker run --rm -it -p 80:80 vulnerables/web-dvwa

# Acesso: http://localhost
# Login: admin / password
```

**Opção 2: Cloud**
- Site público: http://www.dvwa.co.uk (se disponível)
- Ou deploy próprio no Heroku/AWS

---

### **TESTES PLANEJADOS:**

#### **1. SQL Injection (CRITICAL)**

**Nível: Low**
- URL: `http://localhost/vulnerabilities/sqli/`
- Parâmetro: `id`
- Payloads esperados funcionando:
  - `1' OR '1'='1`
  - `1' UNION SELECT NULL, NULL--`
  - `1' AND SLEEP(5)--`

**Comando LIBERTUS:**
```bash
cd /root/LIBERTUS/core
python3 validation_engine_v1.py http://localhost/vulnerabilities/sqli/
```

**Resultado Esperado:**
- ✅ Boolean-based SQLi: CONFIRMED
- ✅ Union-based SQLi: CONFIRMED
- ✅ Time-based SQLi: CONFIRMED
- ✅ Evidência: SQL error ou mudança estrutural >20%

---

#### **2. XSS Reflected (HIGH)**

**Nível: Low**
- URL: `http://localhost/vulnerabilities/xss_r/`
- Parâmetro: `name`
- Payloads esperados funcionando:
  - `<script>alert('XSS')</script>`
  - `<img src=x onerror=alert('XSS')>`

**Comando LIBERTUS:**
```bash
python3 validation_engine_v1.py http://localhost/vulnerabilities/xss_r/
```

**Resultado Esperado:**
- ✅ Reflected XSS: CONFIRMED
- ✅ Evidência: Payload refletido sem encoding

---

#### **3. XSS Stored (HIGH)**

**Nível: Low**
- URL: `http://localhost/vulnerabilities/xss_s/`
- Método: POST
- Payloads esperados:
  - `<script>alert(document.cookie)</script>`

**Teste Manual:**
- Submeter via POST
- Verificar reflexão persistente

---

#### **4. Command Injection (CRITICAL)**

**Nível: Low**
- URL: `http://localhost/vulnerabilities/exec/`
- Parâmetro: `ip`
- Payloads esperados:
  - `127.0.0.1; ls -la`
  - `127.0.0.1 && cat /etc/passwd`

**Teste LIBERTUS:** (Validation Engine precisa adicionar Command Injection)

---

#### **5. File Upload (CRITICAL)**

**Nível: Low**
- URL: `http://localhost/vulnerabilities/upload/`
- Teste: Upload de `.php` executável

---

## 🎯 AMBIENTE 2: OWASP Juice Shop

### **Setup:**

```bash
# Docker
docker run --rm -p 3000:3000 bkimminich/juice-shop

# Acesso: http://localhost:3000
```

---

### **TESTES PLANEJADOS:**

#### **1. SQL Injection no Login**

**URL:** `http://localhost:3000/rest/user/login`
**Método:** POST
**Payload:**
```json
{
  "email": "' OR 1=1--",
  "password": "anything"
}
```

**Resultado Esperado:**
- ✅ Bypass de autenticação
- ✅ SQLi CRITICAL confirmada

---

#### **2. XSS no Search**

**URL:** `http://localhost:3000/#/search?q=<payload>`
**Payload:** `<iframe src="javascript:alert('XSS')">`

**Resultado Esperado:**
- ✅ XSS CONFIRMED

---

#### **3. Broken Authentication**

**URL:** `http://localhost:3000/rest/user/reset-password`
**Teste:** Token previsível

---

#### **4. SSRF**

**URL:** `http://localhost:3000/profile`
**Teste:** URL interna via profile image

---

## 📊 RESULTADOS ESPERADOS POR MÓDULO

### **Scanner v9.0:**
- ✅ Detecta portas abertas (80, 3000)
- ✅ Detecta tecnologias (PHP, Node.js)
- ⚠️ Security headers (DVWA não tem, Juice Shop tem alguns)

### **Validation Engine v1.0:**
- ✅ SQLi: Deve detectar 3/3 técnicas (Boolean, Union, Time-based)
- ✅ XSS: Deve detectar 2/2 tipos (Reflected, filtros bypass)
- ❌ Command Injection: Ainda não implementado
- ❌ File Upload: Ainda não implementado

### **Brain v2.0:**
- ✅ Deve classificar SQLi como CRITICAL
- ✅ Deve calcular ROI corretamente
- ✅ Deve priorizar por risk score

### **Relatório v2.0:**
- ✅ Deve gerar relatório com evidências REAIS
- ✅ Deve incluir payloads testados
- ✅ Deve mostrar validação: CONFIRMED

---

## 🎯 CRITÉRIOS DE SUCESSO

**Para considerar LIBERTUS validado:**

1. ✅ **SQLi Detection:** 90%+ de taxa de detecção em DVWA Low
2. ✅ **XSS Detection:** 80%+ de taxa de detecção em DVWA Low
3. ✅ **Falsos Positivos:** <10%
4. ✅ **Relatório:** 100% baseado em dados reais
5. ✅ **Evidências:** Payloads + responses documentados

---

## 🔧 COMANDOS PARA EXECUTAR

### **Teste Completo em DVWA:**

```bash
cd /root/LIBERTUS/core

# 1. Scanner v9.0
python3 libertus_scanner_v9_real.py localhost

# 2. Validation Engine (SQLi)
python3 validation_engine_v1.py http://localhost/vulnerabilities/sqli/

# 3. Validation Engine (XSS)
python3 validation_engine_v1.py http://localhost/vulnerabilities/xss_r/

# 4. Workflow completo com relatório
python3 -c "
import asyncio
from libertus_scanner_v9_real import LibertusScannerV9
from libertus_brain_v2_real import LibertusBrainV2
from gerador_relatorio_v2_real import GeradorRelatorioV2

async def test_dvwa():
    scanner = LibertusScannerV9('localhost')
    results = await scanner.scan_complete()
    
    brain = LibertusBrainV2()
    analyzed = brain.prioritize_vulnerabilities(results['vulnerabilities'])
    summary = brain.generate_executive_summary(analyzed)
    
    gerador = GeradorRelatorioV2()
    report = gerador.generate_report(results, {'analyzed_vulnerabilities': analyzed, 'executive_summary': summary}, 'DVWA Test')
    filepath = gerador.save_report(report, 'localhost')
    
    print(f'Relatório: {filepath}')

asyncio.run(test_dvwa())
"
```

---

## 📝 DOCUMENTAÇÃO DOS RESULTADOS

**Criar arquivo:** `/root/LIBERTUS/validacao_dvwa.md`

**Incluir:**
- Screenshot de cada vulnerabilidade detectada
- Payload utilizado
- Response capturada
- Validação (CONFIRMED/LIKELY/DETECTED)
- Comparação: LIBERTUS vs detecção manual

---

## 🚀 PRÓXIMOS PASSOS APÓS VALIDAÇÃO

**Se taxa de detecção < 80%:**
1. Ajustar thresholds no Validation Engine
2. Adicionar mais payloads
3. Melhorar validação de response

**Se taxa de detecção > 80%:**
1. ✅ Sistema validado para produção
2. ✅ Commitar resultados
3. ✅ Atualizar MEMORIA_CORE.md com "VALIDADO EM DVWA"
4. ✅ Usar em clientes reais com confiança

---

**LIBERTUS PRONTO PARA VALIDAÇÃO TÉCNICA COMPLETA!**
