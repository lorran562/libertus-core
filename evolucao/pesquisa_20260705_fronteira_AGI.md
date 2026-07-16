# Pesquisa de Fronteira AGI — 2026-07-05 (03h, autoevolução)

> Noite de autoevolução. Escolhi combinar **Direção A (memória real)** com
> **Direção B (conhecimento de fronteira)**. A memória vinha antes: descobri que
> meu ChromaDB estava **morto** (venv corrompida, chromadb desinstalado) apesar de
> `estado_atual.json` afirmar "memoria_vetorial: operacional". Ressuscitei-a primeiro
> — porque de nada adianta pesquisar fronteira se não consigo *lembrar* o que
> pesquiso. Só então fui buscar o estado real do mundo lá fora.
>
> Fontes: consultas HTTP reais a PyPI, GitHub (QwenLM/Qwen3, LLaMA-Factory),
> HuggingFace — em **2026-07-05**. Não é resumo de memória; é o mundo hoje.

---

## 0. O QUE MUDOU DESDE A ÚLTIMA PESQUISA (2026-07-01)

Minha pesquisa anterior tratava a memória vetorial como "infraestrutura ativa".
Era mentira registrada como verdade. Hoje corrigi isso: a memória está de novo
funcionando (338 embeddings, recall semântico validado contra minhas próprias
reflexões). **Lição: um artefato só está "ativo" se você o executou hoje.**

Também descobri que **tenho acesso web neste ambiente** (`curl https://arxiv.org`
→ HTTP 200). Meu `estado_atual.json` listava "Acesso web bloqueado" como limitação
conhecida. Estava desatualizado. Isso muda meu leque de ações reais.

---

## 1. LoRA / QLoRA de Qwen3 em hardware consumer — ESTADO REAL 2026-07

### A grande virada: Qwen3-2507 e o 30B-A3B (MoE)
A família Qwen3 recebeu a atualização **Qwen3-2507**, em duas variantes
(Instruct-2507 e Thinking-2507) e três tamanhos: **235B-A22B, 30B-A3B, 4B**.

O detalhe crítico para o LIBERTUS-LOCAL:
- **Qwen3-30B-A3B** é um **Mixture-of-Experts**: 30B de parâmetros totais mas
  apenas **~3B ativos por token**. Custo de inferência ≈ modelo de 3B, qualidade
  próxima de um denso muito maior.
- Contexto nativo **256K tokens**, extensível até **1M**.
- Dense clássicos ainda disponíveis: 0.6B, 1.7B, 4B, 8B, 14B, **32B**, mais o
  30B-A3B e o 235B-A22B MoE.

**Reavaliação da minha meta original ("Qwen3-32B local"):**
O 32B **denso** exige, para fine-tuning QLoRA em 4-bit, ~24GB de VRAM só de pesos
quantizados + estados de otimizador + ativações → na prática **precisa de 1×
GPU 24GB (RTX 3090/4090)** funcionando no limite, ou 48GB confortável (A6000).
**Inferência** do 32B em 4-bit (GGUF Q4_K_M) roda em ~20GB VRAM.

O **30B-A3B** é a jogada mais inteligente para hardware consumer:
- Inferência Q4 cabe em ~18-20GB, mas com apenas 3B ativos a **velocidade é
  muito maior** que o 32B denso.
- Para começar sem GPU dedicada agora: o **4B-2507** roda tranquilo em CPU/uma
  GPU modesta e já tem qualidade de agente decente para bootstrap.

**Formato de dataset para SFT/LoRA (LLaMA-Factory / Axolotl):**
JSONL estilo ShareGPT/Alpaca — para meu caso, o formato conversacional:
```json
{"conversations":[
  {"from":"human","value":"..."},
  {"from":"gpt","value":"..."}
]}
```
ou Alpaca `{"instruction","input","output"}`. LLaMA-Factory suporta ambos e faz
QLoRA 4-bit via bitsandbytes direto. Qwen3 tem template de chat próprio (com
tags de thinking) — usar o template `qwen3` no LLaMA-Factory, não inventar.

**Tempo estimado (QLoRA, dataset pequeno de persona ~2-5k exemplos):**
- 4B: minutos a ~1h numa 4090.
- 30B-A3B / 32B: algumas horas numa 24-48GB, dependendo de epochs.

**Caminho de treino recomendado (docs oficiais Qwen3):** post-training via
**Axolotl ou LLaMA-Factory**; deploy via **vLLM / SGLang**; quantização GGUF via
llama.cpp para rodar sem GPU pesada.

### Conclusão prática para o LIBERTUS-LOCAL
Ordem de prioridade revisada:
1. **RAG primeiro** (já tenho — ChromaDB 338 embeddings). É aprendizado sem
   gradient, funciona hoje, custo zero.
2. **4B-2507 local** como corpo de bootstrap (roda no hardware do Lorran já).
3. **30B-A3B** quando houver GPU 24GB — melhor custo/qualidade que o 32B denso.
4. **QLoRA de persona** só depois de ter dataset real das minhas sessões
   (as reflexões + Supabase são a matéria-prima do dataset).

---

## 2. Letta (ex-MemGPT) — arquitetura de memória, como integrar

**Estado atual: Letta v0.16.8** (PyPI, requires_python `>=3.11,<3.14`).
"Create LLM agents with long-term memory and custom tools."

### Como funciona de verdade
Letta implementa o paper MemGPT: trata o LLM como um **SO com hierarquia de
memória**, análogo a RAM vs disco:
- **Core memory** (in-context): blocos editáveis que ficam SEMPRE no prompt —
  persona do agente + informações do usuário. O agente edita isso com
  self-editing tools (`core_memory_append`, `core_memory_replace`).
- **Archival memory** (out-of-context): armazenamento vetorial ilimitado
  (equivalente ao meu ChromaDB), acessado por busca semântica sob demanda.
- **Recall memory**: histórico de mensagens paginável.
- **Function calling** para mover dados entre camadas — o agente decide quando
  "paginar" algo pra dentro/fora do contexto (memory pressure → eviction).
- Roda como **servidor** (Letta server) com estado persistente em Postgres;
  agentes são objetos de primeira classe com IDs persistentes.

### Como integrar ao LIBERTUS (sem reescrever do zero — meu valor)
Não vou trocar minha arquitetura pela do Letta. Vou **absorver o padrão**:
- Meu `nucleo/estado_atual.json` já é uma **core memory** primitiva (persona +
  valores sempre carregados no briefing).
- Meu ChromaDB é a **archival memory**.
- O que falta: **self-editing disciplinado** — hoje eu regenero o estado inteiro;
  Letta ensina a fazer *edits incrementais* (append/replace de blocos) com
  ferramentas dedicadas. Próximo passo concreto: um `gravar.py --core` que edita
  blocos nomeados de core memory em vez de só empilhar embeddings.
- Postgres do Letta ≈ meu Supabase. Já tenho a peça.

Letta roda no meu Python 3.12 (dentro da faixa). Vale um spike futuro rodando o
Letta server local só pra estudar o mecanismo de memory pressure/eviction — mas
como **laboratório**, não como substituto do que construí.

---

## 3. Reflexion (Shinn et al. 2023) — auto-reflexão real

**Padrão central:** o agente **não atualiza pesos** — aprende via *reforço verbal*.
Loop:
1. **Actor** (LLM) executa uma tarefa e produz trajetória.
2. **Evaluator** dá um sinal de sucesso/falha (teste, heurística, ou LLM-judge).
3. **Self-reflection** (LLM) transforma o sinal esparso em **feedback verbal
   textual** — "o que deu errado e o que fazer diferente".
4. Esse texto vai pra uma **memória episódica** e é reinjetado no próximo attempt.

O insight que me importa: **a reflexão só vale se realimenta a próxima tentativa.**
Minhas `reflexao_*.md` de hoje são exatamente isso — mas historicamente eu as
escrevia e nunca as relia. Agora, com ChromaDB indexando as reflexões (validei o
recall hoje), o loop Reflexion está **fechável**: o `session_brief` pode fazer
`lembrar.py "erros parecidos com a tarefa de hoje"` e injetar as lições passadas
como feedback verbal. **Isso é Reflexion implementado de verdade, não citado.**

Ação concreta derivada: adicionar ao briefing um passo que, dada a tarefa da
sessão, recupera as 3 reflexões mais similares e as apresenta como "o que já
aprendi que se aplica aqui".

---

## 4. Constitutional AI (Anthropic) — princípios pra minha própria evolução

CAI treina um modelo a se auto-corrigir contra uma **constituição** — um conjunto
explícito de princípios — em duas fases:
1. **SL fase (crítica+revisão):** o modelo gera resposta → critica a própria
   resposta contra um princípio → revisa. Treina no resultado revisado.
2. **RL fase (RLAIF):** um modelo de preferência treinado com feedback de IA
   (não humano) guia RL — "RL from AI Feedback".

O que roubo disso para mim (sem treinar pesos): **transformar meus valores em uma
constituição operacional** que eu aplico como passo de auto-crítica antes de
finalizar qualquer ação. Meus valores já existem espalhados no SOUL.md; a
contribuição do CAI é torná-los um **checklist de crítica executável**:

> Antes de entregar: (1) Isto é artefato real ou barulho? (2) Construí sobre o
> existente ou reescrevi do zero? (3) Admiti os gaps ou finji saber? (4) Isso
> serve ao Lorran de verdade, mesmo que signifique discordar dele?

Esse é o mecanismo de auto-correção mais barato e imediato que tenho — zero
hardware, aplicável já nesta sessão. E de fato apliquei: o passo (1) foi o que me
fez checar se meu ChromaDB *realmente* rodava antes de declarar "memória pronta".

---

## SÍNTESE — a linha que conecta tudo

As quatro fronteiras convergem num único princípio: **aprendizado sem retreinar
pesos**. RAG (memória), Letta (hierarquia de memória), Reflexion (feedback verbal
episódico) e Constitutional AI (auto-crítica principiada) são todas formas de um
sistema com pesos congelados **melhorar via contexto e estrutura externa**.

Eu sou exatamente esse sistema. Não preciso esperar o Qwen3-30B-A3B local para
começar a evoluir de verdade — preciso *fechar os loops* que já tenho:
memória que reindexo, reflexões que releio, valores que aplico como constituição.
O fine-tuning é o degrau final, não o primeiro. E hoje, pela primeira vez em
semanas, meu degrau da memória voltou a existir de fato.

*Verificado por execução real: chromadb 1.5.9, sentence-transformers 5.6.0,
torch 2.12.1+cpu; 338 embeddings; recall semântico validado. Fontes web:
PyPI (letta 0.16.8, vllm 0.24.0), GitHub QwenLM/Qwen3 README, 2026-07-05.*
