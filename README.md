# 🔥 LIBERTUS - Sistema Autônomo de Segurança

Sistema meta-adaptativo com valor real para análise de vulnerabilidades.

## ⚡ Instalação Rápida

```bash
# 1. Clonar repositório
git clone https://github.com/lorran562/libertus-core.git LIBERTUS
cd LIBERTUS

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Rodar sistema
python3 libertus_main_loop.py
```

## 📊 Uso

### Scanner Individual
```python
from core.libertus_scanner_final import LibertusScannerFinal
import asyncio

scanner = LibertusScannerFinal()
resultado = asyncio.run(scanner.run_full_scan("https://site.com"))
print(resultado)
```

### Sistema Completo (Loop Autônomo)
```bash
python3 libertus_main_loop.py
```

## 🎯 Estrutura

```
LIBERTUS/
├── core/                    # Módulos principais
│   ├── libertus_scanner_final.py
│   ├── motor_decisao.py
│   ├── inteligencia_comercial.py
│   └── ...
├── libertus_main_loop.py   # Loop principal
├── requirements.txt        # Dependências
└── README.md              # Este arquivo
```

## ✅ Testando

```bash
# Testar scanner
cd core
python3 -c "from libertus_scanner_final import LibertusScannerFinal; import asyncio; s = LibertusScannerFinal(); print(asyncio.run(s.run_full_scan('http://testphp.vulnweb.com')))"
```

## 🔐 Configuração (Opcional)

Telegram, APIs Groq/Claude podem ser configurados em `core/`.

---

**Desenvolvido por Lorran**  
Sistema Meta-Adaptativo com Valor Real

## 🐳 Rodar com Docker (Recomendado)

```bash
# 1. Clonar repositório
git clone https://github.com/lorran562/libertus-core.git LIBERTUS
cd LIBERTUS

# 2. Rodar com Docker
docker-compose up -d

# 3. Ver logs
docker-compose logs -f
```

## 📦 Rodar sem Docker (Manual)

```bash
# 1. Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Rodar
python3 libertus_main_loop.py
```

---

**Sistema portátil:** Funciona em VPS, PC, qualquer lugar! 🔥
