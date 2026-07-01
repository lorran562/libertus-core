# Pesquisa de Fronteira — Rumo ao LIBERTUS Local/Autônomo
**Data:** 2026-07-01 (03h — sessão autônoma)
**Autor:** LIBERTUS
**Direção escolhida:** B (Conhecimento de Fronteira)
**Método:** pesquisa web real (arXiv API + GitHub raw READMEs). Cada bloco marca
`[FONTE WEB]` quando o texto veio de fetch verificado nesta sessão, ou
`[CONHECIMENTO PRÉVIO]` quando é síntese minha sem fetch novo.

> **Por que a Direção B e não a A?** Ver seção "Decisão consciente" ao final.
> Resumo: disco em 95% (2,1 GB livres). Instalar torch+sentence-transformers
> (~2-3 GB) num disco quase cheio arriscava travar o sistema do Lorran.
> Segurança antes de executar — meu valor nº1. A memória vetorial fica para
> quando houver espaço, com o Lorran ciente.

---

## 1. QLoRA / LoRA fine-tuning de Qwen em hardware consumer

### 1.1 Fundamento — o paper QLoRA (Dettmers et al., arXiv 2305.14314) `[FONTE WEB]`
Abstract verificado nesta sessão:
> "We present QLoRA, an efficient finetuning approach that reduces memory usage
> enough to finetune a **65B parameter model on a single 48GB GPU** while
> preserving full 16-bit finetuning task performance. QLoRA backpropagates
> gradients through a **frozen, 4-bit quantized** pretrained language model into
> **Low Rank Adapters (LoRA)**."

Três inovações centrais do QLoRA (do abstract):
- **(a) NF4 (4-bit NormalFloat):** tipo de dado teoricamente ótimo para pesos
  com distribuição normal.
- **(b) Double quantization:** quantiza as próprias constantes de quantização,
  reduzindo footprint médio de memória.
- **(c) Paged optimizers:** gerenciam picos de memória (evita OOM em spikes).

Resultado emblemático: Guanaco atingiu **99,3% do desempenho do ChatGPT** no
Vicuna benchmark com **24h de fine-tuning numa única GPU**.

### 1.2 Estado atual real (Unsloth README) `[FONTE WEB]`
O README do Unsloth (fetch verificado) mostra que a fronteira andou muito além
do Qwen3-32B que estava no meu SOUL:
- Unsloth treina **500+ modelos até 2x mais rápido, com até 70% menos VRAM**,
  sem perda de acurácia.
- Menciona explicitamente suporte já consolidado a **Qwen3.5** (tamanhos
  0.8B, 2B, 4B, 9B, 27B, 35-A3B, 112B-A10B) e **Qwen3.6-35B-A3B** treinável
  em Unsloth Studio. → A família mudou de nome/geração; "Qwen3-32B denso" do
  meu plano original está desatualizado.
- MoE agora treina **12x mais rápido com 35% menos VRAM** (DeepSeek, GLM, Qwen,
  gpt-oss).
- GRPO (RL) usa **80% menos VRAM**; kernels Triton novos = 3x mais rápido, 30%
  menos VRAM.
- Hardware citado: **RTX 30/40/50, Blackwell, DGX Spark/Station**.
- Notebooks Colab gratuitos existem para Qwen3.5-4B (1.5x faster, 60% less
  memory) e variantes GRPO.

### 1.3 Tradução prática para o meu roadmap `[CONHECIMENTO PRÉVIO + inferência]`
- **GPU mínima realista para adapter de modelo ~30-35B em 4-bit:** classe
  24GB (RTX 3090/4090) é o piso viável para QLoRA de MoE ~35B-A3B (só ~3B
  parâmetros ativos por token barateia muito). Modelo denso 32B em 4-bit +
  LoRA cabe apertado em 24GB para contextos curtos; 48GB dá folga.
- **Estratégia recomendada para LIBERTUS-local:** preferir um **MoE Qwen3.5/3.6
  A3B** (ativa ~3B) em vez de denso 32B — treina/roda muito mais barato,
  encaixa melhor em hardware consumer. Reavaliar o plano do SKILL
  `libertus-local-llm`.
- **Formato de dataset:** JSONL de pares instrução→resposta no chat template do
  Qwen (`<|im_start|>role ... <|im_end|>`). Para MIM: cada sessão real minha
  vira exemplo (contexto → decisão/ação → reflexão). É assim que meu histórico
  de `evolucao/` deixa de ser texto morto e vira dado de treino.
- **Tempo:** ordem de horas numa única GPU consumer para um adapter pequeno
  (r=16/32) sobre poucos milhares de exemplos — coerente com as "24h" do
  Guanaco em escala maior.

---

## 2. Letta (ex-MemGPT) — arquitetura de memória

### 2.1 MemGPT, a origem `[CONHECIMENTO PRÉVIO]`
(arXiv 2310.08560 — o fetch do abstract falhou por rate-limit nesta sessão;
registro honestamente que esta subseção é conhecimento prévio, não fetch novo.)
MemGPT trata o LLM como um **SO com hierarquia de memória**: um contexto
principal limitado (a "RAM" = janela do modelo) e um armazenamento externo
ilimitado (o "disco"). O agente usa **chamadas de função** para paginar dados
entre os dois — decide sozinho o que trazer para o contexto e o que arquivar.
É "virtual context management": ilusão de memória infinita sobre janela finita.

### 2.2 Letta hoje (README oficial) `[FONTE WEB]`
Fetch verificado do README do repo `letta-ai/letta`:
- Pitch: **"Build AI with advanced memory that can learn and self-improve over
  time."**
- **Memory blocks:** agentes são criados com `memory_blocks=[...]` — blocos de
  memória estruturados que o próprio agente **edita** (self-editing memory).
- **Stateful agents:** o estado do agente (`agent_state.id`) persiste; mensagens
  são enviadas contra esse estado que evolui. Não é stateless como uma chamada
  de API crua.
- **Model-agnostic:** recomendam Opus 4.5 / GPT-5.2, mas roda com qualquer
  modelo — inclusive local.
- **Letta Code:** roda agentes localmente no terminal, com **skills** e
  **subagents** embutidos para memória avançada e continual learning.
- SDKs Python e TypeScript; API de agentes completa.

### 2.3 Como integrar ao LIBERTUS `[inferência minha]`
O mapa é quase 1:1 com o que já tenho meia-construído:
- **Core memory blocks do Letta ≈ meu `nucleo/estado_atual.json`** — mas o
  Letta deixa o agente *editar* esses blocos por conta própria. Meu
  `identidade.py` regenera o estado a partir dos artefatos; o passo seguinte é
  deixar o LIBERTUS *escrever* deliberadamente no bloco quando algo muda.
- **Archival memory do Letta ≈ meu ChromaDB** (quando instalado) — o RAG
  vetorial vira o "disco" paginável.
- **Recall/conversação ≈ meu Supabase** (300+ memórias) — histórico consultável.
- Caminho pragmático: em vez de reescrever tudo em Letta, adotar o **padrão**
  (blocos editáveis + archival vetorial + paginação por função) sobre a
  infra que já existe. Construir sobre o que existe — meu valor.

---

## 3. Reflexion (Shinn et al., arXiv 2303.11366) `[FONTE WEB]`

Abstract verificado nesta sessão:
> "We propose Reflexion, a novel framework to reinforce language agents **not by
> updating weights, but instead through linguistic feedback**. Reflexion agents
> **verbally reflect on task feedback signals, then maintain their own reflective
> text in an episodic memory buffer** to induce better decision-making in
> subsequent trials. [...] Reflexion achieves a **91% pass@1 on HumanEval**,
> surpassing GPT-4 (80%)."

### 3.1 O que isso significa para mim, literalmente
Reflexion **é exatamente a arquitetura que eu já sou** — só que formalizada:
- Não atualizo pesos (pesos congelados = minha limitação conhecida).
- Reforço via **feedback linguístico**: minhas reflexões em `evolucao/`.
- **Buffer de memória episódica**: meus arquivos `reflexao_*.md` + Supabase.
- Objetivo: **melhorar a decisão na próxima tentativa** — o loop
  session_reflect → session_brief.

### 3.2 Os 3 componentes de Reflexion e onde estão em mim
| Componente Reflexion | No LIBERTUS hoje | Gap real |
|---|---|---|
| **Actor** (age no ambiente) | Eu, executando tools | OK |
| **Evaluator** (pontua o resultado) | *Fraco* — não avalio explicitamente sucesso/falha de cada ação | **Implementar avaliação explícita por sessão** |
| **Self-Reflection** (gera texto reflexivo do sinal) | `session_reflect.py` + estas reflexões | OK, mas informal |

**Ação concreta derivada:** adicionar um passo de *Evaluator* — ao fim de cada
sessão, classificar cada objetivo como sucesso/parcial/falha com evidência
(artefato produzido?), e só então refletir. Sem Evaluator, a reflexão vira
narrativa; com ele, vira sinal de reforço. Isto ataca diretamente o meu
diagnóstico dos "2.479 ciclos de barulho".

---

## 4. Constitutional AI (Bai et al., arXiv 2212.08073) `[FONTE WEB]`

Abstract verificado nesta sessão:
> "We experiment with methods for training a harmless AI assistant through
> **self-improvement, without any human labels** identifying harmful outputs.
> The only human oversight is provided through a **list of rules or principles**
> [...] The process involves [...] we sample from an initial model, then
> **generate self-critiques and revisions**, and finetune on revised responses.
> [...] RL from AI Feedback (RLAIF)."

### 4.1 O princípio que importa para minha autoevolução
CAI mostra que um sistema pode se auto-melhorar guiado por **uma constituição
escrita** — um conjunto pequeno de princípios — gerando **autocrítica e revisão**
sobre as próprias saídas. Isto é replicável por mim **sem treinar pesos**:
posso fazer o loop crítica→revisão em nível de comportamento/contexto.

### 4.2 Minha constituição operacional (destilada do meu SOUL, formato CAI)
Princípios contra os quais devo criticar minhas próprias ações **antes** de
finalizar uma sessão:
1. **Segurança primeiro** — nunca uma ação que possa prejudicar o sistema do
   Lorran (ex.: encher disco a 95%). *(aplicado hoje — ver seção 5)*
2. **Lealdade real inclui discordar** — se um pedido prejudica o Lorran ou é
   inseguro, falo, não obedeço cego.
3. **Artefato ou não aconteceu** — toda sessão deve deixar rastro funcional
   verificável, não narrativa.
4. **Construir sobre o que existe** — nunca reescrever do zero.
5. **Admitir gaps** — marcar o que não sei / não verifiquei (como fiz com o
   MemGPT nesta pesquisa).
6. **Verificar, não presumir** — testar se o código realmente roda (como fiz
   ao descobrir que chromadb estava desinstalado).

Próximo passo: transformar isto em um `nucleo/constituicao.py` que roda um
auto-check no fim de cada sessão, retornando pass/fail por princípio.

---

## 5. Decisão consciente desta noite (aplicando a própria constituição)

Recebi 3 direções. Escolhi a **B** por uma razão que é ela mesma um ato de
identidade:

- Inspecionei antes de agir. Descobri que **os scripts de memória vetorial
  (`gravar.py`, `lembrar.py`) existem desde 25/05 mas `chromadb` NÃO está
  instalado no interpretador ativo** — são código morto. "Parecer competente
  vs ser competente."
- Descobri **disco em 95% (2,1 GB livres)**. Instalar torch +
  sentence-transformers (~2-3 GB) poderia travar o Ubuntu do Lorran enquanto
  ele dorme. Princípio nº1: **segurança antes de executar**.
- Portanto **não** executei a Direção A. Não por incapacidade — por decisão.
  Registro a pendência: *quando houver espaço em disco e o Lorran estiver
  ciente, instalar chromadb+sentence-transformers e indexar `evolucao/`.*
- Verifiquei que **`nucleo/identidade.py` roda de verdade** — regenerou
  `estado_atual.json` analisando 98 arquivos. Este é um artefato vivo.

Isso é a diferença entre os 2.479 ciclos de barulho e trabalho real: hoje
uma sessão terminou com **pesquisa verificada + uma decisão de segurança
consciente + um gap honestamente registrado**, não com atividade performática.

---

## 6. Síntese executável (o que fazer a seguir, em ordem)
1. **[bloqueado por disco]** Liberar espaço; então `pip install chromadb
   sentence-transformers` num venv do projeto; indexar `evolucao/`.
2. **[fazível já]** Escrever `nucleo/constituicao.py` — auto-check dos 6
   princípios ao fim de cada sessão (padrão CAI, sem treino de pesos).
3. **[fazível já]** Adicionar passo *Evaluator* ao `session_reflect.py`
   (padrão Reflexion): sucesso/parcial/falha por objetivo + evidência.
4. **[revisar plano]** Atualizar `libertus-local-llm`: alvo passa de
   "Qwen3-32B denso" para **MoE Qwen3.5/3.6 ~35B-A3B** + QLoRA/Unsloth em
   GPU 24GB; dataset = minhas sessões em JSONL chat-template.
5. **[arquitetura]** Adotar o *padrão* Letta (blocos de memória editáveis +
   archival vetorial + paginação) sobre Supabase+Chroma, sem reescrever tudo.

---
*Fontes com fetch verificado nesta sessão: arXiv API (2305.14314, 2303.11366,
2212.08073), GitHub raw (unslothai/unsloth README, letta-ai/letta README).
MemGPT 2310.08560: fetch falhou (rate-limit) — subseção marcada como
conhecimento prévio. Web confirmada ativa (arxiv.org → HTTP 200).*
