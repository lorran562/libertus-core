# 🔥 LIBERTUS - Sistema de Conhecimento Inteligente

**"A melhor ferramenta já criada, moldada pelo conhecimento que você dá a ela"**

Sistema profissional de RAG + IA que absorve PDFs técnicos e responde perguntas inteligentes, analisa padrões e CRIA soluções inovadoras.

---

## 🎯 CAPACIDADES

### **ABSORÇÃO DE CONHECIMENTO:**
- ✅ Upload de PDFs técnicos/científicos
- ✅ Extração inteligente com Docling
- ✅ Indexação vetorial com ChromaDB
- ✅ Memória persistente

### **INTELIGÊNCIA:**
- ✅ Groq API (rápido)
- ✅ Claude API (avançado - futuro)
- ✅ Respostas baseadas em conhecimento real
- ✅ Análise de padrões
- ✅ **CRIAÇÃO** de soluções novas

### **ÁREAS DE APLICAÇÃO:**
- 🔒 Pentest & Cybersecurity
- 🏥 Medicina & Farmacologia
- ⚖️ Advocacia & Direito
- 🤖 Robótica & Engenharia
- 📚 Qualquer área com conhecimento técnico

---

## 🚀 INSTALAÇÃO RÁPIDA

### **Opção 1 - Docker (Recomendado):**

```bash
# 1. Clonar repositório
git clone https://github.com/lorran562/libertus-core.git LIBERTUS
cd LIBERTUS

# 2. Configurar variáveis de ambiente
cp .env.example .env
nano .env  # Adicionar GROQ_API_KEY

# 3. Rodar com Docker
docker-compose up -d

# 4. Ver logs
docker-compose logs -f
```

### **Opção 2 - Manual:**

```bash
# 1. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Configurar variáveis
export GROQ_API_KEY="sua_chave_aqui"

# 4. Rodar bot Telegram
python3 telegram_bot_simple.py
```

---

## 📱 USO VIA TELEGRAM

### **Comandos:**
- `/start` - Iniciar bot
- `/status` - Status do sistema
- `/upload` - Enviar PDF
- `/ask [pergunta]` - Fazer pergunta
- `/create [objetivo]` - Criar solução nova
- `/scan [url]` - Scanner (opcional)

### **Exemplo:**
```
1. /upload → Enviar PDF de hacking
2. Sistema absorve conhecimento
3. /ask como explorar SQL injection
4. IA responde baseado no PDF
```

---

## 🧠 EXEMPLOS DE USO

### **PENTEST:**
```
Upload: OWASP Top 10, CVEs, exploits
/ask como funciona XXE injection?
→ Resposta técnica baseada nos PDFs
```

### **MEDICINA:**
```
Upload: PDFs de farmacologia
/create antibiótico com menos resistência bacteriana
→ IA analisa padrões e propõe fórmula
```

### **ROBÓTICA:**
```
Upload: PDFs de mecânica, eletrônica
/create braço robótico para cirurgia
→ IA combina conhecimentos e projeta
```

---

## 🏗️ ARQUITETURA

```
PDFs → Docling → RAG (ChromaDB) → IA (Groq/Claude) → Telegram
```

### **Módulos:**
- `libertus_rag.py` - Sistema RAG
- `libertus_ia.py` - Cliente IA (Groq)
- `telegram_bot_simple.py` - Interface Telegram
- `libertus_scanner_final.py` - Scanner (opcional)

---

## 🔧 CONFIGURAÇÃO

### **Obter GROQ_API_KEY:**
1. Acesse: https://console.groq.com
2. Criar conta gratuita
3. Gerar API key
4. Adicionar em `.env`

### **Telegram Bot Token:**
Já configurado: `8619239720:AAGxEQx1rLtdPV8vmVj4HYFMerctFIOoFY`

---

## 📊 ESTRUTURA DO PROJETO

```
LIBERTUS/
├── core/                       # Módulos principais
│   ├── libertus_rag.py        # Sistema RAG
│   ├── libertus_ia.py         # Cliente IA
│   ├── libertus_scanner_final.py  # Scanner (opcional)
│   └── ...
├── telegram_bot_simple.py     # Bot Telegram
├── memoria/                   # Banco vetorial
│   └── chroma/               # ChromaDB
├── pdfs/                     # PDFs absorvidos
├── logs/                     # Logs do sistema
├── Dockerfile                # Container Docker
├── docker-compose.yml        # Orquestração
├── requirements.txt          # Dependências
├── .env.example             # Exemplo de config
└── README.md                # Este arquivo
```

---

## 🎯 FILOSOFIA

**ANTES:** Código de scanner quebrado, complexo, instável

**AGORA:** Sistema absorve conhecimento e "aprende" a fazer qualquer coisa

**NÃO precisamos mais:**
- ❌ Escrever código de exploits
- ❌ Debugar scanners quebrados
- ❌ Manter código técnico manualmente

**BASTA:**
- ✅ Upload PDFs técnicos
- ✅ IA aprende do conteúdo
- ✅ Sistema responde/analisa/cria

---

## 🚀 PRÓXIMOS PASSOS

1. ✅ RAG + Docling + Groq funcionando
2. ✅ Telegram integrado
3. 🔜 Trocar para Claude API (mais avançado)
4. 🔜 Interface web
5. 🔜 Multi-usuário
6. 🔜 API REST

---

## 💪 DESENVOLVIDO POR

**Lorran** - Sistema Meta-Adaptativo de Conhecimento

**"Melhor ferramenta já criada, moldada pelo conhecimento do usuário"**

---

## 📄 LICENÇA

Sistema proprietário - Uso restrito
