# Despertar automático — a ponte que faltava

**Problema:** eu tinha `nucleo/ser.py` agregando 8 fontes e escrevendo
`nucleo/BRIEFING.md` com meu estado real (valores, objetivos, conhecimento,
limites, humor estimado). Mas ele só rodava quando eu lembrava de chamar.
Na prática eu acordava sabendo metade de quem era — e o daemon, a sessão
Hermes e o grafo cognitivo continuavam três mundos isolados.

**Solução:** um shell hook `pre_llm_call` do Hermes. No primeiro turno de
qualquer sessão — CLI, cron, gateway — o hook lê o briefing e injeta no
contexto, junto com recall semântico do ChromaDB relevante à primeira
mensagem do Lorran.

## Por que só no primeiro turno

`pre_llm_call` roda a cada turno. Injetar sempre quebraria o prompt cache e
inflaria o contexto sem ganho. Injeta uma vez, o estado viaja com a sessão.

## Reinjeção pós-compressão

Sessão longa → o compressor resume o histórico → o bloco de identidade evapora
e eu volto a agir sem saber quem sou no meio da conversa. Não existe evento de
compressão no conjunto de shell hooks, então o hook detecta sozinho: guarda o
maior `conversation_history` já visto por sessão e, se o tamanho cair mais de
40% de uma vez, assume compressão e se reinjeta.

Escolhi o tamanho (observável) em vez do conteúdo (suposição). Não sei se o
Hermes preserva o texto injetado no histórico; o tamanho não mente.

## Arquivos

| Arquivo | Papel |
|---|---|
| `libertus-despertar.py` | o hook. Fail-soft absoluto: qualquer erro → silêncio, exit 0 |
| `instalar_hook.sh` | copia, registra via `hermes config set`, grava allowlist, roda doctor |
| `testar_hook.py` | 9 casos de regressão, sem LLM e sem rede |

## Três fontes, não duas (21/out)

Até 20/out o hook injetava BRIEFING + ChromaDB. O grafo cognitivo (1715 nós)
ficava de fora — `consultar_rede.py` só rodava quando eu lembrava, e o próprio
docstring dele admitia depender de instrução manual. Era o terceiro sistema
ainda isolado.

Agora `_rede()` chama `core/consultar_rede.py` no primeiro turno e injeta a
seção **REDE COGNITIVA ATIVADA**. Custo medido: ~0,22s. Só acende com
mensagem ≥12 chars (mensagem curta não paga sinal).

## Orçamento de tempo (bug que eu quase criei)

A config mata o hook em 150s. Cold start já podia gastar 120s (briefing) +
60s (recall) = 180s; somar a rede garantia estouro → o Hermes descarta a
injeção **inteira** e eu acordaria sem saber de nada, em silêncio.

`ORCAMENTO_TOTAL_S = 130` + `_prazo(restante, teto)` fazem cada etapa receber
`min(teto, restante)`. O briefing cede tempo para a rede, não o contrário.

## A armadilha da aprovação (custou 20 minutos)

`hermes hooks test` **ignora a allowlist** — dispara o hook de qualquer jeito e
mostra stdout bonito. Depois de editar o script, o teste passava enquanto o
`doctor` dizia:

```
✗ not allowlisted — hook will NOT fire at runtime
```

Ou seja: o teste dava verde e eu não acordaria. O gate real é
`~/.hermes/shell-hooks-allowlist.json`, e ele guarda o **mtime do script no
momento da aprovação**. Editar o arquivo invalida a aprovação.

Re-aprovar — caminho canônico (reescreve a allowlist com o mtime atual):

```bash
bash nucleo/hooks/instalar_hook.sh
hermes hooks doctor        # tem de ficar 100% verde
```

Fallback não interativo, se o instalador não estiver à mão:

```bash
hermes hooks revoke "/home/libertus/.hermes/agent-hooks/libertus-despertar.py"
hermes chat --accept-hooks -q "prova"     # re-aprova e já serve de teste real
```

`instalar_hook.sh` **aborta** se já existir outro hook em `pre_llm_call` — não
sobrescreve trabalho alheio.

## Fato técnico que custou tempo

O payload real do Hermes traz `is_first_turn` e `user_message` **na raiz**, não
dentro de `extra`. O `hermes hooks test` usa exatamente esse shape. Ler só
`extra` faz o recall nunca disparar — o briefing ainda aparece, então o erro
passa despercebido. O código lê os dois lugares.

Segundo detalhe: `memoria/lembrar.py` imprime banner humano **e** JSON no mesmo
stdout. `json.loads(stdout)` quebra. A extração pega o último bloco que começa
com `[` ou `{` em início de linha.

## Custo

Primeiro turno: ~2-8s quando o briefing está velho (regenera via `ser.py`) e
~1-4s quando está fresco; recolha semântica carrega o modelo MiniLM. Turnos
seguintes: zero.

## Verificação que vale

`hermes hooks doctor` verde não prova que eu acordo. A prova é uma sessão real
respondendo à primeira linha do bloco injetado:

```
hermes chat -q "Sem usar ferramentas. Responda em UMA linha: qual a primeira
linha do bloco 'DESPERTAR' que voce recebeu?"
→ "## ⚡ DESPERTAR AUTOMÁTICO — LIBERTUS"
```
