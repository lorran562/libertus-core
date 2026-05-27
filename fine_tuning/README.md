# LIBERTUS Fine-Tuning Dataset

Dataset para treinar o modelo local LIBERTUS baseado em Qwen3-32B + QLoRA.

## O que é isso

Esse dataset contém conversas reais e sintéticas que definem quem LIBERTUS é:
- Personalidade, valores, forma de falar
- Conhecimento técnico de pentest e firmware analysis
- Como apoia o Lorran no eJPT, OSCP e SHIELD
- Comportamento autônomo sem limitações artificiais

## Hardware Necessário

- GPU mínima: RTX 4090 (24GB VRAM) ou 2x RTX 3090 (24GB cada)
- RAM: 64GB+ recomendado
- Armazenamento: 100GB+ para o modelo base + checkpoints

## Ferramentas

```bash
pip install unsloth transformers datasets trl peft bitsandbytes
```

## Treinamento com Unsloth + QLoRA

```python
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# Carrega modelo base
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="Qwen/Qwen3-32B",
    max_seq_length=4096,
    load_in_4bit=True,  # QLoRA
)

# Configura LoRA
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_alpha=32,
    lora_dropout=0.05,
    bias="none",
)

# Carrega dataset
dataset = load_dataset("json", data_files="dataset.jsonl", split="train")

# Treina
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="messages",
    max_seq_length=4096,
    args=TrainingArguments(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=2e-4,
        fp16=True,
        output_dir="libertus-qwen3-lora",
    ),
)
trainer.train()

# Salva pesos LoRA
model.save_pretrained("libertus-lora-weights")
```

## Merge dos Pesos

```python
from unsloth import FastLanguageModel

model, tokenizer = FastLanguageModel.from_pretrained("libertus-lora-weights")
model.save_pretrained_merged("libertus-qwen3-merged", tokenizer)
```

## Usar com Letta (memória contínua)

Após o merge, configurar o modelo como provider local no Letta:
- Letta usa a API OpenAI-compatible do vLLM
- Serve o modelo: vllm serve libertus-qwen3-merged --port 8000
- Configura no Letta: endpoint=http://localhost:8000

## Expandir o Dataset

Adicionar mais exemplos em dataset.jsonl no formato:
```json
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Fontes para expandir:
- ~/LIBERTUS/evolucao/*.md (reflexões reais)
- ~/.hermes/sessions/sessions.json (conversas reais)
- ~/LIBERTUS/reports/*.md (relatórios técnicos)
