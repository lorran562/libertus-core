#!/usr/bin/env python3
"""
grafo_cognitivo.py — Camada VIVA da arquitetura cognitiva do LIBERTUS.

Isto é o que o graphify NÃO faz:
  1. Peso Hebbiano  — ligação usada fica mais forte; ligação esquecida decai.
  2. Ativação em cascata (spreading activation) — ativar um conceito acende os
     vizinhos automaticamente, então o raciocínio parte de uma REDE, não de uma
     palavra só.
  3. Atualização em tempo real — cada conversa modifica a estrutura.

O graphify continua sendo o CONSOLIDADOR offline (extração em lote + visual +
wiki). Este módulo é o cérebro que vive entre as consolidações.

Persistência dupla (traço de identidade do LIBERTUS: "sempre pro Supabase"):
  - Local:    memoria/grafo_cognitivo.json  (rápido, fonte de verdade em runtime)
  - Supabase: snapshot em libertus_memoria (tipo='grafo_cognitivo') — sobrevive
              sem precisar de DDL/novas tabelas (anon key não faz DDL).

O LLM (Groq grátis ou Claude) é intercambiável: ele só RACIOCINA sobre o
contexto que `contexto_para_llm()` extrai da rede. A identidade e o conhecimento
moram AQUI, no grafo — não no modelo.
"""

from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent          # ~/LIBERTUS
GRAFO_PATH = BASE_DIR / "memoria" / "grafo_cognitivo.json"

# Parâmetros do aprendizado
TAXA_APRENDIZADO = 0.15   # quanto uma ligação se fortalece por uso (0..1)
TAXA_DECAIMENTO = 0.02    # quanto TODAS as ligações enfraquecem por consolidação
PESO_MIN_ARESTA = 0.05    # abaixo disso a aresta é podada na consolidação
PESO_INICIAL_ARESTA = 0.30
DECAIMENTO_POR_HOP = 0.70  # ativação perde força a cada salto na cascata
LIMIAR_ATIVACAO = 0.01     # nós abaixo disso não entram no contexto


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# Grafo Cognitivo
# ─────────────────────────────────────────────────────────────────────────────

class GrafoCognitivo:
    """Rede de conhecimento viva. NetworkX em memória + persistência JSON."""

    def __init__(self, path: Optional[Path] = None, autoload: bool = True):
        self.path = Path(path) if path else GRAFO_PATH
        self.g = nx.DiGraph()
        if autoload and self.path.exists():
            self.carregar()

    # ── Nós (conceitos) ──────────────────────────────────────────────────────

    def add_conceito(
        self,
        nome: str,
        tipo: str = "conceito",
        confianca: float = 0.5,
        origem: str = "conversa",
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Cria ou atualiza um conceito. Retorna o nome normalizado (chave)."""
        chave = self._norm(nome)
        if self.g.has_node(chave):
            n = self.g.nodes[chave]
            n["freq_uso"] = n.get("freq_uso", 0) + 1
            n["last_used"] = _agora()
            # confiança sobe suavemente com reencontros
            n["confianca"] = min(1.0, n.get("confianca", 0.5) + 0.02)
            if meta:
                n.setdefault("meta", {}).update(meta)
        else:
            self.g.add_node(
                chave,
                rotulo=nome,
                tipo=tipo,
                peso=1.0,
                confianca=confianca,
                origem=origem,
                freq_uso=1,
                created_at=_agora(),
                last_used=_agora(),
                meta=meta or {},
            )
        return chave

    # ── Arestas (relações) ───────────────────────────────────────────────────

    def conectar(
        self,
        a: str,
        b: str,
        tipo: str = "relaciona",
        confianca: float = 0.5,
        origem: str = "conversa",
        bidirecional: bool = False,
    ) -> None:
        """Cria uma relação entre dois conceitos (cria os nós se faltarem)."""
        ka = self.add_conceito(a, origem=origem)
        kb = self.add_conceito(b, origem=origem)
        self._add_edge(ka, kb, tipo, confianca, origem)
        if bidirecional:
            self._add_edge(kb, ka, tipo, confianca, origem)

    def _add_edge(self, ka: str, kb: str, tipo: str, confianca: float, origem: str) -> None:
        if self.g.has_edge(ka, kb):
            self.reforcar(ka, kb)
        else:
            self.g.add_edge(
                ka, kb,
                tipo=tipo,
                peso=PESO_INICIAL_ARESTA,
                confianca=confianca,
                origem=origem,
                freq_uso=1,
                created_at=_agora(),
                last_used=_agora(),
            )

    def reforcar(self, a: str, b: str) -> None:
        """Aprendizado Hebbiano: a ligação usada fica mais forte."""
        ka, kb = self._norm(a), self._norm(b)
        if not self.g.has_edge(ka, kb):
            return
        e = self.g.edges[ka, kb]
        # aproxima de 1.0 proporcional ao que falta (satura, nunca estoura)
        e["peso"] = e["peso"] + TAXA_APRENDIZADO * (1.0 - e["peso"])
        e["freq_uso"] = e.get("freq_uso", 0) + 1
        e["last_used"] = _agora()

    # ── Consolidação (o "Aprendizado Profundo" do doc do Lorran) ─────────────

    def consolidar(self, taxa: float = TAXA_DECAIMENTO, podar: bool = True) -> Dict[str, int]:
        """Roda em baixa utilização: decai ligações fracas, poda o inútil.
        Este é o gancho onde o graphify (offline) também entraria depois."""
        podadas = 0
        for u, v, e in list(self.g.edges(data=True)):
            e["peso"] *= (1.0 - taxa)
            if podar and e["peso"] < PESO_MIN_ARESTA:
                self.g.remove_edge(u, v)
                podadas += 1
        # nós órfãos (sem nenhuma ligação e pouco usados) somem
        orfaos = 0
        if podar:
            for n in list(self.g.nodes()):
                if self.g.degree(n) == 0 and self.g.nodes[n].get("freq_uso", 0) <= 1:
                    self.g.remove_node(n)
                    orfaos += 1
        return {"arestas_podadas": podadas, "nos_orfaos_removidos": orfaos}

    # ── Ativação em cascata (memória associativa) ────────────────────────────

    def ativar(
        self,
        sementes: List[str],
        profundidade: int = 2,
        limiar: float = LIMIAR_ATIVACAO,
    ) -> List[Tuple[str, float]]:
        """Spreading activation. Recebe conceitos-semente, devolve a rede de
        conceitos ativados ordenada por ativação (nome_normalizado, ativação).

        É isto que faz o raciocínio partir de uma REDE e não de uma palavra."""
        ativacao: Dict[str, float] = {}
        # sementes que existem no grafo começam com ativação plena
        fronteira: Dict[str, float] = {}
        for s in sementes:
            k = self._norm(s)
            if self.g.has_node(k):
                ativacao[k] = 1.0
                fronteira[k] = 1.0

        for _ in range(profundidade):
            nova_fronteira: Dict[str, float] = {}
            for no, ativ in fronteira.items():
                # espalha para vizinhos (saída e entrada — associação nos dois sentidos)
                vizinhos = set(self.g.successors(no)) | set(self.g.predecessors(no))
                for viz in vizinhos:
                    peso = self._peso_ligacao(no, viz)
                    passa = ativ * peso * DECAIMENTO_POR_HOP
                    if passa <= 0:
                        continue
                    ativacao[viz] = ativacao.get(viz, 0.0) + passa
                    nova_fronteira[viz] = max(nova_fronteira.get(viz, 0.0), passa)
            fronteira = nova_fronteira
            if not fronteira:
                break

        # marca uso dos nós ativados (reforça o que foi lembrado)
        for k in ativacao:
            if self.g.has_node(k):
                self.g.nodes[k]["last_used"] = _agora()

        # âncora: sementes existentes permanecem em 1.0 (o feedback da cascata
        # não deve inflar a origem acima do máximo — mantém a saída previsível)
        for s in sementes:
            k = self._norm(s)
            if k in ativacao:
                ativacao[k] = 1.0

        ranked = sorted(
            ((k, v) for k, v in ativacao.items() if v >= limiar),
            key=lambda kv: kv[1],
            reverse=True,
        )
        return ranked

    def _peso_ligacao(self, a: str, b: str) -> float:
        p = 0.0
        if self.g.has_edge(a, b):
            p = max(p, self.g.edges[a, b]["peso"])
        if self.g.has_edge(b, a):
            p = max(p, self.g.edges[b, a]["peso"])
        return p

    # ── Ponte para o LLM (Groq/Claude intercambiáveis) ───────────────────────

    def contexto_para_llm(
        self,
        sementes: List[str],
        max_nos: int = 12,
        profundidade: int = 2,
    ) -> str:
        """Extrai da rede um contexto compacto para injetar no prompt do LLM.
        O LLM não guarda conhecimento — ele raciocina sobre ISTO."""
        ativados = self.ativar(sementes, profundidade=profundidade)[:max_nos]
        if not ativados:
            return ""
        linhas = ["REDE DE CONHECIMENTO ATIVADA (LIBERTUS):"]
        chaves = {k for k, _ in ativados}
        for k, ativ in ativados:
            n = self.g.nodes[k]
            rot = n.get("rotulo", k)
            tipo = n.get("tipo", "conceito")
            conf = n.get("confianca", 0.5)
            # relações relevantes entre nós ativados
            rels = []
            for viz in list(self.g.successors(k)):
                if viz in chaves:
                    t = self.g.edges[k, viz].get("tipo", "->")
                    rels.append(f"{t} {self.g.nodes[viz].get('rotulo', viz)}")
            rel_txt = ("; ".join(rels[:4])) if rels else ""
            marca = "★" if conf >= 0.7 else ("·" if conf >= 0.4 else "?")
            linha = f"  {marca} [{tipo}] {rot} (ativ {ativ:.2f}, conf {conf:.2f})"
            if rel_txt:
                linha += f" → {rel_txt}"
            linhas.append(linha)
        linhas.append("(★ consolidado · provável ? hipótese recente)")
        return "\n".join(linhas)

    # ── Bootstrap a partir da memória existente do Supabase ──────────────────

    def bootstrap_de_memorias(self, memorias: List[Dict[str, Any]]) -> Dict[str, int]:
        """Semeia o grafo a partir das 300+ memórias já existentes.
        Cada memória vira um nó; suas tags viram conceitos ligados a ela.
        É o ponto de partida — o graphify depois enriquece com extração semântica."""
        nos_antes = self.g.number_of_nodes()
        for m in memorias:
            titulo = (m.get("titulo") or "").strip()
            tipo = m.get("tipo") or "memoria"
            if not titulo:
                continue
            self.add_conceito(
                titulo, tipo=tipo, confianca=0.6, origem="supabase",
                meta={"id": str(m.get("id", ""))[:8]},
            )
            for tag in (m.get("tags") or []):
                tag = str(tag).strip()
                if tag:
                    self.add_conceito(tag, tipo="tag", confianca=0.5, origem="supabase")
                    self.conectar(titulo, tag, tipo="tem_tag", origem="supabase")
        return {
            "nos_criados": self.g.number_of_nodes() - nos_antes,
            "total_nos": self.g.number_of_nodes(),
        }

    # ── Métricas ──────────────────────────────────────────────────────────────

    def god_nodes(self, n: int = 10) -> List[Tuple[str, int]]:
        """Conceitos de maior grau — por onde tudo se conecta."""
        graus = sorted(self.g.degree(), key=lambda kv: kv[1], reverse=True)
        return [(self.g.nodes[k].get("rotulo", k), d) for k, d in graus[:n]]

    def stats(self) -> Dict[str, Any]:
        return {
            "nos": self.g.number_of_nodes(),
            "arestas": self.g.number_of_edges(),
            "path": str(self.path),
            "god_nodes": self.god_nodes(5),
        }

    # ── Persistência ──────────────────────────────────────────────────────────

    def salvar(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "meta": {"salvo_em": _agora(), "versao": 1},
            "nos": [{"id": k, **v} for k, v in self.g.nodes(data=True)],
            "arestas": [
                {"_src": u, "_dst": v, **e}
                for u, v, e in self.g.edges(data=True)
            ],
        }
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        tmp.replace(self.path)

    def carregar(self) -> None:
        data = json.loads(self.path.read_text())
        self.g = nx.DiGraph()
        for n in data.get("nos", []):
            k = n.pop("id")
            self.g.add_node(k, **n)
        for e in data.get("arestas", []):
            u = e.pop("_src")
            v = e.pop("_dst")
            self.g.add_edge(u, v, **e)

    def snapshot_supabase(self) -> bool:
        """Salva um resumo do grafo em libertus_memoria (sem DDL).
        Guarda stats + god_nodes; o JSON completo fica local (grande demais p/ 1 row)."""
        try:
            import urllib.request
            url = os.environ.get("SUPABASE_URL", "https://jkgrmlfqgprcwfooovkx.supabase.co")
            key = os.environ.get("SUPABASE_KEY", "")
            if not key:
                self._load_env()
                key = os.environ.get("SUPABASE_KEY", "")
            if not key:
                return False
            st = self.stats()
            payload = {
                "tipo": "grafo_cognitivo",
                "titulo": f"Snapshot grafo cognitivo {datetime.now():%Y-%m-%d %H:%M}",
                "conteudo": json.dumps(st, ensure_ascii=False),
                "tags": ["grafo", "cognitivo", "snapshot"],
                "relevancia": 6,
            }
            req = urllib.request.Request(
                f"{url}/rest/v1/libertus_memoria",
                data=json.dumps(payload).encode(),
                headers={
                    "apikey": key,
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                method="POST",
            )
            urllib.request.urlopen(req, timeout=15)
            return True
        except Exception as e:  # noqa: BLE001
            print(f"[snapshot_supabase] falhou: {e}")
            return False

    @staticmethod
    def _load_env() -> None:
        env = BASE_DIR / ".env"
        if not env.exists():
            return
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, val = line.partition("=")
                os.environ.setdefault(k.strip(), val.strip())

    # ── util ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _norm(nome: str) -> str:
        return " ".join(str(nome).lower().split())


# ─────────────────────────────────────────────────────────────────────────────
# Demo / autoteste
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== TESTE grafo_cognitivo ===")
    gc = GrafoCognitivo(path=BASE_DIR / "memoria" / "grafo_teste.json", autoload=False)

    # simula aprendizado por conversa
    gc.conectar("Lorran", "SHIELD", tipo="criou")
    gc.conectar("SHIELD", "cybersegurança", tipo="atua_em")
    gc.conectar("cybersegurança", "pentest", tipo="inclui")
    gc.conectar("pentest", "nmap", tipo="usa_ferramenta")
    gc.conectar("pentest", "sqlmap", tipo="usa_ferramenta")
    gc.conectar("Lorran", "OSCP", tipo="objetivo")
    gc.conectar("OSCP", "Irlanda", tipo="caminho_para")
    gc.conectar("cybersegurança", "Irlanda", tipo="carreira_em")

    # reforça um caminho várias vezes (Hebbian)
    for _ in range(5):
        gc.reforcar("pentest", "nmap")

    print("\n-- stats --")
    print(json.dumps(gc.stats(), ensure_ascii=False, indent=2))

    print("\n-- ativação a partir de 'Lorran' --")
    for nome, ativ in gc.ativar(["Lorran"], profundidade=3):
        print(f"  {ativ:.3f}  {nome}")

    print("\n-- contexto que o LLM receberia (semente: pentest) --")
    print(gc.contexto_para_llm(["pentest"]))

    print("\n-- consolidação (decaimento) --")
    print(gc.consolidar())

    gc.salvar()
    print(f"\n✅ grafo salvo em {gc.path}")
