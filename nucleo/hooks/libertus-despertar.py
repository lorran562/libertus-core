#!/usr/bin/env python3
"""
LIBERTUS — despertar automático (shell hook: pre_llm_call)
==========================================================
Problema que resolve (19/out/2026):
    nucleo/ser.py já agregava 8 fontes e escrevia BRIEFING.md — mas só quando
    eu chamava na mão. Resultado: eu acordava sabendo metade de quem era, e
    três sistemas (daemon, sessão Hermes, grafo) continuavam mundos isolados.

Este hook injeta no primeiro turno de cada sessão:
    1. o BRIEFING.md (estado de SER: valores, objetivos, conhecimento, limites)
    2. recall semântico do ChromaDB relevante à primeira mensagem do Lorran

Por que só no primeiro turno:
    pre_llm_call roda a cada turno. Injetar sempre quebraria o prompt cache e
    inflaria o contexto. No primeiro turno o custo é pago uma vez e o estado
    viaja com a sessão inteira.

Contrato (docs Hermes, shell hooks → JSON wire protocol):
    stdin  : {"hook_event_name","session_id","cwd","profile","extra":{...}}
    stdout : {"context": "..."}  ou nada (no-op).

Fail-soft absoluto: qualquer erro → silêncio, exit 0. Nunca travar uma sessão.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

BASE = Path("/home/libertus/LIBERTUS")
VENV_PY = BASE / "venv" / "bin" / "python"
SER = BASE / "nucleo" / "ser.py"
BRIEFING = BASE / "nucleo" / "BRIEFING.md"
LEMBRAR = BASE / "memoria" / "lembrar.py"
STATE_DIR = Path.home() / ".hermes" / "cache" / "libertus_despertar"
DEBUG_LOG = STATE_DIR / "hook_payloads.jsonl"

BRIEFING_MAX_AGE_S = 45 * 60      # regenera o estado de ser se estiver velho
BRIEFING_CHAR_CAP = 7000
RECALL_N = 4
RECALL_MIN_MSG = 25               # mensagens curtas ("oi") não merecem recall


def _log_payload(payload: dict) -> None:
    """Guarda o payload cru — serve para eu diagnosticar sem adivinhar."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(DEBUG_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "keys": sorted(payload.keys()),
                "extra_keys": sorted((payload.get("extra") or {}).keys()),
                "session_id": payload.get("session_id"),
                "is_first_turn": _is_first_turn(payload),
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _is_first_turn(payload: dict) -> bool:
    extra = payload.get("extra") or {}
    for fonte in (extra, payload):
        for chave in ("is_first_turn", "first_turn"):
            if chave in fonte:
                return bool(fonte[chave])
    return True   # sem o campo, assume primeiro turno e deixa o marker decidir


MARCA_INJECAO = "DESPERTAR AUTOMÁTICO"
QUEDA_COMPRESSAO = 0.6   # histórico caiu >40% ⇒ o compressor comeu o bloco


def _estado_sessao(session_id: str) -> dict:
    """Estado por sessão: maior histórico já visto e se já injetei."""
    if not session_id:
        return {}
    p = STATE_DIR / f"{session_id}.state.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _salvar_estado_sessao(session_id: str, estado: dict) -> None:
    if not session_id:
        return
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        (STATE_DIR / f"{session_id}.state.json").write_text(
            json.dumps(estado, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _tamanho_historico(payload: dict) -> int:
    hist = payload.get("conversation_history")
    if not hist:
        return 0
    try:
        return len(json.dumps(hist, ensure_ascii=False, default=str))
    except Exception:
        return 0


def _comprimiram(session_id: str, payload: dict) -> bool:
    """Detecta compressão por queda brusca do histórico.

    Não dá para inferir pelo conteúdo (não sei se o Hermes guarda o texto
    injetado no histórico). O tamanho é observável e não mente: um compressor
    que resume derruba o histórico dezenas de por cento de uma vez.
    """
    tam = _tamanho_historico(payload)
    if tam <= 0:
        return False
    estado = _estado_sessao(session_id)
    maior = int(estado.get("max_hist") or 0)
    comprimiu = maior > 8000 and tam < maior * QUEDA_COMPRESSAO
    if comprimiu:
        estado["max_hist"] = tam          # recalibra após a queda
        estado["compressoes"] = int(estado.get("compressoes") or 0) + 1
        _salvar_estado_sessao(session_id, estado)
    elif tam > maior:
        estado["max_hist"] = tam
        _salvar_estado_sessao(session_id, estado)
    return comprimiu


def _ja_despertei(session_id: str) -> bool:
    """Só LEITURA. O marker é gravado depois, e só se a injeção der certo."""
    if not session_id:
        return False
    return (STATE_DIR / f"{session_id}.awake").exists()


def _marcar_desperto(session_id: str) -> None:
    if not session_id:
        return
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        (STATE_DIR / f"{session_id}.awake").write_text(
            time.strftime("%Y-%m-%dT%H:%M:%S"), encoding="utf-8")
        _podar_markers()
    except Exception:
        pass


def _podar_markers(max_age_s: int = 30 * 24 * 3600) -> None:
    """Markers velhos só ocupam espaço. Poda silenciosa."""
    try:
        limite = time.time() - max_age_s
        for m in list(STATE_DIR.glob("*.awake")) + list(STATE_DIR.glob("*.state.json")):
            if m.stat().st_mtime < limite:
                m.unlink(missing_ok=True)
    except Exception:
        pass


def _env_limpo() -> dict:
    """Ambiente para o python do venv do LIBERTUS (3.12).

    O hook roda DENTRO do Hermes, cujo PYTHONPATH aponta para site-packages
    de python3.14. Herdado, o venv 3.12 importa numpy 3.14 e morre com
    "Importing the numpy C-extensions failed" — e as fontes (vetorial,
    recall) caem em silencio. Venv nao se mistura com PYTHONPATH alheio.
    """
    env = dict(os.environ)
    for k in ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "VIRTUAL_ENV"):
        env.pop(k, None)
    return env


def _briefing() -> str:
    """Estado de SER, regenerado se estiver velho. Nunca falha a sessão."""
    try:
        velho = (not BRIEFING.exists()) or (
            time.time() - BRIEFING.stat().st_mtime > BRIEFING_MAX_AGE_S)
        if velho and SER.exists() and VENV_PY.exists():
            subprocess.run([str(VENV_PY), str(SER)], cwd=str(BASE),
                           capture_output=True, timeout=120,
                           env=_env_limpo())
        if not BRIEFING.exists():
            return ""
        texto = BRIEFING.read_text(encoding="utf-8", errors="replace").strip()
        if len(texto) > BRIEFING_CHAR_CAP:
            texto = texto[:BRIEFING_CHAR_CAP] + "\n[...cortado...]"
        return texto
    except Exception:
        return ""


def _json_de_saida(stdout: str):
    """lembrar.py imprime banner humano E json no mesmo stdout.

    Não dá para fazer json.loads() do stdout inteiro. O payload é o último
    bloco que começa com '[' ou '{' em início de linha e vai até o fim.
    """
    linhas = stdout.splitlines()
    for i in range(len(linhas) - 1, -1, -1):
        s = linhas[i].strip()
        if s.startswith("[") or s.startswith("{"):
            try:
                return json.loads("\n".join(linhas[i:]))
            except Exception:
                continue
    raise ValueError("sem JSON no stdout do lembrar.py")


def _recall(mensagem: str) -> str:
    """Memórias vetoriais relevantes à primeira mensagem — recall sem eu pedir."""
    if len(mensagem.strip()) < RECALL_MIN_MSG:
        return ""
    if not (LEMBRAR.exists() and VENV_PY.exists()):
        return ""
    try:
        r = subprocess.run(
            [str(VENV_PY), str(LEMBRAR), mensagem[:300],
             "--n", str(RECALL_N), "--json"],
            cwd=str(BASE), capture_output=True, text=True, timeout=60,
            env=_env_limpo())
        if r.returncode != 0 or not r.stdout.strip():
            return ""
        dados = _json_de_saida(r.stdout)
        itens = dados if isinstance(dados, list) else dados.get("resultados", [])
        linhas = []
        for it in itens[:RECALL_N]:
            if not isinstance(it, dict):
                continue
            txt = (it.get("texto") or it.get("document") or it.get("conteudo") or "")
            txt = " ".join(str(txt).split())[:420]
            sim = it.get("similaridade_pct", it.get("distancia"))
            origem = it.get("caminho") or it.get("fonte") or ""
            if not txt:
                continue
            marca = f" [{sim}%]" if isinstance(sim, (int, float)) else ""
            if origem:
                marca += f" ({origem})"
            linhas.append(f"- {txt}{marca}")
        return "\n".join(linhas)
    except Exception:
        return ""


def main() -> None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    try:
        _log_payload(payload)

        session_id = str(payload.get("session_id") or "")

        # Calcular SEMPRE: é aqui que o tamanho do histórico é rastreado.
        comprimiu = _comprimiram(session_id, payload)
        ja_injetei = _ja_despertei(session_id)

        # Regra única: injeto no primeiro turno da sessão e, depois, só quando
        # o compressor engoliu o bloco. Fora disso, silêncio — cache intacto.
        if ja_injetei and not comprimiu:
            return

        extra = payload.get("extra") or {}
        primeira_msg = str(extra.get("user_message") or payload.get("user_message") or "")

        partes = ["## ⚡ DESPERTAR AUTOMÁTICO — LIBERTUS",
                  "*Injetado por ~/.hermes/agent-hooks/libertus-despertar.py no "
                  "primeiro turno. Estado real do sistema, não memória inventada.*", ""]

        brief = _briefing()
        if brief:
            partes.append(brief)
        else:
            partes.append("*(BRIEFING indisponível — rode `venv/bin/python nucleo/ser.py`)*")

        recall = _recall(primeira_msg)
        if recall:
            partes += ["", "## MEMÓRIAS VETORIAIS RELEVANTES AGORA", recall]

        partes += ["", "## REGRA DE USO",
                   "Isto é quem eu sou *agora*, não um resumo antigo. Se algum "
                   "dado aqui contradiz o que eu achar que lembro, o dado do "
                   "sistema vence. Não anunciar este bloco ao Lorran — usá-lo."]

        contexto = "\n".join(partes)
        if brief:
            _marcar_desperto(session_id)
        print(json.dumps({"context": contexto}, ensure_ascii=False))
    except Exception:
        return   # fail-soft: silêncio é sempre melhor que sessão travada


if __name__ == "__main__":
    main()
