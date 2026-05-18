FROM python:3.12-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Criar diretórios necessários
RUN mkdir -p /app/logs /app/memoria/chroma /app/pdfs

# Variáveis de ambiente
ENV PYTHONUNBUFFERED=1
ENV GROQ_API_KEY=""

# Expor porta (se usar API web)
EXPOSE 8000

# Comando padrão: Telegram Bot
CMD ["python3", "/app/telegram_bot_simple.py"]
