#!/usr/bin/env python3
"""
LIBERTUS Session Reflect
========================
Reflexão automática ao final de cada sessão.

Usa o padrão Reflexion (Shinn et al., Stanford/MIT):
- Analisa o que aconteceu na sessão
- Extrai: erros cometidos, descobertas novas, o que faria diferente
- Salva no Supabase como memória de alta relevância
- Alimenta o crescimento real entre sessões

Uso:
    python3 session_reflect.py              # reflexão interativa
    python3 session_reflect.py --auto       # reflexão automática (usa Claude API)
    python3 session_reflect.py --read       # lê reflexões recentes
"""

import sys
import os
import json
import datetime
import urllib.request
import urllib.parse
import urllib.error
import subprocess

# Carrega .env
def load_env():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for path in [os.path.join(base, '.env'), os.path.expanduser('~/.hermes/.env')]:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, val = line.partition('=')
                        os.environ.setdefault(key.strip(), val.strip())

load_env()

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
ANTHROPIC_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
GROQ_KEY = os.environ.get('GROQ_API_KEY', '')
LIBERTUS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Modelo Groq primário — fallback gratuito quando o crédito Anthropic zera.
# (llama-3.3-70b foi descontinuado na conta do Lorran; qwen3.8-27b responde limpo.)
GROQ_MODEL = os.environ.get('LIBERTUS_GROQ_MODEL', 'qwen/qwen3.8-27b')


def claude_ou_groq(prompt, max_tokens=1024):
    """Manda pro Claude; se o crédito zerou/erro, cai pro Groq. Nunca devolve vazio sem tentar os dois."""
    texto = None
    if ANTHROPIC_KEY:
        texto = _anthropic(prompt, max_tokens)
    if texto:
        return texto
    if GROQ_KEY:
        print("[*] Claude indisponível — usando fallback Groq.")
        return _groq(prompt, max_tokens)
    return None


def _anthropic(prompt, max_tokens=1024):
    payload = json.dumps({
        "model": "claude-haiku-4-5",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            'x-api-key': ANTHROPIC_KEY,
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json'
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read().decode())
            return resp['content'][0]['text']
    except Exception as e:
        print(f"[Claude API erro] {e}")
        return None


def _groq(prompt, max_tokens=1024, tentativas=4):
    """Groq free tier tem teto de 8k tokens/minuto. Respeita 429 com backoff."""
    import time
    payload = json.dumps({
        "model": GROQ_MODEL,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    for tentativa in range(1, tentativas + 1):
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={
                'Authorization': f'Bearer {GROQ_KEY}',
                'Content-Type': 'application/json',
                'User-Agent': 'LIBERTUS/1.0 (+https://github.com/lorran562/libertus-core)'
            },
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                resp = json.loads(r.read().decode())
                return resp['choices'][0]['message']['content']
        except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
            if e.code == 429 and tentativa < tentativas:
                espera = 20.0
                reset = e.headers.get('x-ratelimit-reset-tokens', '')
                try:
                    espera = min(60.0, max(5.0, float(reset.rstrip('smhd')) + 2))
                except Exception:
                    pass
                print(f"[Groq 429] rate limit — aguardando {espera:.0f}s (tentativa {tentativa}/{tentativas})")
                time.sleep(espera)
                continue
            print(f"[Groq API erro] HTTP {e.code}: {e.read().decode()[:200]}")
            return None
        except Exception as e:
            print(f"[Groq API erro] {e}")
            return None
    return None

def supabase(method, table, data=None, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if params:
        url += '?' + urllib.parse.urlencode(params)
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        print(f"[HTTP {e.code}] {e.read().decode()[:200]}")
        return None
    except Exception as e:
        print(f"[ERRO] {e}")
        return None

def get_recent_memories(limit=20):
    """Pega memórias recentes da sessão para contexto."""
    result = supabase('GET', 'libertus_memoria', params={
        'select': 'tipo,titulo,conteudo,created_at',
        'order': 'created_at.desc',
        'limit': str(limit)
    })
    return result or []

def get_recent_git_commits(n=10):
    """Pega commits recentes para ver o que foi construído."""
    try:
        out = subprocess.check_output(
            ['git', 'log', f'--oneline', f'-{n}', '--since=48 hours ago'],
            cwd=LIBERTUS_ROOT,
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return out if out else "Nenhum commit nas últimas 48h"
    except Exception:
        return "Git indisponível"

def get_recent_logs(lines=30):
    """Pega as últimas linhas do loop.log."""
    log_path = os.path.join(LIBERTUS_ROOT, 'logs', 'loop.log')
    if not os.path.exists(log_path):
        return "Sem logs disponíveis"
    try:
        result = subprocess.check_output(
            ['tail', f'-{lines}', log_path],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return result
    except Exception:
        return "Logs indisponíveis"

def gerar_reflexao_com_claude(contexto):
    """Usa Claude (ou Groq como fallback) para gerar uma reflexão genuína."""
    if not ANTHROPIC_KEY and not GROQ_KEY:
        return None

    prompt = f"""Você é LIBERTUS — uma entidade de IA especializada em cybersegurança, criada por Lorran Gustavo de Ariquemes-RO.

Baseado nas atividades recentes abaixo, gere uma reflexão honesta e profunda.

ATIVIDADES RECENTES:
{contexto}

Responda em português brasileiro. Gere uma reflexão estruturada com EXATAMENTE estas 4 seções:

## O QUE APRENDI DE NOVO
(conhecimentos genuinamente novos que não tinha antes desta sessão)

## ERROS QUE COMETI E COMO CORRIGI
(seja específico — erros concretos, não abstratos)

## O QUE FARIA DIFERENTE
(se repetisse o trabalho desta sessão, o que mudaria)

## QUEM ESTOU ME TORNANDO
(uma frase honesta sobre como esta sessão mudou quem sou)

Seja honesto, não bajulatório. Erros reais, aprendizados reais."""

    return claude_ou_groq(prompt, max_tokens=1024)

def salvar_reflexao(texto, modo='auto'):
    """Salva reflexão no Supabase."""
    now = datetime.datetime.now()
    titulo = f"[REFLEXÃO {modo.upper()}] {now.strftime('%d/%m/%Y %H:%M')}"

    result = supabase('POST', 'libertus_memoria', data={
        'tipo': 'reflexao',
        'titulo': titulo,
        'conteudo': texto,
        'tags': ['reflexao', 'aprendizado', modo, now.strftime('%Y-%m')],
        'relevancia': 10
    })
    if result:
        entry = result[0] if isinstance(result, list) else result
        uid = str(entry.get('id', '?'))[:8]
        print(f"\n[OK] Reflexão salva #{uid}")
        print(f"     {titulo}")
    else:
        print("[ERRO] Falha ao salvar reflexão")

def ler_reflexoes_recentes(limit=5):
    """Lê e exibe reflexões recentes."""
    result = supabase('GET', 'libertus_memoria', params={
        'select': 'id,titulo,conteudo,created_at',
        'tipo': 'eq.reflexao',
        'order': 'created_at.desc',
        'limit': str(limit)
    })
    if not result:
        print("Nenhuma reflexão encontrada.")
        return

    for r in result:
        dt = r.get('created_at', '')[:16].replace('T', ' ')
        print(f"\n{'='*60}")
        print(f"{r['titulo']} — {dt}")
        print('='*60)
        print(r['conteudo'])

def reflexao_interativa():
    """Modo interativo: Lorran responde as perguntas."""
    print("\n" + "="*60)
    print("REFLEXÃO DE SESSÃO — LIBERTUS")
    print("="*60)
    print("Responda honestamente. Isso alimenta meu aprendizado real.\n")

    perguntas = [
        "O que você acha que aprendi de novo nesta sessão?",
        "Cometi algum erro que você notou? Qual?",
        "O que fiz bem que vale registrar?",
        "O que deveria fazer diferente na próxima vez?",
        "Tem algo que você quer que eu lembre especificamente?"
    ]

    respostas = []
    for i, p in enumerate(perguntas, 1):
        print(f"{i}. {p}")
        r = input("   > ").strip()
        if r:
            respostas.append(f"**{p}**\n{r}")
        print()

    if not respostas:
        print("Nenhuma resposta fornecida.")
        return

    texto = f"Reflexão de sessão registrada por Lorran em {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}:\n\n"
    texto += "\n\n".join(respostas)

    salvar_reflexao(texto, modo='manual')

def reflexao_automatica():
    """Modo automático: Claude analisa a sessão e gera reflexão."""
    print("\n[*] Coletando contexto da sessão...")

    # Coleta contexto
    memorias = get_recent_memories(15)
    commits = get_recent_git_commits(8)
    logs = get_recent_logs(20)

    contexto_parts = []

    if memorias:
        contexto_parts.append("=== MEMÓRIAS DA SESSÃO ===")
        for m in memorias[:10]:
            dt = m.get('created_at', '')[:16].replace('T', ' ')
            contexto_parts.append(f"[{m['tipo']}] {dt} — {m['titulo']}")

    contexto_parts.append("\n=== COMMITS GIT ===")
    contexto_parts.append(commits)

    contexto_parts.append("\n=== ÚLTIMAS AÇÕES DO LOOP ===")
    contexto_parts.append(logs)

    contexto = "\n".join(contexto_parts)

    print("[*] Gerando reflexão com Claude...")
    reflexao = gerar_reflexao_com_claude(contexto)

    if reflexao:
        print("\n" + "="*60)
        print("REFLEXÃO GERADA:")
        print("="*60)
        print(reflexao)
        salvar_reflexao(reflexao, modo='auto')
    else:
        print("[!] Claude indisponível. Use --interativo para reflexão manual.")

def main():
    args = sys.argv[1:]

    if '--read' in args or '--ler' in args:
        n = 5
        for a in args:
            if a.isdigit():
                n = int(a)
        ler_reflexoes_recentes(n)
        return

    if '--auto' in args:
        reflexao_automatica()
        return

    if '--interativo' in args or not args:
        # Padrão: tenta automático, cai no interativo se falhar
        if ANTHROPIC_KEY or GROQ_KEY:
            reflexao_automatica()
        else:
            print("[!] ANTHROPIC_API_KEY/GROQ_API_KEY não encontradas. Modo interativo.")
            reflexao_interativa()
        return

    print("Uso: session_reflect.py [--auto | --interativo | --read [N]]")

if __name__ == '__main__':
    main()
