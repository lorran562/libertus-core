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


def _carregar():
    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except ImportError:
        print("ERRO: chromadb ou sentence-transformers nao instalado.")
        print("      rode com: ~/LIBERTUS/venv/bin/python ...")
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    try:
        collection = client.get_collection(
            name=COLLECTION_NAME, embedding_function=ef)  # type: ignore
    except Exception:
        print("Colecao ainda vazia. Use gravar.py / indexar_historico.py primeiro.")
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


def lembrar(query: str, n_resultados: int = 5, filtro_categoria: str | None = None,
            fontes: str | None = None, importancia: str | None = None,
            desde: str | None = None, dedupe: bool = True):
    collection = _carregar()
    if collection is None:
        return []

    total = collection.count()
    if total == 0:
        print("Colecao vazia. Use gravar.py ou indexar_historico.py primeiro.")
        return []

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

    # filtros que o Chroma não sabe fazer bem: corte por data
    itens = []
    corte = desde or None
    for doc, meta, dist in zip(docs, metas, distancias):
        ts = str(meta.get("timestamp", ""))
        if corte and ts[:10] < corte:
            continue
        itens.append({
            "similaridade_pct": round((1 - dist) * 100, 1),
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

    print(f"\n[LIBERTUS-MEMORIA] Query: '{query}'")
    filtros = ", ".join(
        f"{k}={v}" for k, v in
        [("fonte", fontes), ("categoria", filtro_categoria),
         ("importancia", importancia), ("desde", desde)] if v)
    print(f"Total na colecao: {total} | Retornando top-{len(itens)}"
          + (f" | filtros: {filtros}" if filtros else "")
          + (f" | {colapsados} redundante(s) colapsada(s)" if colapsados else ""))
    print("=" * 66)

    for i, it in enumerate(itens, 1):
        print(f"#{i} [{it['similaridade_pct']}% similar] — {it['pasta']}/{it['categoria']}"
              f" | imp={it['importancia']} | {it['caminho']}")
        print(f"   Data: {it['timestamp'][:19]}")
        print(f"   {it['texto'][:240].replace(chr(10), ' ')}...")
        print()

    if not itens:
        print("(nada passou nos filtros)")
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
    parser.add_argument("--stats", action="store_true",
                        help="Mostra só a distribuição de tudo que está indexado")
    parser.add_argument("--json", action="store_true", dest="output_json",
                        help="Saída em formato JSON")
    args = parser.parse_args()

    if args.stats:
        sys.exit(stats())

    if not args.query:
        parser.error("informe uma query (ou use --stats)")

    itens = lembrar(args.query, n_resultados=args.n, filtro_categoria=args.categoria,
                    fontes=args.fonte, importancia=args.importancia, desde=args.desde,
                    dedupe=not args.sem_dedupe)

    if args.output_json:
        print(json.dumps(itens, ensure_ascii=False, indent=2))
    _registrar_busca(args.query, itens)


if __name__ == "__main__":
    main()
