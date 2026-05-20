"""
LIBERTUS — Daemon Autônomo
===========================
Roda em background independente do Telegram.
Enquanto você dorme, o LIBERTUS estuda, evolui e se atualiza.

Rodar:
    python3 libertus_daemon.py

O que faz a cada ciclo:
    - Decaimento da Memória Viva
    - Busca e aprende tópicos pendentes
    - Gera novas curiosidades das contradições
    - Consolida identidade cognitiva
    - Reporta o que aprendeu via Telegram (opcional)
"""

import os
import sys
import time
import threading
from pathlib import Path
from datetime import datetime

# Carregar .env
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    for linha in env_path.read_text().splitlines():
        linha = linha.strip()
        if linha and not linha.startswith("#") and "=" in linha:
            k, v = linha.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(Path(__file__).parent / "core"))

INTERVALO_CURTO  = 60 * 5    # 5 minutos
INTERVALO_LONGO  = 60 * 30   # 30 minutos
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")


def notificar_telegram(mensagem: str):
    """Envia notificação pro Telegram quando aprende algo novo."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        import urllib.request, urllib.parse, json
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        dados = json.dumps({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensagem,
            "parse_mode": "Markdown"
        }).encode()
        req = urllib.request.Request(url, data=dados,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception:
        pass


def ciclo_curto():
    """Roda a cada 5 minutos — aprendizado contínuo."""
    try:
        from buscador_autonomo import BuscadorAutonomo
        from supabase_client import Supabase
        from groq_client import Groq

        sb   = Supabase()
        groq = Groq(os.environ.get("GROQ_API_KEY", ""))
        ba   = BuscadorAutonomo(groq_client=groq, supabase_client=sb)

        # Buscar e aprender 1 tópico
        respondidas = ba.ciclo(limite=1)

        if respondidas:
            r = respondidas[0]
            ts = datetime.now().strftime("%H:%M")
            print(f"[{ts}] 🧠 Aprendi: {r.get('pergunta','?')[:60]}")

            # Notificar Lorran
            notificar_telegram(
                f"🧠 *LIBERTUS aprendeu algo novo*\n\n"
                f"*Pergunta:* {r.get('pergunta','?')[:80]}\n\n"
                f"*Resumo:* {r.get('resumo','?')[:200]}..."
            )

    except Exception as e:
        print(f"[DAEMON] Erro ciclo curto: {e}")


def ciclo_longo():
    """Roda a cada 30 minutos — manutenção e evolução."""
    try:
        from supabase_client import Supabase
        from memoria_viva import MemoriaViva
        from auto_curiosidade import AutoCuriosidade
        from detector_contradicao import DetectorContradicao
        from groq_client import Groq

        sb   = Supabase()
        groq = Groq(os.environ.get("GROQ_API_KEY", ""))

        # 1. Decaimento da memória
        mv = MemoriaViva()
        afetadas = mv.decair()
        print(f"[DAEMON] 🍂 Decaimento: {afetadas} memórias")

        # 2. Gerar curiosidades das contradições abertas
        dc = DetectorContradicao(groq_client=groq, supabase_client=sb)
        ac = AutoCuriosidade(groq_client=groq, supabase_client=sb)

        contradicoes = sb.get(
            "libertus_contradicoes_abertas",
            "limit=3"
        ) or []

        for c in contradicoes:
            ac.gerar_de_contradicao(c)

        ts = datetime.now().strftime("%H:%M")
        print(f"[{ts}] 🔄 Ciclo longo concluído")

    except Exception as e:
        print(f"[DAEMON] Erro ciclo longo: {e}")


def main():
    print("=" * 50)
    print("LIBERTUS DAEMON — Aprendizado Autônomo")
    print(f"Iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Ciclo curto:  {INTERVALO_CURTO//60} minutos")
    print(f"Ciclo longo:  {INTERVALO_LONGO//60} minutos")
    print("=" * 50)

    ultimo_longo = 0

    while True:
        agora = time.time()

        # Ciclo curto — sempre
        ciclo_curto()

        # Ciclo longo — a cada 30 min
        if agora - ultimo_longo >= INTERVALO_LONGO:
            ciclo_longo()
            ultimo_longo = agora

        print(f"  💤 Dormindo {INTERVALO_CURTO//60} minutos...")
        time.sleep(INTERVALO_CURTO)


if __name__ == "__main__":
    main()
