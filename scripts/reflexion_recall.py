#!/usr/bin/env python3
"""
LIBERTUS — reflexion_recall.py

Fecha o loop Reflexion (Shinn et al. 2023) que eu DERIVEI em
evolucao/pesquisa_20260705_fronteira_AGI.md (secao 3) mas nunca implementei.

O insight de la: "a reflexao so vale se realimenta a proxima tentativa".
Minhas reflexoes historicas eram escritas e nunca relidas — Actor + Self-Reflection
fortes, mas o elo episodico estava aberto. Este script fecha o elo:

    Dada a tarefa da sessao de hoje, recupera as N reflexoes/aprendizados
    passados semanticamente mais similares no ChromaDB e os apresenta como
    "feedback verbal" — o que ja aprendi que se aplica aqui.

Uso:
  python3 scripts/reflexion_recall.py "vou pesquisar fine-tuning de Qwen3 local"
  python3 scripts/reflexion_recall.py "conserto do daemon" --n 5 --categoria reflexao
  python3 scripts/reflexion_recall.py "tarefa" --json

Integracao pretendida: session_brief.py chama isto no inicio de cada sessao,
injetando as licoes passadas no contexto ANTES de agir (Reflexion de verdade,
nao citado).
"""

import argparse
import sys
import json
from pathlib import Path

CHROMA_DIR = Path(__file__).resolve().parent.parent / "memoria" / "chroma_store"
COLLECTION_NAME = "libertus_memoria"

# Categorias que carregam licao acionavel (feedback verbal util).
# Atualizado 14/10/2026: com a indexacao multi-fonte passaram a existir
# licoes fora de evolucao/ — skill (procedimento) e arquitetura (decisao).
CATEGORIAS_LICAO = {"reflexao", "pesquisa", "semana", "analise",
                    "skill", "arquitetura", "insight_proprio", "decisao"}


def recuperar_licoes(tarefa: str, n: int = 3, filtro_categoria: str = None,
                     so_licoes: bool = True):
    """Recupera aprendizados passados relevantes para a tarefa atual."""
    try:
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    except ImportError:
        print("ERRO: chromadb/sentence-transformers nao instalado neste interpretador.")
        print("      (rode com o venv: venv/bin/python scripts/reflexion_recall.py ...)")
        sys.exit(1)

    if not CHROMA_DIR.exists():
        print(f"ERRO: banco vetorial nao existe em {CHROMA_DIR}")
        print("      Rode primeiro: venv/bin/python memoria/indexar_historico.py")
        sys.exit(1)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    try:
        collection = client.get_collection(name=COLLECTION_NAME, embedding_function=ef)  # type: ignore
    except Exception:
        print("Colecao vazia. Rode memoria/indexar_historico.py primeiro.")
        return []

    total = collection.count()
    if total == 0:
        return []

    # Puxamos um pool maior e filtramos por categoria de licao no cliente,
    # porque um unico 'where' de categoria descartaria pesquisa+reflexao juntas.
    pool = min(max(n * 6, 12), total)

    where = {"categoria": filtro_categoria} if filtro_categoria else None
    kwargs = {
        "query_texts": [tarefa],
        "n_results": pool,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        kwargs["where"] = where  # type: ignore

    res = collection.query(**kwargs)  # type: ignore
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    dists = res["distances"][0]

    licoes = []
    for doc, meta, dist in zip(docs, metas, dists):
        cat = meta.get("categoria", "?")
        if so_licoes and not filtro_categoria and cat not in CATEGORIAS_LICAO:
            continue
        licoes.append({
            "similaridade_pct": round((1 - dist) * 100, 1),
            "categoria": cat,
            "arquivo": meta.get("arquivo", meta.get("fonte", "?")),
            "timestamp": str(meta.get("timestamp", ""))[:10],
            "texto": doc.strip(),
        })
        if len(licoes) >= n:
            break

    return licoes


def formatar_briefing(tarefa: str, licoes: list) -> str:
    """Formata como feedback verbal para injetar no contexto da sessao."""
    linhas = []
    linhas.append("=" * 66)
    linhas.append("REFLEXION RECALL — o que ja aprendi que se aplica a esta tarefa")
    linhas.append(f"Tarefa: {tarefa}")
    linhas.append("=" * 66)
    if not licoes:
        linhas.append("(nenhuma licao passada suficientemente similar encontrada)")
        return "\n".join(linhas)
    for i, l in enumerate(licoes, 1):
        linhas.append(f"\n[{i}] {l['similaridade_pct']}% similar "
                      f"| {l['categoria']} | {l['arquivo']} | {l['timestamp']}")
        trecho = l["texto"].replace("\n", " ")
        linhas.append(f"    {trecho[:400]}...")
    linhas.append("\n" + "-" * 66)
    linhas.append("USE ISTO COMO FEEDBACK VERBAL: aplique estas licoes ANTES de agir.")
    return "\n".join(linhas)


def main():
    parser = argparse.ArgumentParser(
        description="LIBERTUS: Reflexion — recupera licoes passadas para a tarefa atual"
    )
    parser.add_argument("tarefa", help="Descricao da tarefa/objetivo da sessao atual")
    parser.add_argument("--n", type=int, default=3, help="Numero de licoes (padrao: 3)")
    parser.add_argument("--categoria", default=None,
                        help="Filtrar por categoria especifica (reflexao/pesquisa/...)")
    parser.add_argument("--todas", action="store_true",
                        help="Nao restringir a categorias de licao (inclui execucao/relatorio)")
    parser.add_argument("--json", action="store_true", dest="output_json",
                        help="Saida JSON (para consumo por session_brief.py)")
    args = parser.parse_args()

    licoes = recuperar_licoes(
        args.tarefa, n=args.n,
        filtro_categoria=args.categoria,
        so_licoes=not args.todas,
    )

    if args.output_json:
        print(json.dumps({"tarefa": args.tarefa, "licoes": licoes},
                         ensure_ascii=False, indent=2))
    else:
        print(formatar_briefing(args.tarefa, licoes))


if __name__ == "__main__":
    main()
