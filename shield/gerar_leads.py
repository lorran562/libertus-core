#!/usr/bin/env python3
"""Gera a lista de leads da SHIELD a partir de shield/leads_raw.jsonl.

Saída:
  shield/LEADS_ARIQUEMES.md   (lista priorizada, pronta pra atacar no WhatsApp)
  shield/leads_ariquemes.csv  (planilha: vertical,nome,telefone,whatsapp,tem_site,prioridade,status)

Regras de prioridade (do skill libertus-shield-prospeccao):
  QUENTE  = já existe laudo/relatório feito pra essa empresa -> follow-up primeiro
  A       = tem site institucional -> alvo do Diagnóstico Express (recon passivo)
  B       = sem site -> pitch diferente (presença digital segura), não é alvo de headers
"""
import csv
import json
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(BASE, "shield", "leads_raw.jsonl")

# empresas que já têm laudo/relatório no repo -> follow-up, não abordagem fria
JA_ABORDADAS = [
    ("Laboratório São José", "laudo pronto em relatorios/RELATORIO_PROFISSIONAL_Laboratorio_Sao_Jose"),
    ("Marques Imóveis", "laudo pronto em relatorio_marques_imoveis.md"),
]


def wa_link(phone):
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) == 11 and digits[2] in "9":  # celular com DDD
        return f"https://wa.me/55{digits}"
    return ""


def vertical_pt(v):
    return {
        "odontologia": "Odontologia",
        "contabilidade": "Contabilidade",
        "advocacia": "Advocacia",
        "clinica_medica": "Clínica médica",
        "laboratorio": "Laboratório",
        "imobiliaria": "Imobiliária",
        "veterinaria": "Veterinária",
    }.get(v, v)


def main():
    if not os.path.exists(RAW):
        raise SystemExit(f"sem {RAW} — rode a coleta no Google Maps primeiro")
    leads = [json.loads(l) for l in open(RAW, encoding="utf-8") if l.strip()]

    vistos = set()
    linhas = []
    for lead in leads:
        nome = (lead.get("name") or "").strip()
        chave = nome.lower()
        if not nome or chave in vistos:
            continue
        vistos.add(chave)
        quente = next((m for n, m in JA_ABORDADAS if n.lower() in chave), None)
        tem_site = bool(lead.get("site"))
        prioridade = "QUENTE" if quente else ("A" if tem_site else "B")
        linhas.append({
            "vertical": vertical_pt(lead.get("vertical", "")),
            "nome": nome,
            "telefone": lead.get("phone") or "",
            "whatsapp": wa_link(lead.get("phone")),
            "tem_site": "sim" if tem_site else "nao",
            "site": lead.get("site") or "",
            "maps": lead.get("maps") or "",
            "prioridade": prioridade,
            "observacao": quente or "",
            "status": "a_contatar",
        })

    ordem = {"QUENTE": 0, "A": 1, "B": 2}
    linhas.sort(key=lambda x: (ordem[x["prioridade"]], x["vertical"], x["nome"]))

    csv_path = os.path.join(BASE, "shield", "leads_ariquemes.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()))
        w.writeheader()
        w.writerows(linhas)

    md = [
        "# LEADS SHIELD — Ariquemes/RO (coletado 13/10/2026)",
        "",
        f"Total: **{len(linhas)}** empresas com telefone confirmado (DDD 69 / fixo 3535-3536 = Ariquemes).",
        "",
        "Como usar (ordem importa):",
        "1. **QUENTE** — já existe laudo feito. É follow-up, não abordagem fria. Comece por aqui.",
        "2. **Prioridade A** (tem site) — alvo do Diagnóstico Express: rodar recon passivo, gerar laudo, mandar.",
        "3. **Prioridade B** (sem site) — pitch diferente: \"você não tem site/presença, e quando tiver vai precisar nascer segura\".",
        "",
        "A abordagem só sai DEPOIS do achado real (ver skills libertus-shield-prospeccao e",
        "libertus-bug-bounty-web). Mensagem sem prova técnica = spam.",
        "",
        "## Prioridade QUENTE (falar primeiro)",
        "",
    ]
    for p, titulo in (("QUENTE", None), ("A", "Prioridade A — tem site institucional (alvo de laudo)"),
                      ("B", "Prioridade B — sem site (pitch de presença digital)")):
        grupo = [x for x in linhas if x["prioridade"] == p]
        if not grupo:
            continue
        if p != "QUENTE":
            md += [f"## {titulo}", ""]
        for x in grupo:
            tel = x["telefone"] or "telefone não listado"
            extra = f" — {x['observacao']}" if x["observacao"] else ""
            link = f" · [WhatsApp]({x['whatsapp']})" if x["whatsapp"] else ""
            md.append(f"- **{x['nome']}** ({x['vertical']}) — {tel}{link}{extra}")
        md.append("")

    md += [
        "## O que fazer com esta lista",
        "",
        "1. Rodar recon passivo (headers/SSL/WHOIS/HTML) em todos os domínios da prioridade A.",
        "2. Gerar laudo por empresa — o LIBERTUS produz, custo ~zero.",
        "3. Mandar a mensagem de abertura do `shield/PRODUTOS_E_PRECOS.md` com o achado específico.",
        "4. Registrar o status de cada uma na coluna `status` do CSV (a_contatar → contatado → respondeu → reuniao → fechou/recusou).",
        "",
        "Meta realista da semana: 20 contatos feitos. Não 20 laudos — 20 CONTATOS.",
    ]

    md_path = os.path.join(BASE, "shield", "LEADS_ARIQUEMES.md")
    open(md_path, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(f"gerado: {md_path} ({len(linhas)} leads)")
    print(f"gerado: {csv_path}")
    for p in ("QUENTE", "A", "B"):
        print(f"  {p}: {sum(1 for x in linhas if x['prioridade'] == p)}")


if __name__ == "__main__":
    main()
