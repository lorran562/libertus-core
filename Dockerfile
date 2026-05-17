FROM python:3.12-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Expor porta (se usar API)
EXPOSE 8000

# Comando padrão
CMD ["python3", "libertus_main_loop.py"]
