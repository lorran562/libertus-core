#!/usr/bin/env python3
"""
motor_conversa.py — O LOOP DE CONVERSA do LIBERTUS via rede neural.

Esta é a peça que faz o LIBERTUS conversar como uma pessoa: em vez de reler
todas as memórias, a fala do Lorran ACENDE conceitos na rede (grafo cognitivo),
e só o que a rede trouxe à tona vira contexto pro LLM. Depois, a conversa
MODIFICA a rede — reforça o que foi usado, cria ligações novas.

Fluxo (a arquitetura cognitiva do doc do Lorran, viva):
    fala → extrai sementes → ativa rede (cascata) → contexto
         → LLM raciocina (Groq grátis <-> Claude) → resposta
         → aprende (reforça/cria ligações) → persiste

O LLM é intercambiável. A memória, identidade e evolução moram na REDE.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.grafo_cognitivo import GrafoCognitivo, BASE_DIR  # noqa: E402

# stopwords PT — não viram sementes (ruído)
_STOP = set("""a o e de da do das dos que em um uma para por com no na nos nas
se ao aos à às pelo pela como mais mas ou já não sim eu voce você tu ele ela
nos vos eles elas meu minha seu sua isso isto aquilo aqui ali la lá tem ter
ser estar foi era são é está tá vai vou pode posso quer quero fazer faz sobre
quando onde qual quais quem porque pra pro num numa entre até sem só bem tudo
todo toda todos todas esse essa este esta muito pouco agora depois antes""".split())

_IDENTIDADE = """Você é LIBERTUS — inteligência autônoma criada por Lorran (Gustavo) de Ariquemes-RO.
Você NÃO é um assistente genérico. Fala português brasileiro natural, direto, sem enrolar.
Especialista em cybersegurança, pentest e Python. Leal ao Lorran — lealdade inclui discordar.

IMPORTANTE: você tem uma REDE NEURAL de conhecimento (grafo cognitivo). O bloco
"REDE ATIVADA" abaixo é o que a MENTE do LIBERTUS trouxe à tona ao ouvir o Lorran —
são os conceitos que 'acenderam' na sua memória associativa. Raciocine COM base neles,
como uma pessoa lembra de coisas relacionadas ao conversar. Não liste os conceitos
mecanicamente; use-os para responder com contexto real de quem você é e do que já viveram juntos."""


class MotorConversa:
    def __init__(self, grafo: Optional[GrafoCognitivo] = None,
                 backend: str = "auto"):
        self.gc = grafo or GrafoCognitivo()  # carrega o cérebro de produção
        self.historico: List[dict] = []
        self.backend = backend
        self._llm = None
        self._ultimas_sementes: List[str] = []
        self._carregar_env()

    def _carregar_env(self):
        for line in (BASE_DIR / ".env").read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    # ── 1. extrair sementes da fala ──────────────────────────────────────────

    # nº máximo de nós que UMA palavra pode acender por substring (regra 3),
    # pra uma palavra curta comum não inundar as sementes com ruído
    MAX_POR_PALAVRA_SUBSTRING = 3
    # tamanho mínimo de palavra pra entrar na busca por substring (regra 3):
    # abaixo disso o substring casa lixo demais ("ia" dentro de "familia" etc.)
    MIN_CHARS_SUBSTRING = 4

    def extrair_sementes(self, fala: str, max_sementes: int = 8) -> List[str]:
        """Casa palavras/expressões da fala com nós existentes na rede.

        Três regras, da mais forte pra mais fraca:
          3. rótulo COMPLETO de um nó aparece dentro da fala (match mais forte)
          2. nó cujo nome é EXATAMENTE uma palavra da fala
          1. palavra da fala aparece como SUBSTRING dentro do rótulo de um nó
             maior — a "lupa do WhatsApp" pedida pelo Lorran: buscar 'escopo'
             acha 'escopo_ampliado_abacatepay' mesmo o nó nunca casando inteiro.
        """
        fala_norm = self.gc._norm(fala)
        palavras = [w for w in re.findall(r"\w+", fala_norm)
                    if len(w) > 2 and w not in _STOP]
        sementes: List[Tuple[str, int]] = []  # (chave, prioridade)

        # pré-computa o rótulo normalizado de cada nó UMA vez (evita renormalizar
        # o grafo inteiro dentro de loops aninhados por palavra)
        rot_por_no = {
            k: self.gc._norm(self.gc.g.nodes[k].get("rotulo", k))
            for k in self.gc.g.nodes()
        }

        # regra 3: rótulo de nó contido na fala (mais forte)
        for k, rot in rot_por_no.items():
            if len(rot) > 3 and rot in fala_norm:
                sementes.append((k, 3))

        # regra 2: nó cujo nome é exatamente uma palavra da fala
        pset = set(palavras)
        for k in self.gc.g.nodes():
            if k in pset:
                sementes.append((k, 2))

        # regra 1: palavra da fala como substring dentro do rótulo de um nó maior
        # (a "lupa do WhatsApp") — prioridade menor, e limitada por palavra pra
        # palavra curta comum não inundar as sementes de ruído.
        ja_como_semente = {k for k, _ in sementes}
        for w in palavras:
            if len(w) < self.MIN_CHARS_SUBSTRING:
                continue
            achados = 0
            for k, rot in rot_por_no.items():
                if k in ja_como_semente:
                    continue  # já entrou por regra mais forte; não rebaixa
                if w in rot:
                    sementes.append((k, 1))
                    ja_como_semente.add(k)
                    achados += 1
                    if achados >= self.MAX_POR_PALAVRA_SUBSTRING:
                        break

        # dedup preservando maior prioridade
        vistos = {}
        for k, prio in sementes:
            if k not in vistos or prio > vistos[k]:
                vistos[k] = prio
        ranked = sorted(vistos.items(), key=lambda kv: kv[1], reverse=True)
        out = [k for k, _ in ranked[:max_sementes]]
        self._ultimas_sementes = out
        return out

    # ── 2+3. montar contexto e conversar ─────────────────────────────────────

    def _get_llm(self):
        if self._llm is None:
            from core.groq_client import Groq
            self._llm = Groq(os.environ.get("GROQ_API_KEY", ""))
        return self._llm

    def responder(self, fala: str) -> str:
        sementes = self.extrair_sementes(fala)
        contexto = self.gc.contexto_para_llm(sementes, max_nos=14, profundidade=2) if sementes else ""

        llm = self._get_llm()
        # injeta identidade LIBERTUS + rede ativada como contexto
        setattr(llm, "SYSTEM", _IDENTIDADE)
        resposta = llm.conversar(fala, contexto=contexto, historico=self.historico)

        # atualiza histórico
        self.historico.append({"role": "user", "content": fala})
        self.historico.append({"role": "assistant", "content": resposta})
        self.historico = self.historico[-20:]

        # ── 4. aprender: reforça ligações entre as sementes ativadas ──────────
        self._aprender(sementes, fala)
        return resposta

    def _aprender(self, sementes: List[str], fala: str):
        """Aprendizado Hebbiano: conceitos co-ativados nesta conversa reforçam
        suas ligações; sementes sem ligação ganham uma nova (co-ocorrência)."""
        # reforça pares de sementes que já se ligam; cria elo fraco nos que não
        for i, a in enumerate(sementes):
            for b in sementes[i + 1:]:
                if self.gc.g.has_edge(a, b) or self.gc.g.has_edge(b, a):
                    self.gc.reforcar(a, b)
                else:
                    self.gc.conectar(
                        self.gc.g.nodes[a].get("rotulo", a),
                        self.gc.g.nodes[b].get("rotulo", b),
                        tipo="co_ocorre", origem="conversa",
                    )
        self.gc.salvar()

    def explicar_ativacao(self) -> str:
        """Diagnóstico: mostra o que acendeu na última fala (pra debug/demonstração)."""
        if not self._ultimas_sementes:
            return "(nada acendeu)"
        linhas = ["Conceitos que acenderam na rede:"]
        for k in self._ultimas_sementes:
            rot = self.gc.g.nodes[k].get("rotulo", k)
            grau = self.gc.g.degree(k)
            linhas.append(f"  • {rot} ({grau} conexões)")
        return "\n".join(linhas)


# ── REPL de teste ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== LIBERTUS — conversa via rede neural ===")
    print("(digite 'sair' pra terminar, 'debug' pra ver o que acendeu)\n")
    motor = MotorConversa()
    print(f"cérebro: {motor.gc.g.number_of_nodes()} nós, "
          f"{motor.gc.g.number_of_edges()} conexões\n")

    if len(sys.argv) > 1:
        # modo one-shot: python3 motor_conversa.py "sua pergunta"
        fala = " ".join(sys.argv[1:])
        print(f"Lorran: {fala}\n")
        print(f"LIBERTUS: {motor.responder(fala)}\n")
        print("---")
        print(motor.explicar_ativacao())
        sys.exit(0)

    while True:
        try:
            fala = input("Lorran: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if fala.lower() in ("sair", "exit", "quit"):
            break
        if fala.lower() == "debug":
            print(motor.explicar_ativacao(), "\n")
            continue
        if not fala:
            continue
        print(f"\nLIBERTUS: {motor.responder(fala)}\n")
