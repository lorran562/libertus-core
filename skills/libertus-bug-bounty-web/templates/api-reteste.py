#!/usr/bin/env python3
"""
api-reteste.py — TEMPLATE de re-teste ÉTICO de findings de API.

Copiar e adaptar por alvo. Re-verifica vulnerabilidades já reportadas usando
EXCLUSIVAMENTE a própria conta/chave de dev. NÃO completa transações reais —
só checa validação de entrada. Legal porque testa o próprio recurso autenticado.

REGRAS (não remover):
- Chave vem de um .env dedicado fora do git. NUNCA hardcoded, nunca impressa.
- Recusa rodar com placeholder/vazio (falha segura).
- Tenta endpoint novo E antigo (APIs renomeiam rotas).
- Não finaliza pagamento; manda valor inválido e lê a resposta de validação.

Uso:
    1. Crie .env.<alvo> com  CHAVE_DEV=<sua_chave>  e adicione ao .gitignore
    2. python3 api-reteste.py
"""
import json, sys
from pathlib import Path
import httpx  # no ambiente LIBERTUS, httpx é o cliente padrão (curl bloqueado)

BASE = "https://api.EXEMPLO.com/v2"          # <-- ajustar
ENV_FILE = Path(__file__).resolve().parent / ".env.exemplo"  # <-- ajustar
KEY_VAR = "CHAVE_DEV"


def carregar_chave() -> str:
    if not ENV_FILE.exists():
        sys.exit(f"ERRO: {ENV_FILE} não existe. Crie e preencha {KEY_VAR}.")
    chave = ""
    for linha in ENV_FILE.read_text().splitlines():
        linha = linha.strip()
        if linha.startswith(f"{KEY_VAR}="):
            chave = linha.split("=", 1)[1].strip().strip('"').strip("'")
    if not chave or "COLE_SUA" in chave or "<" in chave:
        sys.exit(f"ERRO: preencha {KEY_VAR} em {ENV_FILE} com a chave real.")
    return chave


def headers(chave): return {"Authorization": f"Bearer {chave}",
                            "Content-Type": "application/json"}


def post(path, chave, body):
    try:
        r = httpx.post(f"{BASE}{path}", headers=headers(chave),
                       json=body, timeout=20)
        try:    return r.status_code, r.json()
        except Exception: return r.status_code, r.text[:300]
    except Exception as e:
        return None, f"erro de conexão: {e}"


def aceito(status, corpo) -> bool:
    """API ACEITOU o valor inválido (vuln ainda aberta)?"""
    if status is None or not (200 <= status < 300):
        return False
    if isinstance(corpo, dict):
        return corpo.get("success") is True or corpo.get("error") in (None, "")
    return True


def main():
    chave = carregar_chave()
    resultados = {}

    # ── Exemplo de finding: valor inválido aceito ──────────────────────
    # Adaptar bodies/endpoints às findings reais reportadas.
    body_invalido = {"products": [{"name": "reteste", "quantity": 1,
                                   "price": -100}]}  # <-- ajustar
    for path in ("/billing/create", "/checkouts/create"):  # novo E antigo
        st, corpo = post(path, chave, body_invalido)
        if st is not None:
            ainda = aceito(st, corpo)
            resultados[f"valor_invalido{path}"] = ainda
            print(f"  {path}: status {st} -> "
                  f"{'AINDA ACEITA (aberta)' if ainda else 'rejeitado (corrigido)'}")

    abertas = [k for k, v in resultados.items() if v]
    print(f"\nAbertas: {len(abertas)} | Corrigidas: "
          f"{len(resultados) - len(abertas)}")
    Path("reteste_resultado.json").write_text(
        json.dumps(resultados, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
