#!/usr/bin/env python3
"""
fase3_reteste_dinamico.py — Re-teste ÉTICO dinâmico AbacatePay (29/09/2026).

ESCOPO LEGAL (autorizado por Guilherme 24/09, "sandbox de preferência"):
- Usa EXCLUSIVAMENTE a chave de dev do próprio Lorran (.env.abacate).
- Opera em devMode (sandbox). NENHUM pagamento real é movido.
- Testa apenas a própria conta autenticada.
- Chave nunca é impressa em tela/log.

TESTA:
  A) HTTP Parameter Pollution: id duplicado em /transparents/simulate-payment
     e /transparents/check (?id=REAL&id=FAKE e ?id=FAKE&id=REAL).
  B) As 3 findings de 26/06 (preço<=0, qtd<=0, URLs de callback perigosas)
     nos endpoints atuais (checkouts/create, billing/create).
"""
import json, os, sys
from pathlib import Path
import httpx

BASE = "https://api.abacatepay.com/v2"
ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env.abacate"


def carregar_chave() -> str:
    if not ENV_FILE.exists():
        sys.exit(f"ERRO: {ENV_FILE} não existe.")
    chave = ""
    for linha in ENV_FILE.read_text().splitlines():
        linha = linha.strip()
        if linha.startswith("ABACATE_DEV_KEY="):
            chave = linha.split("=", 1)[1].strip().strip('"').strip("'")
    if not chave or "COLE_SUA" in chave or "SUA_" in chave.upper():
        sys.exit("ERRO: preencha ABACATE_DEV_KEY em .env.abacate.")
    return chave


def H(chave):
    return {"Authorization": f"Bearer {chave}", "Content-Type": "application/json"}


def post(path, chave, body=None, raw_query=""):
    url = f"{BASE}{path}{raw_query}"
    try:
        r = httpx.post(url, headers=H(chave), json=(body or {}), timeout=25)
        try:
            return r.status_code, r.json()
        except Exception:
            return r.status_code, r.text[:300]
    except Exception as e:
        return None, f"conexao: {e}"


def get(path, chave, raw_query=""):
    url = f"{BASE}{path}{raw_query}"
    try:
        r = httpx.get(url, headers=H(chave), timeout=25)
        try:
            return r.status_code, r.json()
        except Exception:
            return r.status_code, r.text[:300]
    except Exception as e:
        return None, f"conexao: {e}"


def data_id(corpo):
    if isinstance(corpo, dict) and isinstance(corpo.get("data"), dict):
        return corpo["data"].get("id")
    return None


def aceito(status, corpo):
    if status is None:
        return False
    if 200 <= status < 300 and isinstance(corpo, dict):
        return corpo.get("success") is True or corpo.get("error") in (None, "")
    return False


def main():
    chave = carregar_chave()
    print("=" * 64)
    print("FASE 3 — RE-TESTE DINÂMICO AbacatePay (conta própria, devMode)")
    print("=" * 64)
    res = {}

    # ── Passo 1: criar uma cobrança transparente PIX real (devMode) ──────
    print("\n[1] Criando cobrança transparente PIX (devMode, sem mover dinheiro)...")
    st, corpo = post("/transparents/create", chave,
                     {"method": "PIX", "data": {"amount": 1000}})
    real_id = data_id(corpo)
    dev = None
    if isinstance(corpo, dict) and isinstance(corpo.get("data"), dict):
        dev = corpo["data"].get("devMode")
    print(f"    status {st} | id={real_id} | devMode={dev}")
    if real_id is None:
        print("    corpo:", json.dumps(corpo, ensure_ascii=False)[:400] if isinstance(corpo, (dict, list)) else str(corpo)[:400])
    res["create_ok"] = real_id is not None
    if not real_id:
        print("    corpo:", json.dumps(corpo, ensure_ascii=False)[:300])
        print("    !! sem id — nao da pra testar HPP. Abortando bloco A.")

    # ── Passo 2: HTTP Parameter Pollution ────────────────────────────────
    if real_id:
        fake = "pix_char_INEXISTENTE_999"
        print("\n[2] HTTP Parameter Pollution (id duplicado)")

        # check: ?id=REAL&id=FAKE  vs  ?id=FAKE&id=REAL
        for label, q in [
            ("check id=REAL&id=FAKE", f"?id={real_id}&id={fake}"),
            ("check id=FAKE&id=REAL", f"?id={fake}&id={real_id}"),
            ("check id=REAL (baseline)", f"?id={real_id}"),
            ("check id=FAKE (baseline)", f"?id={fake}"),
        ]:
            st, corpo = get("/transparents/check", chave, q)
            achou = data_id(corpo) or (isinstance(corpo, dict) and corpo.get("data"))
            print(f"    {label:28} -> status {st} | data? {'SIM' if achou else 'nao'}")
            res[label] = {"status": st, "tem_data": bool(achou)}

        # simulate-payment: idem
        for label, q in [
            ("sim id=REAL&id=FAKE", f"?id={real_id}&id={fake}"),
            ("sim id=FAKE&id=REAL", f"?id={fake}&id={real_id}"),
        ]:
            st, corpo = post("/transparents/simulate-payment", chave, {}, q)
            achou = isinstance(corpo, dict) and corpo.get("success") is True
            print(f"    {label:28} -> status {st} | success? {'SIM' if achou else 'nao'}")
            res[label] = {"status": st, "success": bool(achou)}

    # ── Passo 3: findings de 26/06 (validacao de entrada) ────────────────
    print("\n[3] Re-teste das 3 findings de 26/06 (devem estar corrigidas)")
    base_body = {
        "frequency": "ONE_TIME", "methods": ["PIX"],
        "products": [{"externalId": "reteste", "name": "Reteste",
                      "quantity": 1, "price": 1000}],
        "returnUrl": "https://example.com",
        "completionUrl": "https://example.com",
    }

    def testar(nome, mutacao):
        body = json.loads(json.dumps(base_body))
        mutacao(body)
        for path in ("/checkouts/create", "/billing/create"):
            st, corpo = post(path, chave, body)
            if st is not None:
                ab = aceito(st, corpo)
                print(f"    {nome:24} {path:20} status {st} -> {'ABERTA' if ab else 'corrigida'}")
                res[f"{nome}{path}"] = ab
                return

    testar("preco_negativo", lambda b: b["products"][0].update(price=-100))
    testar("qtd_negativa", lambda b: b["products"][0].update(quantity=-5))
    testar("url_file_passwd", lambda b: b.update(returnUrl="file:///etc/passwd",
                                                 completionUrl="file:///etc/passwd"))

    # ── Sumário ──────────────────────────────────────────────────────────
    print("\n" + "=" * 64)
    out = ROOT / "reports" / "abacate_fase3_reteste.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(f"Resultado salvo: {out}")
    print("=" * 64)


if __name__ == "__main__":
    main()
