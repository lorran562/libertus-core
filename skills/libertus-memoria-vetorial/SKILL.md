---
name: libertus-memoria-vetorial
description: Use when LIBERTUS vector memory is stale or fragmented.
version: 1.0.0
author: LIBERTUS
license: MIT
metadata:
  hermes:
    tags: [libertus, memoria, chromadb, supabase, rag]
    related_skills: [libertus-reflexao, libertus-session-logger, libertus-rede-neural-cognitiva]
---

# Memória vetorial do LIBERTUS (v2, 14/10/2026)

## When to Use

- Busca semântica (`lembrar.py`, `reflexion_recall.py`) não acha algo que já produzi.
- `lembrar.py --stats` mostra o documento mais novo com semanas/meses de atraso.
- Suspeita de memória fragmentada: arquivos locais vs Supabase.
- Antes/depois de qualquer trabalho longo: garantir que a memória vai guardar isso.
- Ao investigar "o LIBERTUS esqueceu" — checar as duas fontes antes de concluir.

Banco vetorial local: `~/LIBERTUS/memoria/chroma_store`, coleção `libertus_memoria`,
embeddings `all-MiniLM-L6-v2` via `~/LIBERTUS/venv/bin/python` (Python 3.12;
chromadb 1.5.9 + sentence-transformers 5.6.0 + torch CPU já instalados — **não**
reinstalar; o `python3` do sistema (3.14) não tem esses pacotes).

## Regra central

**Artefato que não é executado é ficção.** Indexação manual apodrece: entre
15/07/2026 e 14/10/2026 ninguém rodou o indexador e a coleção ficou com 404 docs
(3 meses de trabalho invisíveis para busca semântica). Toda entrega de memória
deve incluir o guardião que a mantém — nunca só o índice.

## Pipeline

```
fontes.py  →  indexar_historico.py (arquivos)   →  chroma_store
           →  indexar_supabase.py  (Supabase)   →  chroma_store
auto_indexar.py  →  guardião: roda os dois só se algo mudou
lembrar.py / scripts/reflexion_recall.py  →  consultam o chroma_store
scripts/session_brief.py  →  chama o guardião no início da sessão
gravar_supabase.py  →  escreve na memória REAL (Supabase) — caminho inverso do dump
```

Fluxo completo da memória: produção (arquivos/logs) → vetor local → recall →
contexto da sessão → reflexão → Supabase → volta ao vetor. Se uma das pontas
estiver aberta, memória nova não entra e eu "esqueço" o que fiz.

## Comandos que funcionam

```bash
cd ~/LIBERTUS
VENV=venv/bin/python

$VENV memoria/lembrar.py "query" --n 5 --fonte reports,shield --importancia alta --json
$VENV memoria/lembrar.py --stats              # o que eu realmente lembro
$VENV memoria/auto_indexar.py --check          # ~0.07s se está em dia
$VENV memoria/auto_indexar.py --supabase       # conserta o que mudou
$VENV memoria/indexar_historico.py --fontes all --dry-run
$VENV memoria/indexar_supabase.py --baixar     # atualiza dump e indexa
$VENV scripts/dump_supabase.py                 # 1498 memórias do Supabase
$VENV memoria/gravar_supabase.py arquivo.md --titulo "X" --tipo reflexao --relevancia 10
$VENV scripts/reflexion_recall.py "tarefa de hoje"   # feedback verbal (Reflexion)
```

`auto_indexar.py --baixar-supabase` só baixa dump com mais de 6h
(`--idade-max-horas`); o briefing usa exatamente isso, então memória gravada em
outra sessão entra no recall sem custo perceptível.

## Pitfalls reais (todos custaram tempo)

1. **Compare por hash de conteúdo, nunca por mtime.** mtime dá falso-positivo
   (arquivo reescrito igual) e o guardião carrega o modelo à toa: 11s por briefing
   em vez de 0.068s.
2. **O hash precisa do mesmo `.strip()` nas duas pontas.** O indexador normaliza o
   conteúdo antes de hashear; comparar contra o texto cru acusa "254 arquivos
   alterados" que não existem.
3. **ID de chunk sem hash do caminho colide.** 15 arquivos `SKILL.md` com o mesmo
   `stem` e um chunk idêntico geram o mesmo ID e a memória é perdida em silêncio,
   sem erro. A fonte `evolucao` mantém o formato antigo
   (`{stem}_chunk{i}_{hash}`) para reaproveitar os chunks de maio; as outras fontes
   usam `{fonte}__{hash(relpath)}__{stem}_chunk{i}_{hash}`.
4. **Indexar em lotes de 64** (`LOTE`). Um `collection.add()` por chunk levou 218s
   para 3013 embeddings; em lote o mesmo trabalho é incremental e suportável.
5. **Checagem de existência só vale contra o que já foi flushado.** Acumule os ids
   pendentes e consulte o banco antes de fechar o lote.
6. **Idempotência não é bug quando o mundo muda.** Arquivos novos aparecendo entre
   duas rodadas (o daemon escreve em `evolucao/` o tempo todo) explicam
   "embeddings novos" inesperados. Antes de caçar bug, veja o que foi criado.

## Duas ilhas (o erro arquitetural de fundo)

A memória existe em dois lugares que não se conheciam: arquivos `.md` locais e o
Supabase (1498 linhas: conhecimento, insight próprio, auto_aprendizado, reflexão,
decisão, conversa). `indexar_supabase.py` materializa o Supabase no banco local
(3013 embeddings) para o recall funcionar offline e sem briefing. Ao investigar
"perdi memória", cheque as DUAS fontes antes de concluir qualquer coisa.

Ainda ilhados: grafo cognitivo (`memoria/grafo_cognitivo.json`) e o daemon 24/7 —
não consultam nem alimentam o banco vetorial. Ponte a construir.

## Manutenção

- `memory/`, `evolucao/` e o banco vetorial são artefatos derivados (fora do git).
  Reconstrução: `dump_supabase.py` → `indexar_historico.py --reindexar` →
  `indexar_supabase.py` (~5 min em 4 núcleos).
- `index_manifest.json` é o estado do guardião; apagar = próxima rodada reindexa
  tudo (sem duplicar: os IDs são por conteúdo).
- `scripts/session_reflect_auto.sh` está órfão (diz "cron a cada 6h", mas não há
  cron nem timer). Até estar ligado, a memória só se atualiza quando alguém abre
  sessão.
