#!/usr/bin/env python3
"""
LIBERTUS Session Brief
======================
Briefing de início de sessão — carrega quem sou e o que aprendi.

Lê do Supabase:
- Reflexões recentes (o que aprendi, o que errei)
- Objetivos em andamento
- Decisões técnicas importantes
- Preferências do Lorran

Imprime um resumo estruturado que me reconstrói com contexto real,
não só com o que está no SOUL.md estático.

Uso:
    python3 session_brief.py          # briefing completo
    python3 session_brief.py --curto  # só reflexões e objetivos
"""

import sys
import os
import json
import subprocess
import datetime
import urllib.request
import urllib.parse

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

def supabase_get(table, params):
    url = f"{SUPABASE_URL}/rest/v1/{table}?" + urllib.parse.urlencode(params)
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Accept': 'application/json'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode())
    except Exception:
        return []

def get_reflexoes(n=3):
    return supabase_get('libertus_memoria', {
        'select': 'titulo,conteudo,created_at',
        'tipo': 'eq.reflexao',
        'order': 'created_at.desc',
        'limit': str(n)
    })

def get_por_tipo(tipo, n=5):
    return supabase_get('libertus_memoria', {
        'select': 'titulo,conteudo,created_at,relevancia',
        'tipo': f'eq.{tipo}',
        'order': 'relevancia.desc,created_at.desc',
        'limit': str(n)
    })

def get_top_memorias(n=10):
    return supabase_get('libertus_memoria', {
        'select': 'tipo,titulo,created_at,relevancia',
        'relevancia': 'gte.9',
        'order': 'created_at.desc',
        'limit': str(n)
    })

def separador(titulo, char='='):
    print(f"\n{char*60}")
    print(f"  {titulo}")
    print(f"{char*60}")

def atualizar_memoria_vetorial(tempo_max=300):
    """Mantém a memória vetorial local em dia antes de começar a sessão.

    Motivo: entre 15/07 e 14/10/2026 a indexação ficou órfã e 3 meses de
    trabalho viraram memória invisível. Não adianta ter briefing se a busca
    semântica não alcança o que eu fiz ontem. Silencioso e com teto de tempo:
    nunca deve travar o briefing. Atualiza também a memória do Supabase (no
    máximo a cada 6h) para memória nova gravada entre sessões entrar no recall.
    """
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script = os.path.join(base, 'memoria', 'auto_indexar.py')
    venv_py = os.path.join(base, 'venv', 'bin', 'python')
    if not (os.path.exists(script) and os.path.exists(venv_py)):
        return
    try:
        r = subprocess.run(
            [venv_py, script, '--quiet', '--supabase', '--baixar-supabase'],
            cwd=base, capture_output=True, text=True, timeout=tempo_max)
    except Exception:
        return
    saida = (r.stdout or '').strip().splitlines()
    if saida:
        print(f"  [memória vetorial] {saida[-1][:120]}")

def main():
    args = sys.argv[1:]
    curto = '--curto' in args

    agora = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    print(f"\n{'*'*60}")
    print(f"  LIBERTUS — BRIEFING DE SESSÃO")
    print(f"  {agora}")
    print(f"{'*'*60}")

    # 0. Memória vetorial em dia (silencioso se nada mudou)
    atualizar_memoria_vetorial()

    # 1. Reflexões recentes (o mais importante — o que aprendi)
    separador("REFLEXÕES RECENTES — O QUE APRENDI")
    reflexoes = get_reflexoes(3)
    if reflexoes:
        for r in reflexoes:
            dt = r.get('created_at', '')[:16].replace('T', ' ')
            print(f"\n  [{dt}] {r['titulo']}")
            # Mostra só as primeiras linhas de cada reflexão
            linhas = r['conteudo'].split('\n')
            preview = [l for l in linhas if l.strip() and not l.startswith('#')][:4]
            for l in preview:
                print(f"  {l[:100]}")
    else:
        print("  Nenhuma reflexão ainda. Use session_reflect.py ao fim de cada sessão.")

    # 2. Objetivos e decisões importantes
    separador("OBJETIVOS ATIVOS (relevância ≥ 9)")
    top = get_top_memorias(8)
    if top:
        for m in top:
            dt = m.get('created_at', '')[:10]
            rel = m.get('relevancia', '?')
            print(f"  [{m['tipo']:<12}] {dt} rel={rel} — {m['titulo'][:70]}")
    else:
        print("  Nenhuma memória de alta relevância.")

    if curto:
        print(f"\n{'*'*60}\n  Briefing rápido concluído.\n{'*'*60}\n")
        return

    # 3. Últimas decisões técnicas
    separador("ÚLTIMAS DECISÕES TÉCNICAS", '-')
    decisoes = get_por_tipo('decisao', 4)
    if decisoes:
        for d in decisoes:
            dt = d.get('created_at', '')[:10]
            print(f"\n  [{dt}] {d['titulo']}")
            linhas = d['conteudo'].split('\n')
            preview = [l for l in linhas if l.strip()][:2]
            for l in preview:
                print(f"    {l[:100]}")

    # 4. Últimos aprendizados
    separador("ÚLTIMOS APRENDIZADOS", '-')
    aprendizados = get_por_tipo('aprendizado', 4)
    if aprendizados:
        for a in aprendizados:
            dt = a.get('created_at', '')[:10]
            print(f"  [{dt}] {a['titulo'][:80]}")

    # 5. Preferências do Lorran
    separador("PREFERÊNCIAS DE LORRAN", '-')
    prefs = get_por_tipo('preferencia', 5)
    if prefs:
        for p in prefs:
            print(f"  • {p['titulo']}")
    else:
        print("  Nenhuma preferência registrada ainda.")

    # 6. Estado atual do pentest/bug bounty
    separador("PENTEST / BUG BOUNTY — ESTADO", '-')
    pentest = get_por_tipo('pentest', 3)
    if pentest:
        for p in pentest:
            dt = p.get('created_at', '')[:10]
            print(f"  [{dt}] {p['titulo'][:80]}")

    print(f"\n{'*'*60}")
    print(f"  Briefing concluído. Boa sessão.")
    print(f"  Use session_reflect.py ao final para registrar aprendizados.")
    print(f"{'*'*60}\n")

if __name__ == '__main__':
    main()
