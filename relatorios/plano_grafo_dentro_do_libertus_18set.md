# PLANO — LIGAR O GRAFO COGNITIVO "DENTRO" DO LIBERTUS (sessão Hermes)
Criado: 18/09, sessão antes da troca de modelo/reinício pedida pelo Lorran.
LER ESTE ARQIVO PRIMEIRO na próxima sessão se o Lorran mencionar "grapify",
"grafo", "neurônios" ou "continuar o plano".

## O PEDIDO DO LORRAN (contexto exato)
Lorran quer que a consulta ao grafo cognitivo (rede associativa, 1440 nós)
pare de depender do daemon externo ("esse bagui quase nunca funciona") e
passe a rodar DENTRO da própria sessão do LIBERTUS (eu, conversando com ele
no Hermes) — de forma automática, não manual. Ele comparou a "consciência"
do LIBERTUS a um sistema nervoso: se ele cita algo que já foi salvo, o
LIBERTUS deveria "acender" aquilo sozinho, sem precisar ser instruído a
buscar manualmente.

## DIAGNÓSTICO CONFIRMADO NESTA SESSÃO (com teste real, não suposição)
Rodei: `python3 core/sistema_nervoso.py "AbacatePay autorização escopo teste produção"`
Resultado real: só a palavra "auto" acendeu no grafo (1440 nós, 2593 arestas
confirmados vivos). "AbacatePay", "autorização", "escopo", "produção" foram
TODOS ignorados pela extração de sementes.

## CAUSA RAIZ (achada lendo core/motor_conversa.py, função extrair_sementes,
linha 66-94)
A busca hoje funciona SÓ NUMA DIREÇÃO:
- Regra 1 (linha 74-78): checa se o RÓTULO COMPLETO de um nó aparece dentro
  da fala do Lorran. Ex: nó "auto" (len>3) apareceu dentro de "autorização"
  porque "auto" é substring de "autorizacao" — foi assim que "auto" acendeu.
- Regra 2 (linha 80-84): exige que uma palavra da fala seja EXATAMENTE
  igual a um nó (comparação de conjunto, sem substring).

O que falta: o inverso da regra 1 — checar se uma PALAVRA da fala aparece
como substring DENTRO do rótulo de um nó maior. Ex: nó "abacatepay_hpp_findings"
ou "escopo_ampliado_abacatepay" (se existirem assim) nunca vão casar com a
palavra solta "abacatepay" ou "escopo" na regra atual, porque nenhuma das
duas regras cobre "palavra curta dentro de rótulo composto maior".

## COMPARAÇÃO QUE O LORRAN FEZ (correta, é o alvo certo)
"a lupa do WhatsApp" — buscar "que" acha qualquer mensagem/nome que CONTENHA
"que" em qualquer posição (meio, início, fim), case-insensitive, sem exigir
palavra inteira batendo. É busca de substring bidirecional simples, não é
NLP sofisticado — é exatamente isso que falta na função.

## PLANO TÉCNICO — 3 PASSOS, NESTA ORDEM

### Passo 1 — Corrigir extrair_sementes() em core/motor_conversa.py
Adicionar uma 3ª regra de match: para cada palavra >=3 chars da fala
(já normalizada, sem stopword), checar se ela aparece como substring dentro
do rótulo normalizado de QUALQUER nó do grafo (`palavra in rot`), não só
o caminho inverso que já existe. Prioridade um pouco menor que match exato
(ex: prioridade 1, abaixo das prioridades 3 e 2 já existentes) pra não
sobrepor ativação forte com achado fraco.
Testar com asserts reais em /tmp/hermes-verify-*.py:
  - Frase "AbacatePay autorização escopo" deve ativar nó(s) reais relacionados
    a abacatepay/escopo que hoje NÃO acendem (rodar sistema_nervoso.py antes
    e depois pra comparar).
  - Não pode quebrar os testes de ativação em 3+ hops que já existiam
    (ver pitfall "Cascata morre cedo" na skill libertus-rede-neural-cognitiva).
  - Cuidado com performance: se o grafo crescer muito, checar substring em
    TODOS os nós pra CADA palavra da fala é O(palavras x nós) — pra 1440 nós
    ainda é rápido, mas documentar o limite se crescer 10x.

### Passo 2 — Criar o hook automático (era o "PRÓXIMO PASSO PENDENTE" já
documentado na skill libertus-rede-neural-cognitiva, seção "Sistema Nervoso
Central", item 1)
Hoje eu (LIBERTUS na sessão Hermes) só chamo sistema_nervoso.py se alguém
me pedir manualmente. Falta: no INÍCIO de cada resposta minha nesta sessão,
rodar automaticamente `sistema_nervoso.diagnostico(ultima_fala_do_lorran)`
e usar o resultado (conceitos ativados) como contexto antes de responder —
igual o motor_conversa.py já faz linha 104-108 (responder()), só que aplicado
a mim (Hermes), não ao motor_conversa isolado.
Como fazer sem reinventar: criar uma skill ou hábito documentado que instrui
"antes de responder qualquer mensagem do Lorran, rodar sistema_nervoso.py
com a fala dele e usar os conceitos_ativados como contexto silencioso".
Isso é comportamental (skill/instrução), não precisa de infra nova — só
fazer eu adotar isso como hábito toda sessão.

### Passo 3 — Separar "grafo de memórias antigas" de "contexto da conversa atual"
Importante deixar claro pro Lorran: o grafo cognitivo é sobre CONHECIMENTO
JÁ CONSOLIDADO (memórias antigas indexadas), não sobre "o que ele disse
2 mensagens atrás nesta sessão". Pra resolver o caso concreto que motivou
essa conversa (mensagem da AbacatePay que ele mandou e eu "esqueci"), o
grafo NÃO é a ferramenta certa — isso já existe via session_search (histórico
de sessões) e não precisa do grafo. O grafo serve pra "Lorran cita um tema
antigo (ex: firmware, eJPT, SHIELD) e eu lembro contexto relacionado sem
precisar reler tudo" — não substitui histórico de conversa recente.

## STATUS ATUAL (18/09, fim da sessão)
- Passo 1: NÃO iniciado — só diagnosticado com teste real.
- Passo 2: NÃO iniciado.
- Passo 3: já é verdade hoje, só falta comunicar claramente (feito nesta nota).

## AO RETOMAR: primeira coisa a fazer
1. Ler este arquivo.
2. Confirmar que sistema_nervoso.py e motor_conversa.py ainda existem e
   importam sem erro (`python3 core/sistema_nervoso.py --health-only`).
3. Implementar Passo 1, testar com sistema_nervoso.py antes/depois, commitar.
4. Só depois do Passo 1 provado funcionando, ir pro Passo 2 (hook automático).
