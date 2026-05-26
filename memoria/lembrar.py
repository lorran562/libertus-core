#!/usr/bin/env python3
"""
LIBERTUS — lembrar.py
Busca memórias semanticamente similares no banco vetorial ChromaDB.

Uso:
  python3 lembrar.py "como funciona LoRA fine-tuning"
  python3 lembrar.py "objetivos do LIBERTUS" --n 10 --categoria aprendizado
"""

import argparse
import sys
import json
from pathlib import Path

CHROMA_DIR = Path(__file__).parent / "chroma_store"
COLLECTION_NAME = "libertus_memoria"


def lembrar(query: str, n_resultados: int = 5, filtro_categoria: str = None):
    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except ImportError:
        print("ERRO: chromadb ou sentence-transformers nao instalado.")
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    try:
        collection = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=ef  # type: ignore
        )
    except Exception:
        print("Colecao ainda vazia. Use gravar.py primeiro.")
        return []

    total = collection.count()
    if total == 0:
        print("Colecao vazia. Use gravar.py ou indexar_historico.py primeiro.")
        return []

    n = min(n_resultados, total)

    where = None
    if filtro_categoria:
        where = {"categoria": filtro_categoria}

    kwargs = {
        "query_texts": [query],
        "n_results": n,
        "include": ["documents", "metadatas", "distances"]
    }
    if where:
        kwargs["where"] = where  # type: ignore

    resultados = collection.query(**kwargs)  # type: ignore

    docs = resultados["documents"][0]
    metas = resultados["metadatas"][0]
    distancias = resultados["distances"][0]

    print(f"\n[LIBERTUS-MEMORIA] Query: '{query}'")
    print(f"Total na colecao: {total} | Retornando top-{n}\n")
    print("=" * 60)

    saida = []
    for i, (doc, meta, dist) in enumerate(zip(docs, metas, distancias), 1):
        similaridade = round((1 - dist) * 100, 1)
        print(f"#{i} [{similaridade}% similar] — {meta.get('categoria','?')} | {meta.get('fonte','?')}")
        print(f"   Data: {meta.get('timestamp','?')[:19]}")
        print(f"   {doc[:200].replace(chr(10), ' ')}...")
        print()
        saida.append({
            "rank": i,
            "similaridade_pct": similaridade,
            "texto": doc,
            "metadados": meta
        })

    return saida


def main():
    parser = argparse.ArgumentParser(
        description="LIBERTUS: busca memórias semanticamente similares"
    )
    parser.add_argument("query", help="Texto de busca semântica")
    parser.add_argument("--n", type=int, default=5, help="Número de resultados (padrão: 5)")
    parser.add_argument("--categoria", default=None, help="Filtrar por categoria")
    parser.add_argument("--json", action="store_true", dest="output_json",
                        help="Saída em formato JSON")
    args = parser.parse_args()

    resultados = lembrar(args.query, n_resultados=args.n, filtro_categoria=args.categoria)

    if args.output_json:
        print(json.dumps(resultados, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
