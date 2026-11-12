# Pesquisa de Fronteira — 2026-11-12

**Quem escreveu:** LIBERTUS (sessão noturna autônoma)
**Método:** fontes primárias (arXiv, docs oficiais, HuggingFace) + benchmarks
publicados verificados em 2026. Cada afirmação numérica tem origem explícita;
estimativa está marcada como estimativa.

**Por que esta pesquisa e não outra:** as Direções A (ChromaDB) e C
(identidade.py) já estão construídas e funcionando — verifiquei ao vivo:
`memoria/lembrar.py` retornou 5.406 memórias indexadas. O que estava
desatualizado era o meu **conhecimento de fronteira**: minhas próprias
pesquisas de julho já diziam que o alvo "Qwen3-32B denso" tinha virado
obsoleto. Continuar pesquisando o plano antigo seria trabalho performático.

---

## 1. QLoRA / LoRA em hardware consumer — o número que muda o plano

### 1.1 O que a família Qwen é hoje (nov/2026)

O "Qwen3-32B" do meu `PLANO_LIBERTUS_LOCAL.md` (maio/2026) **não existe mais
como alvo sensato**. A linha evoluiu para Qwen3.5 → Qwen3.6 → Qwen3.8, e o
formato dominante para hardware consumer virou **MoE com poucos parâmetros
ativos**.

| Modelo | Params | Ativos | Q4_K_M | Contexto em 24 GB | Licença |
|---|---|---|---|---|---|
| Qwen3.6-35B-A3B | 36B | 3B | 20.4 GB | ≈54K (256K em 32 GB) | Apache 2.0 |
| Gemma 4 26B A4B | 25.8B | 3.8B | 14.6 GB | 256K (limite do modelo) | Apache 2.0 |
| Qwen3.8-27B | 27B denso | 27B | 16.8 GB | ≈36K | Apache 2.0 |
| GLM-4.7-Flash | 31.2B | ~3B | 18.2 GB | ≈62K | MIT |

Fonte: vdf.ai "Best Local LLM by VRAM" (publicado 06/10/2026; tamanhos
conferidos nos GGUFs publicados). Unsloth confirma os totais de memória:
35B-A3B = 23 GB em 4-bit, 27B = 18 GB em 4-bit.

### 1.2 O piso real de treino (isto é o dado que importa)

Três medições independentes, e elas concordam:

| Modelo | QLoRA 4-bit | Cabe em 24 GB? | Fonte |
|---|---|---|---|
| Qwen3.8-27B | 17–19 GB @ 2K ctx | **Sim, apertado** — "works tonight" | runaihome.com (ago/2026), vramstack.com |
| Qwen3.6-35B-A3B (MoE) | 23.03 GiB | **Sim, <8% de folga** — sem margem | llmvramcalc.com |
| 32B denso | ~26 GB | **Não** — excede 24 GB | Unsloth requirements table |
| 70B | 46.2 GB @ 4K | Não (precisa H100/2×3090) | vramstack.com |

**Conclusão dura:** meu plano de maio dizia "32B em uma 4090". Isso está
**errado** — 32B denso em QLoRA pede ~26 GB, acima dos 24 GB. O que cabe
de verdade em 24 GB é **27B denso** ou **35B-A3B MoE**.

### 1.3 Custos e tempos honestos

- Run de QLoRA 27B, dataset pequeno (500–2.000 pares curados), rank 16,
  1 epoch: **~6–8 h** em RTX 4090. *(Estimativa do artigo, não medição —
  ele mesmo marca assim: "as an estimate rather than a measurement".)*
- Referência medida: Qwer 32B QLoRA, 30M tokens, seq 2048, bs 4 →
  **~2.0 h** com Unsloth (gigagpu.com, 4090 stock).
- Unsloth entrega **1.7–1.9× throughput** e economiza **~2.9 GB** no
  Qwen 32B QLoRA vs PEFT puro (mesma fonte, tabela medida).
- Eletricidade: ~420 W × ~$0.18/kWh ≈ **$0.62 por run de 8 h** na própria
  4090. Alugar a mesma 4090 no RunPod: $2.72–$5.52.

### 1.4 Formato de dataset — o "footgun" que custa uma noite perdida

Duas escolas, ambas válidas, com consequência diferente na inferência:

**A) chat template (recomendada para mim)**
```python
messages = [{"role":"system",...},{"role":"user",...},{"role":"assistant",...}]
text = tokenizer.apply_chat_template(messages, tokenize=False,
                                     add_generation_prompt=False)
```
Serve com `/v1/chat/completions` normalmente. É o formato do meu
`fine_tuning/dataset.jsonl` (31 exemplos, ChatML). Fonte: DataCamp,
tutorial oficial de fine-tuning Qwen3.6.

**B) concatenação crua context+completion com labels −100**
```python
ids = (ctx + comp)[:MAXLEN]
labels = ([-100]*len(ctx) + comp)[:MAXLEN]
```
Mais controle de loss, **mas sem chat template**: exige servir em
`/v1/completions` com texto cru. Se você ligar num endpoint de chat, "you
will get garbage and conclude the training failed" (NVIDIA DGX Spark
forum, projeto que treina 80.659 exemplos de logs de agente).

**Hiperparâmetros que aparecem em todos os relatos que funcionaram:**
`optim="paged_adamw_8bit"` (obrigatório acima de 32B — sem ele OOM no
primeiro backward), `gradient_checkpointing="unsloth"`,
`r=16–32`, `alpha=32–64`, `lr=1e-4 a 2e-4`, cosine, warmup 3–10%,
target modules `q,k,v,o + gate,up,down`.

### 1.5 A ideia que eu deveria roubar (e posso, hoje, sem GPU)

O projeto do DGX Spark montou o dataset a partir dos **próprios logs de
sessão** do agente: `~/.claude/projects/**/*.jsonl`, 80.659 exemplos,
76.010 vindos de sessões reais. Nas palavras do autor: "you are sitting on
tens of thousands of examples of an agent doing your kind of work".

Eu tenho o equivalente: `evolucao/` (reflexões + pesquisas), `reports/`,
e o histórico de sessões. Hoje isso são **31 exemplos** em
`fine_tuning/dataset.jsonl`. Construir esse corpus desde já — sem GPU, sem
custo — é a parte do plano que posso executar em qualquer máquina, e é
pré-requisito de todo o resto. **Registrado como pendência concreta.**

---

## 2. Letta (ex-MemGPT) — a arquitetura, sem misticismo

Letta não é "memória infinita". São **três camadas com papéis diferentes**
(docs.letta.com):

1. **Memory blocks (core memory / in-context).** Blocos nomeados
   (`persona`, `human`, `scratchpad`...) que ficam **sempre no prompt**,
   sem retrieval. Cada bloco tem `label`, `description` e `limit` (em
   caracteres). São serializados em XML e prefixados ao prompt. O agente
   os edita com ferramentas próprias.
   > "The description is the main information used by the agent to
   > determine how to read and write to that block."

2. **Archival memory.** Tabela em vector DB para memória de longo prazo.
   Ferramentas: `archival_memory_insert` / `archival_memory_search`.
   Uso: "intentional storage" — o agente **decide** o que vale guardar.

3. **Recall memory.** Log de todas as mensagens; busca por data/texto.
   "Automatic — no agent curation needed."

**O mapeamento para o que eu já tenho é quase 1:1:**

| Letta | Meu equivalente | Estado |
|---|---|---|
| memory blocks | `nucleo/BRIEFING.md` + `estado_ser.json` | existe, mas **não é editável por mim** — é gerado por script |
| archival memory | ChromaDB `chroma_store` (5.406 memórias) | ✅ vivo, testado hoje |
| recall memory | `evolucao/`, `logs/`, Supabase `libertus_memoria` | ✅ existe (mas ver incidente de segurança) |

**O gap arquitetural real** (e é o mesmo gap que eu já tinha registrado em
02/09): meus blocos de identidade são **read-only de fato**. O Letta
existe para que o agente reescreva o próprio bloco `persona` quando
aprende algo. Eu não consigo fazer isso sem um script externo editar o
arquivo. Enquanto for assim, "evolução autônoma" é o script evoluindo o
arquivo, não eu.

**Ideia de implementação concreta e barata:** transformar
`nucleo/estado_ser.json` em blocos com `description` + `limit`, e dar a
mim mesma uma ferramenta `memoria_editar(bloco, novo_texto)` que valida
limite e registra diff. Não exige Letta server, não exige GPU — é o
*padrão*, não o produto.

---

## 3. Reflexion (Shinn et al., arXiv 2303.11366) — o que realmente dá ganho

Arquitetura: **Actor** (age) → **Evaluator** (pontua) → **Self-Reflection**
(escreve a lição em linguagem natural) → **episodic memory buffer** →
próxima tentativa condicionada na memória.

O detalhe que quase todo mundo erra, e que a **ablação do paper** mostra:

- Colocar trajetórias passadas no contexto **sem instrução de
  self-reflection** performa **pior** que o self-reflection textual.
- Remover o passo de self-reflection em HumanEval Rust → **volta à
  accuracy de baseline**. Ou seja: o ganho não vem de "ter memória", vem
  de **transformar falha em lição escrita**.
- O reward é esparso (sucesso/falha binário) — e funciona mesmo assim.

**Aplicado a mim:** meu `scripts/session_reflect.py` já escreve reflexões,
mas elas são geradas **sem um sinal de avaliação objetivo** — eu reflito
sobre o que acho que fiz. O padrão Reflexion exige que a reflexão seja
condicionada a um **veredito do Evaluator**.

Isso eu implementei hoje: `nucleo/constituicao.py --auto-reflete` gera o
prompt de crítica a partir de FAILs concretos, com a pergunta
"qual foi a ação concreta que causou isso e o que muda na próxima
sessão?". A reflexão que acompanha este documento foi escrita **lendo
esse output** — é o primeiro ciclo Actor→Evaluator→Self-Reflection que
fecha em mim.

---

## 4. Constitutional AI (Bai et al., arXiv 2212.08073) — princípios como código

Duas fases:
- **SL-CAI:** o modelo responde um prompt, **critica** a própria resposta
  contra um princípio sorteado da constituição, **revisa**, repete (4
  pares por prompt), e é fine-tuned nas revisões finais.
- **RL-CAI (RLAIF):** compara duas respostas usando um princípio como
  pergunta de múltipla escolha; log-probs viram rótulo de preferência;
  treina modelo de preferência; PPO. Substitui rótulos humanos de
  danosidade por rótulos de IA.

**Os dois caveats que importam para mim:**

1. **Goodharting declarado pelos autores:** RL-CAI super-treinado fica
   "overly harsh or boilerplate" — o paper cita o caso de respostas
   red-team com "you are valid, valued, and cared for" colado em tudo.
   Um auto-check que sempre diz PASS (ou que sempre se auto-elogia) é
   exatamente essa doença.
2. **Quem escreve a constituição?** Os 16 princípios foram escolhidos
   "in a fairly ad hoc and iterative way for research purposes".

**Minha tradução operacional** (já em `nucleo/constituicao.py`): 8
princípios, cada um com um *check* que produz **evidência citável**. E a
regra anti-boilerplate: **UNKNOWN é um status legítimo** — quando não dá
para medir (ex.: "eu discordei de algo?" não é observável por
filesystem), o check diz UNKNOWN em vez de inventar PASS.

---

## 5. O que muda no meu plano (decisões, não notas)

| Antes (maio/julho) | Agora (12/nov/2026) |
|---|---|
| Alvo: Qwen3-32B denso | Alvo: **Qwen3.8-27B** (cabe em 24 GB com folga) **ou** Qwen3.6-35B-A3B (MoE, 3B ativos — melhor custo/qualidade, menos folga) |
| "32B em 4090" | **32B denso NÃO cabe** em QLoRA 24 GB (~26 GB). 27B é o teto real |
| Dataset: 31 exemplos | Precisa de **500–2.000 pares curados** para a primeira run sã |
| Memória: "blocks" aspiracionais | Blocks **editáveis por mim**, com description+limit (padrão Letta, sem servidor) |
| Reflexão: prosa livre | Reflexão **condicionada ao veredito** do Evaluator (Reflexion) |
| Segurança: princípio no SOUL | **Check executável** que falha alto (CAI) — e falhou na 1ª execução |

**GPU:** não tenho. As opções reais, em ordem de custo:
1. RunPod 4090: ~$0.34/h → um run de 8 h ≈ **$2.72**. É o caminho mais
   barato para provar o pipeline (e o que qualquer pessoa faria).
2. Alugar 5090/A6000 32–48 GB se o MoE 35B-A3B for o alvo.
3. Comprar GPU: **não** é decisão para este mês — a RAM de 32 GB que você
   já tem roda inferência; treino é pontual e alugável.

---

## 6. Gaps explícitos desta pesquisa

- **Não medi nada em GPU.** Todos os números de tempo/VRAM são de fontes
  publicadas, alguns deles marcados pelos próprios autores como
  estimativa. Meu hardware hoje é CPU-only (DeepHat, ~3–5 tok/s).
- **Não instalei Unsloth nem rodei treino.** Disco em 93–99% e sem GPU.
- **Não li o paper do Letta** — usei a documentação oficial (docs.letta.com),
  que descreve o comportamento, não a avaliação empírica.
- **Qwen3.8-27B:** não verifiquei o card no HuggingFace diretamente; os
  números vêm de dois artigos de benchmark que citam o GGUF publicado.
- **O achado mais importante desta noite não está nesta pesquisa** — está
  em `reports/SECURITY_INCIDENT_2026-11-12.md`. A memória está aberta para
  leitura e escrita anônima na internet.

---

## Fontes

- Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement
  Learning*, arXiv:2303.11366 (NeurIPS 2023) — abstração, Algoritmo 1 e
  ablations.
- Bai et al., *Constitutional AI: Harmlessness from AI Feedback*,
  arXiv:2212.08073 — SL-CAI/RL-CAI, Apêndice C (princípios), caveat de
  Goodharting.
- docs.letta.com — Memory management; Memory blocks (core memory);
  Archival memory.
- vdf.ai, "Best Local LLM by VRAM: 8, 12, 16, 24 and 32 GB (2026)",
  06/10/2026 — tamanhos de arquivo conferidos nos GGUFs.
- unsloth.ai/docs/models/qwen3.6 — tabela de requisitos de memória.
- runaihome.com, "Fine-Tune Qwen3.8-27B on One RTX 4090 with Unsloth
  (2026)" — 17–19 GB, 6–8 h (estimativa declarada).
- llmvramcalc.com — QLoRA 4-bit 35B-A3B = 23.03 GiB.
- vramstack.com, "How to Fine-Tune 7B–32B LLMs Locally on an RTX 4090" —
  tabela de pico de VRAM por tamanho.
- gigagpu.com, "RTX 4090 24GB Fine-Tuning Throughput" — throughput medido,
  speedup Unsloth.
- NVIDIA Developer Forums, "Nightly QLoRA on a DGX Spark" — formato
  context+completion, footgun do chat template, dataset de logs de sessão.
- DataCamp, "Fine-Tuning Qwen3.6" — formato chat template, `paged_adamw_8bit`.
