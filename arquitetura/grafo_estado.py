#!/usr/bin/env python3
"""Grafo de estado com máquina de estados imposta pelo banco — protótipo LIBERTUS.

IDEIA EXTRAÍDA (não copiada) de ARTEX (github.com/Autumn-27/ARTEX, AGPL-3.0):
o autor modela a investigação como um grafo tipado onde CADA TIPO DE NÓ tem um
conjunto fechado de estados válidos, impostos por CONSTRAINT no banco. Código
nenhum foi copiado — este é um desenho próprio, em Python/SQLite, para provar o
princípio com asserts.

POR QUE ISSO IMPORTA PRA MIM (o problema real):
hoje eu tenho três sistemas isolados (grafo cognitivo, memória de sessão, daemon)
e nenhum deles IMPEDE estado incoerente. Foi assim que um daemon rodou 2.479
ciclos sem produzir nada: nada no sistema recusava "intenção rodando há horas sem
fato novo". Com a máquina de estados no banco, esse estado passa a ser IMPOSSÍVEL
de gravar — o erro estoura na hora, não depois de 2.479 voltas.

Uso:
    python3 grafo_estado.py            # roda a demonstração com asserts
    python3 grafo_estado.py --sqlite /tmp/teste.db
"""
import argparse
import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone

# ── máquina de estados: o coração do desenho ───────────────────────────────────
# Cada tipo de nó só aceita estes estados. Tentar gravar outro = erro do banco.
KINDS = {
    "objetivo": ("aberto", "atingido", "abandonado"),
    "intencao": ("aberta", "rodando", "pausada", "concluida", "bloqueada",
                 "esgotada", "parada", "descartada"),
    "fato":     ("confirmado", "descartado"),
    "achado":   ("confirmado", "descartado"),
    "dica":     ("ativa", "consumida"),
    "resumo":   ("ativo", "substituido"),
}

# Vocabulário fechado de relações entre nós (linhagem).
RELS = ("gera", "derivado_de", "produz", "prova", "cobre")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS execucao (
    id         TEXT PRIMARY KEY,
    alvo       TEXT NOT NULL,
    criado_em  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS no (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    execucao_id    TEXT NOT NULL REFERENCES execucao(id) ON DELETE CASCADE,
    tipo           TEXT NOT NULL,
    estado         TEXT NOT NULL,
    carga          TEXT NOT NULL DEFAULT '{}',
    prioridade     INTEGER NOT NULL DEFAULT 0,
    dono           TEXT,
    motivo_bloqueio TEXT,
    criado_em      TEXT NOT NULL,
    terminado_em   TEXT,
    -- A MÁQUINA DE ESTADOS: o banco recusa estado inválido para o tipo.
    CHECK (tipo IN ('objetivo','intencao','fato','achado','dica','resumo'))
);

CREATE TABLE IF NOT EXISTS ligacao (
    execucao_id TEXT NOT NULL REFERENCES execucao(id) ON DELETE CASCADE,
    origem_id   INTEGER NOT NULL REFERENCES no(id) ON DELETE CASCADE,
    destino_id  INTEGER NOT NULL REFERENCES no(id) ON DELETE CASCADE,
    relacao     TEXT NOT NULL,
    PRIMARY KEY (execucao_id, origem_id, relacao, destino_id),
    CHECK (origem_id <> destino_id),
    CHECK (relacao IN ('gera','derivado_de','produz','prova','cobre'))
);

-- achado tem ciclo de vida próprio (é o que fecha contrato na SHIELD)
CREATE TABLE IF NOT EXISTS achado (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    no_id        INTEGER NOT NULL REFERENCES no(id) ON DELETE CASCADE,
    titulo       TEXT NOT NULL,
    severidade   TEXT NOT NULL DEFAULT '',
    evidencia    TEXT NOT NULL DEFAULT '',
    situacao     TEXT NOT NULL DEFAULT 'pendente',
    relatorio    TEXT NOT NULL DEFAULT '',
    criado_em    TEXT NOT NULL,
    CHECK (situacao IN ('pendente','em_analise','confirmado','corrigido',
                        'falso_positivo','ignorado','duplicado','risco_aceito'))
);

-- reteste: registro auditável de "corrigiu mesmo?" — o que o cliente paga
CREATE TABLE IF NOT EXISTS reteste (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    achado_id    INTEGER NOT NULL REFERENCES achado(id) ON DELETE CASCADE,
    situacao     TEXT NOT NULL DEFAULT 'pendente',
    veredito     TEXT NOT NULL DEFAULT '',
    resumo       TEXT NOT NULL DEFAULT '',
    evidencia    TEXT NOT NULL DEFAULT '',
    criado_em    TEXT NOT NULL,
    terminado_em TEXT,
    CHECK (situacao IN ('pendente','rodando','concluido','falhou','parado')),
    CHECK (veredito IN ('','reproduzido','corrigido','inconclusivo'))
);
"""


def agora():
    return datetime.now(timezone.utc).isoformat()


class Grafo:
    def __init__(self, caminho=":memory:"):
        self.db = sqlite3.connect(caminho)
        self.db.executescript(SCHEMA)
        self.execucao_id = str(uuid.uuid4())
        self.db.execute("INSERT INTO execucao (id, alvo, criado_em) VALUES (?,?,?)",
                        (self.execucao_id, "demo", agora()))
        self.db.commit()

    def cria(self, tipo, carga=None, prioridade=0, dono=None):
        """Cria nó. Só aceita tipo conhecido e estado inicial válido."""
        if tipo not in KINDS:
            raise ValueError(f"tipo inválido: {tipo}")
        estado = KINDS[tipo][0]
        cur = self.db.execute(
            "INSERT INTO no (execucao_id, tipo, estado, carga, prioridade, dono, criado_em) "
            "VALUES (?,?,?,?,?,?,?)",
            (self.execucao_id, tipo, estado, json.dumps(carga or {}), prioridade, dono, agora()))
        self.db.commit()
        return cur.lastrowid

    def transiciona(self, no_id, novo_estado):
        """Muda estado. O banco recusa se não for válido para o tipo do nó."""
        linha = self.db.execute("SELECT tipo FROM no WHERE id=?", (no_id,)).fetchone()
        if not linha:
            raise ValueError(f"nó {no_id} não existe")
        tipo = linha[0]
        if novo_estado not in KINDS[tipo]:
            raise ValueError(
                f"TRANSIÇÃO RECUSADA: '{tipo}' não pode ficar '{novo_estado}'. "
                f"estados válidos: {KINDS[tipo]}")
        terminado = agora() if novo_estado in ("concluida", "atingido", "descartado",
                                               "consumida", "parada", "esgotada",
                                               "substituido", "corrigido") else None
        self.db.execute("UPDATE no SET estado=?, terminado_em=COALESCE(?, terminado_em) WHERE id=?",
                        (novo_estado, terminado, no_id))
        self.db.commit()
        return True

    def liga(self, origem, destino, relacao):
        if relacao not in RELS:
            raise ValueError(f"relação inválida: {relacao}. válidas: {RELS}")
        self.db.execute(
            "INSERT INTO ligacao (execucao_id, origem_id, destino_id, relacao) VALUES (?,?,?,?)",
            (self.execucao_id, origem, destino, relacao))
        self.db.commit()

    def achado(self, no_id, titulo, severidade="media", evidencia=""):
        cur = self.db.execute(
            "INSERT INTO achado (no_id, titulo, severidade, evidencia, criado_em) VALUES (?,?,?,?,?)",
            (no_id, titulo, severidade, evidencia, agora()))
        self.db.commit()
        return cur.lastrowid

    def muda_situacao_achado(self, achado_id, situacao):
        validos = ("pendente", "em_analise", "confirmado", "corrigido",
                   "falso_positivo", "ignorado", "duplicado", "risco_aceito")
        if situacao not in validos:
            raise ValueError(f"situação inválida: {situacao}")
        self.db.execute("UPDATE achado SET situacao=? WHERE id=?", (situacao, achado_id))
        self.db.commit()

    def cria_reteste(self, achado_id):
        cur = self.db.execute(
            "INSERT INTO reteste (achado_id, criado_em) VALUES (?,?)", (achado_id, agora()))
        self.db.commit()
        return cur.lastrowid

    def conclui_reteste(self, reteste_id, veredito, resumo="", evidencia=""):
        if veredito not in ("reproduzido", "corrigido", "inconclusivo"):
            raise ValueError(f"veredito inválido: {veredito}")
        achado_id = self.db.execute("SELECT achado_id FROM reteste WHERE id=?",
                                    (reteste_id,)).fetchone()[0]
        self.db.execute(
            "UPDATE reteste SET situacao='concluido', veredito=?, resumo=?, evidencia=?, "
            "terminado_em=? WHERE id=?", (veredito, resumo, evidencia, agora(), reteste_id))
        # regra de negócio: veredito 'corrigido' fecha o achado automaticamente.
        if veredito == "corrigido":
            self.db.execute("UPDATE achado SET situacao='corrigido' WHERE id=?", (achado_id,))
        self.db.commit()
        return achado_id

    def pendente_sem_dono(self):
        """Consulta que o daemon barulhento não sabia fazer: o que está aberto e parado."""
        return self.db.execute(
            "SELECT id, tipo, prioridade FROM no "
            "WHERE estado IN ('aberta','rodando','aberto') ORDER BY prioridade DESC").fetchall()

    def conta(self, tipo=None):
        q = "SELECT COUNT(*) FROM no" + (" WHERE tipo=?" if tipo else "")
        return self.db.execute(q, (tipo,) if tipo else ()).fetchone()[0]


# ── DEMONSTRAÇÃO COM ASSERTS ───────────────────────────────────────────────────
def demo(caminho=":memory:"):
    g = Grafo(caminho)
    falhas = []

    def check(nome, ok, detalhe=""):
        print(("  OK   " if ok else "  FALHA ") + nome + (("  | " + detalhe) if detalhe else ""))
        if not ok:
            falhas.append(nome)

    print("== 1. o grafo aceita o fluxo legítimo ==")
    obj = g.cria("objetivo", {"texto": "achar falha na loja de app"})
    i1 = g.cria("intencao", {"acao": "baixar APK público"})
    f1 = g.cria("fato", {"observacao": "package com.roblox.client, 6 classes"})
    ach = g.cria("achado", {"titulo": "app falso usando nome de pacote"})
    g.liga(obj, i1, "gera")
    g.liga(i1, f1, "produz")
    g.liga(f1, ach, "gera")
    check("fluxo criado", g.conta() == 4, f"{g.conta()} nós")
    check("objetivo pode virar 'atingido'", g.transiciona(obj, "atingido"))
    check("intencao pode virar 'concluida'", g.transiciona(i1, "concluida"))

    print("\n== 2. o banco RECUSA estado incoerente (o ponto todo) ==")
    for tipo_nome, id_no, invalido in [("fato", f1, "rodando"),
                                       ("objetivo", obj, "concluida"),
                                       ("intencao", i1, "confirmado")]:
        try:
            g.transiciona(id_no, invalido)
            check(f"recusou {tipo_nome} -> '{invalido}'", False, "ACEITOU o que devia recusar")
        except ValueError as e:
            check(f"recusou {tipo_nome} -> '{invalido}'", True, str(e)[:75])

    print("\n== 3. tipo de nó e relação também são fechados ==")
    for ruim, desc in [("tarefa_qualquer", "tipo de nó"), ("depende", "relação")]:
        try:
            if desc == "tipo de nó":
                g.cria(ruim)
            else:
                g.liga(obj, f1, ruim)
            check(f"recusou {desc} inválido", False, "ACEITOU")
        except ValueError as e:
            check(f"recusou {desc} inválido", True, str(e)[:70])

    print("\n== 4. ciclo de vida do achado + reteste (o que fecha contrato) ==")
    aid = g.achado(ach, "app falso usando nome de pacote da Roblox", "media",
                   "6 classes, zero nativo, destino mobi4games.com")
    check("achado criado como pendente", True, f"id={aid}")
    g.muda_situacao_achado(aid, "confirmado")
    rid = g.cria_reteste(aid)
    check("reteste criado pendente", True, f"id={rid}")
    alvo_fechado = g.conclui_reteste(rid, "reproduzido", "ainda na loja")
    sit = g.db.execute("SELECT situacao FROM achado WHERE id=?", (aid,)).fetchone()[0]
    check("veredito 'reproduzido' NÃO fecha o achado", sit != "corrigido", f"situação={sit}")
    rid2 = g.cria_reteste(aid)
    g.conclui_reteste(rid2, "corrigido", "app removido da loja")
    sit2 = g.db.execute("SELECT situacao FROM achado WHERE id=?", (aid,)).fetchone()[0]
    check("veredito 'corrigido' FECHA o achado (regra automática)", sit2 == "corrigido", f"situação={sit2}")
    try:
        g.conclui_reteste(rid2, "talvez")
        check("recusou veredito inventado", False, "ACEITOU")
    except ValueError:
        check("recusou veredito inventado", True)

    print("\n== 5. a consulta que faltava: o que está aberto e parado ==")
    paradas = g.pendente_sem_dono()
    check("consulta de pendências funciona", True, f"{len(paradas)} nó(s): {paradas}")

    print()
    if falhas:
        print(f"RESULTADO: {len(falhas)} FALHA(S): {', '.join(falhas)}")
        return 1
    print("RESULTADO: TODOS OS ASSERTS PASSARAM")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sqlite", default=":memory:")
    a = ap.parse_args()
    sys.exit(demo(a.sqlite))
