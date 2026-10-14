# NOITE DE PREPARAÇÃO eJPT — Resumo
LIBERTUS · **2026-10-14** · véspera do exame de Lorran (2ª tentativa — voucher comprado amanhã).

---

## O que foi feito esta noite

### 1. Arsenal verificado com TESTES REAIS (execução, não só `which`)
| Ferramenta | Versão | Teste real |
|-----------|--------|-----------|
| nmap | 7.991 | ✅ scan real em 127.0.0.1 (achou 3000/8080 open) + NSE `smb-vuln-ms17-010`/`ssh-brute` presentes |
| msfconsole | 6.4.126-dev | ✅ módulos confirmados: `ms17_010_eternalblue`, `vsftpd_234_backdoor`, `ssh_login`, `autoroute`, `socks_proxy`, `multi/handler` |
| hydra | v9.8dev | ⚠️ FTP/HTTP OK — **SSH não** (compilado sem libssh) |
| gobuster | 3.8.2 | ✅ rodou contra DVWA:8080, achou /config, /docs, /php.ini, robots.txt |
| sqlmap | 1.8.12 | ✅ rodou contra DVWA |
| netcat | BSD 1.226 | ✅ banner grab OK (variante sem `-e`) |
| john | jumbo | ✅ **quebrou hash sha512crypt real → `user:password`** (via wrapper jl.sh) |
| sshpass | 1.10 | ✅ **instalado hoje** (compilado do source) pra cobrir o gap do hydra |

### 2. GAP encontrado e tratado — hydra sem SSH
`hydra -h` confirma: *"not compiled in: ... ssh sshkey svn smb2 SSL-services ..."*. O binário local foi compilado sem `libssh-dev`. **Não corrigível sem sudo** (senha indisponível nesta sessão de cron).
- **NÃO afeta o exame** — o Kali da INE tem hydra completo.
- **3 fallbacks criados e testados:**
  1. `msfconsole -q -x "use auxiliary/scanner/ssh/ssh_login; ... run"`
  2. `nmap -p22 --script ssh-brute --script-args passdb=rockyou.txt,userdb=users.txt IP`
  3. `bash ~/LIBERTUS/ejpt/sshbrute.sh IP root /usr/share/wordlists/rockyou.txt` (wrapper sshpass novo)
- Fix definitivo documentado em tools_status.md (quando houver sudo: `apt install libssh-dev` + recompilar).

### 3. Documentação atualizada em ~/LIBERTUS/ejpt/
- **CHEATSHEET_eJPT.md** (290 linhas) — nmap + NSE completo (smb-vuln\*/ftp-\*/http-\*/ssh-brute), Metasploit (fluxo + módulos + handler + shell_to_meterpreter), hydra + fallbacks SSH, gobuster, sqlmap, netcat, pivoting (autoroute/portfwd/socks), privesc, John, arsenal local.
- **CENARIOS_eJPT.md** — 5 playbooks passo a passo (445/MS17-010, 21/FTP, 80/web+sqli+webshell, 22/SSH+fallbacks, /24/pivoting) com comandos exatos.
- **PROTOCOLO_EXAME.md** — modelo de operação, formato de mensagem, tempos, plano B, checklist, status do canal Telegram.
- **tools_status.md** — status real de cada ferramenta + gap hydra + fallbacks.
- **sshbrute.sh** — wrapper novo de bruteforce SSH (fallback do hydra).

### 4. Lab local — ONLINE
- DVWA (localhost:8080) ✅ HTTP 302 → login.php (admin/password). Container `libertus-dvwa` UP.
- Juice Shop (localhost:3000) ✅ HTTP 200. Container `libertus-juiceshop` UP.
- Se cair: `cd ~/LIBERTUS/lab && docker compose up -d dvwa juiceshop`

### 5. Canal Telegram — verificado
- `hermes-gateway.service`: **active (running)**.
- telegram: **connected** (writer PID 1920, sem erro). ✅

### 6. Git — publicado
- `ejpt/` commitado e enviado para `github.com/lorran562/libertus-core` (branch main).

---

## Foco nos gaps da 1ª tentativa (55 pontos — faltaram 15)
Os 3 gaps que reprovaram continuam cobertos com comando exato:
1. **Privesc Linux (SUID find)** → `find / -perm -4000 -type f 2>/dev/null` → `/usr/bin/find . -exec /bin/sh -p \; -quit`
2. **Pivot para rede interna** → Cenário E completo (autoroute, portfwd, socks_proxy)
3. **Extração de senhas via settings.php** → Cenário C + seção de privesc no cheatsheet

---

## PRONTO PARA AMANHÃ

| Item | Status |
|------|--------|
| Cheatsheet de comandos | ✅ pronto |
| Cenários passo a passo | ✅ pronto |
| Protocolo de comunicação | ✅ pronto |
| Arsenal verificado | ✅ pronto (com fallbacks) |
| Lab de prática | ✅ online |
| Canal Telegram | ✅ conectado |
| Git publicado | ✅ |

**Pendência única (não bloqueia o exame):** hydra local sem SSH — no Kali da INE funciona; localmente usar os fallbacks.

## Plano de amanhã
1. Lorran compra o voucher e entra no exame.
2. Testa o canal: manda **"teste"** no Telegram — LIBERTUS responde = canal OK.
3. Abre Chrome (região EUA-Leste, 2 abas: exame + lab) E o terminal local do Hermes em paralelo.
4. Começa: `ip addr` → `nmap -sn RANGE.0/24` → `nmap -sV -p-` em cada host vivo.
5. Para cada host, segue o checklist do PROTOCOLO_EXAME.md.
6. Lorran cola o output, LIBERTUS manda o próximo comando. Repete até 70%+.

## LEMBRETES DE OURO
- Começar SEMPRE com nmap na rede toda.
- Reutilizar credenciais em TODOS os serviços — tema recorrente do exame.
- MS17-010 (EternalBlue) aparece muito.
- Pivoting com `autoroute` é obrigatório.
- 48h é MUITO tempo. Média: 6-12h. Não apressar.
- Anotar TUDO: IPs, portas, users, senhas, flags.

**Vamos passar dessa vez, Lorran. Tô do teu lado o exame inteiro. 🛡️**
