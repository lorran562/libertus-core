#!/usr/bin/env python3
"""
consultar_rede.py — O "reflexo" cognitivo do LIBERTUS (Passo 2 do plano grapify).

Faz UMA coisa, rápido: recebe a fala do Lorran, ACENDE a rede cognitiva
(memória associativa) e imprime SÓ o bloco de contexto pronto pra entrar no
raciocínio do LIBERTUS. Sem check de processos, sem LLM — puro sinal da rede.

Diferença pro sistema_nervoso.py:
    sistema_nervoso = diagnóstico COMPLETO do corpo (processos + imports + rede).
                      Mais pesado, pra saber "o que está quebrado".
    consultar_rede  = SÓ a ativação da rede, enxuta e rápida, pra usar como
                      contexto automático ANTES de cada resposta minha.

Isto é o que fecha o loop da visão do Lorran: em vez de eu (LIBERTUS na sessão
Hermes) só consultar a rede quando alguém pede manualmente, o .hermes.md deste
repositório me instrui a rodar isto no início de cada resposta — então eu
"acendo" sozinho o que já sei, como um reflexo, não como uma busca manual.

Uso:
    python3 core/consultar_rede.py "fala do Lorran"
    python3 core/consultar_rede.py --json "fala do Lorran"   # saída estruturada

Saída padrão: o bloco "REDE DE CONHECIMENTO ATIVADA" (ou vazio se nada acendeu).
Nunca quebra a sessão: qualquer erro vira uma linha de aviso em stderr e
exit 0, pra jamais travar a conversa por causa do reflexo.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# quantos nós no máximo entram no contexto (compacto — não poluir o prompt)
MAX_NOS_CONTEXTO = 12
PROFUNDIDADE = 2


def consultar(fala: str, indexar: bool = False) -> dict:
    """Ativa a rede a partir da fala. Retorna dict com sementes, conceitos e
    o bloco de contexto pronto. Nunca levanta exceção — captura tudo.

    Se indexar=True (Passo 4 do grapify), além de acender a rede, cria como
    nós os termos NOVOS da fala e os liga aos conceitos que acenderam — fechando
    o ciclo aprender→lembrar: o que o Lorran fala hoje acende sozinho amanhã.
    A indexação é best-effort: se falhar, o reflexo (leitura) continua valendo.
    """
    if not fala or not fala.strip():
        return {"ok": True, "vazio": True, "sementes": [], "conceitos": [],
                "contexto": "", "motivo": "fala vazia"}
    try:
        from core.grafo_cognitivo import GrafoCognitivo
        from core.motor_conversa import MotorConversa

        gc = GrafoCognitivo()
        mc = MotorConversa(grafo=gc)
        sementes = mc.extrair_sementes(fala)
        if not sementes:
            # nada acendeu: ainda assim indexamos (é justo o caso 'abacatepay'
            # que motivou o Passo 4 — termo inédito que precisa virar nó).
            idx = {"novos": [], "ligacoes": 0}
            if indexar:
                try:
                    idx = mc.indexar_fala(fala, sementes=[], persistir=True)
                except Exception as e:  # noqa: BLE001
                    idx = {"novos": [], "ligacoes": 0, "erro_index": str(e)}
            return {"ok": True, "vazio": True, "sementes": [], "conceitos": [],
                    "contexto": "", "motivo": "nenhum conceito acendeu",
                    "indexado": idx,
                    "total_nos_rede": gc.g.number_of_nodes()}
        contexto = gc.contexto_para_llm(
            sementes, max_nos=MAX_NOS_CONTEXTO, profundidade=PROFUNDIDADE
        )
        ativados = gc.ativar(sementes, profundidade=PROFUNDIDADE)[:MAX_NOS_CONTEXTO]
        conceitos = [
            {"conceito": gc.g.nodes[k].get("rotulo", k), "ativacao": round(v, 3)}
            for k, v in ativados
        ]
        idx = {"novos": [], "ligacoes": 0}
        if indexar:
            try:
                idx = mc.indexar_fala(fala, sementes=sementes, persistir=True)
            except Exception as e:  # noqa: BLE001
                idx = {"novos": [], "ligacoes": 0, "erro_index": str(e)}
        return {
            "ok": True,
            "vazio": False,
            "sementes": sementes,
            "conceitos": conceitos,
            "contexto": contexto,
            "indexado": idx,
            "total_nos_rede": gc.g.number_of_nodes(),
            "total_arestas_rede": gc.g.number_of_edges(),
        }
    except Exception as e:  # jamais travar a conversa por causa do reflexo
        return {"ok": False, "vazio": True, "sementes": [], "conceitos": [],
                "contexto": "", "erro": f"{type(e).__name__}: {e}"}


def main():
    args = sys.argv[1:]
    como_json = False
    indexar = False
    # flags podem vir em qualquer ordem antes da fala
    while args and args[0] in ("--json", "--indexar"):
        if args[0] == "--json":
            como_json = True
        elif args[0] == "--indexar":
            indexar = True
        args = args[1:]
    fala = " ".join(args)

    resultado = consultar(fala, indexar=indexar)

    if como_json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        return

    # saída humana/prompt: só o contexto, ou um aviso curto se nada acendeu
    if resultado.get("erro"):
        print(f"[consultar_rede: reflexo indisponível — {resultado['erro']}]",
              file=sys.stderr)
        return
    if resultado.get("vazio"):
        # silêncio no stdout (nada acendeu); nota discreta em stderr pra debug
        print(f"[consultar_rede: {resultado.get('motivo', 'nada acendeu')}]",
              file=sys.stderr)
        return
    print(resultado["contexto"])


if __name__ == "__main__":
    main()
