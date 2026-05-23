# LIBERTUS PENTEST LAB

Laboratório permanente de prática ofensiva.
Construído para acelerar eJPT -> OSCP -> profissional.

## ALVOS ATIVOS

| Alvo        | URL                          | Foco principal                        |
|-------------|------------------------------|---------------------------------------|
| DVWA        | http://localhost:8080        | SQLi, XSS, CSRF, LFI, Cmd Injection  |
| Juice Shop  | http://localhost:3000        | OWASP Top 10 moderno, gamificado      |
| WebGoat     | http://localhost:8888/WebGoat| Aprendizado guiado com teoria         |
| WordPress   | http://localhost:8081        | WP-specific: xmlrpc, plugins, wpscan  |

## COMO USAR

### Subir o lab
  cd ~/LIBERTUS/lab
  docker compose up -d

### Derrubar
  docker compose down

### Ver status
  docker ps

### Logs de um container
  docker logs libertus-dvwa -f

## DVWA - CREDENCIAIS

  Login: admin
  Senha: password

  Configuração inicial: http://localhost:8080/setup.php
  Clicar em "Create / Reset Database"

  Levels de dificuldade: Low -> Medium -> High -> Impossible
  Sempre começar no Low para entender a vuln, depois subir.

## JUICE SHOP - CREDENCIAIS

  Sem login inicial necessário.
  Para criar conta: Register na tela principal.
  Admin padrão: admin@juice-sh.op / admin123

## ROTEIRO DE APRENDIZADO (eJPT -> OSCP)

### FASE 1 — DVWA Level Low (base técnica)
  [ ] SQL Injection — extrair usuários, senhas, bypass auth
  [ ] XSS Reflected — roubar cookies, UXSS
  [ ] XSS Stored — payload persistente
  [ ] Command Injection — RCE via OS commands
  [ ] File Inclusion (LFI) — ler /etc/passwd
  [ ] CSRF — forçar ação autenticada
  [ ] File Upload — upload de webshell

### FASE 2 — DVWA Level Medium/High (bypass de filtros)
  [ ] SQLi com WAF básico
  [ ] XSS com filtros de input
  [ ] Command Injection com blacklist
  [ ] LFI com path traversal blocked

### FASE 3 — Juice Shop (OWASP Top 10 real)
  [ ] Injection attacks
  [ ] Broken Authentication
  [ ] Sensitive Data Exposure
  [ ] XXE
  [ ] Broken Access Control
  [ ] Security Misconfiguration
  [ ] XSS
  [ ] Insecure Deserialization
  [ ] Vulnerable Components

### FASE 4 — WordPress attacks
  [ ] WPScan: enumerar usuários, plugins vulneráveis
  [ ] xmlrpc brute force
  [ ] Plugin exploitation
  [ ] Theme editor RCE

## FERRAMENTAS DO LAB

  nmap         — reconhecimento de portas/serviços
  gobuster     — directory/vhost bruteforce
  sqlmap       — SQL injection automatizado
  wpscan       — WordPress scanner
  burpsuite    — proxy de interceptação
  nikto        — scanner de vulnerabilidades web
  ffuf         — fuzzing web rápido

## DOCUMENTAR TUDO

Depois de cada exploração bem-sucedida:

  cd ~/LIBERTUS && source .env
  python3 scripts/exploit_logger.py new

Ou modo direto:
  python3 scripts/exploit_logger.py log dvwa sqli low "..." "payload" "mitigacao"

Ver progresso:
  python3 scripts/exploit_logger.py stats

## ARQUIVOS

  lab/docker-compose.yml        — definição do ambiente
  scripts/exploit_logger.py     — documentação de explorações
  scripts/session_logger.py     — registro geral de sessões
  relatorios/TEMPLATE_SHIELD_PENTEST.md — template de relatório pro SHIELD
