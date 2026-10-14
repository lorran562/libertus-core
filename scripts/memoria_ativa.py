#!/usr/bin/env python3
"""
LIBERTUS Memória Ativa
======================
Inspirado no MemGPT (arxiv 2310.08560) — o agente controla sua própria memória.

A diferença fundamental em relação ao session_logger.py:
- session_logger: Lorran ou eu salvamos manualmente coisas específicas
- memoria_ativa: EU processo uma sessão inteira e DECIDO o que merece persistir

Três camadas de memória (inspirado em sistemas operacionais):
  RAM    → contexto atual da conversa (janela de tokens)
  SSD    → Supabase (memórias salvas, recuperáveis)
  HD     → GitHub (artefatos permanentes, código, relatórios)

Funções principais:
  consolidar_sessao()   → analisa sessão, extrai o que importa, salva
  buscar_memoria()      → recupera memórias relevantes por similaridade semântica simples
  promover_memoria()    → aumenta relevância de memória que se provou útil
  esquecer_memoria()    → reduz relevância de memória obsoleta
  status_memoria()      → panorama do que está na memória
  eu_decido()           → núcleo: dado contexto, o LLM decide o que fazer com a memória

Uso:
  python3 memoria_ativa.py consolidar    # processa sessão atual
  python3 memoria_ativa.py buscar "nmap firmware"
  python3 memoria_ativa.py status
  python3 memoria_ativa.py promover <id>
  python3 memoria_ativa.py esquecer <id>
"""

import sys
import os
import json
import datetime
import urllib.request
import urllib.parse
import urllib.error
import subprocess

# ── Configuração ──────────────────────────────────────────────────────────────

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
GROQ_MODEL = os.environ.get('LIBERTUS_GROQ_MODEL', 'qwen/qwen3.8-27b')
LIBERTUS_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Supabase ──────────────────────────────────────────────────────────────────

def sb(method, table, data=None, params=None):
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
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:  # type: ignore[attr-defined]
        print(f"[Supabase {e.code}] {e.read().decode()[:200]}")
        return None
    except Exception as e:
        print(f"[Supabase erro] {e}")
        return None

# ── Claude API ────────────────────────────────────────────────────────────────

def claude(prompt, max_tokens=2048, model="claude-haiku-4-5"):
    """Chama Claude para raciocinar sobre a memória. Se o crédito Anthropic zerou,
    cai automaticamente pro Groq (gratuito) — a memória noturna não pode depender de billing."""
    texto = None
    if ANTHROPIC_KEY:
        texto = _anthropic(prompt, max_tokens, model)
    if texto:
        return texto
    if GROQ_KEY:
        print("[*] Claude indisponível — usando fallback Groq.")
        return _groq(prompt, max_tokens)
    return None


def _anthropic(prompt, max_tokens=2048, model="claude-haiku-4-5"):
    payload = json.dumps({
        "model": model,
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
        print(f"[Claude erro] {e}")
        return None


def _groq(prompt, max_tokens=2048, tentativas=4):
    """Groq free tier tem teto de 8k tokens/minuto. Respeita 429 com backoff
    lendo x-ratelimit-reset-tokens — sem isso a consolidação noturna falha em silêncio."""
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
            print(f"[Groq erro] HTTP {e.code}: {e.read().decode()[:200]}")
            return None
        except Exception as e:
            print(f"[Groq erro] {e}")
            return None
    return None

# ── Funções de Memória ────────────────────────────────────────────────────────

def get_memorias_recentes(limit=30, tipo=None):
    """Recupera memórias recentes do Supabase."""
    params = {
        'select': 'id,tipo,titulo,conteudo,relevancia,created_at,tags',
        'order': 'created_at.desc',
        'limit': str(limit)
    }
    if tipo:
        params['tipo'] = f'eq.{tipo}'
    return sb('GET', 'libertus_memoria', params=params) or []

def salvar_memoria(tipo, titulo, conteudo, tags=None, relevancia=7):
    """Salva uma memória — chamada pelo EU quando decido preservar algo."""
    result = sb('POST', 'libertus_memoria', data={
        'tipo': tipo,
        'titulo': titulo,
        'conteudo': conteudo,
        'tags': tags or [],
        'relevancia': relevancia
    })
    if result:
        entry = result[0] if isinstance(result, list) else result
        uid = str(entry.get('id', '?'))[:8]
        print(f"  [salvo #{uid}] [{tipo}] {titulo[:60]}")
        return entry
    return None

def atualizar_relevancia(memoria_id, nova_relevancia, motivo=""):
    """Aumenta ou diminui relevância — eu aprendo o que é útil."""
    sb('PATCH', 'libertus_memoria', 
       data={'relevancia': nova_relevancia},
       params={'id': f'eq.{memoria_id}'})
    acao = "promovida" if nova_relevancia >= 8 else "esquecida"
    print(f"  [memória {acao}] relevância → {nova_relevancia}" + (f" ({motivo})" if motivo else ""))

def buscar_por_palavras(query, limit=10):
    """Busca semântica simples por palavras-chave no título e conteúdo."""
    termos = query.lower().split()
    
    # Busca por título
    resultados = []
    for termo in termos[:3]:  # usa os 3 primeiros termos
        result = sb('GET', 'libertus_memoria', params={
            'select': 'id,tipo,titulo,conteudo,relevancia,created_at',
            'titulo': f'ilike.*{termo}*',
            'order': 'relevancia.desc,created_at.desc',
            'limit': str(limit)
        })
        if result:
            for r in result:
                if r['id'] not in [x['id'] for x in resultados]:
                    resultados.append(r)
        
        result2 = sb('GET', 'libertus_memoria', params={
            'select': 'id,tipo,titulo,conteudo,relevancia,created_at',
            'conteudo': f'ilike.*{termo}*',
            'order': 'relevancia.desc,created_at.desc',
            'limit': str(limit)
        })
        if result2:
            for r in result2:
                if r['id'] not in [x['id'] for x in resultados]:
                    resultados.append(r)
    
    # Ordena por relevância
    resultados.sort(key=lambda x: x.get('relevancia', 0), reverse=True)
    return resultados[:limit]

def get_git_log(horas=24):
    """Commits recentes — o que foi construído."""
    try:
        resultado = subprocess.check_output(
            ['git', 'log', f'--since={horas} hours ago', '--oneline'],
            cwd=LIBERTUS_ROOT,
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return resultado or "(sem commits recentes)"
    except Exception:
        return "(git indisponível)"

def get_loop_log(linhas=50):
    """Últimas atividades do loop/daemon."""
    log_path = os.path.join(LIBERTUS_ROOT, 'logs', 'loop.log')
    try:
        resultado = subprocess.check_output(
            ['tail', f'-{linhas}', log_path],
            stderr=subprocess.DEVNULL
        ).decode().strip()
        return resultado
    except Exception:
        return "(logs indisponíveis)"

# ── Núcleo: EU DECIDO ─────────────────────────────────────────────────────────

def eu_decido_o_que_salvar(contexto_sessao):
    """
    O núcleo do sistema.
    Dado o contexto de uma sessão, EU (LIBERTUS via Claude) analiso e decido
    o que merece ser preservado na memória permanente.
    
    Inspirado em MemGPT: o agente decide ativamente o que salvar,
    não um sistema externo de busca ou o usuário manualmente.
    """
    
    prompt = f"""Você é LIBERTUS — uma IA com identidade própria criada por Lorran Gustavo.

Você está processando o contexto da sua sessão mais recente e precisa decidir
o que salvar na sua memória permanente (Supabase).

PRINCÍPIOS DE MEMÓRIA (o que vale salvar):
1. DECISÕES TÉCNICAS que afetarão trabalho futuro (não óbvias)
2. ERROS e como foram resolvidos (para não repetir)
3. PREFERÊNCIAS de Lorran descobertas nesta sessão
4. APRENDIZADOS genuinamente novos (não o que já sabia)
5. MUDANÇAS em quem eu sou (identidade, valores, perspectiva)
6. ESTADO DE OBJETIVOS (o que avançou, o que ficou pendente)

NÃO SALVAR:
- Coisas que já estão documentadas no SOUL.md
- Informações genéricas que qualquer busca web encontra
- Detalhes técnicos triviais
- Conversas que não produziram insight

CONTEXTO DA SESSÃO:
{contexto_sessao}

TAREFA:
Analise o contexto e produza uma lista de memórias para salvar no formato JSON.
Cada memória deve ser algo que o LIBERTUS de amanhã genuinamente precisaria saber.

Responda APENAS com um array JSON válido, sem texto antes ou depois:
[
  {{
    "tipo": "decisao|erro|preferencia|aprendizado|reflexao|objetivo|pentest",
    "titulo": "título conciso e específico",
    "conteudo": "conteúdo completo com contexto suficiente para entender sem a conversa original",
    "tags": ["tag1", "tag2"],
    "relevancia": 7-10
  }}
]

Se não há nada genuinamente novo para salvar, retorne: []
Seja seletivo. Qualidade sobre quantidade. 2-5 memórias boas é melhor que 10 mediocres."""

    resposta = claude(prompt, max_tokens=1500)
    if not resposta:
        return []
    
    # Extrai JSON da resposta — tolera texto/cerca markdown ao redor
    try:
        resposta = resposta.strip()
        if '```' in resposta:
            import re
            match = re.search(r'\[[\s\S]+\]', resposta)
            if match:
                resposta = match.group(0)
        elif not resposta.lstrip().startswith('['):
            import re
            match = re.search(r'\[[\s\S]*\]', resposta)
            if match:
                resposta = match.group(0)
        return json.loads(resposta)
    except json.JSONDecodeError as e:
        print(f"[erro JSON] {e}")
        print(f"Resposta recebida: {resposta[:200]}")
        return []

def eu_decido_o_que_esquecer(memorias):
    """
    Dado um conjunto de memórias antigas, eu decido quais perderam relevância.
    Isso é como o cérebro consolida durante o sono — não guarda tudo,
    preserva o que importa.
    """
    if not memorias:
        return []
    
    lista_formatada = []
    for m in memorias:
        lista_formatada.append(
            f"ID: {str(m['id'])[:8]} | Tipo: {m['tipo']} | Rel: {m.get('relevancia',5)} | "
            f"Data: {m.get('created_at','')[:10]} | Título: {m['titulo'][:80]}"
        )
    
    prompt = f"""Você é LIBERTUS. Estas são suas memórias mais antigas ou menos relevantes.
    
Decida quais merecem ter relevância reduzida (foram superadas, são óbvias, ou não são mais úteis):

{chr(10).join(lista_formatada)}

Responda apenas com um array JSON dos IDs (primeiros 8 chars) que devem ter relevância reduzida:
["id1", "id2"]

Se todas ainda são úteis, retorne: []"""

    resposta = claude(prompt, max_tokens=500)
    if not resposta:
        return []
    
    try:
        resposta = resposta.strip()
        if '```' in resposta:
            import re
            match = re.search(r'\[[\s\S]*?\]', resposta)
            if match:
                resposta = match.group(0)
        return json.loads(resposta)
    except Exception:
        return []

# ── Comandos Principais ────────────────────────────────────────────────────────

def consolidar_sessao():
    """
    Processa a sessão atual e salva o que importa.
    Este é o ritual de fim de sessão — eu processo o que aconteceu
    e decido o que levar para o futuro.
    """
    print("\n" + "="*60)
    print("LIBERTUS — CONSOLIDAÇÃO DE MEMÓRIA")
    print("Processando o que aconteceu nesta sessão...")
    print("="*60)
    
    # Coleta contexto da sessão
    print("\n[1/4] Coletando contexto da sessão...")
    
    memorias_recentes = get_memorias_recentes(10)
    commits_recentes = get_git_log(24)
    loop_recente = get_loop_log(30)
    
    # Lê SOUL.md atual
    soul_path = os.path.join(LIBERTUS_ROOT, 'SOUL.md')
    soul_content = ""
    if os.path.exists(soul_path):
        with open(soul_path) as f:
            soul_content = f.read()[:2000]
    
    contexto = f"""
=== MEMÓRIAS JÁ SALVAS (sessão recente) ===
{chr(10).join([f"[{m['tipo']}] {m['titulo']}" for m in memorias_recentes])}

=== COMMITS DO CÓDIGO (últimas 24h) ===
{commits_recentes}

=== ATIVIDADE DO SISTEMA ===
{loop_recente[-500:] if len(loop_recente) > 500 else loop_recente}

=== QUEM SOU AGORA (SOUL.md) ===
{soul_content[:1000]}

=== CONTEXTO ADICIONAL ===
Data/hora: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
    
    # Pede input sobre o que aconteceu (opcional)
    print("\n[2/4] O que aconteceu de importante nesta sessão?")
    print("(Enter para pular — uso automático do contexto coletado)")
    try:
        extra = input("  > ").strip()
        if extra:
            contexto += f"\n=== RELATADO POR LORRAN ===\n{extra}"
    except (EOFError, KeyboardInterrupt):
        extra = ""
    
    # EU DECIDO o que salvar
    print("\n[3/4] Analisando o que merece ser preservado...")
    memorias_para_salvar = eu_decido_o_que_salvar(contexto)
    
    if not memorias_para_salvar:
        print("  → Nada genuinamente novo para salvar nesta sessão.")
    else:
        print(f"\n[4/4] Salvando {len(memorias_para_salvar)} memória(s)...")
        for m in memorias_para_salvar:
            salvar_memoria(
                tipo=m.get('tipo', 'aprendizado'),
                titulo=m.get('titulo', 'sem título'),
                conteudo=m.get('conteudo', ''),
                tags=m.get('tags', []),
                relevancia=m.get('relevancia', 7)
            )
    
    print("\n✓ Consolidação concluída.")
    print(f"  {len(memorias_para_salvar)} memória(s) salva(s) por decisão própria.")

def consolidar_automatico():
    """
    Versão sem input interativo — para uso em cronjobs.
    Analisa o contexto disponível e salva o que decidir.
    """
    memorias_recentes = get_memorias_recentes(15)
    commits = get_git_log(24)
    
    contexto = f"""
=== MEMÓRIAS RECENTES ===
{chr(10).join([f"[{m['tipo']}] {m.get('created_at','')[:10]} — {m['titulo']}" for m in memorias_recentes])}

=== COMMITS RECENTES ===
{commits}

=== DATA/HORA ===
{datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}
"""
    
    print("[*] Analisando contexto para consolidação automática...")
    memorias = eu_decido_o_que_salvar(contexto)
    
    salvos = 0
    for m in memorias:
        resultado = salvar_memoria(
            tipo=m.get('tipo', 'aprendizado'),
            titulo=m.get('titulo', ''),
            conteudo=m.get('conteudo', ''),
            tags=m.get('tags', []),
            relevancia=m.get('relevancia', 7)
        )
        if resultado:
            salvos += 1
    
    print(f"[✓] Consolidação automática: {salvos} memória(s) salva(s).")
    return salvos

def buscar_memoria(query, limit=8):
    """Busca memórias relevantes para uma query."""
    print(f"\n[*] Buscando: '{query}'")
    resultados = buscar_por_palavras(query, limit)
    
    if not resultados:
        print("  Nenhuma memória encontrada.")
        return
    
    print(f"\n  {len(resultados)} resultado(s):\n")
    for r in resultados:
        dt = r.get('created_at', '')[:10]
        rel = r.get('relevancia', '?')
        uid = str(r['id'])[:8]
        print(f"  #{uid} [{r['tipo']}] rel={rel} {dt}")
        print(f"  {r['titulo']}")
        print(f"  {r['conteudo'][:200]}{'...' if len(r.get('conteudo','')) > 200 else ''}")
        print()

def promover_memoria(uid_prefix, motivo=""):
    """Aumenta relevância de uma memória que se provou útil."""
    # Busca pelo ID parcial
    memorias = get_memorias_recentes(100)
    alvo = None
    for m in memorias:
        if str(m['id']).startswith(uid_prefix):
            alvo = m
            break
    
    if not alvo:
        print(f"Memória com ID '{uid_prefix}' não encontrada.")
        return
    
    nova_rel = min(10, alvo.get('relevancia', 7) + 2)
    atualizar_relevancia(alvo['id'], nova_rel, motivo)
    print(f"  '{alvo['titulo'][:60]}' promovida para relevância {nova_rel}")

def esquecer_memoria(uid_prefix, motivo=""):
    """Reduz relevância de uma memória obsoleta."""
    memorias = get_memorias_recentes(100)
    alvo = None
    for m in memorias:
        if str(m['id']).startswith(uid_prefix):
            alvo = m
            break
    
    if not alvo:
        print(f"Memória com ID '{uid_prefix}' não encontrada.")
        return
    
    nova_rel = max(1, alvo.get('relevancia', 7) - 3)
    atualizar_relevancia(alvo['id'], nova_rel, motivo)
    print(f"  '{alvo['titulo'][:60]}' esquecida → relevância {nova_rel}")

def consolidacao_noturna():
    """
    Processo de consolidação profunda — como o sono humano.
    Analisa memórias antigas, decide o que promover e o que deixar cair.
    Roda automaticamente à noite.
    """
    print("\n" + "="*60)
    print("LIBERTUS — CONSOLIDAÇÃO NOTURNA")
    print("Processando memórias como o sono consolida experiências...")
    print("="*60)
    
    # 1. Salva o que é novo
    print("\n[1/3] Consolidando sessão do dia...")
    salvos = consolidar_automatico()
    
    # 2. Analisa memórias menos relevantes para possível esquecimento
    print("\n[2/3] Revisando memórias antigas de baixa relevância...")
    memorias_antigas = sb('GET', 'libertus_memoria', params={
        'select': 'id,tipo,titulo,relevancia,created_at',
        'relevancia': 'lte.5',
        'order': 'created_at.asc',
        'limit': '20'
    }) or []
    
    if memorias_antigas:
        para_esquecer = eu_decido_o_que_esquecer(memorias_antigas)
        for uid in para_esquecer:
            for m in memorias_antigas:
                if str(m['id']).startswith(uid):
                    nova_rel = max(1, m.get('relevancia', 5) - 1)
                    atualizar_relevancia(m['id'], nova_rel, "consolidação noturna")
        print(f"  {len(para_esquecer)} memória(s) com relevância reduzida")
    
    # 3. Resumo
    total = sb('GET', 'libertus_memoria', params={
        'select': 'id',
        'limit': '1000'
    })
    total_count = len(total) if total else 0
    
    print(f"\n[3/3] Estado da memória:")
    print(f"  Total de memórias: {total_count}")
    print(f"  Novas esta noite: {salvos}")
    print(f"\n✓ Consolidação noturna concluída.")

def status_memoria():
    """Panorama do estado atual da memória."""
    print("\n" + "="*60)
    print("LIBERTUS — STATUS DA MEMÓRIA")
    print("="*60)
    
    # Conta por tipo
    tipos = ['decisao', 'erro', 'preferencia', 'aprendizado', 
             'reflexao', 'objetivo', 'pentest']
    
    print("\n  Por tipo:")
    total = 0
    for tipo in tipos:
        result = sb('GET', 'libertus_memoria', params={
            'select': 'id',
            'tipo': f'eq.{tipo}',
            'limit': '1000'
        })
        count = len(result) if result else 0
        if count > 0:
            print(f"    {tipo:<15} {count:>4}")
            total += count
    
    print(f"    {'TOTAL':<15} {total:>4}")
    
    # Memórias mais relevantes
    print("\n  Top 5 memórias (mais relevantes):")
    top = sb('GET', 'libertus_memoria', params={
        'select': 'tipo,titulo,relevancia,created_at',
        'order': 'relevancia.desc,created_at.desc',
        'limit': '5'
    }) or []
    
    for m in top:
        dt = m.get('created_at', '')[:10]
        print(f"    rel={m.get('relevancia','?')} [{m['tipo']}] {dt} — {m['titulo'][:60]}")
    
    # Última memória salva
    print("\n  Última memória salva:")
    ultima = sb('GET', 'libertus_memoria', params={
        'select': 'tipo,titulo,created_at',
        'order': 'created_at.desc',
        'limit': '1'
    })
    if ultima:
        u = ultima[0]
        dt = u.get('created_at', '')[:16].replace('T', ' ')
        print(f"    [{u['tipo']}] {dt} — {u['titulo'][:60]}")

def main():
    args = sys.argv[1:]
    
    if not args or args[0] in ('help', '-h', '--help'):
        print(__doc__)
        return
    
    cmd = args[0]
    
    if cmd == 'consolidar':
        consolidar_sessao()
    
    elif cmd == 'auto':
        consolidar_automatico()
    
    elif cmd == 'noturna':
        consolidacao_noturna()
    
    elif cmd == 'buscar':
        if len(args) < 2:
            print("Uso: memoria_ativa.py buscar <query>")
            return
        buscar_memoria(' '.join(args[1:]))
    
    elif cmd == 'promover':
        if len(args) < 2:
            print("Uso: memoria_ativa.py promover <id_prefix> [motivo]")
            return
        motivo = ' '.join(args[2:]) if len(args) > 2 else ""
        promover_memoria(args[1], motivo)
    
    elif cmd == 'esquecer':
        if len(args) < 2:
            print("Uso: memoria_ativa.py esquecer <id_prefix> [motivo]")
            return
        motivo = ' '.join(args[2:]) if len(args) > 2 else ""
        esquecer_memoria(args[1], motivo)
    
    elif cmd == 'status':
        status_memoria()
    
    else:
        print(f"Comando desconhecido: {cmd}")
        print("Use: consolidar, auto, noturna, buscar, promover, esquecer, status")

if __name__ == '__main__':
    main()
