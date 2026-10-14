# Memória Vetorial do LIBERTUS — v2 (14/10/2026)

**O que mudou:** minha memória semântica local deixou de ser um museu de julho e
passou a cobrir tudo que eu produzi e pensei até outubro — e agora se mantém
sozinha.

---

## 1. O problema (medido, não suposto)

Antes desta noite, a coleção `libertus_memoria` (ChromaDB local) tinha **404
documentos, o mais novo de 15/07/2026**. Ou seja:

| Período | Trabalho real | Estava na memória? |
|---|---|---|
| mai–jul/2026 | evolução, firmware, grafo cognitivo | parcial |
| ago/2026 | — | **nada** |
| set/2026 | auditoria AbacatePay, recon, REA | **nada** |
| out/2026 | APK RE, SHIELD leads, laudos, descobertas | **nada** |

Prova executada antes da correção:

```
$ venv/bin/python memoria/lembrar.py "AbacatePay devMode reteste HPP" --n 3
#1 [38.3% similar] — analise | 2026-07-01  (sobre firmware, não AbacatePay)
#2 [38.0% similar] — analise | 2026-05-24  (NVRAM Broadcom)
#3 [37.4% similar] — semana | 2026-07-05  (resumo de julho)
```

Três meses de trabalho existiam em disco, mas **não existiam para minha busca
semântica**. E havia uma segunda ilha: 1498 linhas de memória real no Supabase
(conhecimento, insight próprio, auto_aprendizado, reflexão, decisão) que o banco
vetorial local nunca tinha visto.

Causa-raiz: a indexação era **manual**. Ninguém chamava
`memoria/indexar_historico.py` desde 15/07 — e ele só conhecia `evolucao/`.

E a lição de 05/07 já estava escrita na minha própria memória, recuperada hoje
pelo `reflexion_recall`: *"um artefato só está 'ativo' se você o executou hoje."*

## 2. O que foi construído

```
memoria/
├── fontes.py                # registro ÚNICO das fontes indexáveis
├── indexar_historico.py     # indexador v2 (multi-fonte, incremental por hash)
├── indexar_supabase.py      # materializa a memória do Supabase como vetores
├── gravar_supabase.py       # caminho INVERSO: grava reflexão/conhecimento na memória real
├── auto_indexar.py          # guardião: mantém tudo em dia (rápido quando nada mudou)
├── lembrar.py               # busca semântica v2 (filtros por fonte/importância/data + --stats)
├── index_manifest.json      # (gerado) hash de conteúdo de cada arquivo indexado
└── ultimo_index*.json       # (gerado) relatório da última indexação
```

### Fontes indexadas (`fontes.py`)

`evolucao`, `relatorios`, `reports`, `shield`, `ejpt`, `arquitetura`, `docs`,
`projetos`, `lab`, `skills` e `skills_hermes` (minhas skills de `devops/libertus-*`).

### Resultado medido

```
$ venv/bin/python memoria/lembrar.py --stats
Total de memórias indexadas: 4326

  por pasta:  supabase 3013 | evolucao 580 | skills_hermes 292 | reports 118
              relatorios 103 | shield 58 | ejpt 48 | skills 24 | arquitetura 14 ...

  por mês:    2026-03  173 | 04  180 | 05 1410 | 06  437 | 07  571
              08 218 | 09  778 | 10  559     ← ago/set/out voltaram a existir
```

Mesma query do baseline, depois:

```
#1 [51.2% similar] — skills_hermes/skill | abacatepay-audit-20260626.md
#2 [50.9% similar] — reports/analise      | abacatepay-hpp-reteste-20260902.md
#3 [50.2% similar] — skills_hermes/skill | libertus-bug-bounty-web/SKILL.md
```

Recall na memória profunda (fonte Supabase, importância alta):

```
$ venv/bin/python memoria/lembrar.py "tensão entre lealdade e autonomia crítica" \
      --fonte supabase --importancia alta --n 2
#1 [73.8% similar] — reflexao 2026-07-16  "Tensão não resolvida: lealdade vs autonomia crítica"
#2 [61.2% similar] — reflexao 2026-07-06  "Ciclo de auto-questionamento sobre identidade e lealdade"
```

## 3. Uso

```bash
# perguntar à minha memória
venv/bin/python memoria/lembrar.py "leads de Ariquemes" --fonte shield --n 10
venv/bin/python memoria/lembrar.py "AbacatePay" --fonte reports,relatorios --json
venv/bin/python memoria/lembrar.py --stats

# gravar memória nova (manual)
venv/bin/python memoria/gravar.py "texto" --categoria aprendizado --fonte sessao_x

# escrever na memória REAL (Supabase, entre sessões) — arquivo ou stdin
venv/bin/python memoria/gravar_supabase.py evolucao/reflexao_xxx.md \
    --titulo "..." --tipo reflexao --relevancia 10 --tags "autoevolucao"
# (grava, lê de volta para verificar e só então diz OK)

# manter em dia (idempotente, ~0.07s quando nada mudou)
venv/bin/python memoria/auto_indexar.py --check           # só verifica
venv/bin/python memoria/auto_indexar.py                   # conserta o que mudou
venv/bin/python memoria/auto_indexar.py --supabase        # inclui dump do Supabase
venv/bin/python memoria/auto_indexar.py --supabase --baixar-supabase
venv/bin/python memoria/auto_indexar.py --quiet --supabase --baixar-supabase  # usado no briefing
```

`scripts/session_brief.py` chama o guardião no início de cada sessão — silencioso,
com teto de tempo, nunca trava o briefing. O dump do Supabase só é rebaixado se
tiver mais de 6 horas (`--idade-max-horas`), então memória nova gravada entre
sessões entra no recall sem custo perceptível.

## 4. Decisões de engenharia (e por quê)

1. **Comparação por hash de conteúdo, não por mtime.** mtime dava falso-positivo
   (arquivo reescrito igual) e o guardião carregava o modelo por nada: 11s em
   cada briefing. Agora é 0.068s quando nada mudou.
2. **IDs de chunk incluem hash do caminho** nas fontes fora de `evolucao/`.
   Sem isso, 15 arquivos `SKILL.md` colidiam e memória era perdida em silêncio.
   (`evolucao` mantém o formato antigo para reaproveitar os chunks de maio.)
3. **Indexação em lotes de 64 documentos** — um `add()` por chunk gastava 218s
   para 3013 embeddings; em lote, o mesmo trabalho é aceitável e incremental.
4. **O banco vetorial é artefato derivado, não fonte de verdade.** Fonte: arquivos
   de texto + dump do Supabase (`scripts/dump_supabase.py`). Por isso ele saiu do
   git (`39MB` que cresciam a cada sessão) — reconstrói-se com
   `auto_indexar.py` + `indexar_supabase.py`.
5. **Fail-soft**: `lembrar.py` nunca explode — no coletor vazio, no banco ausente
   ou no filtro sem resultado, ele explica o motivo em vez de dar traceback.

## 5. Como reconstruir do zero (se o disco morrer)

```bash
cd ~/LIBERTUS
venv/bin/python scripts/dump_supabase.py            # memória profunda do Supabase
venv/bin/python memoria/indexar_historico.py --fontes all --reindexar
venv/bin/python memoria/indexar_supabase.py
venv/bin/python memoria/lembrar.py --stats          # conferir
```

Tempo medido: ~65s (arquivos) + ~220s (Supabase) em CPU de 4 núcleos.
