#!/usr/bin/env python3
"""Varredura estática profunda (monstro) — SDKs oficiais AbacatePay.

Base legal: código-fonte PÚBLICO no GitHub. Nenhuma requisição à infraestrutura.
Autorização: Guilherme (AbacatePay) 24/09/2026; confirmada 29/09/2026
("o que der para fazer em sandbox, melhor") — este script é 100% estático.

Objetivo: ir além dos 8 greps do audit de 29/09. Aqui são 14 classes, varredura
por arquivo e por linguagem, com linha e trecho de evidência para revisão.

Uso: python3 varredura_monstra.py [--json saida.json]
"""
import argparse
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
SDKS = os.path.join(RAIZ, "sdks")

EXCLUI_DIR = {".git", "node_modules", "vendor", "dist", "build", "target",
              "__pycache__", ".venv", "venv", "coverage", ".idea", "Pods",
              ".dart_tool", "bin", "obj", "deps", "_build"}
EXCLUI_EXT = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf", ".zip",
              ".tar", ".gz", ".jar", ".class", ".so", ".dll", ".dylib", ".woff",
              ".woff2", ".ttf", ".eot", ".mp4", ".lock"}

# 14 classes. Cada uma: (id, severidade esperada, descrição, lista de regex)
CLASSES = [
    ("SECRET_HARDCODED", "Média-Alta",
     "Segredo/credencial em código-fonte público",
     [r"""(?i)(api[_-]?key|secret|token|password|passwd|senha|private[_-]?key|client[_-]?secret)\s*[:=]\s*["'][A-Za-z0-9_\-]{16,}["']""",
      r"""(?i)(sk|pk|api|key|token)_(live|test|prod)_[A-Za-z0-9]{10,}""",
      r"-----BEGIN [A-Z ]*PRIVATE KEY-----"]),

    ("WEBHOOK_VERIFY_FRACA", "Alta",
     "Verificação de webhook: só HMAC de chave pública, sem webhookSecret (CWE-347)",
     [r"(?i)hmac[a-z_]*\s*\(|hash_hmac\s*\(|createHmac\s*\(|HMAC\w*\s*\(",
      r"(?i)verify[_a-z]*signature|verify[_a-z]*webhook|verify[_a-z]*hmac|check[_a-z]*signature"]),

    ("COMPARE_NAO_CONSTANTE", "Média",
     "Comparação de assinatura/segredo sem tempo constante (timing attack, CWE-208)",
     [r"""(?i)(signature|hmac|secret|token|hash)\s*={2,3}\s*(expected|computed|received|signature|hmac)""",
      r"""(?i)if\s*\(\s*(signature|hmac|secret)\s*==\s*"""]),

    ("URL_SEM_ENCODE", "Média",
     "Parâmetro concatenado em query string sem encoding → HPP/divergência (CWE-88)",
     [r"""["'`][^"'`]*\?[^"'`]*["'`]\s*\+\s*""",
      r"""\$\{[a-zA-Z_.]+\}""",
      r"""\+\s*[a-z_]*[Ii]d\s*\+\s*["'`&]""",
      r"""(?i)(taxId|cpf|cnpj|status|id)\s*=\s*["'`]\s*\+\s*"""]),

    ("SSL_VERIFY_OFF", "Alta",
     "Verificação de certificado TLS desabilitada (CWE-295)",
     [r"(?i)verify\s*=\s*False", r"(?i)rejectUnauthorized\s*:\s*false",
      r"(?i)InsecureSkipVerify\s*:\s*true", r"(?i)CURLOPT_SSL_VERIFYPEER,\s*false",
      r"(?i)ssl[_-]?verify\s*=>?\s*(false|0)", r"(?i)VERIFY_NONE",
      r"(?i)trustAllCerts|ALLOW_ALL_HOSTNAME|NoopHostnameVerifier"]),

    ("CMD_INJECTION", "Alta",
     "Execução de comando com entrada interpolada (CWE-78)",
     [r"(?i)child_process|execSync|exec\(|spawn\(|shell_exec|passthru|subprocess\.(run|call|Popen|check_output)|os\.system|Runtime\.getRuntime\(\)\.exec|Process\.start|system\("]),

    ("DESERIALIZACAO_INSEGURA", "Alta",
     "Desserialização / eval / pickle / YAML inseguro (CWE-502)",
     [r"(?i)pickle\.loads|yaml\.load\((?!.*Safe)|Marshal\.load|unserialize\(|eval\(|new Function\(|ObjectInputStream|JSON\.parse\(.*\)\s*\?\s*eval"]),

    ("LOG_DADO_PESSOAL", "Baixa-Média",
     "Dado pessoal (CPF/taxId/email/cartão) em log",
     [r"(?i)(log|logger|print|console\.log|puts|fmt\.Print)[^\n]{0,60}(taxId|cpf|cnpj|email|card|document|phone|celular)"]),

    ("SSRF_URL_USUARIO", "Média-Alta",
     "URL/chamada HTTP com valor vindo do chamador (SSRF, CWE-918)",
     [r"(?i)(fetch|axios|requests?\.(get|post)|http\.Get|HttpClient|curl_exec|RestClient|get_for|Net::HTTP)[^\n]{0,80}(url|callback|webhook|returnUrl|completionUrl|endpoint)"]),

    ("SECRETO_EM_URL", "Baixa",
     "Segredo/token transmitido em query string (exposição em log/histórico)",
     [r"(?i)\?(secret|token|key|api_key|webhookSecret|access_token)=",
      r"(?i)(webhookSecret|apiKey|secret)\s*\+\s*[\x22\x27`]\s*&?\s*(&|$|[\x22\x27`])"]),

    ("VALIDACAO_AUSENTE_VALOR", "Média",
     "Valor monetário/quantidade sem validação de positivo (CWE-20)",
     [r"(?i)(price|amount|quantity|valor|qtd)\s*[:=]\s*(data|payload|body|input|req)[\.\[a-zA-Z]*",
      r"(?i)float\(\s*(data|payload|body)\["]),

    ("AUTH_FRACO", "Média-Alta",
     "Comparação de auth fraca / token previsível / auth opcional",
     [r"(?i)(token|key)\s*==\s*[\x22\x27](admin|test|dev|123|secret)[\x22\x27]",
      r"(?i)if\s*\(\s*!?\s*(token|key|auth)\s*\)\s*\{?\s*return\s*;?\s*\}?\s*//?",
      r"(?i)skip[_-]?(auth|verify|signature)\s*[:=]\s*true"]),

    ("DEP_LOCKFILE", "Informativo",
     "Arquivo de lock para auditoria de dependência (CVE)",
     [r"^$"]),  # tratado separadamente por nome de arquivo
]

LOCKFILES = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "requirements.txt",
             "poetry.lock", "Gemfile.lock", "composer.lock", "go.sum",
             "Cargo.lock", "mix.lock", "Package.resolved", "pom.xml",
             "build.gradle", "build.gradle.kts", "*.csproj"]

COMPILED_EXT = {".jar", ".class", ".so", ".dll", ".dylib", ".wasm", ".asar",
                ".apk", ".aab", ".ipa", ".zip", ".woff", ".ttf"}


def arquivos(raiz):
    for atual, dirs, files in os.walk(raiz):
        dirs[:] = [d for d in dirs if d not in EXCLUI_DIR]
        for f in files:
            if os.path.splitext(f)[1].lower() in EXCLUI_EXT:
                continue
            p = os.path.join(atual, f)
            try:
                if os.path.getsize(p) > 3_000_000:
                    continue
            except OSError:
                continue
            yield p


def varre():
    achados = {c[0]: [] for c in CLASSES}
    locks = []
    binarios = []
    total_arquivos = 0
    compilados = []

    for repo in sorted(os.listdir(SDKS)):
        rpath = os.path.join(SDKS, repo)
        if not os.path.isdir(rpath):
            continue
        for p in arquivos(rpath):
            rel = os.path.relpath(p, SDKS)
            base = os.path.basename(p)
            if base in LOCKFILES or base.endswith((".csproj",)):
                locks.append(rel)
            ext = os.path.splitext(base)[1].lower()
            if ext in COMPILED_EXT:
                compilados.append({"arquivo": rel, "bytes": os.path.getsize(p)})
                continue
            total_arquivos += 1
            try:
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            linhas = txt.splitlines()
            for cid, sev, desc, pats in CLASSES:
                if cid == "DEP_LOCKFILE":
                    continue
                for pat in pats:
                    try:
                        rx = re.compile(pat)
                    except re.error:
                        continue
                    for i, linha in enumerate(linhas, 1):
                        if rx.search(linha):
                            achados[cid].append({
                                "repo": repo, "arquivo": rel, "linha": i,
                                "trecho": linha.strip()[:180],
                            })
    return achados, locks, compilados, total_arquivos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=os.path.join(RAIZ, "varredura_monstra.json"))
    a = ap.parse_args()

    achados, locks, compilados, total = varre()
    print(f"Arquivos de texto varridos: {total}")
    print(f"Lockfiles para auditoria de dependencia: {len(locks)}")
    print(f"Artefatos compilados (alvo de engenharia reversa): {len(compilados)}")
    print("=" * 100)
    for cid, sev, desc, _ in CLASSES:
        itens = achados[cid]
        if not itens:
            continue
        repos = sorted({i["repo"] for i in itens})
        print(f"\n[{cid}] ({sev}) — {len(itens)} ocorrencia(s) em {len(repos)} repo(s)")
        print(f"   {desc}")
        por_repo = {}
        for i in itens:
            por_repo.setdefault(i["repo"], []).append(i)
        for r, lst in sorted(por_repo.items()):
            print(f"   - {r}: {len(lst)}")
            for i in lst[:3]:
                print(f"       {i['arquivo']}:{i['linha']}  {i['trecho'][:110]}")
    print("\n" + "=" * 100)
    print("Artefatos compilados encontrados:")
    for c in compilados[:20]:
        print(f"   {c['bytes']:>9} bytes  {c['arquivo']}")
    print("\nLockfiles:")
    for l in locks[:25]:
        print("   " + l)

    json.dump({"achados": achados, "locks": locks, "compilados": compilados,
               "arquivos_varridos": total},
              open(a.json, "w"), indent=1, ensure_ascii=False)
    print(f"\nJSON salvo em {a.json}")


if __name__ == "__main__":
    main()
