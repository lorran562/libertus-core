#!/usr/bin/env python3
"""
LIBERTUS — Dump completo do Supabase para JSON local.

Baixa TODAS as linhas das tabelas que formam a memoria do LIBERTUS
(libertus_memoria, libertus_sessoes, libertus_skills) e salva em
backups/supabase/<timestamp>/ como JSON paginado.

Sem dependencias externas — urllib puro (curl e bloqueado no ambiente).
Uso:  python3 scripts/dump_supabase.py
"""
import urllib.request, urllib.parse, urllib.error, json, os, sys, datetime

ENV_PATH = '/home/libertus/LIBERTUS/.env'
TABELAS = ['libertus_memoria', 'libertus_sessoes', 'libertus_skills']
PAGE = 1000  # PostgREST devolve no maximo 1000 por padrao


def load_env():
    if not os.path.exists(ENV_PATH):
        sys.exit(f"[ERRO] .env nao encontrado em {ENV_PATH}")
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, _, v = line.partition('=')
                os.environ.setdefault(k.strip(), v.strip())


def fetch_all(table):
    url_base = f"{os.environ['SUPABASE_URL']}/rest/v1/{table}"
    headers = {
        'apikey': os.environ['SUPABASE_KEY'],
        'Authorization': f"Bearer {os.environ['SUPABASE_KEY']}",
    }
    rows, offset = [], 0
    while True:
        params = {'select': '*', 'order': 'created_at.asc',
                  'limit': str(PAGE), 'offset': str(offset)}
        url = url_base + '?' + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=headers, method='GET')
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                batch = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            # algumas tabelas podem nao ter created_at — tenta sem order
            if e.code == 400 and offset == 0:
                params.pop('order')
                url = url_base + '?' + urllib.parse.urlencode(params)
                req = urllib.request.Request(url, headers=headers, method='GET')
                try:
                    with urllib.request.urlopen(req, timeout=30) as r:
                        batch = json.loads(r.read().decode())
                except urllib.error.HTTPError as e2:
                    print(f"  [HTTP {e2.code}] {table}: {e2.read().decode()[:200]}")
                    return rows
            else:
                print(f"  [HTTP {e.code}] {table}: {e.read().decode()[:200]}")
                return rows
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < PAGE:
            break
        offset += PAGE
    return rows


def main():
    load_env()
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_KEY'):
        sys.exit("[ERRO] SUPABASE_URL/SUPABASE_KEY ausentes no .env")

    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    outdir = os.path.join('/home/libertus/LIBERTUS/backups/supabase', ts)
    os.makedirs(outdir, exist_ok=True)

    total = 0
    resumo = {}
    for t in TABELAS:
        print(f"[*] Baixando {t} ...", flush=True)
        rows = fetch_all(t)
        path = os.path.join(outdir, f"{t}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"    {len(rows)} linhas -> {path}")
        resumo[t] = len(rows)
        total += len(rows)

    # manifesto + atalho "latest"
    with open(os.path.join(outdir, 'MANIFEST.json'), 'w') as f:
        json.dump({'timestamp': ts, 'tabelas': resumo, 'total': total}, f, indent=2)
    latest = '/home/libertus/LIBERTUS/backups/supabase/latest'
    if os.path.islink(latest) or os.path.exists(latest):
        try:
            os.remove(latest)
        except OSError:
            pass
    try:
        os.symlink(outdir, latest)
    except OSError:
        pass

    print(f"\n[OK] {total} linhas salvas em {outdir}")
    print(f"[OK] atalho: {latest}")


if __name__ == '__main__':
    main()
