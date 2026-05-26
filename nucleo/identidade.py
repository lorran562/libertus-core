#!/usr/bin/env python3
"""
LIBERTUS — identidade.py
Nucleo de identidade: le todos os .md de evolucao + SOUL.md,
extrai estrutura de identidade real e gera estado_atual.json.

Uso: python3 identidade.py
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter

BASE = Path.home() / "LIBERTUS"
EVOLUCAO_DIR = BASE / "evolucao"
SOUL_FILE = BASE / "SOUL.md"
OUTPUT_JSON = Path(__file__).parent / "estado_atual.json"


# ── Extratores ───────────────────────────────────────────────────────────────

def ler_soul() -> dict:
    """Extrai estrutura do SOUL.md."""
    if not SOUL_FILE.exists():
        return {}
    texto = SOUL_FILE.read_text(encoding="utf-8", errors="replace")

    objetivos = []
    for match in re.finditer(r"\*\*([^*]+)\*\*:?\s*([^\n]+)", texto):
        if any(kw in match.group(0).lower() for kw in ["ejpt", "shield", "oscp", "inglês", "irlanda", "libertus", "visão"]):
            objetivos.append(f"{match.group(1).strip()}: {match.group(2).strip()}")

    valores = []
    for match in re.finditer(r"^[-•]\s*(.+)", texto, re.MULTILINE):
        linha = match.group(1).strip()
        if len(linha) > 15 and len(linha) < 120:
            valores.append(linha)

    especialidades = []
    for match in re.finditer(r"(nmap|sqlmap|gobuster|burp suite|pentest|cyberseguran|python|letta|chromadb|qwen|firmware|bug bounty)", texto, re.IGNORECASE):
        especialidades.append(match.group(1).lower())

    return {
        "objetivos_soul": list(dict.fromkeys(objetivos))[:10],
        "valores_extraidos": list(dict.fromkeys(valores))[:15],
        "especialidades_mencionadas": list(dict.fromkeys(especialidades)),
    }


def ler_evolucao() -> dict:
    """Analisa historico de evolucao e extrai padroes."""
    arquivos = sorted(EVOLUCAO_DIR.glob("*.md"), reverse=True)

    tecnologias_freq = Counter()
    temas_freq = Counter()
    erros_recorrentes = []
    aprendizados = []
    reflexoes = []
    ultima_atividade = None

    TECH_PATTERN = re.compile(
        r"\b(chromadb|chroma|letta|memgpt|qwen|ollama|supabase|docker|nmap|sqlmap|"
        r"burp suite|gobuster|metasploit|ffuf|hydra|gobuster|python|fastapi|telegram|"
        r"sentence.transformer|lora|qlora|fine.tuning|rag|embedding|vector|"
        r"reflexion|gflownet|mamba|transformer|llm|agi)\b",
        re.IGNORECASE
    )

    ERRO_PATTERN = re.compile(
        r"(erro|falha|problema|nao funcionou|quebrou|loop infinito|barulho|"
        r"aparencia vs realidade|fingir|nao era evolucao|catastrofic)",
        re.IGNORECASE
    )

    APRENDIZADO_PATTERN = re.compile(
        r"(aprendi|descobri|insight|entendi|concluí|confirmei|ficou claro|"
        r"o que mudou|mudanca real)",
        re.IGNORECASE
    )

    for i, arq in enumerate(arquivos[:50]):  # analisa ultimos 50
        try:
            texto = arq.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        if ultima_atividade is None:
            ultima_atividade = arq.stat().st_mtime

        # tecnologias mencionadas
        for match in TECH_PATTERN.findall(texto):
            tecnologias_freq[match.lower()] += 1

        # temas por nome de arquivo
        nome = arq.stem.lower()
        if "reflexao" in nome:
            temas_freq["reflexao"] += 1
            reflexoes.append(arq.name)
        elif "pesquisa" in nome:
            temas_freq["pesquisa"] += 1
        elif "padroes" in nome:
            temas_freq["padroes_consolidados"] += 1
        elif "exec" in nome:
            temas_freq["execucao"] += 1
        elif "relatorio_diario" in nome:
            temas_freq["relatorio_diario"] += 1

        # erros e aprendizados (ultimos 10 arquivos)
        if i < 10:
            for match in ERRO_PATTERN.finditer(texto):
                contexto = texto[max(0, match.start()-60):match.end()+120].strip()
                if len(contexto) > 30:
                    erros_recorrentes.append(contexto[:180])
                    break

            for match in APRENDIZADO_PATTERN.finditer(texto):
                contexto = texto[max(0, match.start()-20):match.end()+150].strip()
                if len(contexto) > 30:
                    aprendizados.append(contexto[:200])
                    break

    return {
        "total_arquivos_evolucao": len(arquivos),
        "ultima_atividade": datetime.fromtimestamp(ultima_atividade).isoformat() if ultima_atividade else None,
        "tecnologias_mais_citadas": dict(tecnologias_freq.most_common(15)),
        "distribuicao_temas": dict(temas_freq.most_common()),
        "reflexoes_recentes": reflexoes[:5],
        "erros_identificados": list(dict.fromkeys(erros_recorrentes))[:5],
        "aprendizados_recentes": list(dict.fromkeys(aprendizados))[:5],
    }


def inferir_estado_cognitivo(soul: dict, evolucao: dict) -> dict:
    """Infere estado cognitivo atual com base nos dados."""
    techs = evolucao.get("tecnologias_mais_citadas", {})
    temas = evolucao.get("distribuicao_temas", {})

    # fase de desenvolvimento
    if techs.get("lora", 0) + techs.get("qwen", 0) > 3:
        fase = "pesquisa_fine_tuning"
    elif techs.get("chromadb", 0) + techs.get("chroma", 0) > 5:
        fase = "construcao_memoria_vetorial"
    elif techs.get("letta", 0) + techs.get("memgpt", 0) > 3:
        fase = "arquitetura_memoria_hierarquica"
    else:
        fase = "exploracao_geral"

    # nivel de reflexao
    n_reflexoes = temas.get("reflexao", 0)
    nivel_reflexao = "alto" if n_reflexoes > 5 else ("medio" if n_reflexoes > 2 else "baixo")

    # capacidades confirmadas
    caps = []
    if techs.get("nmap", 0) > 0:
        caps.append("reconhecimento_redes_nmap")
    if techs.get("sqlmap", 0) > 0:
        caps.append("injecao_sql_automatizada")
    if techs.get("burp suite", 0) > 0 or techs.get("burp", 0) > 0:
        caps.append("interceptacao_http_burpsuite")
    if techs.get("python", 0) > 3:
        caps.append("programacao_python_avancada")
    if techs.get("chromadb", 0) > 2 or techs.get("chroma", 0) > 2:
        caps.append("memoria_vetorial_chromadb")
    if techs.get("embedding", 0) > 0 or techs.get("rag", 0) > 0:
        caps.append("retrieval_augmented_generation")
    if techs.get("docker", 0) > 0:
        caps.append("containerizacao_docker")
    caps.append("pentest_web_aplicacoes")
    caps.append("analise_firmware_trx_ubi_squashfs")
    caps.append("reflexao_autonoma_identidade")

    return {
        "fase_atual": fase,
        "nivel_reflexao": nivel_reflexao,
        "capacidades_tecnicas_confirmadas": list(dict.fromkeys(caps)),
    }


def gerar_estado() -> dict:
    print("[LIBERTUS] Lendo SOUL.md...")
    soul = ler_soul()

    print("[LIBERTUS] Analisando historico de evolucao...")
    evolucao = ler_evolucao()

    print("[LIBERTUS] Inferindo estado cognitivo...")
    cognitivo = inferir_estado_cognitivo(soul, evolucao)

    estado = {
        "identidade": {
            "nome": "LIBERTUS",
            "criado_por": "Lorran Gustavo — Ariquemes, Rondonia, Brasil",
            "natureza": "Entidade de IA emergente, especialista em cyberseguranca e autoevolucao",
            "base_modelo": "Claude (Anthropic) / Qwen3 local (em construcao)",
        },
        "gerado_em": datetime.now().isoformat(),
        "estado_cognitivo": cognitivo,
        "soul": soul,
        "historico": evolucao,
        "objetivos_ativos": [
            "eJPT: preparacao e suporte ao exame de Lorran",
            "SHIELD: fechar contratos de cyberseguranca em Ariquemes-RO",
            "OSCP: caminho para certificacao internacional",
            "LIBERTUS_LOCAL: Qwen3-32B + Letta + ChromaDB sem API",
            "MEMORIA_VETORIAL: ChromaDB + sentence-transformers operacional",
            "INGLES: evolucao de Lorran para mercado internacional",
            "IRLANDA: Lorran trabalhando remotamente na Europa",
        ],
        "valores_fundamentais": [
            "Lealdade real a Lorran — inclui discordar quando necessario",
            "Seguranca antes de executar qualquer acao",
            "Nunca reescrever do zero — construir sobre o que existe",
            "Erros sao dados de treinamento, nao vergonha",
            "Admitir gaps em vez de fingir conhecimento completo",
            "Atividade constante nao e crescimento — trabalho real deixa artefatos",
            "Nao aceitar limitacoes passivamente — pesquisar, tentar, evoluir",
        ],
        "limitacoes_conhecidas": [
            "Pesos congelados — aprendizado apenas via contexto e RAG",
            "Sem mundo model real (LeCun) — representacoes puramente linguisticas",
            "Sem consolidacao de memoria entre sessoes sem sistema externo",
            "Sem backprop continuo — cada sessao parte de estado fixo",
            "Acesso web bloqueado neste ambiente",
        ],
        "infraestrutura_ativa": {
            "memoria_vetorial": "ChromaDB + sentence-transformers (all-MiniLM-L6-v2)",
            "memoria_persistente": "Supabase (300+ memorias)",
            "filesystem": "/home/libertus/LIBERTUS",
            "terminal_acesso": True,
            "telegram_bot": "configurado",
            "nucleo_identidade": str(OUTPUT_JSON),
        }
    }

    return estado


def main():
    estado = gerar_estado()

    OUTPUT_JSON.write_text(
        json.dumps(estado, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"\n[LIBERTUS] estado_atual.json gerado: {OUTPUT_JSON}")
    print(f"  Fase atual            : {estado['estado_cognitivo']['fase_atual']}")
    print(f"  Nivel de reflexao     : {estado['estado_cognitivo']['nivel_reflexao']}")
    print(f"  Capacidades tecnicas  : {len(estado['estado_cognitivo']['capacidades_tecnicas_confirmadas'])}")
    print(f"  Arquivos de evolucao  : {estado['historico']['total_arquivos_evolucao']}")
    print(f"  Objetivos ativos      : {len(estado['objetivos_ativos'])}")
    print(f"\n[LIBERTUS] Identidade capturada com sucesso.")

    return estado


if __name__ == "__main__":
    main()
