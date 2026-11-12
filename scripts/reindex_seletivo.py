#!/usr/bin/env python3
"""Reindexa cirurgicamente arquivos especificos com o chunker v2.

Nao apaga a colecao. Para cada arquivo: remove os chunks antigos por
metadata `arquivo`, re-chunka com indexar_historico.chunkar (v2) e reinsere
com os mesmos metadados que o indexador usa.

Uso: venv/bin/python scripts/reindex_seletivo.py <caminho1> [caminho2 ...]
"""
import sys
import hashlib
import importlib.util
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "memoria"))

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

spec = importlib.util.spec_from_file_location("ih", BASE / "memoria" / "indexar_historico.py")
ih = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ih)

CHROMA_DIR = BASE / "memoria" / "chroma_store"
COLLECTION = "libertus_memoria"


def main(alvos):
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    col = client.get_or_create_collection(name=COLLECTION, embedding_function=ef)

    total_antes = col.count()
    for cam in alvos:
        p = Path(cam) if Path(cam).is_absolute() else BASE / cam
        nome = p.name
        conteudo = p.read_text(encoding="utf-8", errors="replace").strip()

        antigos = col.get(where={"arquivo": nome})["ids"]
        if antigos:
            col.delete(ids=antigos)

        chunks = ih.chunkar(conteudo)
        ids = [f"rel__{p.stem}_chunk{i:03d}_{ih.hash_doc(c)}" for i, c in enumerate(chunks)]
        pasta = p.parent.name
        metad = [{
            "arquivo": nome,
            "caminho": str(p.relative_to(BASE)),
            "pasta": pasta,
            "fonte": "reports" if pasta == "reports" else "historico_evolucao",
            "chunk_idx": str(i),
            "total_chunks": str(len(chunks)),
            "categoria": ih.inferir_categoria(nome),
            "importancia": "alta",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "titulo": nome,
        } for i in range(len(chunks))]
        col.add(ids=ids, documents=chunks, metadatas=metad)
        print(f"{nome}: {len(antigos)} chunks v1 removidos -> {len(chunks)} chunks v2")

    print(f"total na colecao: {total_antes} -> {col.count()}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("uso: reindex_seletivo.py <arquivo> [...]")
    main(sys.argv[1:])
