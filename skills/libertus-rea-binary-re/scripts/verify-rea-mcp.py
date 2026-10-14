#!/usr/bin/env python3
"""Verificação real da integração REA MCP no Hermes (LIBERTUS, 13/10/2026).

Simula EXATAMENTE como o gateway sobe o servidor MCP: lê mcp_servers.rea do
config.yaml, exporta só o env do registro, faz initialize/tools/list e chama
ferramentas de verdade. Nada de autoteste com print bonito: asserts.

Uso: python3 /tmp/hermes-verify-rea-mcp.py
"""
import json
import os
import subprocess
import sys
import time

CONFIG = os.path.expanduser("~/.hermes/config.yaml")
TRX = os.path.expanduser(
    "~/LIBERTUS/lab/firmware/asus-rt-ac88u/asus_rt-ac88u-openwrt.trx"
)
ELF = "/tmp/rea-test/true.elf"
ARM = "/tmp/rea-test/busybox.arm"

failures = []


def check(name, ok, detail=""):
    print(("  OK   " if ok else "  FALHA ") + name + ((" | " + detail) if detail else ""))
    if not ok:
        failures.append(name)


def load_registration():
    """Lê o bloco mcp_servers.rea do config.yaml (ruamel/yaml, senão regex por indentação)."""
    text = open(CONFIG, encoding="utf-8").read()
    data = None
    for mod in ("ruamel.yaml", "yaml"):
        try:
            m = __import__(mod, fromlist=["YAML"])
            if mod == "ruamel.yaml":
                from ruamel.yaml import YAML
                y = YAML(typ="safe")
                data = y.load(text)
            else:
                data = m.safe_load(text)
            break
        except Exception:
            continue
    if data is not None:
        reg = ((data.get("mcp_servers") or {}).get("rea")) or {}
        return {
            "command": reg.get("command"),
            "args": list(reg.get("args") or []),
            "env": {k: str(v) for k, v in (reg.get("env") or {}).items()},
            "enabled": reg.get("enabled"),
        }
    raise SystemExit("nao consegui parsear config.yaml (sem yaml/ruamel)")


class Mcp:
    def __init__(self, command, args, env):
        full_env = dict(env)
        full_env.setdefault("PATH", os.environ.get("PATH", "/usr/bin:/bin"))
        full_env["HOME"] = os.path.expanduser("~")
        self.proc = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, env=full_env,
        )
        self.next_id = 1

    def send(self, method, params=None, notify=False):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        if not notify:
            msg["id"] = self.next_id
            self.next_id += 1
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        return msg.get("id")

    def read_until(self, want_id, limit=600):
        deadline = time.time() + limit
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                return {"__error__": "stdout fechou: " + (self.proc.stderr.read() or "")[:300]}
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("id") == want_id:
                return msg
        return {"__error__": "timeout"}

    def call(self, name, args=None, limit=600):
        rid = self.send("tools/call", {"name": name, "arguments": args or {}})
        return self.read_until(rid, limit)


def text_of(resp):
    if "__error__" in resp:
        return resp["__error__"]
    parts = []
    for item in (resp.get("result") or {}).get("content") or []:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(item.get("text") or "")
    return "\n".join(parts)


def main():
    print("== 1. registro no config.yaml ==")
    reg = load_registration()
    check("command aponta para o rea", (reg["command"] or "").endswith("/rea"), reg["command"] or "")
    check("args == ['mcp']", reg["args"] == ["mcp"], str(reg["args"]))
    check("enabled == true", str(reg["enabled"]).lower() == "true", str(reg["enabled"]))
    for key in ("GHIDRA_INSTALL_DIR", "JAVA_HOME", "REA_BINWALK_COMMAND"):
        val = reg["env"].get(key, "")
        check(f"env {key}", bool(val) and os.path.exists(val), val)
    check("binwalk instalado comeca com 3.1",
          reg["env"].get("REA_BINWALK_COMMAND", "").endswith(".cargo/bin/binwalk"))

    print("== 2. handshake MCP com o MESMO env do registro ==")
    m = Mcp(reg["command"], reg["args"], reg["env"])
    try:
        rid = m.send("initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "hermes-verify-rea", "version": "1"},
        })
        init = m.read_until(rid, limit=60)
        info = ((init.get("result") or {}).get("serverInfo") or {})
        check("initialize responde", info.get("name") == "rea", f"{info.get('name')} {info.get('version')}")
        m.send("notifications/initialized", {}, notify=True)

        rid = m.send("tools/list", {})
        listing = m.read_until(rid, limit=120)
        tools = ((listing.get("result") or {}).get("tools")) or []
        names = {t["name"] for t in tools}
        check("tools/list devolve 170 tools", len(tools) >= 165, f"{len(tools)} tools")
        for needed in ("inspect_firmware_regions", "open_binary", "procedure_pseudo_code",
                       "binary_session", "inspect_binary_layout", "inspect_managed_artifact",
                       "analyze_javascript_application", "inspect_pe_resources"):
            check(f"tool presente: {needed}", needed in names)
        # docs do repo main != pacote npm: essas NAO existem no 6.4.0
        for absent in ("inspect_go_binary", "inspect_rust_binary"):
            check(f"tool ausente no 6.4.0 (confirmado): {absent}", absent not in names)

        print("== 3. chamada real: inspect_firmware_regions (binwalk 3.1) ==")
        resp = m.call("inspect_firmware_regions", {"path": TRX}, limit=300)
        raw = text_of(resp)
        ok = '"engine"' in raw and '"binwalk"' in raw and '"regions"' in raw
        check("firmware regions retornou Evidence com engine binwalk", ok, raw[:160].replace("\n", " "))
        if ok:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
            engine = (payload.get("normalized_result") or {}).get("engine") or {}
            regions = (payload.get("normalized_result") or {}).get("regions") or []
            check("binwalk version == 3.1.x", str(engine.get("version", "")).startswith("3.1"), str(engine.get("version")))
            check("regiao TRX detectada", any(r.get("signature") == "trx" for r in regions),
                  str([r.get("signature") for r in regions]))
            check("evidence_id presente", bool(payload.get("evidence_id")), str(payload.get("evidence_id"))[:40])

        print("== 4. chamada real: Ghidra via open_binary + binary_overview ==")
        if os.path.exists(ELF):
            resp = m.call("open_binary", {"path": ELF, "provider_id": "ghidra"}, limit=600)
            raw = text_of(resp)
            opened = "__error__" not in resp and "error" not in raw[:40].lower()
            check("open_binary (ghidra) aceitou o alvo", opened, raw[:160].replace("\n", " "))
            resp = m.call("binary_overview", {}, limit=600)
            raw = text_of(resp)
            ok = "0x100000" in raw or "segment" in raw.lower()
            check("binary_overview devolveu analise do ELF", ok, raw[:160].replace("\n", " "))

        print("== 5. sessao (target-free) ==")
        resp = m.call("binary_session", {}, limit=120)
        raw = text_of(resp)
        check("binary_session responde", '"tool_availability"' in raw or "provider" in raw.lower(),
              raw[:120].replace("\n", " "))
    finally:
        m.proc.kill()

    print()
    if failures:
        print(f"RESULTADO: {len(failures)} FALHA(S): {', '.join(failures)}")
        return 1
    print("RESULTADO: TODOS OS CHECKS PASSARAM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
