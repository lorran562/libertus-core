#!/usr/bin/env python3
"""Insere o aprendizado de 14/10/2026 na memoria do Supabase e VERIFICA a leitura.

Escreve em `libertus_memoria` (tipo='aprendizado', relevancia=9) e em seguida
faz GET do registro pelo id para provar que persistiu — sem confiar no 201.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
for path in (os.path.join(BASE, '.env'), os.path.expanduser('~/.hermes/.env')):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, _, v = line.partition('=')
                    os.environ.setdefault(k.strip(), v.strip())

URL = os.environ.get('SUPABASE_URL', '').rstrip('/')
KEY = os.environ.get('SUPABASE_KEY', '')
if not URL or not KEY:
    sys.exit('[erro] SUPABASE_URL/SUPABASE_KEY ausentes no .env')

H = {
    'apikey': KEY,
    'Authorization': f'Bearer {KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation',
}

REGISTRO = {
    'tipo': 'aprendizado',
    'titulo': 'Comparacao de assinatura: 7 modos de falha (medidos em PHP/Node/Python/Go)',
    'conteudo': (
        'Pesquisa da madrugada 14/10/2026, continuação do Finding 1 (webhook) da '
        'auditoria AbacatePay. Objetivo: além da chave errada, a COMPARAÇÃO da '
        'assinatura pode falhar? Sim, de 7 formas — e a mais famosa (timing) é a '
        'menos provável de ser achado real.\n\n'
        'EXECUTADO NESTA MAQUINA (PHP 8.3.35 via docker php:8.3-cli, Node v22.22.3, '
        'Python 3.14.7, Go):\n'
        '1. Exceção não tratada = 500/DoS. Node timingSafeEqual lança '
        'ERR_CRYPTO_TIMING_SAFE_EQUAL_LENGTH com assinatura de tamanho diferente e '
        'ERR_INVALID_ARG_TYPE com objeto. Python hmac.compare_digest lança TypeError '
        'com str não-ASCII (header HTTP é str em todo framework — X-Signature: é '
        'derruba o endpoint). Go subtle.ConstantTimeCompare devolve 0 e não quebra. '
        'Ordem correta: tipo -> comprimento -> comparação constante.\n'
        '2. PHP loose comparison vivo no PHP 8.3: "0" == "0e462097...base64/hex" '
        'retorna true (magic hash). Ataque prático: mandar sig=0. CVE-2025-48952 '
        '(NetAlertX, CVSS 9.4) é exatamente isso. Em HMAC puro o atacante não força '
        'o digest esperado — não inflar severidade.\n'
        '3. Prefixo truncado: substr(digest,0,6) = 24 bits; forjar custou 5.398.790 '
        'tentativas medidas (esperado 16^6/2=8,4M).\n'
        '4. Fail-open com segredo vazio devolve true para assinatura lixo (medido).\n'
        '5. Encoding: hex vs base64, com/sem prefixo sha256=, caixa.\n'
        '6. Corpo re-serializado em vez de raw body (nunca confere -> dev desliga a '
        'verificação).\n'
        '7. TIMING medido com controle positivo (servidor que dorme 50us por byte '
        'correto): vazamento do loop interpretado 21-66 ns/byte; memcmp C ~0,5-1,8 '
        'ns/byte (piso do ruído); jitter sigma do loopback 52-153 us (razão 1000-35000x). '
        'Regressão RTT x prefixo: naive t=-0,82 (SEM sinal); controle t=+38,6 r=0,990 '
        '(sinal). Recuperação real do 1o byte: naive posição 143-236 de 256 (sorteio), '
        'controle posição 4-9. Regra: para caber em 10^7 requisições o alvo precisa '
        'vazar >=15 us/byte — 690x acima do medido. Só vira achado real com valor '
        'comparado >=~690 bytes (4KB -> 2,8x10^5 req, possível) ou vazamento de '
        'microssegundos (RSA/Brumley-Boneh).\n\n'
        'PITFALLS DE MEDIÇÃO aprendidos quebrando: (a) sem TCP_NODELAY o loopback mede '
        '41 ms de RTT e sigma 1,9 ms (Nagle + delayed-ACK) — é ruído do instrumento; '
        '(b) sigma variou uma ordem de grandeza entre execuções (52us -> 1,84ms), então '
        'reportar faixa e adotar o lote mais quieto; (c) "slope" de dois pontos não é '
        'evidência — regressão com r e t; (d) controle positivo é obrigatório, senão '
        '"não achei sinal" é indistinguível de instrumento quebrado.\n\n'
        'Artefatos: evolucao/analise_2026-10-14_comparacao-assinatura.md, '
        'scripts/audit_assinatura/ (timing_signature_compare.py, '
        'php_loose_compare_poc.php, node_webhook_verify_probe.js, '
        'go_constant_time_probe.go), reports/timing_assinatura_2026-10-14.txt. '
        'Skill libertus-bug-bounty-web atualizada + references/comparacao-assinatura-runbook.md.'
    ),
    'tags': ['webhook', 'hmac', 'comparacao', 'timing', 'php', 'node', 'golang', 'auditoria-sdk'],
    'relevancia': 9,
}


def req(method, url, data=None):
    r = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
                               headers=H, method=method)
    with urllib.request.urlopen(r, timeout=20) as resp:
        return json.loads(resp.read().decode() or 'null')


tabela = f'{URL}/rest/v1/libertus_memoria'

# tenta com relevancia; se a coluna nao existir, cai para o insert minimo
payload = dict(REGISTRO)
try:
    resp = req('POST', tabela, payload)
except urllib.error.HTTPError as e:
    corpo = e.read().decode()[:200]
    print(f'[aviso] insert com relevancia falhou ({e.code}): {corpo}')
    payload.pop('relevancia', None)
    resp = req('POST', tabela, payload)

if not resp:
    sys.exit('[erro] insert nao retornou registro')
entry = resp[0] if isinstance(resp, list) else resp
mid = entry['id']
print(f'[ok] inserido id={mid}')

# VERIFICACAO: ler de volta do servidor
lido = req('GET', f'{tabela}?id=eq.{mid}&select=id,tipo,titulo,relevancia,tags,created_at')
assert lido, '[erro] leitura de volta vazia'
reg = lido[0]
print('[verify]', json.dumps({k: reg.get(k) for k in
                              ('id', 'tipo', 'titulo', 'relevancia', 'created_at')},
                             ensure_ascii=False))
assert reg['tipo'] == 'aprendizado', 'tipo divergente na leitura de volta'
assert reg['titulo'] == REGISTRO['titulo'], 'titulo divergente'
if 'relevancia' in reg:
    assert reg['relevancia'] == 9, f"relevancia={reg['relevancia']}"
    print('[verify] relevancia=9 confirmada')
else:
    print('[verify] ATENCAO: coluna relevancia nao existe na tabela (insert caiu no minimo)')
print('[ok] aprendizado persistido e confirmado por leitura')
