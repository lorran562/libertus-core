#!/usr/bin/env python3
"""
LIBERTUS — indexar_historico.py  (v2, multi-fonte)
===================================================
Lê TODAS as fontes de conhecimento registradas em fontes.py e indexa como
embeddings vetoriais no ChromaDB persistente.

Por que v2: a v1 (mai/2026) só conhecia ~/LIBERTUS/evolucao/ e parou de rodar
em 15/07/2026 — a memória vetorial ficou cega para 3 meses de trabalho
(reports/, shield/, ejpt/, arquitetura/, skills/). Agora a fonte da verdade
é fontes.py e a indexação é incremental por hash de chunk.

Uso:
  python3 indexar_historico.py                      # tudo que é novo (all)
  python3 indexar_historico.py --fontes evolucao
  python3 indexar_historico.py --fontes reports,shield --desde 2026-07-15
  python3 indexar_historico.py --reindexar          # limpa e reindexa tudo
  python3 indexar_historico.py --dry-run            # só mostra o que faria
"""

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path

MEM_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(MEM_DIR))

from fontes import FONTES, listar_arquivos, resolver_fontes  # noqa: E402

CHROMA_DIR = MEM_DIR / "chroma_store"
COLLECTION_NAME = "libertus_memoria"
MANIFEST = MEM_DIR / "index_manifest.json"
ULTIMO_INDEX = MEM_DIR / "ultimo_index.json"
CHUNK_SIZE = 800       # chars por chunk
CHUNK_OVERLAP = 100    # overlap entre chunks
MIN_CHARS = 50         # ignora arquivos menores que isso
LOTE = 64              # documentos por add() — um por um é lento demais


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
    if nome == "skill.md":
        return "skill"
    return "evolucao"


def inferir_importancia(nome_arquivo: str, padrao: str = "normal") -> str:
    nome = nome_arquivo.lower()
    if any(x in nome for x in ["agi", "fronteira", "pesquisa", "reflexao", "identidade"]):
        return "alta"
    if "relatorio_diario" in nome:
        return "baixa"
    return padrao


def _executar(fontes_txt: str, desde: str, reindexar: bool, dry_run: bool):
    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except ImportError:
        print("ERRO: pip install chromadb sentence-transformers  (use venv/bin/python)")
        sys.exit(1)

    t0 = time.time()
    nomes = resolver_fontes(fontes_txt)
    arquivos = listar_arquivos(fontes_txt, desde=desde or None)

    print(f"[LIBERTUS] Indexacao v2 — fontes: {', '.join(nomes)}"
          + (f" (desde {desde})" if desde else ""))
    print(f"[LIBERTUS] Banco vetorial: {CHROMA_DIR}")
    print(f"[LIBERTUS] Arquivos candidatos: {len(arquivos)}")

    if dry_run:
        por_fonte: dict[str, list[str]] = {}
        for it in arquivos:
            por_fonte.setdefault(it["fonte"], []).append(it["path"].name)
        for f, nomes_arq in sorted(por_fonte.items()):
            print(f"  [{f}] {len(nomes_arq)} arquivos")
            for n in nomes_arq[:5]:
                print(f"      - {n}")
            if len(nomes_arq) > 5:
                print(f"      ... +{len(nomes_arq)-5}")
        print("\n[LIBERTUS] --dry-run: nada foi gravado.")
        return

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if reindexar:
        try:
            client.delete_collection(COLLECTION_NAME)
            print("[LIBERTUS] Colecao anterior deletada para reindexacao.")
        except Exception:
            pass

    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,  # type: ignore
        metadata={"hnsw:space": "cosine"},
    )

    # manifest: relpath -> {mtime, size} por fonte (para auto_indexar.py)
    manifest = {}
    if MANIFEST.exists():
        try:
            manifest = json.loads(MANIFEST.read_text(encoding="utf-8")).get("fontes", {})
        except Exception:
            manifest = {}

    pendentes_id: list[str] = []
    pendentes_doc: list[str] = []
    pendentes_meta: list[dict] = []

    total_chunks = total_novos = total_skip = 0
    resumo_fontes: dict[str, dict] = {}

    def flush():
        if not pendentes_id:
            return
        collection.add(
            documents=list(pendentes_doc),
            metadatas=list(pendentes_meta),
            ids=list(pendentes_id),
        )
        pendentes_id.clear()
        pendentes_doc.clear()
        pendentes_meta.clear()

    for idx, item in enumerate(arquivos, 1):
        arq: Path = item["path"]
        fonte: str = item["fonte"]
        cfg = FONTES[fonte]
        rel = str(arq.relative_to(cfg["path"])) if arq.is_relative_to(cfg["path"]) else arq.name

        try:
            conteudo = arq.read_text(encoding="utf-8", errors="replace").strip()
        except OSError as e:
            print(f"  [SKIP] {rel}: {e}")
            continue

        manifest.setdefault(fonte, {})[rel] = {
            "mtime": round(item["mtime"], 3),
            "size": item["tamanho"],
            "hash": hash_doc(conteudo),
        }

        if len(conteudo) < MIN_CHARS:
            total_skip += 1
            continue

        chunks = chunkar(conteudo)
        total_chunks += len(chunks)

        # compatibilidade: ids da fonte 'evolucao' seguem o formato da v1,
        # para não duplicar os chunk já indexados. Nas outras fontes o stem
        # colide (ex: 15 arquivos SKILL.md) — então entra o hash do caminho.
        prefixo = "" if fonte == "evolucao" else f"{fonte}__{hash_doc(rel)}__"

        ids_lote = [
            f"{prefixo}{arq.stem}_chunk{i:03d}_{hash_doc(c)}"
            for i, c in enumerate(chunks)
        ]
        existentes = set(collection.get(ids=ids_lote)["ids"])  # type: ignore

        cat_padrao = cfg.get("categoria_padrao") or "evolucao"

        for i, (chunk, cid) in enumerate(zip(chunks, ids_lote)):
            if cid in existentes:
                continue
            cat = inferir_categoria(arq.name)
            if cat == "evolucao" and cat_padrao != "evolucao":
                cat = cat_padrao
            pendentes_id.append(cid)
            pendentes_doc.append(chunk)
            pendentes_meta.append({
                "arquivo": arq.name,
                "caminho": rel,
                "pasta": fonte,
                "fonte": "historico_evolucao" if fonte == "evolucao" else fonte,
                "chunk_idx": str(i),
                "total_chunks": str(len(chunks)),
                "categoria": cat,
                "importancia": inferir_importancia(arq.name, cfg["importancia"]),
                "timestamp": item["timestamp"],
            })
            total_novos += 1

        r = resumo_fontes.setdefault(fonte, {"arquivos": 0, "chunks_novos": 0})
        r["arquivos"] += 1
        r["chunks_novos"] += len(ids_lote) - len(existentes)

        if len(pendentes_id) >= LOTE:
            flush()

        if idx % 50 == 0 or idx == len(arquivos):
            print(f"  ... {idx}/{len(arquivos)} arquivos | {total_novos} embeddings novos")

    flush()

    MANIFEST.write_text(json.dumps({
        "gerado_em": datetime.now().isoformat(),
        "total_docs": collection.count(),
        "fontes": manifest,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    dur = round(time.time() - t0, 1)
    relatorio = {
        "gerado_em": datetime.now().isoformat(),
        "fontes": nomes,
        "desde": desde,
        "arquivos_processados": len(arquivos),
        "arquivos_pulados_curtos": total_skip,
        "chunks_encontrados": total_chunks,
        "embeddings_novos": total_novos,
        "total_na_colecao": collection.count(),
        "duracao_s": dur,
        "por_fonte": resumo_fontes,
    }
    ULTIMO_INDEX.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n[LIBERTUS] Indexacao concluida!")
    for f, r in sorted(resumo_fontes.items()):
        print(f"  {f:<14} {r['arquivos']:>4} arquivos | {r['chunks_novos']:>5} embeddings novos")
    print(f"  {'TOTAL':<14} {len(arquivos):>4} arquivos | {total_novos:>5} embeddings novos")
    print(f"  Total na colecao : {collection.count()}")
    print(f"  Duracao          : {dur}s")
    print(f"  Manifest         : {MANIFEST}")
    return relatorio


def main():
    import sys as _s
    from pathlib import Path as _P
    _s.path.insert(0, str(_P(__file__).resolve().parent.parent))
    from core.ambiente import sanear_ambiente
    sanear_ambiente()

    parser = argparse.ArgumentParser(
        description="LIBERTUS: indexa fontes de conhecimento no banco vetorial (v2 multi-fonte)")
    parser.add_argument("--fontes", default="all",
                        help="all | lista separada por virgula (evolucao,reports,shield,...)")
    parser.add_argument("--desde", default="", help="YYYY-MM-DD (filtra por mtime)")
    parser.add_argument("--reindexar", action="store_true",
                        help="Limpa colecao e reindexa tudo do zero")
    parser.add_argument("--dry-run", action="store_true", help="Mostra o que seria indexado")
    args = parser.parse_args()

    _executar(args.fontes, args.desde, args.reindexar, args.dry_run)


if __name__ == "__main__":
    main()
