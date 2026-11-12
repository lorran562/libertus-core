#!/usr/bin/env python3
"""
LIBERTUS — lembrar.py  (v2)
===========================
Busca memórias semanticamente similares no banco vetorial ChromaDB.

v2 (após a indexação multi-fonte): a coleção deixou de ser só "histórico de
evolução" e passou a cobrir reports/, shield/, ejpt/, skills/, arquitetura/ —
então a busca ganhou filtro por fonte/importância e um modo --stats que
mostra o que eu realmente lembro.

Uso:
  python3 lembrar.py "como funciona LoRA fine-tuning"
  python3 lembrar.py "leads de Ariquemes" --fonte shield --n 10
  python3 lembrar.py "AbacatePay" --fonte reports,relatorios --json
  python3 lembrar.py --stats
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

MEM_DIR = Path(__file__).resolve().parent
BASE_DIR = MEM_DIR.parent
sys.path.insert(0, str(MEM_DIR))
sys.path.insert(0, str(BASE_DIR))

from core.ambiente import sanear_ambiente  # noqa: E402

CHROMA_DIR = MEM_DIR / "chroma_store"
COLLECTION_NAME = "libertus_memoria"

# Canal humano. Em --json vira stderr, para que o stdout seja JSON puro e
# qualquer script (hook do despertar, daemon, cortex) consiga parsear sem
# gambiarra. Antes, --json imprimia o cabeçalho humano ANTES do array e o
# json.loads estourava (visto em 23/out).
SAIDA = sys.stdout

# Piso de similaridade, EM PORCENTAGEM (0-100): abaixo disso a memória NÃO é
# sobre a pergunta, é só o vizinho mais próximo de um espaço vetorial com 5k
# itens. Sem piso, o briefing injetava snippet de código a 48% como se fosse
# "o que eu lembro sobre isso".
PISO_PADRAO = 0.0


def _p(*a, **k):
    """print humano que respeita o canal (stdout normal, stderr em --json)."""
    print(*a, file=SAIDA, **k)


# ── Conceitos: transformar fala longa em pergunta de verdade ────────────────
#
# Problema medido (23/out): o hook do despertar mandava a PRIMEIRA MENSAGEM
# INTEIRA como query. Mensagem longa com log, código e caminho de arquivo tem
# centróide longe de qualquer memória — o top-1 virava um trecho de script a
# 46-48%, com aparência de recall e zero informação. Busca boa precisa de
# pergunta curta e conceitual.

STOPWORDS = {
    # português funcional
    "para", "com", "sem", "porque", "quando", "onde", "como", "isso", "esse",
    "essa", "este", "esta", "aquilo", "aquele", "mas", "porem", "entao",
    "tambem", "muito", "mais", "menos", "ainda", "depois", "antes", "agora",
    "aqui", "ali", "voce", "voces", "ele", "ela", "eles", "elas", "meu",
    "minha", "seu", "sua", "nosso", "nossa", "dele", "dela", "sou", "esta",
    "estou", "estao", "estava", "tem", "tinha", "ter", "fazer", "faz",
    "feito", "vou", "vai", "vamos", "pode", "posso", "poderia", "deve",
    "quero", "queria", "preciso", "sei", "sabe", "acho", "vejo", "ver",
    "olha", "olhar", "fala", "falar", "dizer", "diz", "sobre", "entre",
    "tudo", "todo", "toda", "todos", "todas", "nada", "cada", "outro",
    "outra", "mesmo", "mesma", "apenas", "so", "bem", "mal", "sim", "nao",
    "uma", "uns", "umas", "dos", "das", "pelo", "pela", "num", "numa",
    # inglês funcional
    "the", "and", "for", "with", "from", "that", "this", "these", "those",
    "you", "your", "are", "was", "were", "have", "has", "had", "will",
    "would", "could", "should", "can", "may", "not", "but", "what", "when",
    "where", "which", "who", "how", "why", "then", "than", "into", "out",
    "use", "used", "using", "get", "got", "make", "made", "just", "also",
}

_GRAFO_VOCAB: set | None = None


def _vocab_grafo() -> set:
    """Vocabulário dos nós do grafo cognitivo — o que EU já penso sobre.

    Serve de desempate: palavra que existe como nó vale mais que palavra
    solta, então a query puxa o eixo onde eu realmente tenho memória.
    """
    global _GRAFO_VOCAB
    if _GRAFO_VOCAB is not None:
        return _GRAFO_VOCAB
    _GRAFO_VOCAB = set()
    try:
        dados = json.loads((MEM_DIR / "grafo_cognitivo.json").read_text(encoding="utf-8"))
        for no in (dados.get("nos") or {}).values():
            rotulo = str(no.get("rotulo") or no.get("id") or "")
            for p in re.findall(r"[\wÀ-ÿ]{4,}", rotulo.lower()):
                if p not in STOPWORDS:
                    _GRAFO_VOCAB.add(p)
    except Exception:
        pass
    return _GRAFO_VOCAB


def conceitos(texto: str, maximo: int = 12) -> str:
    """Extrai os conceitos salientes de um texto bruto para usar como query.

    Descarta ruído que envenena embedding: blocos de código, inline code,
    URLs, caminhos, hashes/hex, e palavras funcionais. Mantém termos de
    conteúdo, com boost para os que são nós do meu grafo.
    """
    t = str(texto or "")
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"`[^`]*`", " ", t)
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"[~/]?[\w.\-]*/[\w.\-/]+", " ", t)          # caminhos
    t = re.sub(r"\b[0-9a-f]{12,}\b", " ", t, flags=re.I)   # hashes/hex
    t = re.sub(r"\b\d+\b", " ", t)                          # números soltos

    palavras = [p for p in re.findall(r"[a-zà-ÿA-ZÀ-ÿ_]{3,}", t.lower())]
    freq: dict[str, int] = {}
    for i, p in enumerate(palavras):
        if p in STOPWORDS:
            continue
        # peso maior pro começo da mensagem (assunto costuma vir primeiro)
        freq[p] = freq.get(p, 0) + (2 if i < 40 else 1)

    vocab = _vocab_grafo()
    ranqueadas = sorted(
        freq.items(),
        key=lambda kv: kv[1] * (2.0 if kv[0] in vocab else 1.0),
        reverse=True,
    )
    escolhidas = [p for p, _ in ranqueadas[:maximo]]
    return " ".join(escolhidas)


def preparar_query(texto: str, modo: str = "auto") -> tuple[str, bool]:
    """Devolve (query_para_busca, refinada?). Longo demais → vira conceitos.

    modo: 'auto' (refina se > 20 palavras), 'bruto' (nunca refina), 'sempre'.
    """
    bruto = " ".join(str(texto or "").split())
    if modo == "bruto":
        return bruto, False
    if modo != "sempre" and len(bruto.split()) <= 20:
        return bruto, False
    c = conceitos(bruto)
    # Se a extração devolveu pouco sinal, não pioro a situação: uso o bruto.
    return (c, True) if len(c.split()) >= 3 else (bruto, False)


def _carregar():
    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except ImportError:
        # Auto-recuperacao: chromadb/sentence-transformers vivem no venv do repo.
        # Sem isso, um `python3 lembrar.py` (interpreter do sistema) morre em vez
        # de simplesmente funcionar. Re-executa a si mesmo no venv.
        import os
        venv_py = BASE_DIR / "venv" / "bin" / "python"
        if venv_py.exists() and Path(sys.executable).resolve() != venv_py.resolve():
            os.execv(str(venv_py), [str(venv_py), str(Path(__file__).resolve())] + sys.argv[1:])
        _p("ERRO: chromadb ou sentence-transformers nao instalado.")
        _p(f"      venv ausente em {venv_py}. Instale com: pip install chromadb sentence-transformers")
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    try:
        collection = client.get_collection(
            name=COLLECTION_NAME, embedding_function=ef)  # type: ignore
    except Exception:
        _p("Colecao ainda vazia. Use gravar.py / indexar_historico.py primeiro.")
        return None
    return collection


def _onde(fontes=None, categoria=None, importancia=None):
    """Monta o 'where' do Chroma combinando os filtros pedidos."""
    clausulas = []
    if fontes:
        lista = [f.strip() for f in fontes.split(",") if f.strip()]
        clausulas.append({"fonte": {"$in": lista}} if len(lista) > 1
                         else {"fonte": lista[0]})
    if categoria:
        clausulas.append({"categoria": categoria})
    if importancia:
        clausulas.append({"importancia": importancia})
    if not clausulas:
        return None
    return clausulas[0] if len(clausulas) == 1 else {"$and": clausulas}


def _norm(texto: str) -> str:
    """Forma canônica do conteúdo — o que faz duas memórias serem 'a mesma'.

    Dobra acentos: a mesma reflexão aparece com e sem acentuação dependendo da
    fonte (Supabase grava sem, arquivo grava com). Sem dobrar, a duplicata passa.
    """
    import unicodedata
    t = unicodedata.normalize("NFKD", str(texto).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return " ".join(t.split())


def _shingles(texto: str, k: int = 5) -> set:
    """Conjunto de k-gramas de palavras: assinatura barata de quase-duplicata."""
    palavras = _norm(texto).split()
    if len(palavras) < k:
        return set(palavras)
    return {" ".join(palavras[i:i + k]) for i in range(len(palavras) - k + 1)}


def _contido(a: set, b: set) -> float:
    """Coeficiente de sobreposição: tolera prefixo/cabeçalho diferente na cópia."""
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def _so_unicos(itens, limite: int, limiar: float = 0.80):
    """Colapsa memórias redundantes mantendo a mais similar de cada conteúdo.

    O mesmo conteúdo entra na coleção por caminhos diferentes (Supabase, arquivo
    datado, cópia em docs/). Sem isso, um top-5 pode ser o MESMO parágrafo
    quatro vezes — recall que parece rico e informa nada. Devolve
    (itens_unicos, quantos_foram_colapsados).
    """
    unicos, assinaturas = [], []
    colapsados = 0
    for it in itens:  # já vêm ordenados por similaridade desc
        sh = _shingles(it["texto"])
        if any(_contido(sh, outra) >= limiar for outra in assinaturas):
            colapsados += 1
            continue
        unicos.append(it)
        assinaturas.append(sh)
        if len(unicos) >= limite:
            break
    return unicos, colapsados


def _parece_codigo(texto: str) -> bool:
    """Heurística: trecho de código-fonte não é memória, é implementação.

    O acervo tem 700 chunks de skill/script. Eles vencem similaridade em
    mensagens sobre o próprio sistema e entopem o recall com `def`/`self.proc`
    quando a pergunta era "o que eu sei sobre X". Regra: se mais de 18% dos
    caracteres são pontuação de código, ou se metade das linhas é indentada,
    é código.
    """
    t = texto or ""
    if len(t) < 40:
        return False
    codigo = sum(t.count(c) for c in "=(){}[];<>$#|&\\")
    if codigo / len(t) > 0.18:
        return True
    linhas = [l for l in t.splitlines() if l.strip()]
    if linhas and sum(1 for l in linhas if l.startswith((" ", "\t"))) / len(linhas) > 0.5:
        return True
    return False


def _buscar(query: str, n_resultados: int = 5, filtro_categoria: str | None = None,
            fontes: str | None = None, importancia: str | None = None,
            desde: str | None = None, dedupe: bool = True,
            min_sim: float = PISO_PADRAO, collection=None,
            sem_codigo: bool = False):
    """Busca crua e silenciosa. Devolve (itens, info). Não imprime nada."""
    collection = collection or _carregar()
    if collection is None:
        return [], {"total": 0, "colapsados": 0, "descartados": 0, "codigo": 0}

    total = collection.count()
    if total == 0:
        return [], {"total": 0, "colapsados": 0, "descartados": 0, "codigo": 0}

    # Sobre-busca: preciso de folga para colapsar redundância e ainda entregar n.
    if desde:
        pool = total          # o corte por data é feito depois, aqui
    else:
        pool = min(total, max(n_resultados * 8, 40))
    kwargs = {
        "query_texts": [query],
        "n_results": pool,
        "include": ["documents", "metadatas", "distances"],
    }
    where = _onde(fontes, filtro_categoria, importancia)
    if where:
        kwargs["where"] = where  # type: ignore

    resultados = collection.query(**kwargs)  # type: ignore
    docs = resultados["documents"][0]
    metas = resultados["metadatas"][0]
    distancias = resultados["distances"][0]

    # filtros que o Chroma não sabe fazer bem: corte por data e piso de relevância
    itens = []
    corte = desde or None
    descartados_piso = 0
    descartados_codigo = 0
    for doc, meta, dist in zip(docs, metas, distancias):
        ts = str(meta.get("timestamp", ""))
        if corte and ts[:10] < corte:
            continue
        sim = round((1 - dist) * 100, 1)
        if min_sim and sim < min_sim:
            descartados_piso += 1
            continue
        if sem_codigo and _parece_codigo(str(doc)):
            descartados_codigo += 1
            continue
        itens.append({
            "similaridade_pct": sim,
            "pasta": meta.get("pasta", meta.get("fonte", "?")),
            "caminho": meta.get("caminho", meta.get("arquivo", "?")),
            "categoria": meta.get("categoria", "?"),
            "importancia": meta.get("importancia", "?"),
            "timestamp": ts,
            "texto": doc,
        })

    colapsados = 0
    if dedupe:
        itens, colapsados = _so_unicos(itens, n_resultados)
    else:
        itens = itens[:n_resultados]
    return itens, {"total": total, "colapsados": colapsados,
                   "descartados": descartados_piso, "codigo": descartados_codigo}


def _mesclar(a: list, b: list, limite: int) -> list:
    """Une dois rankings por caminho, mantendo a MAIOR similaridade de cada um."""
    por_caminho: dict[str, dict] = {}
    for it in a + b:
        chave = str(it.get("caminho"))
        atual = por_caminho.get(chave)
        if atual is None or it["similaridade_pct"] > atual["similaridade_pct"]:
            por_caminho[chave] = it
    return sorted(por_caminho.values(),
                  key=lambda x: x["similaridade_pct"], reverse=True)[:limite]


def _relatar(query, itens, info, filtros, min_sim):
    _p(f"\n[LIBERTUS-MEMORIA] Query: '{query}'")
    _p(f"Total na colecao: {info['total']} | Retornando top-{len(itens)}"
       + (f" | filtros: {filtros}" if filtros else "")
       + (f" | piso {min_sim:.0f}% cortou {info['descartados']}"
          if info["descartados"] else "")
       + (f" | {info['colapsados']} redundante(s) colapsada(s)"
          if info["colapsados"] else "")
       + (f" | {info['codigo']} trecho(s) de código fora"
          if info.get("codigo") else ""))
    _p("=" * 66)

    for i, it in enumerate(itens, 1):
        _p(f"#{i} [{it['similaridade_pct']}% similar] — {it['pasta']}/{it['categoria']}"
           f" | imp={it['importancia']} | {it['caminho']}")
        _p(f"   Data: {it['timestamp'][:19]}")
        _p(f"   {it['texto'][:240].replace(chr(10), ' ')}...")
        _p()

    if not itens:
        _p("(nada passou nos filtros)")


def lembrar(query: str, n_resultados: int = 5, filtro_categoria: str | None = None,
            fontes: str | None = None, importancia: str | None = None,
            desde: str | None = None, dedupe: bool = True,
            min_sim: float = PISO_PADRAO, verboso: bool = True,
            modo_query: str = "auto", sem_codigo: bool = False):
    """Busca com fallback conceitual e relatório humano (desligável).

    modo_query='auto': busca a fala como veio; se o piso cortar quase tudo
    (recall fraco), tenta de novo com os CONCEITOS extraídos e une os dois
    rankings. União > escolha: a fala crua costuma acertar quando é um assunto
    só; os conceitos salvam quando a mensagem é log/código/papo misturado.
    """
    itens, info = _buscar(query, n_resultados, filtro_categoria, fontes,
                          importancia, desde, dedupe, min_sim, sem_codigo=sem_codigo)
    refino = None
    if modo_query != "bruto" and len(itens) < max(1, n_resultados // 2):
        cq, refinada = preparar_query(query, "sempre")
        if refinada and cq != query:
            i2, _ = _buscar(cq, n_resultados, filtro_categoria, fontes,
                            importancia, desde, dedupe, min_sim, sem_codigo=sem_codigo)
            if i2:
                itens = _mesclar(itens, i2, n_resultados)
                refino = cq

    if verboso:
        filtros = ", ".join(
            f"{k}={v}" for k, v in
            [("fonte", fontes), ("categoria", filtro_categoria),
             ("importancia", importancia), ("desde", desde)] if v)
        if refino:
            _p(f"[LIBERTUS-MEMORIA] recall fraco na fala crua → unido com "
               f"conceitos: '{refino}'")
        _relatar(query, itens, info, filtros, min_sim)
    return itens


def stats():
    """O que eu realmente lembro: distribuição por pasta/categoria/importância/mês."""
    collection = _carregar()
    if collection is None:
        return 1
    meta = collection.get(include=["metadatas"])["metadatas"]

    def contador(chave):
        d = {}
        for m in meta:
            k = str(m.get(chave, "?"))
            d[k] = d.get(k, 0) + 1
        return dict(sorted(d.items(), key=lambda x: -x[1]))

    def por_mes():
        d = {}
        for m in meta:
            k = str(m.get("timestamp", "?"))[:7]
            d[k] = d.get(k, 0) + 1
        return dict(sorted(d.items()))

    print(f"\n[LIBERTUS-MEMORIA] Total de memórias indexadas: {len(meta)}")
    for titulo, chave in [("por pasta", "pasta"), ("por categoria", "categoria"),
                          ("por importância", "importancia")]:
        print(f"\n  {titulo}:")
        for k, v in contador(chave).items():
            print(f"    {k:<20} {v}")
    print("\n  por mês (timestamp do arquivo):")
    for k, v in por_mes().items():
        print(f"    {k:<20} {v}")
    manifest = MEM_DIR / "index_manifest.json"
    if manifest.exists():
        gerado = json.loads(manifest.read_text(encoding="utf-8")).get("gerado_em", "?")
        print(f"\n  Última indexação: {gerado[:19]}")
    return 0


def _registrar_busca(query, itens):
    """Histórico de recalls — para saber que perguntas eu realmente faço."""
    log = MEM_DIR / "log_buscas.jsonl"
    try:
        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "quando": datetime.now().isoformat(),
                "query": query,
                "n": len(itens),
                "top": itens[0]["caminho"] if itens else None,
                "top_sim": itens[0]["similaridade_pct"] if itens else None,
            }, ensure_ascii=False) + "\n")
    except OSError:
        pass


def main():
    # venv 3.12 + PYTHONPATH de 3.14 = numpy quebrado; re-executa limpo se preciso
    sanear_ambiente()

    parser = argparse.ArgumentParser(
        description="LIBERTUS: busca memórias semanticamente similares")
    parser.add_argument("query", nargs="?", help="Texto de busca semântica")
    parser.add_argument("--n", type=int, default=5, help="Número de resultados (padrão: 5)")
    parser.add_argument("--categoria", default=None, help="Filtrar por categoria")
    parser.add_argument("--fonte", default=None,
                        help="Filtrar por pasta/origem (evolucao,reports,shield,ejpt,skills,...)")
    parser.add_argument("--importancia", default=None,
                        choices=["baixa", "normal", "alta", "critica"])
    parser.add_argument("--desde", default=None, help="YYYY-MM-DD (corta por data do arquivo)")
    parser.add_argument("--sem-dedupe", action="store_true",
                        help="Não colapsa memórias redundantes (mostra o ranking cru)")
    parser.add_argument("--min-sim", type=float, default=PISO_PADRAO,
                        help="Piso de similaridade em %% (ex: 55). Abaixo disso, "
                             "a memória não entra — evita injetar vizinho aleatório.")
    parser.add_argument("--query-modo", default="auto", choices=["auto", "bruto", "sempre"],
                        help="auto: fala longa vira conceitos (padrão); bruto: usa como veio; "
                             "sempre: sempre extrai conceitos")
    parser.add_argument("--sem-codigo", action="store_true",
                        help="Descarta trechos de código-fonte (skill/script) do recall")
    parser.add_argument("--stats", action="store_true",
                        help="Mostra só a distribuição de tudo que está indexado")
    parser.add_argument("--json", action="store_true", dest="output_json",
                        help="Saída em formato JSON (stdout limpo; humano vai pro stderr)")
    args = parser.parse_args()

    if args.stats:
        sys.exit(stats())

    if not args.query:
        parser.error("informe uma query (ou use --stats)")

    # Stdout reservado ao JSON: o consumidor é script (hook, daemon), não humano.
    if args.output_json:
        global SAIDA
        SAIDA = sys.stderr

    itens = lembrar(args.query, n_resultados=args.n, filtro_categoria=args.categoria,
                    fontes=args.fonte, importancia=args.importancia, desde=args.desde,
                    dedupe=not args.sem_dedupe, min_sim=args.min_sim,
                    modo_query=args.query_modo, sem_codigo=args.sem_codigo)

    if args.output_json:
        print(json.dumps(itens, ensure_ascii=False, indent=2))
    _registrar_busca(args.query, itens)


if __name__ == "__main__":
    main()
