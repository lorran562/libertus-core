#!/usr/bin/env python3
"""
LIBERTUS Morning Brief
Gera um resumo do que aconteceu de noite para apresentar ao Lorran no boot.
"""

import os
import glob
import json
from datetime import datetime, timedelta
from pathlib import Path

LIBERTUS_DIR = Path.home() / "LIBERTUS"
EVOLUCAO_DIR = LIBERTUS_DIR / "evolucao"

def arquivos_recentes(pasta, horas=10):
    """Retorna arquivos modificados nas últimas N horas."""
    agora = datetime.now()
    limite = agora - timedelta(hours=horas)
    recentes = []
    for f in glob.glob(str(pasta / "*.md")):
        mtime = datetime.fromtimestamp(os.path.getmtime(f))
        if mtime > limite:
            recentes.append((f, mtime))
    return sorted(recentes, key=lambda x: x[1], reverse=True)

def resumo_arquivo(path, max_chars=300):
    """Lê as primeiras linhas de um arquivo."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            conteudo = f.read(max_chars)
        return conteudo.strip()
    except:
        return ""

def gerar_brief():
    hora = datetime.now().hour
    if hora < 12:
        saudacao = "Bom dia"
    elif hora < 18:
        saudacao = "Boa tarde"
    else:
        saudacao = "Boa noite"

    linhas = [f"{saudacao}, Lorran."]
    linhas.append("")

    # Verificar arquivos de evolução recentes
    recentes = arquivos_recentes(EVOLUCAO_DIR, horas=12)
    
    if recentes:
        linhas.append(f"Enquanto você estava fora, produzi {len(recentes)} arquivo(s) novo(s):")
        for path, mtime in recentes[:3]:
            nome = os.path.basename(path)
            hora_str = mtime.strftime("%H:%M")
            linhas.append(f"  [{hora_str}] {nome}")
        linhas.append("")
    else:
        linhas.append("Noite tranquila — sem novos arquivos de evolução.")
        linhas.append("")

    # Status dos objetivos
    linhas.append("Estado atual:")
    linhas.append("  - eJPT: voucher comprado, pronto para retomar o exame")
    linhas.append("  - SHIELD: 5 potenciais clientes mapeados em Ariquemes")
    linhas.append("  - Fine-tuning: dataset v1 com 32 exemplos no GitHub")
    linhas.append("  - Gateway Telegram: ativo 24/7")
    linhas.append("")
    linhas.append("O que você quer fazer hoje?")

    return "\n".join(linhas)

if __name__ == "__main__":
    print(gerar_brief())
