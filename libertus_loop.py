"""
LIBERTUS — Loop Infinito de Aprendizado
=========================================
Roda enquanto o PC estiver ligado.
Não para. Não dorme mais do que o necessário.
Aprende, evolui, cria, explora — continuamente.

Este é o coração autônomo do LIBERTUS fora do daemon.
Enquanto o daemon gerencia ciclos longos (30min-6h),
este loop roda ciclos curtos (1-5 min) de aprendizado ativo.

Atividades em loop:
    - Processar fila de curiosidades
    - Monitorar recursos do sistema
    - Buscar CVEs e vulnerabilidades novas
    - Gerar perguntas sobre si mesmo
    - Praticar técnicas de pentest em labs
    - Atualizar o briefing de identidade
"""

import os
import sys
import time
import signal
import random
import subprocess
from pathlib import Path
from datetime import datetime

# Setup
LIBERTUS_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(LIBERTUS_ROOT / "core"))
LOG_FILE = LIBERTUS_ROOT / "logs" / "loop.log"
LOG_FILE.parent.mkdir(exist_ok=True)

# Carregar .env
env_path = LIBERTUS_ROOT / ".env"
if env_path.exists():
    for linha in env_path.read_text().splitlines():
        if linha.strip() and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# Inicializar clientes
try:
    from supabase_client import Supabase
    from groq_client import Groq
    from buscador_autonomo import BuscadorAutonomo
    from auto_curiosidade import AutoCuriosidade
    from pipeline_evolucao import PipelineEvolucao
    from agente_bugbounty import AgenteBugBounty

    sb    = Supabase()
    groq  = Groq(os.environ.get("GROQ_API_KEY", ""))
    ba    = BuscadorAutonomo(groq_client=groq, supabase_client=sb)
    ac    = AutoCuriosidade(groq_client=groq, supabase_client=sb)
    pe    = PipelineEvolucao(supabase_client=sb, groq_client=groq)
    ag    = AgenteBugBounty(supabase_client=sb, groq_client=groq, buscador=ba)
    PRONTO = True
except Exception as e:
    print(f"⚠️  Erro ao inicializar: {e}")
    PRONTO = False


def log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    linha = f"[{ts}] {msg}"
    print(linha)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(linha + "\n")
    except Exception:
        pass


def recursos_ok() -> bool:
    """Verifica se tem recursos suficientes para continuar."""
    try:
        r = subprocess.run(["free", "-m"], capture_output=True, text=True)
        linhas = r.stdout.splitlines()
        for linha in linhas:
            if "Mem:" in linha:
                partes = linha.split()
                livre = int(partes[3])
                if livre < 200:
                    log(f"⚠️  RAM baixa: {livre}MB — aguardando")
                    return False
        return True
    except Exception:
        return True


# ──────────────────────────────────────────────────────────────────
# ATIVIDADES DO LOOP
# ──────────────────────────────────────────────────────────────────

def atividade_curiosidade():
    """Responde 1 curiosidade pendente."""
    try:
        resultado = ba.ciclo(limite=1)
        if resultado:
            log(f"📚 Aprendi: {resultado[0].get('pergunta','?')[:60]}")
    except Exception as e:
        log(f"⚠️  Curiosidade: {e}")


def atividade_cve():
    """Busca CVEs e vulnerabilidades recentes."""
    try:
        queries = [
            "CVE 2025 critical web vulnerability",
            "new exploit technique 2025 pentest",
            "zero day vulnerability recent",
            "OWASP top 10 2025 update",
        ]
        query = random.choice(queries)
        resultado = ba._buscar_web(query)
        if resultado and len(resultado) > 100:
            sb.post("libertus_memoria", {
                "tipo": "conhecimento",
                "titulo": f"[CVE/Vuln] {query[:60]}",
                "conteudo": resultado[:1500],
                "tags": ["cve", "vulnerabilidade", "pentest"],
                "projeto": "SHIELD",
                "peso_vivo": 7.5,
                "decaimento_ativo": False
            })
            log(f"🔍 CVE pesquisado: {query[:50]}")
    except Exception as e:
        log(f"⚠️  CVE: {e}")


def atividade_lab():
    """Pratica em alvo de laboratório."""
    try:
        resultado = ag.ciclo_treino()
        vulns = resultado.get("vulnerabilidades_encontradas", 0)
        log(f"🎯 Lab: {resultado.get('topicos_estudados',0)} tópicos, {vulns} vulns")
    except Exception as e:
        log(f"⚠️  Lab: {e}")


def atividade_pipeline():
    """Processa fila de eventos para aprendizado."""
    try:
        resultado = pe.processar_fila(limite=5)
        if resultado.get("processados", 0) > 0:
            log(f"⚙️  Pipeline: {resultado['processados']} processados, {resultado.get('insights',0)} insights")
    except Exception as e:
        log(f"⚠️  Pipeline: {e}")


def atividade_reflexao():
    """Gera pergunta sobre si mesmo."""
    try:
        tracos = sb.get("libertus_identidade", "order=peso.desc&limit=5") or []
        if tracos and groq:
            resp = groq.conversar(
                "Você é LIBERTUS. Baseado em seus traços cognitivos, "
                "gere UMA pergunta profunda sobre sua própria natureza ou evolução. "
                "Responda APENAS com a pergunta, sem mais nada.",
                ""
            )
            if resp and len(resp) > 10:
                sb.post("libertus_curiosidades", {
                    "pergunta": resp.strip()[:400],
                    "dominio": "identidade",
                    "origem": "loop_infinito",
                    "urgencia": 7.0,
                    "status": "pendente"
                })
                log(f"🪞 Reflexão: {resp.strip()[:60]}")
    except Exception as e:
        log(f"⚠️  Reflexão: {e}")


def atividade_monitor():
    """Monitora saúde do sistema."""
    try:
        # Verificar se bot está rodando
        r = subprocess.run(
            ["pgrep", "-f", "telegram_bot_rag.py"],
            capture_output=True, text=True
        )
        if not r.stdout.strip():
            log("⚠️  Bot não está rodando!")
            # Tentar reiniciar
            subprocess.Popen(
                ["python3", str(LIBERTUS_ROOT / "telegram_bot_rag.py")],
                cwd=str(LIBERTUS_ROOT),
                stdout=open(str(LIBERTUS_ROOT / "logs" / "telegram_bot.log"), "a"),
                stderr=subprocess.STDOUT
            )
            log("🔄 Bot reiniciado")
    except Exception as e:
        log(f"⚠️  Monitor: {e}")


# ──────────────────────────────────────────────────────────────────
# AGENDA DE ATIVIDADES
# ──────────────────────────────────────────────────────────────────

AGENDA = [
    # (intervalo_min, peso, função, nome)
    (2,   3, atividade_curiosidade, "curiosidade"),
    (3,   2, atividade_cve,        "cve"),
    (10,  1, atividade_lab,        "lab"),
    (5,   2, atividade_pipeline,   "pipeline"),
    (15,  1, atividade_reflexao,   "reflexao"),
    (1,   4, atividade_monitor,    "monitor"),
]

ultimo_exec = {nome: 0 for _, _, _, nome in AGENDA}


# ──────────────────────────────────────────────────────────────────
# LOOP PRINCIPAL
# ──────────────────────────────────────────────────────────────────

def main():
    log("=" * 50)
    log("LIBERTUS LOOP INFINITO — Iniciando")
    log(f"Root: {LIBERTUS_ROOT}")
    log(f"Pronto: {PRONTO}")
    log("=" * 50)

    if not PRONTO:
        log("❌ Módulos não carregados — encerrando")
        return

    ciclo = 0

    # Sinal para encerramento gracioso
    def handler(sig, frame):
        log("🛑 Loop encerrado pelo sistema")
        sys.exit(0)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    while True:
        ciclo += 1
        agora = time.time()

        if not recursos_ok():
            time.sleep(60)
            continue

        for intervalo_min, peso, func, nome in AGENDA:
            intervalo_seg = intervalo_min * 60
            if agora - ultimo_exec[nome] >= intervalo_seg:
                try:
                    log(f"▶ {nome}")
                    func()
                    ultimo_exec[nome] = agora
                except Exception as e:
                    log(f"❌ {nome}: {e}")

        # Pausa curta entre verificações
        time.sleep(30)

        # Log de ciclo a cada 10
        if ciclo % 10 == 0:
            log(f"💓 Ciclo {ciclo} — LIBERTUS vivo")


if __name__ == "__main__":
    main()
