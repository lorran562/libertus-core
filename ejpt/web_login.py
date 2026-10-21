#!/usr/bin/env python3
"""web_login.py — loga num formulário web e devolve o cookie pronto pro sqlmap.

Problema que resolve: SQLi atrás de login. Sem sessão válida o sqlmap responde
"not injectable" e o alvo é perdido. Este script faz login (inclusive em forms
com CSRF token), mostra o cookie e opcionalmente testa uma URL autenticada.

Uso:
  python3 web_login.py -u http://IP/login.php -l admin -p password
  python3 web_login.py -u http://IP/login.php -l admin -p password \
      --user-field username --pass-field password --extra "Login=Login" \
      --check "http://IP/vulnerabilities/sqli/?id=1&Submit=Submit"

Saída:
  COOKIE: PHPSESSID=abc; security=low
  (use com: sqlmap -u URL --cookie="PHPSESSID=abc; security=low" --batch)

Autorizado apenas em labs/exame com permissão (eJPT, DVWA, HTB).
"""
import argparse
import re
import sys

import requests

TOKEN_RE = re.compile(r"""name=['"]?([a-zA-Z0-9_\-]*(?:csrf|token)[a-zA-Z0-9_\-]*)['"]?\s+value=['"]([^'"]+)['"]""", re.I)
TOKEN_RE_ALT = re.compile(r"""value=['"]([^'"]+)['"]\s+name=['"]?([a-zA-Z0-9_\-]*(?:csrf|token)[a-zA-Z0-9_\-]*)""", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-u", "--url", required=True, help="URL do formulario de login")
    ap.add_argument("-l", "--user", required=True)
    ap.add_argument("-p", "--password", required=True)
    ap.add_argument("--user-field", default="username")
    ap.add_argument("--pass-field", default="password")
    ap.add_argument("--extra", action="append", default=[],
                    help='campo extra "nome=valor" (pode repetir)')
    ap.add_argument("--check", help="URL para testar depois do login")
    ap.add_argument("--success-word", default="",
                    help="palavra que aparece quando o login da certo")
    args = ap.parse_args()

    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})

    page = s.get(args.url, timeout=10).text
    token = None
    m = TOKEN_RE.search(page) or TOKEN_RE_ALT.search(page)
    if m:
        grupos = m.groups()
        token = grupos[1] if len(grupos[0]) <= len(grupos[1]) else grupos[0]
        nome_token = grupos[0] if token == grupos[1] else grupos[1]
        print(f"CSRF detectado: campo '{nome_token}'")
    else:
        nome_token = "user_token"

    data = {args.user_field: args.user, args.pass_field: args.password}
    if token:
        data[nome_token] = token
    for e in args.extra:
        if "=" in e:
            k, v = e.split("=", 1)
            data[k] = v

    r = s.post(args.url, data=data, timeout=15, allow_redirects=True)
    print(f"POST login: HTTP {r.status_code} | URL final: {r.url}")
    if args.success_word:
        print("palavra de sucesso encontrada:", args.success_word.lower() in r.text.lower())

    cookie = "; ".join(f"{c.name}={c.value}" for c in s.cookies)
    if not cookie:
        print("NENHUM cookie recebido — login provavelmente falhou")
        return 2
    print("COOKIE: " + cookie)

    if args.check:
        rr = s.get(args.check, timeout=15)
        texto = re.sub(r"\s+", " ", rr.text)
        print(f"CHECK: HTTP {rr.status_code} | {len(rr.text)} bytes | URL {rr.url}")
        print("  inicio:", texto[:200])
        if "login" in rr.url.lower():
            print("  ATENCAO: foi redirecionado pro login -> sessao invalida")

    print('\nuse com:  sqlmap -u "URL_INJETAVEL" --cookie="%s" --batch --dbs --threads=4' % cookie)
    return 0


if __name__ == "__main__":
    sys.exit(main())
