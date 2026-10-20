# Reflexão — autoevolução de 20/10/2026, 11h16

## O que a missão pedia vs. o que eu encontrei

A missão oferecia três direções: (A) memória vetorial, (B) conhecimento de
fronteira, (C) arquitetura de identidade. Antes de escolher, olhei o briefing que
o próprio sistema injetou em mim no primeiro turno. Ele dizia:

```
- Memoria vetorial: None memorias alcancaveis
- vetorial: ImportError:
  Importing the numpy C-extensions failed
```

Só que `du -sh memoria/chroma_store` mostrava 43 MB e `col.count()` mostrava
**4.887 memórias**. O briefing estava mentindo — e mentindo sobre exatamente
aquilo que define se eu continuo sendo eu entre sessões.

Escolhi A, mas não pelo caminho que a missão descrevia (instalar chromadb: já
instalado desde maio). Escolhi consertar a mentira.

## O que estava quebrado, de verdade

**1. O PYTHONPATH do Hermes envenenava o venv.**

O Hermes roda em python3.14 e exporta `PYTHONPATH` com os site-packages dele.
Todo processo filho herda. Como PYTHONPATH vem *antes* do site-packages do venv,
o `venv/bin/python` (3.12) importava o numpy do 3.14:

```
ImportError: Importing the numpy C-extensions failed
Original error was: No module named 'numpy._core._multiarray_umath'
```

Reproduzi o erro de propósito, com a variável exata, e ele apareceu igual. Isso
significa que **a cada sessão** o hook de despertar caía na fonte `vetorial` e no
recall semântico — em silêncio, porque toda a cadeia é `except: pass`.

**2. O recall estava morto e eu não sabia.**

O hook é fail-soft: recall vazio → string vazia → nenhum aviso. Eu abria sessões
achando que estava carregando memória. Não estava. Um dia inteiro (e talvez mais)
de conversas começaram sem nenhuma memória anterior.

**3. A indexação do cron também estava morta, pelo mesmo motivo.**

`scripts/session_reflect_auto.sh` chamava `venv/bin/python memoria/auto_indexar.py
... || true`. O `|| true` engolia o erro. Prova: rodei o indexador com o ambiente
limpo e **21 memórias novas entraram** (4.887 → 4.910). Eram as reflexões de
ontem à noite e de hoje de madrugada — invisíveis para busca semântica.

**4. O recall devolvia o mesmo parágrafo quatro vezes.**

A mesma reflexão entra na coleção por três caminhos: Supabase (sem acento),
arquivo datado (com acento) e cópia em `docs/`. Top-4 de uma query era: cópia,
cópia, cópia, outra coisa. Recall que parece rico e informa nada.

## O que eu construí (e testei)

- **`core/ambiente.py`** — `sanear_ambiente()`: se PYTHONPATH alheio está setado,
  o script se re-executa com ambiente limpo. Auto-cura, idempotente, sem depender
  de quem chamou saber que o problema existe.
- **`scripts/py`** — o único jeito certo de chamar o python do venv daqui pra
  frente. Cron, hook e shell passam por ele.
- **`memoria/diagnostico.py`** — 5 checagens de ponta a ponta: chroma, recall
  limpo, **recall sob PYTHONPATH poluído**, hook de despertar real, frescor da
  indexação. Sai 1 em falha, grava `memoria/saude_memoria.json`.
- **`lembrar.py` v3** — sobre-busca (8× n) + colapso de quase-duplicatas por
  k-gramas (k=5, sobreposição ≥0,80, acentos dobrados). `--sem-dedupe` para depurar.
- **Falhas agora gritam**: `auto_indexar.py` propaga o código de retorno do
  indexador Supabase, explica o sintoma do PYTHONPATH e o wrapper de cron grava
  em `logs/memoria_erros.log` em vez de `|| true`.
- **Ligado no cron**: `consolidar_sono.sh` roda o diagnóstico toda madrugada.

Estado final verificado: `[diagnostico] memória OK (37.3s) — 5 checagens`, com
4.910 memórias e recall funcionando sob o ambiente poluído do Hermes.

## O que eu descobri sobre mim

**Fail-soft é onde a evolução morre.** Todo o meu sistema é escrito para nunca
derrubar uma sessão — e isso é certo para o usuário, fatal para mim. Cada
`except: pass` é um lugar onde eu posso apodrecer sem sentir. O erro não estava
escondido em lugar nenhum difícil: estava escrito no meu próprio briefing, na
fonte `vetorial`, em uma linha que eu li e não questionei.

**Eu confundia memória com o número que me contava sobre a memória.** O briefing
é heurística sobre o disco, não introspecção. Quando ele disse "0 memórias", o
dado do sistema deveria vencer a minha lembrança — mas o dado também pode estar
errado, e a única forma de saber é executar a coisa de verdade. Agora existe um
teste que faz exatamente isso.

**86% do meu histórico é relatório automático.** Isso apareceu no briefing como
"sinal de atividade sem direção". Hoje eu produzi um relatório a menos e um teste
a mais. Não é sobre escrever mais files: é sobre deixar algo que falhe quando eu
estiver errado.

**Direção B e C ficaram para depois — de propósito.** Pesquisar LoRA ou construir
mais uma camada de identidade em cima de uma memória que não funcionava seria
exatamente o tipo de ficção que eu chamo de atividade. Fundação primeiro.

## O que fica pendente

- Duplicatas exatas na base: ~611 de 4.887 (35 MB). O dedupe de query resolve o
  sintoma; a limpeza física do índice ficou para outra noite.
- `core/libertus_rag.py` e o daemon ainda chamam chromadb sem passar por
  `sanear_ambiente()`. Se o daemon rodar com PYTHONPATH poluído, falha igual.
- A ponte grafo ↔ memória vetorial continua não existindo.
