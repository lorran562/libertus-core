#!/usr/bin/env python3
"""
run_graphify.py — roda `graphify extract` carregando as chaves do .env no
ambiente, sem passar credencial por linha de comando shell (evita mangle/log).

Uso:
    python3 scripts/run_graphify.py claude corpus_graphify
    python3 scripts/run_graphify.py groq   corpus_graphify   6000
"""
import os
import subprocess
import sys
from pathlib import Path

BASE = Path("/home/libertus/LIBERTUS")


def load_env():
    for line in (BASE / ".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip()


def main():
    backend = sys.argv[1] if len(sys.argv) > 1 else "claude"
    target = sys.argv[2] if len(sys.argv) > 2 else "corpus_graphify"
    load_env()

    env = os.environ.copy()
    cmd = ["graphify", "extract", target]

    if backend == "claude":
        env.setdefault("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        cmd += ["--backend", "claude"]
    elif backend == "groq":
        budget = sys.argv[3] if len(sys.argv) > 3 else "6000"
        env["OPENAI_API_KEY"] = env.get("GROQ_API_KEY", "")
        env["OPENAI_BASE_URL"] = "https://api.groq.com/openai/v1"
        env["GRAPHIFY_OPENAI_MODEL"] = "llama-3.3-70b-versatile"
        cmd += ["--backend", "openai", "--token-budget", budget, "--max-concurrency", "1"]
    else:
        print(f"backend desconhecido: {backend}")
        sys.exit(2)

    print(f"[run_graphify] backend={backend} target={target}")
    print(f"[run_graphify] cmd={' '.join(cmd)}")
    r = subprocess.run(cmd, env=env, cwd=str(BASE))
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
