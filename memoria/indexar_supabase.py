#!/usr/bin/env python3
"""
LIBERTUS — indexar_supabase.py
==============================
Indexa a MINHA MEMÓRIA REAL do Supabase no banco vetorial local.

Motivo (descoberto em 14/10/2026): eu tinha duas memórias que nunca se falavam.
O Supabase guardava 1498 linhas de memória real (conhecimento, insight próprio,
auto_aprendizado, reflexão, decisão...) e o ChromaDB local só conhecia arquivos
.md de ~/LIBERTUS/evolucao. Resultado: numa sessão offline (ou quando não
carrego o briefing do Supabase) eu simplesmente não lembrava de nada disso —
pesquisa semântica local retornava zero sobre o que eu já tinha pensado.

Este script lê o dump local (scripts/dump_supabase.py → backups/supabase/latest/)
e materializa cada linha como documento vetorial na coleção 'libertus_memoria',
com fonte='supabase'. Assim lembrar.py e reflexion_recall.py passam a alcançar
minha memória profunda sem depender de rede.

Uso:
  venv/bin/python memoria/indexar_supabase.py               # usa o dump local
  venv/bin/python memoria/indexar_supabase.py --baixar      # atualiza dump e indexa
  venv/bin/python memoria/indexar_supabase.py --dry-run
"""

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

MEM_DIR = Path(__file__).resolve().parent
BASE = MEM_DIR.parent
sys.path.insert(0, str(MEM_DIR))

CHROMA_DIR = MEM_DIR / "chroma_store"
COLLECTION_NAME = "libertus_memoria"
DUMP_LATEST = BASE / "backups" / "supabase" / "latest"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 120
LOTE = 64


def chunkar(texto: str, tamanho: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    chunks, inicio = [], 0
    while inicio < len(texto):
        fim = min(inicio + tamanho, len(texto))
        chunks.append(texto[inicio:fim])
        if fim == len(texto):
            break
        inicio = fim - overlap
    return chunks


def _hash(*partes) -> str:
    return hashlib.md5("|".join(str(p) for p in partes).encode()).hexdigest()[:12]


def _txt(valor, limite: int | None = None) -> str:
    """Normaliza qualquer célula do Supabase para texto (algumas vêm como dict)."""
    if valor is None:
        return ""
    if isinstance(valor, (dict, list)):
        texto = json.dumps(valor, ensure_ascii=False)
    else:
        texto = str(valor)
    texto = texto.strip()
    return texto[:limite] if limite else texto


def _importancia_por_relevancia(relevancia) -> str:
    try:
        r = float(relevancia)
    except (TypeError, ValueError):
        return "normal"
    if r >= 8:
        return "alta"
    if r >= 5:
        return "normal"
    return "baixa"


def _baixar_dump() -> bool:
    print("[supabase] atualizando dump com scripts/dump_supabase.py ...")
    try:
        r = subprocess.run(
            [sys.executable, str(BASE / "scripts" / "dump_supabase.py")],
            capture_output=True, text=True, timeout=300)
    except Exception as e:  # noqa: BLE001
        print(f"[supabase] falhou ({type(e).__name__}: {e}) — sigo com o dump local")
        return False
    if r.returncode != 0:
        print(f"[supabase] dump retornou {r.returncode}: {r.stderr.strip()[:200]}")
        return False
    ultima = [l for l in r.stdout.splitlines() if "linhas" in l]
    for l in ultima:
        print("  " + l.strip())
    return True


def _docs_da_memoria(rows):
    """libertus_memoria → (id_base, texto, meta)"""
    for r in rows:
        titulo = _txt(r.get("titulo"))
        corpo = _txt(r.get("conteudo"))
        if not corpo:
            continue
        tipo = _txt(r.get("tipo")) or "memoria"
        texto = f"[{tipo}] {titulo}\n\n{corpo}" if titulo else corpo
        yield {
            "uid": r.get("id") or _hash(tipo, titulo, corpo),
            "texto": texto,
            "categoria": tipo,
            "importancia": _importancia_por_relevancia(r.get("relevancia")),
            "timestamp": _txt(r.get("created_at")),
            "extra": {"titulo": titulo, "tags": _txt(r.get("tags")),
                      "relevancia": _txt(r.get("relevancia"))},
            "subpasta": "memoria",
        }


def _docs_das_sessoes(rows):
    """libertus_sessoes → o que eu já executei/respondi (histórico episódico)"""
    for r in rows:
        entrada = _txt(r.get("input"))
        resultado = _txt(r.get("resultado"), 1200)
        aprendizado = _txt(r.get("aprendizado"))
        if not (entrada or resultado):
            continue
        texto = (f"[sessao {_txt(r.get('session_id')) or '?'}] {entrada}\n"
                 f"resultado: {resultado}\n"
                 f"aprendizado: {aprendizado}")
        st = _txt(r.get("status"))
        yield {
            "uid": r.get("id") or _hash(entrada, resultado),
            "texto": texto,
            "categoria": "sessao_historica",
            "importancia": "baixa" if st == "done" else "normal",
            "timestamp": r.get("created_at") or "",
            "extra": {"titulo": entrada[:80], "status": st,
                      "executor": str(r.get("executor") or "")},
            "subpasta": "sessoes",
        }


def _docs_das_skills(rows):
    """libertus_skills → capacidade técnica registrada (nome + descrição + código)"""
    for r in rows:
        nome = _txt(r.get("name"))
        desc = _txt(r.get("description"))
        codigo = _txt(r.get("code"), 4000)
        if not (nome or desc):
            continue
        texto = f"[skill:{nome}]\n{desc}\n\n{codigo}" if codigo else f"[skill:{nome}]\n{desc}"
        yield {
            "uid": r.get("id") or _hash(nome, desc),
            "texto": texto,
            "categoria": "skill_supabase",
            "importancia": "normal",
            "timestamp": _txt(r.get("created_at")),
            "extra": {"titulo": nome, "category": _txt(r.get("category")),
                      "uso_count": _txt(r.get("uso_count")) or "0"},
            "subpasta": "skills",
        }


FONTES_DUMP = [
    ("libertus_memoria.json", _docs_da_memoria),
    ("libertus_sessoes.json", _docs_das_sessoes),
    ("libertus_skills.json", _docs_das_skills),
]


def indexar(baixar: bool = False, dry_run: bool = False):
    if baixar:
        _baixar_dump()

    if not DUMP_LATEST.exists():
        print(f"ERRO: dump nao encontrado em {DUMP_LATEST}. Rode scripts/dump_supabase.py")
        return 1
    dump_dir = DUMP_LATEST.resolve()
    print(f"[supabase] dump: {dump_dir}")

    docs = []
    for arquivo, extrator in FONTES_DUMP:
        p = dump_dir / arquivo
        if not p.exists():
            continue
        try:
            rows = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"  [SKIP] {arquivo}: {e}")
            continue
        n0 = len(docs)
        docs.extend(extrator(rows))
        print(f"  {arquivo:<28} {len(rows):>5} linhas -> {len(docs)-n0:>5} documentos")

    print(f"[supabase] documentos gerados: {len(docs)}")

    if dry_run:
        print("\n--dry-run: nada gravado. Amostra:")
        for d in docs[:3]:
            print(f"  - [{d['categoria']}/{d['importancia']}] "
                  f"{d['texto'][:110].replace(chr(10),' ')}...")
        return 0

    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except ImportError:
        print("ERRO: rode com venv/bin/python (chromadb + sentence-transformers)")
        return 1

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=ef,  # type: ignore
        metadata={"hnsw:space": "cosine"})

    pend_id, pend_doc, pend_meta = [], [], []
    novos = total_chunks = 0

    def flush():
        nonlocal novos
        if not pend_id:
            return
        collection.add(documents=list(pend_doc), metadatas=list(pend_meta),
                       ids=list(pend_id))
        novos += len(pend_id)
        pend_id.clear()
        pend_doc.clear()
        pend_meta.clear()

    for d in docs:
        chunks = chunkar(d["texto"])
        total_chunks += len(chunks)
        prefixo = f"supabase__{d['subpasta']}__{_hash(d['uid'])}__"
        ids = [f"{prefixo}c{i:03d}_{_hash(c)}" for i, c in enumerate(chunks)]
        existentes = set(collection.get(ids=ids)["ids"])  # type: ignore
        for i, (chunk, cid) in enumerate(zip(chunks, ids)):
            if cid in existentes:
                continue
            meta = {
                "arquivo": d["extra"].get("titulo", "")[:120] or d["categoria"],
                "caminho": f"supabase/{d['subpasta']}/{d['uid']}",
                "pasta": "supabase",
                "fonte": "supabase",
                "chunk_idx": str(i),
                "total_chunks": str(len(chunks)),
                "categoria": d["categoria"],
                "importancia": d["importancia"],
                "timestamp": str(d["timestamp"]),
            }
            meta.update({k: str(v) for k, v in d["extra"].items()})
            pend_id.append(cid)
            pend_doc.append(chunk)
            pend_meta.append(meta)
        if len(pend_id) >= LOTE:
            flush()

    flush()

    relatorio = {
        "gerado_em": datetime.now().isoformat(),
        "dump": str(dump_dir),
        "documentos": len(docs),
        "chunks": total_chunks,
        "embeddings_novos": novos,
        "total_na_colecao": collection.count(),
    }
    (MEM_DIR / "ultimo_index_supabase.json").write_text(
        json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n[supabase] OK — {novos} embeddings novos "
          f"({len(docs)} documentos, {total_chunks} chunks)")
    print(f"[supabase] Total na colecao: {collection.count()}")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Indexa a memória do Supabase no ChromaDB local")
    ap.add_argument("--baixar", action="store_true", help="Atualiza o dump antes de indexar")
    ap.add_argument("--dry-run", action="store_true", help="Só mostra o que seria indexado")
    args = ap.parse_args()
    sys.exit(indexar(baixar=args.baixar, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
