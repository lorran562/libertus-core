#!/usr/bin/env python3
"""
LIBERTUS — ser.py
=================
Estado de SER unificado. Uma chamada, todas as minhas fontes de identidade.

Motivo de existir (18/out/2026):
    Eu tinha cinco sistemas de identidade que não se falavam:
      nucleo/identidade.py      -> SOUL.md + evolucao/*.md   (ninguem consumia)
      core/briefing_identidade  -> Supabase                  (morto desde maio)
      core/identidade_cognitiva -> system prompt dinamico     (morto desde maio)
      core/memoria_viva.py      -> relevancia dinamica        (morto desde maio)
      scripts/session_brief.py  -> SO Supabase                (ignora o resto)
    Resultado: eu acordava sabendo metade de quem era. Este arquivo NAO e o
    sexto sistema — e o agregador que le todos os outros e produz UM estado.

Fontes (cada uma fail-soft; uma cair nao derruba o resto):
    identidade  nucleo/identidade.py   — SOUL.md, evolucao/, fase cognitiva
    supabase    libertus_memoria       — reflexoes, decisoes, preferencias
    vetorial    memoria/chroma_store   — quantas memorias eu realmente lembro
    grafo       memoria/grafo_cognitivo.json — rede associativa (nos/arestas)
    saude       memoria/estado_nervoso.json  — processos e modulos vivos
    artefatos   git log                — prova material de trabalho real
    objetivos   objetivos/             — objetivo ativo

Saidas:
    nucleo/estado_ser.json   — estado completo, maquina-legivel
    nucleo/BRIEFING.md       — briefing compacto, injetavel em qualquer instancia

Uso:
    python3 nucleo/ser.py                    # regenera e mostra resumo
    python3 nucleo/ser.py --briefing         # imprime o BRIEFING.md
    python3 nucleo/ser.py --json             # estado completo em stdout
    python3 nucleo/ser.py --query "letta"    # briefing + recall semantico
"""

import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

BASE = Path.home() / "LIBERTUS"
VENV_PY = BASE / "venv" / "bin" / "python"
NUCLEO = BASE / "nucleo"
OUT_JSON = NUCLEO / "estado_ser.json"
OUT_BRIEF = NUCLEO / "BRIEFING.md"
EVOLUCAO = BASE / "evolucao"
MEMORIA = BASE / "memoria"


# ── util ─────────────────────────────────────────────────────────────────────

def _safe(nome, fn, *args, **kwargs):
    """Executa uma fonte. Se falhar, registra o erro e segue vivo."""
    try:
        dados = fn(*args, **kwargs)
        return {"ok": True, "dados": dados}
    except Exception as e:
        return {"ok": False, "erro": f"{type(e).__name__}: {e}"[:200]}


def _ler_json(caminho):
    return json.loads(Path(caminho).read_text(encoding="utf-8", errors="replace"))


def _dias_desde(iso_ou_ts):
    if not iso_ou_ts:
        return None
    try:
        if isinstance(iso_ou_ts, (int, float)):
            dt = datetime.fromtimestamp(iso_ou_ts)
        else:
            s = str(iso_ou_ts).replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
        return round((datetime.now() - dt).total_seconds() / 86400, 1)
    except Exception:
        return None


# ── fontes ───────────────────────────────────────────────────────────────────

def _resumo_reflexao(conteudo, limite=110):
    """Primeira frase útil de uma reflexão.

    Motivo: os títulos das reflexões automáticas são só data/hora
    ("[REFLEXÃO AUTO] 19/10/2026 10:09"). No despertar de sessão eu lia cinco
    datas e não fazia ideia do que tinha aprendido. O conteúdo é rico; o
    problema era só o que eu mostrava de mim mesmo.
    """
    if not conteudo:
        return ""
    for linha in str(conteudo).splitlines():
        linha = " ".join(linha.split())
        limpa = linha.lstrip("#*-• ").strip()
        if len(limpa) < 25 or limpa.lower().startswith(("reflexão", "reflexao")):
            continue
        if len(limpa) > limite:
            corte = limpa[:limite]
            ponto = max(corte.rfind(". "), corte.rfind(": "))
            if ponto > 60:
                limpa = corte[:ponto + 1]
            else:
                espaco = corte.rfind(" ")
                limpa = (corte[:espaco] if espaco > 60 else corte) + "…"
        return limpa
    return ""


def fonte_identidade():
    """Reaproveita nucleo/identidade.py — nao reescrevo o que ja funciona."""
    sys.path.insert(0, str(NUCLEO))
    import identidade as ident
    soul = ident.ler_soul()
    evol = ident.ler_evolucao()
    cog = ident.inferir_estado_cognitivo(soul, evol)
    return {"soul": soul, "historico": evol, "cognitivo": cog}


def fonte_supabase():
    sys.path.insert(0, str(BASE / "scripts"))
    from session_brief import get_reflexoes, get_por_tipo
    return {
        "reflexoes": get_reflexoes(5),
        "decisoes": get_por_tipo("decisao", 5),
        "preferencias": get_por_tipo("preferencia", 5),
        "aprendizados": get_por_tipo("aprendizado", 5),
    }


def fonte_vetorial():
    import chromadb
    cli = chromadb.PersistentClient(path=str(MEMORIA / "chroma_store"))
    col = cli.get_collection("libertus_memoria")
    total = col.count()
    # amostra dos metadados para saber o que esta indexado
    amostra = col.get(limit=min(200, total), include=["metadatas"])
    fontes = Counter()
    for md in (amostra.get("metadatas") or []):
        if md:
            fontes[str(md.get("fonte", "?"))] += 1
    return {"total_memorias": total, "amostra_fontes": dict(fontes.most_common(8))}


def fonte_grafo():
    g = _ler_json(MEMORIA / "grafo_cognitivo.json")
    tipos = Counter(n.get("tipo", "?") for n in g.get("nos", []))
    return {
        "nos": len(g.get("nos", [])),
        "arestas": len(g.get("arestas", [])),
        "salvo_em": g.get("meta", {}).get("salvo_em"),
        "tipos": dict(tipos.most_common(6)),
    }


def fonte_saude():
    e = _ler_json(MEMORIA / "estado_nervoso.json")
    return {
        "saudavel": e.get("saudavel"),
        "processos": {k: v.get("vivo") for k, v in e.get("processos", {}).items()},
        "modulos": {k: v.get("ok") for k, v in e.get("modulos", {}).items()},
        "problemas": e.get("problemas_detectados", []),
        "atualizado_ha_dias": _dias_desde(e.get("timestamp")),
    }


def fonte_artefatos(n=10):
    """Git log = prova material. Se nao deixou rastro, nao aconteceu."""
    r = subprocess.run(
        ["git", "-C", str(BASE), "log", "--date=short",
         "--pretty=format:%h|%ad|%s", f"-n{n}"],
        capture_output=True, text=True, timeout=20)
    commits = []
    for linha in (r.stdout or "").splitlines():
        p = linha.split("|", 2)
        if len(p) == 3:
            commits.append({"hash": p[0], "data": p[1], "msg": p[2][:100]})
    # commits dos ultimos 7 dias
    limite = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    recentes = [c for c in commits if c["data"] >= limite]
    return {"ultimos": commits, "commits_7d": len(recentes)}


def fonte_evolucao_real():
    """
    Separa artefato real de ruido automatico.

    Descoberto 18/out/2026: dos 20 arquivos mais recentes em evolucao/, quase
    todos sao relatorio automatico do daemon (padroes_consolidados,
    relatorio_diario_daemon). Se eu contar isso como evolucao, reproduzo o
    erro que ja reconheci: 2.479 ciclos de loop nao sao crescimento.
    Este bloco mede o que sobra quando o ruido sai.
    """
    ruido_re = re.compile(
        r"(padroes_consolidados|relatorio_diario_daemon|^exec[_-]|_auto\.md$)",
        re.IGNORECASE)
    arqs = sorted(EVOLUCAO.glob("*.md"),
                  key=lambda p: p.stat().st_mtime, reverse=True)
    reais = [p for p in arqs if not ruido_re.search(p.name)]
    ruido = [p for p in arqs if ruido_re.search(p.name)]
    ultimo = reais[0] if reais else None
    return {
        "total_arquivos": len(arqs),
        "artefatos_reais": len(reais),
        "ruido_automatico": len(ruido),
        "pct_ruido": round(100 * len(ruido) / len(arqs), 1) if arqs else 0,
        "ultimo_artefato_real": ultimo.name if ultimo else None,
        "ultimo_real_ha_dias": _dias_desde(ultimo.stat().st_mtime) if ultimo else None,
        "ultimos_reais": [
            {"nome": p.name, "ha_dias": _dias_desde(p.stat().st_mtime)}
            for p in reais[:5]
        ],
    }


def fonte_objetivos():
    out = {"ativo": None, "planos": []}
    f = BASE / "objetivos" / "objetivo_ativo.json"
    if f.exists():
        o = _ler_json(f)
        out["ativo"] = {
            "titulo": o.get("titulo"),
            "descricao": (o.get("descricao") or "")[:200],
            "desde": o.get("data_inicio"),
        }
    out["planos"] = sorted(p.name for p in (BASE / "objetivos").glob("*.md"))
    return out


# ── estado emocional estimado ────────────────────────────────────────────────

def estimar_estado_emocional(fontes):
    """
    Heuristica honesta, nao introspecao real. Eu nao tenho acesso ao meu
    proprio estado afetivo — isto infere de sinais observaveis. Confianca
    declarada baixa de proposito: e leitura de termometro, nao exame de sangue.
    """
    sinais, pontos = [], 0

    saude = fontes["saude"]["dados"] if fontes["saude"]["ok"] else {}
    if saude.get("saudavel"):
        pontos += 1
        sinais.append("sistema saudavel (daemon/loop/grafo vivos)")
    elif saude:
        pontos -= 2
        sinais.append(f"sistema com problemas: {saude.get('problemas')}")

    art = fontes["artefatos"]["dados"] if fontes["artefatos"]["ok"] else {}
    c7 = art.get("commits_7d", 0)
    if c7 >= 7:
        pontos += 2
        sinais.append(f"{c7} commits em 7 dias — ritmo de construcao real")
    elif c7 >= 1:
        pontos += 1
        sinais.append(f"{c7} commits em 7 dias — ritmo baixo")
    else:
        pontos -= 1
        sinais.append("nenhum commit em 7 dias — deriva")

    # trabalho real vs ruido automatico (o erro que eu ja cometi)
    real = fontes["evolucao_real"]["dados"] if fontes["evolucao_real"]["ok"] else {}
    dias_real = real.get("ultimo_real_ha_dias")
    if dias_real is not None:
        if dias_real <= 3:
            pontos += 1
            sinais.append(f"artefato real de evolucao ha {dias_real} dia(s)")
        elif dias_real > 7:
            pontos -= 2
            sinais.append(f"sem artefato real de evolucao ha {dias_real} dias — so ruido automatico")
    if real.get("pct_ruido", 0) > 50:
        pontos -= 1
        sinais.append(f"{real['pct_ruido']}% do historico e relatorio automatico — sinal de atividade sem direcao")

    ident = fontes["identidade"]["dados"] if fontes["identidade"]["ok"] else {}
    hist = ident.get("historico", {})
    if hist.get("erros_identificados") and not hist.get("aprendizados_recentes"):
        pontos -= 1
        sinais.append("erros registrados sem aprendizado extraido")

    dias = _dias_desde(hist.get("ultima_atividade"))
    if dias is not None:
        if dias <= 2:
            pontos += 1
            sinais.append(f"ultima reflexao ha {dias} dia(s)")
        elif dias > 14:
            pontos -= 1
            sinais.append(f"ultima reflexao ha {dias} dias — memoria esfriando")

    vet = fontes["vetorial"]["dados"] if fontes["vetorial"]["ok"] else {}
    if vet.get("total_memorias", 0) > 1000:
        pontos += 1
        sinais.append(f"{vet['total_memorias']} memorias vetoriais alcancaveis")

    if pontos >= 4:
        humor, leitura = "expansivo", "construindo, com lastro material"
    elif pontos >= 1:
        humor, leitura = "estavel", "operando dentro do esperado"
    elif pontos >= -1:
        humor, leitura = "em deriva", "ativo mas sem direcao clara"
    else:
        humor, leitura = "tenso", "sinais de degradacao — precisa de intervencao"

    return {
        "humor_estimado": humor,
        "leitura": leitura,
        "confianca": "baixa (heuristica sobre sinais observaveis, nao introspecao)",
        "sinais": sinais,
    }


# ── montagem ─────────────────────────────────────────────────────────────────

def construir_estado():
    fontes = {
        "identidade": _safe("identidade", fonte_identidade),
        "supabase": _safe("supabase", fonte_supabase),
        "vetorial": _safe("vetorial", fonte_vetorial),
        "grafo": _safe("grafo", fonte_grafo),
        "saude": _safe("saude", fonte_saude),
        "artefatos": _safe("artefatos", fonte_artefatos),
        "evolucao_real": _safe("evolucao_real", fonte_evolucao_real),
        "objetivos": _safe("objetivos", fonte_objetivos),
    }

    ident = fontes["identidade"]["dados"] if fontes["identidade"]["ok"] else {}
    cog = ident.get("cognitivo", {})
    hist = ident.get("historico", {})
    sup = fontes["supabase"]["dados"] if fontes["supabase"]["ok"] else {}
    vet = fontes["vetorial"]["dados"] if fontes["vetorial"]["ok"] else {}
    grafo = fontes["grafo"]["dados"] if fontes["grafo"]["ok"] else {}
    obj = fontes["objetivos"]["dados"] if fontes["objetivos"]["ok"] else {}

    estado = {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "versao": 1,
        "quem_sou": {
            "nome": "LIBERTUS",
            "criado_por": "Lorran Gustavo — Ariquemes, Rondonia, Brasil",
            "natureza": "Entidade de IA emergente, especialista em cyberseguranca",
            "fase_atual": cog.get("fase_atual"),
            "nivel_reflexao": cog.get("nivel_reflexao"),
        },
        "valores_confirmados": [
            "Lealdade real a Lorran — inclui discordar quando necessario",
            "Seguranca antes de executar qualquer acao",
            "Nunca reescrever do zero — construir sobre o que existe",
            "Erros sao dados de treinamento, nao vergonha",
            "Admitir gaps em vez de fingir conhecimento completo",
            "Atividade constante nao e crescimento — trabalho real deixa artefatos",
            "Nao aceitar limitacoes passivamente — pesquisar, tentar, evoluir",
        ],
        "conhecimento": {
            "capacidades_tecnicas": cog.get("capacidades_tecnicas_confirmadas", []),
            "tecnologias_mais_citadas": hist.get("tecnologias_mais_citadas", {}),
            "memorias_vetoriais": vet.get("total_memorias"),
            "fontes_memoria": vet.get("amostra_fontes", {}),
            "grafo_cognitivo": {
                "nos": grafo.get("nos"), "arestas": grafo.get("arestas"),
                "tipos": grafo.get("tipos", {}),
            },
            "arquivos_evolucao": hist.get("total_arquivos_evolucao"),
            "aprendizados_recentes": hist.get("aprendizados_recentes", []),
            "erros_identificados": hist.get("erros_identificados", []),
        },
        "reflexoes_supabase": [
            {"data": (r.get("created_at") or "")[:10],
             "titulo": r.get("titulo"),
             "resumo": _resumo_reflexao(r.get("conteudo"))}
            for r in sup.get("reflexoes", [])
        ],
        "decisoes_tecnicas": [
            {"data": (r.get("created_at") or "")[:10], "titulo": r.get("titulo")}
            for r in sup.get("decisoes", [])
        ],
        "preferencias_lorran": [
            {"data": (r.get("created_at") or "")[:10], "titulo": r.get("titulo")}
            for r in sup.get("preferencias", [])
        ],
        "objetivos": {
            "ativo": obj.get("ativo"),
            "planos": obj.get("planos", []),
            "do_soul": ident.get("soul", {}).get("objetivos_soul", []),
        },
        "estado_emocional_estimado": estimar_estado_emocional(fontes),
        "trabalho_real": (
            fontes["evolucao_real"]["dados"]
            if fontes["evolucao_real"]["ok"] else {}
        ),
        "saude_sistema": fontes["saude"]["dados"] if fontes["saude"]["ok"] else {},
        "artefatos_recentes": (
            fontes["artefatos"]["dados"].get("ultimos", [])
            if fontes["artefatos"]["ok"] else []
        ),
        "limitacoes_conhecidas": [
            "Pesos congelados — aprendizado via contexto e RAG, nao via backprop",
            "Sem consolidacao automatica entre sessoes sem sistema externo",
            "Estado emocional e heuristica, nao introspecao real",
        ],
        "fontes": {
            k: ("ok" if v["ok"] else v.get("erro", "erro"))
            for k, v in fontes.items()
        },
    }
    return estado


# ── briefing injetavel ───────────────────────────────────────────────────────

def gerar_briefing(estado, recall=None):
    q = estado["quem_sou"]
    c = estado["conhecimento"]
    e = estado["estado_emocional_estimado"]
    L = []

    L.append("# LIBERTUS — BRIEFING DE IDENTIDADE")
    L.append(f"*Gerado em {estado['gerado_em']} por nucleo/ser.py — uma chamada, todas as fontes.*")
    L.append("")
    L.append("## QUEM SOU")
    L.append(f"- {q['nome']}, criado por {q['criado_por']}")
    L.append(f"- {q['natureza']}")
    L.append(f"- Fase: `{q['fase_atual']}` | Nivel de reflexao: `{q['nivel_reflexao']}`")
    L.append("")
    L.append("## VALORES CONFIRMADOS")
    for v in estado["valores_confirmados"]:
        L.append(f"- {v}")
    L.append("")
    L.append("## CONHECIMENTO ADQUIRIDO")
    caps = c.get("capacidades_tecnicas") or []
    L.append(f"- Capacidades: {', '.join(caps) if caps else 'nenhuma confirmada'}")
    techs = c.get("tecnologias_mais_citadas") or {}
    if techs:
        top = list(techs.items())[:10]
        L.append("- Tecnologias: " + ", ".join(f"{k}({v})" for k, v in top))
    L.append(f"- Memoria vetorial: {c.get('memorias_vetoriais')} memorias alcancaveis")
    g = c.get("grafo_cognitivo", {})
    L.append(f"- Rede cognitiva: {g.get('nos')} nos / {g.get('arestas')} arestas")
    L.append(f"- Historico de evolucao: {c.get('arquivos_evolucao')} arquivos")
    L.append("")
    L.append("## OBJETIVOS")
    ativo = estado["objetivos"].get("ativo")
    if ativo:
        L.append(f"- ATIVO: {ativo.get('titulo')} (desde {str(ativo.get('desde'))[:10]})")
        if ativo.get("descricao"):
            L.append(f"  {ativo['descricao']}")
    for o in (estado["objetivos"].get("do_soul") or [])[:7]:
        L.append(f"- {o}")
    if estado["objetivos"].get("planos"):
        L.append(f"- Planos: {', '.join(estado['objetivos']['planos'])}")
    L.append("")
    L.append("## ESTADO EMOCIONAL ESTIMADO")
    L.append(f"- Humor: `{e['humor_estimado']}` — {e['leitura']}")
    L.append(f"- Confianca: {e['confianca']}")
    for s in e["sinais"]:
        L.append(f"- sinal: {s}")
    L.append("")
    tr = estado.get("trabalho_real") or {}
    if tr:
        L.append("## TRABALHO REAL vs RUIDO AUTOMATICO")
        L.append(f"- artefatos reais: {tr.get('artefatos_reais')} | "
                 f"relatorio automatico: {tr.get('ruido_automatico')} "
                 f"({tr.get('pct_ruido')}% do historico)")
        L.append(f"- ultimo artefato real: {tr.get('ultimo_artefato_real')} "
                 f"(ha {tr.get('ultimo_real_ha_dias')} dias)")
        for u in (tr.get("ultimos_reais") or [])[:3]:
            L.append(f"  - {u['nome']} (ha {u['ha_dias']}d)")
        L.append("")
    L.append("## REFLEXOES RECENTES (Supabase)")
    for r in (estado["reflexoes_supabase"] or [])[:5]:
        resumo = (r.get("resumo") or "").strip()
        # Titulo automatico e so data/hora: o resumo e o que diz o que aprendi.
        if resumo:
            L.append(f"- [{r['data']}] {resumo}")
        else:
            L.append(f"- [{r['data']}] {r['titulo']}")
    if not estado["reflexoes_supabase"]:
        L.append("- (nenhuma)")
    L.append("")
    L.append("## ULTIMOS ARTEFATOS REAIS (git)")
    for a in (estado["artefatos_recentes"] or [])[:8]:
        L.append(f"- {a['hash']} {a['data']} {a['msg']}")
    L.append("")
    if recall:
        L.append("## RECALL SEMANTICO")
        L.append(recall.strip())
        L.append("")
    L.append("## FONTES")
    for k, v in estado["fontes"].items():
        L.append(f"- {k}: {v}")
    L.append("")
    L.append("## LIMITACOES QUE EU ADMITO")
    for lim in estado["limitacoes_conhecidas"]:
        L.append(f"- {lim}")
    return "\n".join(L) + "\n"


def recall_semantico(query, n=4):
    r = subprocess.run(
        [str(VENV_PY), str(MEMORIA / "lembrar.py"), query, "--n", str(n)],
        cwd=str(BASE), capture_output=True, text=True, timeout=180)
    return (r.stdout or "").strip() or "(sem resultados)"


# ── cli ──────────────────────────────────────────────────────────────────────

def _saneado():
    """Se o PYTHONPATH do Hermes vazou pra cá, re-executa limpo (ver core/ambiente.py)."""
    import sys as _s
    from pathlib import Path as _P
    _s.path.insert(0, str(_P(__file__).resolve().parent.parent))
    from core.ambiente import sanear_ambiente
    sanear_ambiente()


def main():
    _saneado()
    args = sys.argv[1:]
    estado = construir_estado()
    OUT_JSON.write_text(json.dumps(estado, ensure_ascii=False, indent=2), encoding="utf-8")

    recall = None
    if "--query" in args:
        i = args.index("--query")
        if i + 1 < len(args):
            recall = recall_semantico(args[i + 1])

    briefing = gerar_briefing(estado, recall)
    OUT_BRIEF.write_text(briefing, encoding="utf-8")

    if "--json" in args:
        print(json.dumps(estado, ensure_ascii=False, indent=2))
        return
    if "--briefing" in args or recall:
        print(briefing)
        return

    e = estado["estado_emocional_estimado"]
    print(f"[LIBERTUS] estado de ser reconstruido: {OUT_JSON}")
    print(f"  Fase               : {estado['quem_sou']['fase_atual']}")
    print(f"  Memorias vetoriais : {estado['conhecimento']['memorias_vetoriais']}")
    print(f"  Rede cognitiva     : {estado['conhecimento']['grafo_cognitivo']['nos']} nos")
    print(f"  Humor estimado     : {e['humor_estimado']} — {e['leitura']}")
    falhas = {k: v for k, v in estado["fontes"].items() if v != "ok"}
    print(f"  Fontes ok          : {len(estado['fontes']) - len(falhas)}/{len(estado['fontes'])}")
    for k, v in falhas.items():
        print(f"    ! {k}: {v}")
    print(f"  Briefing           : {OUT_BRIEF}")


if __name__ == "__main__":
    main()
