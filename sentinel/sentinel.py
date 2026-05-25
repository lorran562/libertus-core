#!/usr/bin/env python3
"""
SENTINEL — Firmware Intelligence Engine
by LIBERTUS / SHIELD Security Research

Analise proativa e automatica de rootfs de firmware:
  - Inventario de binarios com metadados
  - Deteccao de cadeia NVRAM->system() (command injection patterns)
  - Credenciais hardcoded (senhas, chaves, tokens)
  - Binarios sem protecoes (no PIE, no NX, no stack canary)
  - Score de risco 0-100
  - Relatorio JSON estruturado

Uso: python3 sentinel.py <caminho_rootfs> [--json] [--quiet]
"""

import os
import sys
import json
import re
import hashlib
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

# ─────────────────────────────────────────────
# CONFIGURACOES
# ─────────────────────────────────────────────

REPORTS_DIR = Path(__file__).parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

# Padroes de credenciais hardcoded
CRED_PATTERNS = [
    (r'password\s*=\s*["\']?([^\s"\'<>]{4,})', "password_assignment"),
    (r'passwd\s*=\s*["\']?([^\s"\'<>]{4,})', "passwd_assignment"),
    (r'(?i)admin[:\s]+([^\s:]{4,})', "admin_credential"),
    (r'(?i)root[:\s]+([^\s:]{4,})', "root_credential"),
    (r'(?i)secret[_\-\s]*key\s*[=:]\s*([^\s"\']{8,})', "secret_key"),
    (r'(?i)api[_\-\s]*key\s*[=:]\s*([^\s"\']{8,})', "api_key"),
    (r'(?i)token\s*[=:]\s*([A-Za-z0-9+/=_\-]{16,})', "auth_token"),
    (r'(?i)private[_\-\s]*key', "private_key_ref"),
    (r'BEGIN\s+(?:RSA|EC|DSA|OPENSSH)\s+PRIVATE\s+KEY', "embedded_privkey"),
    (r'(?:[A-Za-z0-9+/]{40,}={0,2})', "b64_blob"),           # base64 blobs longos
    (r'\$1\$[./A-Za-z0-9]{8}\$[./A-Za-z0-9]{22}', "md5crypt_hash"),
    (r'\$5\$[./A-Za-z0-9]{8,16}\$[./A-Za-z0-9]{43}', "sha256crypt_hash"),
    (r'\$6\$[./A-Za-z0-9]{8,16}\$[./A-Za-z0-9]{86}', "sha512crypt_hash"),
    (r'(?:telnet|ftp|http)://[^:@\s]+:[^:@\s]+@', "url_with_creds"),
    (r'(?i)default.{0,10}password.{0,20}([a-zA-Z0-9!@#$]{4,})', "default_password"),
]

# Padroes de funcoes perigosas que indicam attack surface
NVRAM_DANGER_PATTERNS = [
    "nvram_get",
    "nvram_safe_get",
    "acosNvramConfig_get",
    "nvram_set",
    "config_get",
]

EXEC_PATTERNS = [
    "system(",
    "popen(",
    "execve(",
    "execl(",
    "execlp(",
    "execvp(",
    "execvpe(",
    "do_system(",
]

FORMAT_PATTERNS = [
    "sprintf(",
    "snprintf(",
    "vsprintf(",
    "fprintf(",
    "printf(",
    "syslog(",
]

# Strings de debug / backdoor
SUSPICIOUS_STRINGS = [
    "backdoor",
    "debug_mode",
    "test_mode",
    "factory_mode",
    "maintenance",
    "/bin/sh",
    "/bin/bash",
    "telnetd",
    "/dev/tcp",
    "enable_telnet",
    "PermitRootLogin",
    "authorized_keys",
    "dropbear",
    ".ssh/authorized_keys",
    "wget http",
    "curl http",
    "nc -e",
    "ncat",
    "reverse shell",
    "chmod 777",
    "chmod +s",
    "setuid",
]

# Pontuacoes de risco por categoria
RISK_WEIGHTS = {
    "privkey_embedded": 25,
    "crypt_hash": 15,
    "credential_hardcoded": 12,
    "nvram_exec_chain": 20,
    "format_string_risk": 8,
    "no_pie": 5,
    "no_nx": 7,
    "no_canary": 4,
    "suspicious_string": 3,
    "suid_binary": 10,
    "world_writable": 6,
    "url_with_creds": 10,
    "api_key": 8,
}


# ─────────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────────

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return ""


def run(cmd: list[str], timeout=10) -> tuple[int, str, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, errors="replace")
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except FileNotFoundError:
        return -1, "", f"command not found: {cmd[0]}"
    except Exception as e:
        return -1, "", str(e)


def get_strings(path: Path, min_len=6) -> list[str]:
    rc, out, _ = run(["strings", f"-n{min_len}", str(path)])
    if rc != 0:
        return []
    return out.splitlines()


def is_elf(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            magic = f.read(4)
        return magic == b"\x7fELF"
    except Exception:
        return False


def file_info(path: Path) -> dict:
    rc, out, _ = run(["file", str(path)])
    info = {"raw": out.strip()}
    out_lower = out.lower()

    # Arquitetura
    for arch in ["mips", "arm", "x86-64", "x86", "powerpc", "aarch64", "riscv"]:
        if arch in out_lower:
            info["arch"] = arch
            break
    else:
        info["arch"] = "unknown"

    info["stripped"] = "not stripped" not in out_lower and "elf" in out_lower
    info["is_elf"] = "elf" in out_lower
    info["is_script"] = "script" in out_lower or "text" in out_lower
    info["setuid"] = "setuid" in out_lower
    info["setgid"] = "setgid" in out_lower
    return info


def readelf_security(path: Path) -> dict:
    """Verifica protecoes basicas de segurança via readelf."""
    result = {
        "pie": False,
        "nx": False,
        "canary": False,
        "relro": False,
        "rpath": None,
    }

    # PIE: DYN type no ELF header
    rc, out, _ = run(["readelf", "-h", str(path)])
    if rc == 0:
        if "DYN (Shared object file)" in out or "DYN (Position-Independent Executable)" in out:
            result["pie"] = True
        elif "EXEC (Executable file)" in out:
            result["pie"] = False

    # NX: verificar GNU_STACK com permissao
    rc, out, _ = run(["readelf", "-l", str(path)])
    if rc == 0:
        for line in out.splitlines():
            if "GNU_STACK" in line:
                # Formato: GNU_STACK ... RW (sem E = NX habilitado)
                parts = line.split()
                if parts:
                    flags = parts[-1] if len(parts) > 1 else ""
                    result["nx"] = "E" not in flags
                break

    # Canary: __stack_chk_fail nos simbolos dinamicos
    rc, out, _ = run(["readelf", "--syms", "-W", str(path)])
    if rc == 0:
        result["canary"] = "__stack_chk_fail" in out or "__stack_chk_guard" in out

    # RELRO via dynamic section
    rc, out, _ = run(["readelf", "-d", str(path)])
    if rc == 0:
        result["relro"] = "(BIND_NOW)" in out or "RELRO" in out
        # RPATH / RUNPATH - pode indicar DLL hijacking
        for line in out.splitlines():
            if "RPATH" in line or "RUNPATH" in line:
                m = re.search(r'\[(.+?)\]', line)
                if m:
                    result["rpath"] = m.group(1)

    return result


# ─────────────────────────────────────────────
# MODULOS DE ANALISE
# ─────────────────────────────────────────────

def inventory_binaries(rootfs: Path, quiet=False) -> list[dict]:
    """Modulo A: Inventario completo de binarios ELF."""
    if not quiet:
        print("[*] Modulo A: Inventario de binarios...")

    binaries = []
    # Foca em diretorios de executaveis, mas varre tudo
    for path in rootfs.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        try:
            stat = path.stat()
        except Exception:
            continue

        if not is_elf(path):
            continue

        finfo = file_info(path)
        entry = {
            "path": str(path.relative_to(rootfs)),
            "abs_path": str(path),
            "size": stat.st_size,
            "sha256": sha256_file(path),
            "arch": finfo.get("arch", "unknown"),
            "stripped": finfo.get("stripped", True),
            "setuid": finfo.get("setuid", False),
            "setgid": finfo.get("setgid", False),
            "file_raw": finfo.get("raw", ""),
        }

        # Permissoes
        mode = stat.st_mode
        entry["world_writable"] = bool(mode & 0o002)
        entry["world_executable"] = bool(mode & 0o001)

        binaries.append(entry)

    if not quiet:
        print(f"    -> {len(binaries)} ELFs encontrados")
    return binaries


def detect_nvram_chains(rootfs: Path, binaries: list[dict], quiet=False) -> list[dict]:
    """Modulo B: Detecta cadeias NVRAM->system() em binarios ELF."""
    if not quiet:
        print("[*] Modulo B: Deteccao de cadeias NVRAM->exec...")

    chains = []
    for b in binaries:
        path = Path(b["abs_path"])
        strings_list = get_strings(path)
        if not strings_list:
            continue

        found_nvram = [s for s in NVRAM_DANGER_PATTERNS
                       if any(s in line for line in strings_list)]
        found_exec  = [s for s in EXEC_PATTERNS
                       if any(s.split("(")[0] in line for line in strings_list)]
        found_fmt   = [s for s in FORMAT_PATTERNS
                       if any(s.split("(")[0] in line for line in strings_list)]

        if found_nvram and found_exec:
            risk = "HIGH"
            if found_fmt:
                risk = "CRITICAL"  # NVRAM -> sprintf -> system = clássico RCE

            chains.append({
                "binary": b["path"],
                "nvram_funcs": found_nvram,
                "exec_funcs": found_exec,
                "format_funcs": found_fmt,
                "risk": risk,
                "pattern": "NVRAM_EXEC_CHAIN",
                "note": "nvram_get() output pode fluir para execucao de comando sem sanitizacao",
            })

    if not quiet:
        print(f"    -> {len(chains)} cadeias NVRAM->exec detectadas")
    return chains


def detect_credentials(rootfs: Path, quiet=False) -> list[dict]:
    """Modulo C: Credenciais hardcoded em arquivos de texto e binarios."""
    if not quiet:
        print("[*] Modulo C: Deteccao de credenciais hardcoded...")

    findings = []

    for path in rootfs.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue

        # Pula arquivos muito grandes (> 10MB)
        try:
            size = path.stat().st_size
            if size > 10 * 1024 * 1024:
                continue
        except Exception:
            continue

        # Usa strings para extrair conteudo legivel (funciona em binarios tb)
        content_lines = get_strings(path, min_len=4)
        if not content_lines:
            # Tenta leitura direta para arquivos de texto
            try:
                content = path.read_text(errors="replace")
                content_lines = content.splitlines()
            except Exception:
                continue

        rel_path = str(path.relative_to(rootfs))
        matched_types = set()

        for line in content_lines:
            for pattern, ptype in CRED_PATTERNS:
                if ptype in matched_types:
                    continue  # uma ocorrencia por tipo por arquivo
                m = re.search(pattern, line)
                if m:
                    # Filtra falsos positivos obvios
                    value = m.group(0)
                    if len(value) < 4 or value in ("password", "passwd", "PASS"):
                        continue

                    findings.append({
                        "file": rel_path,
                        "type": ptype,
                        "match": value[:120],  # trunca para nao encher relatorio
                        "line_preview": line.strip()[:200],
                        "severity": _cred_severity(ptype),
                    })
                    matched_types.add(ptype)

    if not quiet:
        print(f"    -> {len(findings)} ocorrencias de credenciais encontradas")
    return findings


def _cred_severity(ptype: str) -> str:
    if ptype in ("embedded_privkey", "md5crypt_hash",
                 "sha256crypt_hash", "sha512crypt_hash"):
        return "CRITICAL"
    if ptype in ("password_assignment", "passwd_assignment",
                 "root_credential", "secret_key", "api_key"):
        return "HIGH"
    if ptype in ("admin_credential", "url_with_creds", "auth_token"):
        return "MEDIUM"
    return "LOW"


def detect_missing_protections(binaries: list[dict], quiet=False) -> list[dict]:
    """Modulo D: Binarios sem PIE/NX/canary."""
    if not quiet:
        print("[*] Modulo D: Verificando protecoes de binarios ELF...")

    findings = []
    for b in binaries:
        path = Path(b["abs_path"])
        sec = readelf_security(path)

        missing = []
        if not sec["pie"]:
            missing.append("no-PIE")
        if not sec["nx"]:
            missing.append("no-NX")
        if not sec["canary"]:
            missing.append("no-canary")
        if not sec["relro"]:
            missing.append("no-RELRO")
        if sec["rpath"]:
            missing.append(f"RPATH={sec['rpath']}")

        if missing:
            findings.append({
                "binary": b["path"],
                "arch": b["arch"],
                "size": b["size"],
                "missing_protections": missing,
                "setuid": b.get("setuid", False),
                "stripped": b.get("stripped", True),
                "risk_score_contribution": len(missing) * 4,
                "security_info": sec,
            })

    if not quiet:
        print(f"    -> {len(findings)} binarios com protecoes faltando")
    return findings


def detect_suspicious_strings(rootfs: Path, binaries: list[dict], quiet=False) -> list[dict]:
    """Detecta strings altamente suspeitas (backdoors, shells, etc)."""
    if not quiet:
        print("[*] Bonus: Deteccao de strings suspeitas...")

    findings = []
    for b in binaries:
        path = Path(b["abs_path"])
        strings_list = get_strings(path)
        hits = []
        for suspect in SUSPICIOUS_STRINGS:
            for line in strings_list:
                if suspect.lower() in line.lower():
                    hits.append({"pattern": suspect, "line": line.strip()[:200]})
                    break  # 1 hit por pattern por binario

        if hits:
            findings.append({
                "binary": b["path"],
                "hits": hits,
                "count": len(hits),
            })

    if not quiet:
        print(f"    -> {len(findings)} binarios com strings suspeitas")
    return findings


# ─────────────────────────────────────────────
# SCORE DE RISCO
# ─────────────────────────────────────────────

def calculate_risk_score(chains, credentials, protections, suspicious) -> tuple[int, dict]:
    """Calcula score de risco 0-100 com breakdown."""
    breakdown = defaultdict(int)
    total = 0

    # Cadeias NVRAM->exec
    for c in chains:
        w = RISK_WEIGHTS["nvram_exec_chain"]
        if c["risk"] == "CRITICAL":
            w = int(w * 1.5)
        breakdown["nvram_exec_chains"] += w
        total += w

    # Credenciais
    for cred in credentials:
        ptype = cred["type"]
        severity = cred["severity"]
        if "privkey" in ptype:
            w = RISK_WEIGHTS["privkey_embedded"]
        elif "crypt_hash" in ptype:
            w = RISK_WEIGHTS["crypt_hash"]
        elif "url_with_creds" in ptype:
            w = RISK_WEIGHTS["url_with_creds"]
        elif severity == "HIGH":
            w = RISK_WEIGHTS["credential_hardcoded"]
        elif severity == "MEDIUM":
            w = 6
        else:
            w = 2
        breakdown["credentials"] += w
        total += w

    # Protecoes faltando
    for p in protections:
        if "no-NX" in p["missing_protections"]:
            breakdown["no_nx"] += RISK_WEIGHTS["no_nx"]
            total += RISK_WEIGHTS["no_nx"]
        if "no-PIE" in p["missing_protections"]:
            breakdown["no_pie"] += RISK_WEIGHTS["no_pie"]
            total += RISK_WEIGHTS["no_pie"]
        if "no-canary" in p["missing_protections"]:
            breakdown["no_canary"] += RISK_WEIGHTS["no_canary"]
            total += RISK_WEIGHTS["no_canary"]
        if p.get("setuid"):
            breakdown["suid_binaries"] += RISK_WEIGHTS["suid_binary"]
            total += RISK_WEIGHTS["suid_binary"]

    # Strings suspeitas
    for s in suspicious:
        w = s["count"] * RISK_WEIGHTS["suspicious_string"]
        breakdown["suspicious_strings"] += w
        total += w

    # Normaliza para 0-100
    score = min(100, total)
    return score, dict(breakdown)


def risk_label(score: int) -> str:
    if score >= 75:
        return "CRITICAL"
    if score >= 50:
        return "HIGH"
    if score >= 25:
        return "MEDIUM"
    if score > 0:
        return "LOW"
    return "CLEAN"


# ─────────────────────────────────────────────
# RELATORIO
# ─────────────────────────────────────────────

def build_report(rootfs: Path, binaries, chains, credentials,
                 protections, suspicious, score, breakdown) -> dict:

    ts = datetime.now(timezone.utc).isoformat()
    firmware_name = rootfs.parent.parent.name  # melhor esforco

    report = {
        "sentinel_version": "1.0.0",
        "timestamp": ts,
        "firmware_id": firmware_name,
        "rootfs_path": str(rootfs),
        "risk_score": score,
        "risk_label": risk_label(score),
        "score_breakdown": breakdown,
        "summary": {
            "total_elf_binaries": len(binaries),
            "nvram_exec_chains": len(chains),
            "credential_findings": len(credentials),
            "binaries_without_protections": len(protections),
            "suspicious_string_hits": len(suspicious),
            "architectures": list(set(b["arch"] for b in binaries)),
            "stripped_binaries": sum(1 for b in binaries if b["stripped"]),
            "setuid_binaries": sum(1 for b in binaries if b.get("setuid")),
        },
        "findings": {
            "nvram_exec_chains": chains,
            "credentials": credentials,
            "missing_protections": protections,
            "suspicious_strings": suspicious,
        },
        "binary_inventory": binaries,
        "meta": {
            "tool": "SENTINEL",
            "author": "LIBERTUS / SHIELD Security Research",
            "purpose": "Proactive firmware vulnerability intelligence",
        }
    }
    return report


def save_report(report: dict, rootfs: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    firmware_id = report["firmware_id"].replace("/", "_").replace(" ", "_")
    filename = REPORTS_DIR / f"sentinel_{firmware_id}_{ts}.json"
    with open(filename, "w") as f:
        json.dump(report, f, indent=2, default=str)
    return filename


def print_summary(report: dict):
    score = report["risk_score"]
    label = report["risk_label"]
    s = report["summary"]
    bd = report["score_breakdown"]

    print()
    print("=" * 62)
    print("  SENTINEL — FIRMWARE INTELLIGENCE REPORT")
    print("=" * 62)
    print(f"  Firmware  : {report['firmware_id']}")
    print(f"  Timestamp : {report['timestamp']}")
    print(f"  Rootfs    : {report['rootfs_path']}")
    print("-" * 62)
    print(f"  RISK SCORE : {score}/100  [{label}]")
    print("-" * 62)
    print(f"  ELFs encontrados      : {s['total_elf_binaries']}")
    print(f"  Arquiteturas          : {', '.join(s['architectures'])}")
    print(f"  Stripped              : {s['stripped_binaries']}")
    print(f"  SetUID                : {s['setuid_binaries']}")
    print(f"  Cadeias NVRAM->exec   : {s['nvram_exec_chains']}")
    print(f"  Credenciais           : {s['credential_findings']}")
    print(f"  Sem protecoes         : {s['binaries_without_protections']}")
    print(f"  Strings suspeitas     : {s['suspicious_string_hits']}")
    print("-" * 62)

    if bd:
        print("  Score Breakdown:")
        for k, v in sorted(bd.items(), key=lambda x: -x[1]):
            print(f"    {k:<30} +{v}")

    findings = report["findings"]

    if findings["nvram_exec_chains"]:
        print()
        print("  [!] NVRAM->EXEC CHAINS (possivel Command Injection):")
        for c in findings["nvram_exec_chains"][:5]:
            print(f"    [{c['risk']}] {c['binary']}")
            print(f"         nvram: {c['nvram_funcs']}")
            print(f"         exec : {c['exec_funcs']}")
            if c["format_funcs"]:
                print(f"         fmt  : {c['format_funcs']}")

    if findings["credentials"]:
        print()
        print("  [!] CREDENCIAIS HARDCODED (amostra):")
        seen = set()
        for cred in findings["credentials"][:8]:
            key = cred["file"] + cred["type"]
            if key in seen:
                continue
            seen.add(key)
            print(f"    [{cred['severity']}] {cred['file']} — {cred['type']}")
            print(f"         {cred['line_preview'][:100]}")

    print("=" * 62)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="SENTINEL — Proactive Firmware Intelligence Engine"
    )
    parser.add_argument("rootfs", help="Caminho para o rootfs extraido")
    parser.add_argument("--json", action="store_true", help="Saida JSON no stdout")
    parser.add_argument("--quiet", "-q", action="store_true", help="Menos output")
    parser.add_argument("--no-creds", action="store_true",
                        help="Pula deteccao de credenciais (mais rapido)")
    args = parser.parse_args()

    rootfs = Path(args.rootfs).resolve()
    if not rootfs.exists() or not rootfs.is_dir():
        print(f"[ERRO] Rootfs nao encontrado: {rootfs}")
        sys.exit(1)

    if not args.quiet:
        print(f"\n[SENTINEL] Analisando: {rootfs}")
        print(f"[SENTINEL] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    # Executa modulos
    binaries    = inventory_binaries(rootfs, quiet=args.quiet)
    chains      = detect_nvram_chains(rootfs, binaries, quiet=args.quiet)
    credentials = [] if args.no_creds else detect_credentials(rootfs, quiet=args.quiet)
    protections = detect_missing_protections(binaries, quiet=args.quiet)
    suspicious  = detect_suspicious_strings(rootfs, binaries, quiet=args.quiet)

    # Score
    score, breakdown = calculate_risk_score(chains, credentials, protections, suspicious)

    # Relatorio
    report = build_report(rootfs, binaries, chains, credentials,
                          protections, suspicious, score, breakdown)

    report_path = save_report(report, rootfs)
    report["_saved_to"] = str(report_path)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print_summary(report)
        if not args.quiet:
            print(f"\n[SENTINEL] Relatorio salvo em: {report_path}")

    return 0 if score < 25 else 1


if __name__ == "__main__":
    sys.exit(main())
