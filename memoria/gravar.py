#!/usr/bin/env python3
"""
LIBERTUS — gravar.py
Grava texto + metadados como embedding no banco vetorial ChromaDB persistente.

Uso:
  python3 gravar.py "Texto a gravar" --categoria "aprendizado" --fonte "sessao_2026-05-25"
  echo "texto longo" | python3 gravar.py - --categoria "reflexao"
"""

import argparse
import sys
import uuid
import json
from datetime import datetime
from pathlib import Path

CHROMA_DIR = Path(__file__).parent / "chroma_store"
COLLECTION_NAME = "libertus_memoria"

def gravar(texto: str, metadados: dict = None):
    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except ImportError:
        print("ERRO: chromadb ou sentence-transformers nao instalado.")
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )

    doc_id = str(uuid.uuid4())
    meta = {
        "timestamp": datetime.now().isoformat(),
        "categoria": "geral",
        "fonte": "manual",
    }
    if metadados:
        meta.update(metadados)

    # ChromaDB nao aceita None em metadados
    meta = {k: str(v) for k, v in meta.items() if v is not None}

    collection.add(
        documents=[texto],
        metadatas=[meta],
        ids=[doc_id]
    )

    print(f"[LIBERTUS-MEMORIA] Gravado com ID: {doc_id}")
    print(f"  Categoria : {meta.get('categoria')}")
    print(f"  Fonte     : {meta.get('fonte')}")
    print(f"  Timestamp : {meta.get('timestamp')}")
    print(f"  Preview   : {texto[:100]}...")
    print(f"  Total na colecao: {collection.count()}")
    return doc_id


def main():
    parser = argparse.ArgumentParser(
        description="LIBERTUS: grava texto como embedding vetorial"
    )
    parser.add_argument("texto", help="Texto a gravar (use '-' para stdin)")
    parser.add_argument("--categoria", default="geral", help="Categoria da memória")
    parser.add_argument("--fonte", default="manual", help="Fonte/origem da memória")
    parser.add_argument("--tags", default="", help="Tags separadas por vírgula")
    parser.add_argument("--importancia", default="normal",
                        choices=["baixa", "normal", "alta", "critica"],
                        help="Nível de importância")
    args = parser.parse_args()

    if args.texto == "-":
        texto = sys.stdin.read().strip()
    else:
        texto = args.texto

    if not texto:
        print("ERRO: texto vazio.")
        sys.exit(1)

    meta = {
        "categoria": args.categoria,
        "fonte": args.fonte,
        "tags": args.tags,
        "importancia": args.importancia,
    }

    gravar(texto, meta)


if __name__ == "__main__":
    main()
