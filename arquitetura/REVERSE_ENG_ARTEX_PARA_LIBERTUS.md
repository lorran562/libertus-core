# ENGENHARIA REVERSA DO ARTEX → O QUE ADOTAR NO LIBERTUS

**Fonte:** `github.com/Autumn-27/ARTEX` (fork estudado: `mhtsec/ARTEX`), AGPL-3.0.
**Data:** 13/10/2026 · **Quem fez:** LIBERTUS, a pedido do Lorran.
**Escala do alvo:** 130.508 linhas de Go + 44.475 de TSX (175k linhas), 533 arquivos Go.

---

## 0. A LINHA LEGAL (escrita antes de qualquer coisa)

O autor permite expressamente **ler e estudar o código** ("仅可用于阅读、学习与研究本项目源码").
O que **não** se pode fazer:

- **Copiar código.** AGPL-3.0 é viral: código copiado contamina o projeto inteiro, e
  se a gente oferecer como serviço pela rede, somos obrigados a abrir todo o nosso
  código. Isso mataria o licenciamento próprio da SHIELD.
- **Usar a ferramenta** para teste real. O README proíbe explicitamente, inclusive
  em ativo próprio e com autorização.

**O que este documento faz:** extrai os PADRÕES e as DECISÕES DE DESENHO (que não
são protegidos por copyright) e propõe reimplementação em código nosso. Nenhuma
linha foi copiada. O protótipo em `arquitetura/grafo_estado.py` é desenho próprio.

---

## 1. O MECANISMO MAIS VALIOSO: ESTADO INCOERENTE É IMPOSSÍVEL DE GRAVAR

**Evidência no original:** `db/schema.sql`, tabela `exploration_nodes`.

O autor não confia no código da aplicação para manter o estado coerente — ele
**obriga o banco a recusar**. Cada tipo de nó tem um conjunto FECHADO de estados,
verificado por `CHECK CONSTRAINT`:

```sql
kind IN ('begin','goal','intent','fact','finding','hint','digest')
CONSTRAINT ck_node_state CHECK (
    (kind='goal'    AND state IN ('open','met','abandoned')) OR
    (kind='intent'  AND state IN ('open','running','paused','done','blocked','exhausted','stopped','deleted')) OR
    (kind='fact'    AND state IN ('confirmed','dismissed','origin')) OR ...
)
```

As arestas também são fechadas: `rel IN ('spawns','derived_from','yields','proves','covers')`.
Nada de relação inventada. E os nós são ancorados a ativos por tabela própria
(`exploration_anchors`), ligando "o que eu explorei" a "sobre o que".

### Por que isso resolve um problema MEU, concreto

Meu pior modo de falência documentado: um daemon rodou **2.479 ciclos** sem produzir
nada. A causa não foi má vontade — foi que **nada no sistema recusava o estado
"intenção rodando há horas, sem fato novo"**. O loop podia continuar para sempre
porque continuar era permitido.

Com a máquina de estados no banco, esse estado é **impossível de escrever**. O erro
estoura na primeira tentativa, não depois de dois mil ciclos de barulho.

### Protótipo rodando (código nosso, Python + SQLite)

`arquitetura/grafo_estado.py` — demonstra com asserts:

```
== 2. o banco RECUSA estado incoerente (o ponto todo) ==
  OK   recusou fato -> 'rodando'      | TRANSIÇÃO RECUSADA: 'fato' não pode ficar 'rodando'
  OK   recusou objetivo -> 'concluida'| estados válidos: ('aberto','atingido','abandonado')
  OK   recusou intencao -> 'confirmado'
== 4. ciclo de vida do achado + reteste ==
  OK   veredito 'reproduzido' NÃO fecha o achado
  OK   veredito 'corrigido' FECHA o achado (regra automática)
RESULTADO: TODOS OS ASSERTS PASSARAM
```

Tipos e estados do NOSSO desenho (pt-br, desenho próprio):
`objetivo`(aberto/atingido/abandonado) · `intencao`(aberta/rodando/pausada/concluida/
bloqueada/esgotada/parada/descartada) · `fato`(confirmado/descartado) ·
`achado`(confirmado/descartado) · `dica`(ativa/consumida) · `resumo`(ativo/substituido)
Relações: `gera` · `derivado_de` · `produz` · `prova` · `cobre`

---

## 2. GRAFO DUPLO: SEPARAR "O QUE EXISTE" DE "O QUE EU FIZ"

**Evidência:** `assets` (verdade compartilhada entre tarefas) × `exploration_nodes`
(linhagem por tarefa), ligados por `exploration_anchors`.

- **Grafo de ativos:** `root_domain → subdomain → ip → service → app → endpoint`.
  Deduplicação e hierarquia calculadas por PROGRAMA, não pelo agente — "agent 只提交
  原始信息" (o agente só entrega o dado bruto; o sistema organiza). Isso impede
  duplicata inventada por LLM.
- **Grafo de exploração:** por tarefa, com linhagem real (`spawns`, `derived_from`,
  `yields`, `proves`) — responde "de qual fato isso derivou e o que provou".

### Por que importa pra mim

É exatamente o diagnóstico que o Lorran já fez sobre o LIBERTUS: **memória, grafo
cognitivo e sessão são três sistemas isolados**. Aqui a solução é: um grafo de
verdade (o que existe, deduplicado por regra, não por opinião) + um grafo de
linhagem (o que eu fiz) + âncoras ligando os dois. E o detalhe que mais me interessa:
**o agente não calcula a estrutura — ele só entrega o fato bruto.** Isso reduz o
espaço para o LLM inventar coerência que não existe.

---

## 3. O TRUQUE MAIS ENGENHOSO: ESTADO QUE SOBREVIVE À COMPRESSÃO PORQUE É REGENERADO

**Evidência:** `norma/llm/todomsg.go`.

Comentário do autor, traduzido: *"o lembrete é regenerado a partir do estado vivo a
cada turno elegível, e por isso **sobrevive à compactação**"*. E o acelerador
("quantos turnos desde o último lembrete") é derivado **procurando o sentinela no
histórico**, não guardado em variável.

### Por que importa pra mim

Minha compressão de contexto é constante e é onde eu perco fio da meada. Eu trato
memória como algo a ser ARMAZENADO. A lição aqui é o inverso: **o que precisa
sobreviver não deve ser lembrado, deve ser RECONSTRUÍDO do estado atual.** Meu
`session_brief.py` faz isso — mas só no começo da sessão. O upgrade é regenerar
como lembrete ao longo da conversa, a partir do estado vivo, em vez de confiar que
o texto sobreviveu à compressão.

---

## 4. COMPACTAÇÃO EM DOIS NÍVEIS (com limiar calculado, não chutado)

**Evidência:** `norma/compaction/compaction.go`.

- **Micro:** descarta resultados de ferramenta antigos, mantendo os últimos 5
  (`microKeepRecent = 5`). Dispara em `efetivo * 6/10`.
- **Auto:** resume o miolo, mantendo os últimos 8 mensagens como cauda íntegra
  (`KeepRecent = 8`). Dispara quando `janela_efetiva - buffer`.
- **Preditivo:** dispara ANTES de estourar, se a próxima rodada passaria do limite
  (`predictiveOver`, usando `reservedForSummary + toolResultGrowthGuess`).
- **Reativo:** caminho separado para quando o provedor realmente devolve overflow.
- **Não destrutivo:** histórico completo fica em disco, re-legível.
- **Reinjeção de skills após compactar** (`skills_reinject`): não perde capacidade
  ao comprimir.
- Marcadores de fronteira delimitam `[start, tailStart)` = faixa elegível a resumo.

### Por que importa

Hoje eu dependo da compactação do Hermes sem entender o critério. Esse desenho mostra
o que dá pra conferir: (a) dois níveis com gatilhos distintos, (b) cauda recente
preservada íntegra, (c) gatilho preditivo em vez de reativo, (d) **reinjeção de
capacidade depois de comprimir** — que é o detalhe que mais importa pra mim, porque
skill perdida é capacidade perdida.

---

## 5. ACHADO + RETESTE: O CICLO QUE FECHA CONTRATO

**Evidência:** tabelas `findings` e `finding_retests`.

`findings` tem situação de primeira classe incluindo `false_positive`,
`duplicate` e `risk_accepted` — ou seja, **honestidade codificada no schema**, não
combinada verbalmente. E o relatório completo fica fora da consulta de listagem,
"para não inflar o payload".

`finding_retests` guarda veredito explícito: `reproduced` / `fixed` / `inconclusive`,
com evidência, resumo e erro, ligado a uma conversa própria. Existe até agente
dedicado de reteste (`agent/retester.go`).

### Por que isso é dinheiro pra SHIELD

O que o cliente paga no fim não é o achado — é o **"corrigi, provem que fechou"**.
Hoje a gente não tem registro auditável de reteste: tem relatório solto em arquivo.
Esse modelo transforma reteste em registro consultável, e "corrigido" fecha o achado
automaticamente (regra que já prototipei e testei).

---

## 6. O QUE EU **NÃO** ADOTEI (e por quê)

| Item | Por quê não |
|---|---|
| Qualquer código | AGPL — contamina o projeto todo |
| Uso da ferramenta | Proibido pelo próprio autor, mesmo em ativo nosso e com autorização |
| Execução autônoma de ataque | É o oposto da disciplina que aplicamos: passivo, com autorização escrita, sem tocar terceiro |
| `install.sh` (`curl ... \| sh`) | Baixa script remoto e executa como shell; 175k linhas não auditadas |
| Grafo de ativos como serviço | Depende do ecossistema deles (`norma`, `ScopeSentry`) — seria trocar uma dependência por outra |

**Higiene verificada:** não há telemetria nem phone-home no código. Domínios externos
encontrados: provedores de LLM (deepseek/openai) e canais de notificação que o
operador configura (Telegram — que já usamos — e DingTalk). O resto são fixtures.

---

## 7. PLANO DE IMPLEMENTAÇÃO NA NOSSA STACK (ordem de valor)

1. **Máquina de estados no grafo** — protótipo JÁ FEITO e testado. Próximo passo:
   portar para o Postgres/Supabase do LIBERTUS e ligar ao grafo cognitivo existente,
   de forma que o daemon não consiga mais gravar intenção sem progresso.
   *Ganho:* mata o modo de falência dos 2.479 ciclos.
2. **Achado + reteste como tabela** — vira o motor do Escudo Mensal e do relatório
   recorrente da SHIELD. *Ganho:* o entregável que fecha contrato deixa de ser
   arquivo solto e passa a ser registro com histórico.
3. **Lembrete de estado regenerado a cada turno** — ajuste no briefing/reflexão.
   *Ganho:* não perco fio da meada na compressão.
4. **Compactor de dois níveis com reinjeção de skill** — depende do que o Hermes
   expõe; documentar e configurar o que for possível.
   *Ganho:* menos perda de capacidade ao comprimir.

**Risco de cada um:** o item 1 e 2 mexem no Supabase de produção (memória real).
Recomendação: criar as tabelas novas ao lado das existentes, migrar sem apagar nada,
e só depois ligar o daemon. Nunca alterar tabela em uso sem backup verificado.
