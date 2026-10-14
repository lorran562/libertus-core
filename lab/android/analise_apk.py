#!/usr/bin/env python3
"""Analise estatica de APK Android — classes de falha que PAGAM em bug bounty.

Feito para o alvo de jogo (Roblox) mas serve para qualquer APK.
100% estatico: le um APK local + o manifest decodificado + a saida do jadx.
NAO instala, NAO executa, NAO contata nenhum servidor.

Uso:
    python3 analise_apk.py <arquivo.apk> [--decoded DIR] [--jadx DIR] [--json saida.json]

Pre-requisitos (todos ja instalados nesta maquina):
    apktool   ~/.local/bin/apktool            (wrapper do jar, JDK 21 em ~/tools)
    jadx      ~/.local/bin/jadx
    jadx-headless-mcp  ~/tools/android/jadx-headless-mcp.jar  (para o REA)
"""
import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

NS = "{http://schemas.android.com/apk/res/android}"

# permissoes que costumam virar finding quando combinadas com componente exportado
PERMIGOSAS = {
    "android.permission.READ_EXTERNAL_STORAGE": "leitura de arquivo do usuario",
    "android.permission.WRITE_EXTERNAL_STORAGE": "escrita em arquivo do usuario",
    "android.permission.READ_CONTACTS": "contatos",
    "android.permission.ACCESS_FINE_LOCATION": "localizacao precisa",
    "android.permission.RECORD_AUDIO": "microfone",
    "android.permission.CAMERA": "camera",
    "android.permission.READ_PHONE_STATE": "identificadores do aparelho",
    "android.permission.QUERY_ALL_PACKAGES": "lista todos os apps instalados",
    "android.permission.REQUEST_INSTALL_PACKAGES": "instala APK (vetor de malware)",
    "android.permission.SYSTEM_ALERT_WINDOW": "sobreposicao de tela (overlay)",
    "android.permission.BIND_ACCESSIBILITY_SERVICE": "acessibilidade (le tudo na tela)",
    "android.permission.RECEIVE_BOOT_COMPLETED": "inicia sozinho no boot",
}

# padroes perigosos no codigo decompilado (jadx)
CODIGO_RISCO = [
    ("WEBVIEW_JS_INTERFACE", "addJavascriptInterface",
     "interface Java exposta ao JavaScript da WebView (ponte de ataque classica)"),
    ("WEBVIEW_FILE_ACCESS", "setAllowFileAccess",
     "WebView com acesso a arquivo local"),
    ("WEBVIEW_UNIVERSAL_FILE_ACCESS", "setAllowUniversalAccessFromFileURLs",
     "qualquer origem le arquivo local (file:// -> http)"),
    ("WEBVIEW_FILE_ORIGIN", "setAllowFileAccessFromFileURLs",
     "file:// lendo outras origens"),
    ("SSL_BYPASS", "onReceivedSslError",
     "tratamento custom de erro TLS (se chamar proceed(), desliga a validacao)"),
    ("SSL_PROCEED", "proceed()",
     "prossegue mesmo com erro de certificado"),
    ("TRUST_ALL", "TrustAllCerts|ALLOW_ALL_HOSTNAME|NoopHostnameVerifier|setDefaultHostnameVerifier",
     "verificacao de certificado desativada"),
    ("EXPORTED_ACTIVITY_LAUNCH", "getIntent().getStringExtra|getIntent().getData()",
     "leitura de dado vindo de Intent (se o componente for exportado = superficie real)"),
    ("LOGGING_SENSIVEL", r"Log\.[dve]\(.*(token|senha|password|cpf|email|auth)",
     "dado sensivel em log"),
    ("HARDCODED_SECRET", r"(?i)(api[_-]?key|secret|token|password)\s*=\s*\"[A-Za-z0-9_\-]{16,}\"",
     "segredo em codigo"),
    ("HTTP_URL", r"http://[a-z0-9.\-]+\.[a-z]{2,}",
     "endpoint HTTP sem TLS"),
    ("DEEP_LINK_SCHEME", r'"(roblox|robloxmobile)://',
     "deep link proprio (checar validacao de parametro)"),
]

SENSIVEL_LOG = re.compile(r"(token|senha|password|cpf|email|auth|session)", re.I)


def roda(cmd, timeout=600):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except Exception as e:
        return -1, "", f"{type(e).__name__}: {e}"


def decodifica(apk, saida):
    apktool = os.path.expanduser("~/.local/bin/apktool")
    if not os.path.exists(apktool):
        print("!! apktool nao encontrado", file=sys.stderr)
        return False
    rc, out, err = roda([apktool, "d", "-f", "-s", apk, "-o", saida], timeout=900)
    if rc != 0:
        print("!! apktool falhou:", (err or out)[-400:], file=sys.stderr)
        return False
    return True


def componentes(manifest_xml):
    """Componentes exportados e deeplinks — a superficie que importa."""
    res = {"exportados": [], "deeplinks": [], "perigosos": [], "flags": {}}
    try:
        arv = ET.parse(manifest_xml).getroot()
    except Exception as e:
        res["erro"] = f"{type(e).__name__}: {e}"
        return res

    app = arv.find("application")
    if app is not None:
        res["flags"] = {
            "debuggable": app.get(NS + "debuggable"),
            "allowBackup": app.get(NS + "allowBackup"),
            "usesCleartextTraffic": app.get(NS + "usesCleartextTraffic"),
            "networkSecurityConfig": app.get(NS + "networkSecurityConfig"),
            "taskAffinity": app.get(NS + "taskAffinity"),
            "requestLegacyExternalStorage": app.get(NS + "requestLegacyExternalStorage"),
        }

    for tag in ("activity", "activity-alias", "service", "receiver", "provider"):
        for c in arv.iter(tag):
            nome = c.get(NS + "name")
            exp = c.get(NS + "exported")
            perm = c.get(NS + "permission")
            if exp == "true" or (exp is None and c.findall("intent-filter")):
                res["exportados"].append({
                    "tipo": tag, "nome": nome, "exported": exp,
                    "permission": perm,
                    "tem_filtro": bool(c.findall("intent-filter")),
                    "grantUriPermissions": c.get(NS + "grantUriPermissions"),
                    "authorities": c.get(NS + "authorities"),
                })
            for f in c.findall("intent-filter"):
                for d in f.findall("data"):
                    sch, host, path = d.get(NS + "scheme"), d.get(NS + "host"), d.get(NS + "pathPrefix") or d.get(NS + "path")
                    if sch:
                        res["deeplinks"].append({"componente": nome, "scheme": sch, "host": host, "path": path})

    for p in arv.iter("uses-permission"):
        n = p.get(NS + "name")
        if n in PERMIGOSAS:
            res["perigosos"].append({"permissao": n, "porque": PERMIGOSAS[n]})
    return res


def varre_codigo(jadx_dir, limite_por_padrao=4):
    achados = {}
    if not jadx_dir or not os.path.isdir(jadx_dir):
        return achados
    for raiz, _, arquivos in os.walk(jadx_dir):
        for f in arquivos:
            if not f.endswith((".java", ".kt", ".xml")):
                continue
            p = os.path.join(raiz, f)
            try:
                if os.path.getsize(p) > 3_000_000:
                    continue
                txt = open(p, encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
            for cid, padrao, desc in CODIGO_RISCO:
                if len(achados.get(cid, [])) >= limite_por_padrao:
                    continue
                try:
                    m = re.search(padrao, txt)
                except re.error:
                    continue
                if m:
                    linha = txt[:m.start()].count("\n") + 1
                    trecho = txt.splitlines()[linha - 1].strip()[:150] if linha <= len(txt.splitlines()) else ""
                    achados.setdefault(cid, []).append({
                        "arquivo": os.path.relpath(p, jadx_dir), "linha": linha,
                        "trecho": trecho, "descricao": desc,
                    })
    return achados


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("apk")
    ap.add_argument("--decoded", default=None)
    ap.add_argument("--jadx", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    base = os.path.splitext(a.apk)[0]
    decoded = a.decoded or (base + "_decoded")
    jadx_dir = a.jadx
    if not os.path.isdir(decoded):
        print("decodificando com apktool...", file=sys.stderr)
        if not decodifica(a.apk, decoded):
            sys.exit(1)

    out = {"apk": os.path.abspath(a.apk), "bytes": os.path.getsize(a.apk)}
    man = os.path.join(decoded, "AndroidManifest.xml")
    if os.path.exists(man):
        out["componentes"] = componentes(man)
    if os.path.exists(jadx_dir or ""):
        print("varrendo codigo decompilado...", file=sys.stderr)
        out["codigo"] = varre_codigo(jadx_dir)

    print("=" * 95)
    print("APK:", out["apk"], f"({out['bytes']/1e6:.1f} MB)")
    c = out.get("componentes", {})
    f = c.get("flags", {})
    print("\n-- FLAGS DO MANIFESTO --")
    for k, v in f.items():
        flag = "  <<< ATENCAO" if (k == "debuggable" and v == "true") or (k == "allowBackup" and v != "false") or (k == "usesCleartextTraffic" and v == "true") else ""
        print(f"   {k}: {v}{flag}")
    print(f"\n-- COMPONENTES EXPORTADOS ({len(c.get('exportados', []))}) --")
    for x in c.get("exportados", [])[:20]:
        seg = "" if x.get("permission") else "  <<< SEM permissao exigida"
        print(f"   [{x['tipo']}] {x['nome']}{seg}")
    print(f"\n-- DEEPLINKS ({len(c.get('deeplinks', []))}) --")
    for x in c.get("deeplinks", [])[:15]:
        print(f"   {x['scheme']}://{x.get('host') or ''}{x.get('path') or ''}  -> {x['componente']}")
    print(f"\n-- PERMISSOES RELEVANTES ({len(c.get('perigosos', []))}) --")
    for x in c.get("perigosos", []):
        print(f"   {x['permissao']}  ({x['porque']})")
    cod = out.get("codigo", {})
    if cod:
        print("\n-- PADROES DE RISCO NO CODIGO --")
        for cid, itens in cod.items():
            print(f"\n   [{cid}] {itens[0]['descricao']}  ({len(itens)} ocorrencia(s))")
            for i in itens:
                print(f"      {i['arquivo']}:{i['linha']}  {i['trecho'][:110]}")

    if a.json:
        json.dump(out, open(a.json, "w"), indent=1, ensure_ascii=False)
        print(f"\nJSON: {a.json}")


if __name__ == "__main__":
    main()
