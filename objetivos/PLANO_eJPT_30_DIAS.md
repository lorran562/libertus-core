# PLANO eJPT — 30 DIAS
## Lorran Gustavo → Certificação eJPT em 30 dias

---

## O QUE É O EXAME

- 35 questões práticas em 48 horas (faz de casa, sem webcam)
- Para passar: 25/35 corretas (70%)
- Você hackeia máquinas virtuais reais para encontrar as respostas
- Custo do voucher: $200 USD (~R$1.050)
- Curso de preparação: **GRATUITO** em security.ine.com

---

## FERRAMENTAS QUE O EXAME COBRA

| Ferramenta   | Para quê                        | Já tem? |
|-------------|----------------------------------|---------|
| Nmap        | Escanear redes e serviços       | ✅ sim  |
| Metasploit  | Exploração de vulnerabilidades  | ✅ sim  |
| Hydra       | Brute force de senhas           | ✅ sim  |
| Gobuster    | Encontrar diretórios web        | ✅ sim  |
| SQLmap      | SQL Injection automático        | ✅ sim  |
| Netcat      | Shells e conexões               | ✅ sim  |
| John        | Quebrar hashes de senha         | verificar |

Já temos quase tudo. Só precisa praticar o uso.

---

## OS 30 DIAS — SEMANA A SEMANA

---

### SEMANA 1 — Reconhecimento e Enumeração (Dias 1-7)
**Objetivo:** Dominar Nmap e coleta de informações

**Todo dia:**
- 1 sala do DVWA (localhost:8080) ou TryHackMe
- Praticar Nmap em diferentes cenários

**Conteúdo:**
- Nmap: -sV, -sC, -A, -p-, --script
- Enumeração de serviços: FTP, SSH, HTTP, SMB
- DNS enumeration: nslookup, dig
- Gobuster para diretórios web
- Leitura: módulos 1-3 do curso PTS (gratuito na INE)

**Meta da semana:**
Conseguir mapear uma rede, identificar todos os serviços rodando, e listar diretórios de um site.

---

### SEMANA 2 — Exploração com Metasploit (Dias 8-14)
**Objetivo:** Usar Metasploit com confiança

**Conteúdo:**
- msfconsole: search, use, set, exploit, sessions
- MS17-010 (EternalBlue) — o mais cobrado no exame
- Exploits para FTP, SSH, SMB
- Payloads: meterpreter vs shell
- Post-exploitation: hashdump, sysinfo, getuid

**Prática no DVWA + Metasploitable:**
- Explorar vulnerabilidades encontradas na semana 1
- Conseguir shell em pelo menos 3 máquinas diferentes

**Meta da semana:**
Dado um alvo com serviços vulneráveis, conseguir shell root/admin em menos de 30 minutos.

---

### SEMANA 3 — Web Application + Senhas (Dias 15-21)
**Objetivo:** SQL Injection, brute force, autenticação

**Web (DVWA + Juice Shop em localhost:3000):**
- SQL Injection manual e com sqlmap
- XSS básico (refletido e armazenado)
- Directory traversal / LFI
- Autenticação: bypass e brute force
- Nikto para scanning automático

**Senhas:**
- Hydra: brute force SSH, FTP, HTTP login
- John the Ripper: quebrar hashes MD5, SHA
- Rockyou wordlist: usar e entender

**Meta da semana:**
Dado um site com login e banco de dados, extrair usuários e senhas em menos de 20 minutos.

---

### SEMANA 4 — Pivoting + Simulação do Exame (Dias 22-30)
**Objetivo:** Pivoting entre redes + simular o exame

**Pivoting (o mais difícil do eJPT):**
- O que é pivoting: comprometer máquina A para acessar rede B
- Metasploit routes: `route add`, `run autoroute`
- Port forwarding: `portfwd add`
- Proxychains com Metasploit

**Simulação do exame (dias 27-30):**
- Montar ambiente com múltiplas máquinas (Docker)
- Cronometrar: conseguir comprometer tudo em 8 horas
- Revisar tópicos onde errou
- Ler os módulos finais do PTS

**Meta da semana:**
Simular o exame completo uma vez. Se passar com 28+/35, está pronto.

---

## ROTINA DIÁRIA RECOMENDADA

```
30 min — Teoria (vídeo do curso PTS ou leitura)
60 min — Prática hands-on (DVWA, TryHackMe, ou lab próprio)
10 min — Anotar o que aprendeu no session_logger
```

Total: ~1h40 por dia. Realista para quem trabalha.

---

## ONDE ESTUDAR (GRATUITO)

1. **Curso PTS da INE** (material oficial do exame)
   security.ine.com → cria conta grátis → "Penetration Testing Student"

2. **TryHackMe** (prática gamificada)
   tryhackme.com → salas gratuitas: "Linux Fundamentals", "Network Services", "Metasploit"

3. **DVWA rodando agora:** http://localhost:8080
   Setup: acessa /setup.php, clica "Create Database", começa no nível Low

4. **Juice Shop rodando agora:** http://localhost:3000
   OWASP Top 10 interativo, melhor para web

---

## QUANTO CUSTA

| Item | Custo |
|------|-------|
| Curso PTS (preparação) | R$ 0 — GRATUITO |
| TryHackMe básico | R$ 0 — tem salas grátis |
| DVWA + Juice Shop | R$ 0 — já rodando |
| **Voucher do exame** | **~R$ 1.050 ($200 USD)** |

Só precisa pagar quando estiver pronto pra fazer o exame.

---

## DEPOIS DO eJPT

Com a certificação:
- SHIELD fecha contratos com mais credibilidade (clientes veem o certificado)
- Acesso a programas de bug bounty privados (pagam mais, menos concorrência)
- Base sólida para o OSCP (próximo passo para trabalho remoto na Irlanda)

---

## COMEÇAR HOJE

**Passo 1:** Cria conta grátis em security.ine.com
**Passo 2:** Acessa o curso "Penetration Testing Student"
**Passo 3:** Abre o DVWA em http://localhost:8080/setup.php e clica "Create Database"
**Passo 4:** Me fala quando terminar o dia 1 — monitoro seu progresso

---

*Plano criado por LIBERTUS — 23/05/2026*
*Baseado no conteúdo real do exame eJPT v2 (2025)*
