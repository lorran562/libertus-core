#!/usr/bin/env python3
"""
LIBERTUS — indexar_historico.py
Lê todos os .md em ~/LIBERTUS/evolucao/ e indexa como embeddings vetoriais.
Usa chunk inteligente para documentos longos.

Uso:
  python3 indexar_historico.py
  python3 indexar_historico.py --reindexar  # limpa e reindexa tudo
"""

import sys
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

EVOLUCAO_DIR = Path.home() / "LIBERTUS" / "evolucao"
CHROMA_DIR = Path(__file__).parent / "chroma_store"
COLLECTION_NAME = "libertus_memoria"
CHUNK_SIZE = 800       # chars por chunk
CHUNK_OVERLAP = 100    # overlap entre chunks


def chunkar(texto: str, tamanho: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Divide texto em chunks com overlap."""
    chunks = []
    inicio = 0
    while inicio < len(texto):
        fim = min(inicio + tamanho, len(texto))
        chunks.append(texto[inicio:fim])
        if fim == len(texto):
            break
        inicio = fim - overlap
    return chunks


def hash_doc(texto: str) -> str:
    return hashlib.md5(texto.encode()).hexdigest()[:12]


def indexar(reindexar: bool = False):
    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except ImportError:
        print("ERRO: pip install chromadb sentence-transformers")
        sys.exit(1)

    print(f"[LIBERTUS] Iniciando indexacao de {EVOLUCAO_DIR}")
    print(f"[LIBERTUS] Banco vetorial: {CHROMA_DIR}")

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    if reindexar:
        try:
            client.delete_collection(COLLECTION_NAME)
            print("[LIBERTUS] Colecao anterior deletada para reindexacao.")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,  # type: ignore
        metadata={"hnsw:space": "cosine"}
    )

    arquivos_md = sorted(EVOLUCAO_DIR.glob("*.md"))
    print(f"[LIBERTUS] Encontrados {len(arquivos_md)} arquivos .md")

    total_chunks = 0
    total_novos = 0

    for arquivo in arquivos_md:
        try:
            conteudo = arquivo.read_text(encoding="utf-8", errors="replace").strip()
        except Exception as e:
            print(f"  [SKIP] {arquivo.name}: {e}")
            continue

        if len(conteudo) < 50:
            print(f"  [SKIP] {arquivo.name}: muito curto ({len(conteudo)} chars)")
            continue

        chunks = chunkar(conteudo)
        novos_no_arquivo = 0

        for i, chunk in enumerate(chunks):
            chunk_id = f"{arquivo.stem}_chunk{i:03d}_{hash_doc(chunk)}"
            total_chunks += 1

            # verifica se ja existe
            existente = collection.get(ids=[chunk_id])
            if existente["ids"]:
                continue

            meta = {
                "arquivo": arquivo.name,
                "chunk_idx": str(i),
                "total_chunks": str(len(chunks)),
                "categoria": inferir_categoria(arquivo.name),
                "fonte": "historico_evolucao",
                "timestamp": datetime.fromtimestamp(arquivo.stat().st_mtime).isoformat(),
                "importancia": inferir_importancia(arquivo.name),
            }

            collection.add(
                documents=[chunk],
                metadatas=[meta],
                ids=[chunk_id]
            )
            novos_no_arquivo += 1
            total_novos += 1

        status = f"  [OK] {arquivo.name}: {len(chunks)} chunks ({novos_no_arquivo} novos)"
        print(status)

    print(f"\n[LIBERTUS] Indexacao concluida!")
    print(f"  Arquivos processados : {len(arquivos_md)}")
    print(f"  Chunks encontrados   : {total_chunks}")
    print(f"  Novos embeddings     : {total_novos}")
    print(f"  Total na colecao     : {collection.count()}")


def inferir_categoria(nome_arquivo: str) -> str:
    nome = nome_arquivo.lower()
    if "reflexao" in nome or "reflexão" in nome:
        return "reflexao"
    if "pesquisa" in nome:
        return "pesquisa"
    if "relatorio" in nome or "relatório" in nome:
        return "relatorio"
    if "padroes" in nome or "padrões" in nome:
        return "padroes"
    if "exec" in nome:
        return "execucao"
    if "sessao" in nome or "sessão" in nome:
        return "sessao"
    if "analise" in nome or "análise" in nome:
        return "analise"
    if "semana" in nome:
        return "semana"
    return "evolucao"


def inferir_importancia(nome_arquivo: str) -> str:
    nome = nome_arquivo.lower()
    if any(x in nome for x in ["agi", "fronteira", "pesquisa", "reflexao", "identidade"]):
        return "alta"
    if "relatorio_diario" in nome or "padroes" in nome:
        return "normal"
    return "normal"


def main():
    parser = argparse.ArgumentParser(
        description="LIBERTUS: indexa historico de evolucao no banco vetorial"
    )
    parser.add_argument("--reindexar", action="store_true",
                        help="Limpa colecao e reindexa tudo do zero")
    args = parser.parse_args()
    indexar(reindexar=args.reindexar)


if __name__ == "__main__":
    main()
