#!/usr/bin/env python3
"""
LIBERTUS Session Logger
Registro disciplinado de momentos importantes de cada sessão.
Salva no Supabase: decisões técnicas, erros resolvidos, preferências de Lorran.

Uso:
  python3 session_logger.py log "tipo" "titulo" "conteudo"
  python3 session_logger.py list [tipo]
  python3 session_logger.py search "termo"

Tipos: decisao, erro, preferencia, aprendizado, pentest, objetivo
"""

import sys
import os
import json
import datetime
import urllib.request
import urllib.parse

# Carrega .env do diretório do projeto
def load_env():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, val = line.partition('=')
                    os.environ.setdefault(key.strip(), val.strip())

load_env()

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
TABLE = 'libertus_memoria'

TIPOS_VALIDOS = ['decisao', 'erro', 'preferencia', 'aprendizado', 'pentest', 'objetivo', 'reflexao']

def supabase_request(method, path, data=None, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{path}"
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
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode())
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        err = e.read().decode()
        print(f"Erro HTTP {e.code}: {err}")
        return None
    except Exception as e:
        print(f"Erro: {e}")
        return None

def criar_tabela_se_nao_existe():
    """Verifica se tabela existe tentando um select."""
    result = supabase_request('GET', TABLE, params={
        'select': 'id',
        'limit': '1'
    })
    if result is None:
        print("""
AVISO: Tabela 'libertus_memoria' nao encontrada no Supabase.
Crie ela com este SQL no Supabase Dashboard > SQL Editor:

CREATE TABLE libertus_memoria (
  id          BIGSERIAL PRIMARY KEY,
  tipo        TEXT NOT NULL,
  titulo      TEXT NOT NULL,
  conteudo    TEXT NOT NULL,
  sessao_id   TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  tags        TEXT[]
);

CREATE INDEX idx_libertus_memoria_tipo ON libertus_memoria(tipo);
CREATE INDEX idx_libertus_memoria_created ON libertus_memoria(created_at DESC);
""")
        return False
    return True

def log_entry(tipo, titulo, conteudo, tags=None, relevancia=7):
    if tipo not in TIPOS_VALIDOS:
        print(f"Tipo invalido. Use: {', '.join(TIPOS_VALIDOS)}")
        sys.exit(1)
    
    if not criar_tabela_se_nao_existe():
        sys.exit(1)
    
    # Schema real da tabela libertus_memoria: titulo, conteudo, tipo, tags, relevancia
    data = {
        'tipo': tipo,
        'titulo': titulo,
        'conteudo': conteudo,
        'tags': tags or [],
        'relevancia': relevancia,
    }
    
    result = supabase_request('POST', TABLE, data=data)
    if result:
        entry = result[0] if isinstance(result, list) else result
        print(f"[OK] Registrado #{entry.get('id', '?')} [{tipo}] {titulo}")
        print(f"     {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}")
    else:
        print("[ERRO] Falha ao salvar no Supabase")
        sys.exit(1)

def list_entries(tipo=None, limit=20):
    if not criar_tabela_se_nao_existe():
        sys.exit(1)
    
    params = {
        'select': 'id,tipo,titulo,relevancia,created_at',
        'order': 'created_at.desc',
        'limit': str(limit)
    }
    if tipo:
        params['tipo'] = f'eq.{tipo}'
    
    result = supabase_request('GET', TABLE, params=params)
    if not result:
        print("Nenhum registro encontrado.")
        return
    
    print(f"\n{'ID':>8}  {'TIPO':<12}  {'REL':>3}  {'DATA':<16}  TITULO")
    print("-" * 72)
    for i, r in enumerate(result, 1):
        dt = r.get('created_at', '')[:16].replace('T', ' ')
        rel = r.get('relevancia', '-')
        uid = str(r['id'])[:8]
        print(f"{uid:>8}  {r['tipo']:<12}  {str(rel):>3}  {dt:<16}  {r['titulo']}")

def search_entries(termo, limit=10):
    if not criar_tabela_se_nao_existe():
        sys.exit(1)
    
    params = {
        'select': 'id,tipo,titulo,conteudo,created_at',
        'or': f'titulo.ilike.*{termo}*,conteudo.ilike.*{termo}*',
        'order': 'created_at.desc',
        'limit': str(limit)
    }
    
    result = supabase_request('GET', TABLE, params=params)
    if not result:
        print(f"Nenhum resultado para '{termo}'")
        return
    
    for r in result:
        dt = r['created_at'][:16].replace('T', ' ')
        print(f"\n[{r['id']}] [{r['tipo']}] {dt}")
        print(f"  {r['titulo']}")
        print(f"  {r['conteudo'][:150]}{'...' if len(r['conteudo']) > 150 else ''}")

def show_entry(entry_id):
    if not criar_tabela_se_nao_existe():
        sys.exit(1)
    
    params = {
        'select': '*',
        'id': f'eq.{entry_id}'
    }
    result = supabase_request('GET', TABLE, params=params)
    if not result:
        print(f"Entrada #{entry_id} nao encontrada.")
        return
    
    r = result[0]
    print(f"\n=== #{r['id']} ===")
    print(f"Tipo:    {r['tipo']}")
    print(f"Titulo:  {r['titulo']}")
    print(f"Data:    {r['created_at'][:16].replace('T', ' ')}")
    print(f"Sessao:  {r.get('sessao_id', 'N/A')}")
    if r.get('tags'):
        print(f"Tags:    {', '.join(r['tags'])}")
    print(f"\nConteudo:\n{r['conteudo']}")

def main():
    args = sys.argv[1:]
    
    if not args or args[0] in ('-h', '--help', 'help'):
        print(__doc__)
        sys.exit(0)
    
    cmd = args[0]
    
    if cmd == 'log':
        if len(args) < 4:
            print("Uso: session_logger.py log <tipo> <titulo> <conteudo> [tag1,tag2] [relevancia 1-10]")
            sys.exit(1)
        tipo = args[1]
        titulo = args[2]
        conteudo = args[3]
        tags = args[4].split(',') if len(args) > 4 else []
        relevancia = int(args[5]) if len(args) > 5 else 7
        log_entry(tipo, titulo, conteudo, tags, relevancia)
    
    elif cmd == 'list':
        tipo = args[1] if len(args) > 1 else None
        limit = int(args[2]) if len(args) > 2 else 20
        list_entries(tipo, limit)
    
    elif cmd == 'search':
        if len(args) < 2:
            print("Uso: session_logger.py search <termo>")
            sys.exit(1)
        search_entries(args[1])
    
    elif cmd == 'show':
        if len(args) < 2:
            print("Uso: session_logger.py show <id>")
            sys.exit(1)
        show_entry(args[1])
    
    elif cmd == 'tipos':
        print("Tipos validos:", ', '.join(TIPOS_VALIDOS))
    
    else:
        print(f"Comando desconhecido: {cmd}")
        print("Use: log, list, search, show, tipos")
        sys.exit(1)

if __name__ == '__main__':
    main()
