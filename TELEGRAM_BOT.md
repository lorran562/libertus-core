# 🤖 LIBERTUS TELEGRAM BOT

Controle LIBERTUS remotamente via Telegram.

## 🚀 SETUP:

### 1. Criar Bot no Telegram:

```
1. Abra Telegram
2. Fale com @BotFather
3. /newbot
4. Nome: LIBERTUS Scanner
5. Username: libertus_scanner_bot (ou outro)
6. Copie o TOKEN
```

### 2. Instalar Dependências:

```bash
pip3 install python-telegram-bot --break-system-packages
```

### 3. Configurar Token:

Edite `/root/LIBERTUS/telegram_bot.py` linha 14:
```python
TOKEN = "SEU_TOKEN_AQUI"
```

### 4. Iniciar Bot:

```bash
cd /root/LIBERTUS
python3 telegram_bot.py
```

---

## 📱 COMANDOS:

### `/start`
Inicia o bot e mostra comandos disponíveis

### `/scan <url>`
Escaneia um site

**Exemplo:**
```
/scan google.com
/scan saojoselaboratorio.com.br
```

### `/status`
Ver status do sistema:
- Daemon rodando?
- Comparações shadow mode
- Métricas

### `/help`
Mostra ajuda

---

## 🔧 RODANDO EM BACKGROUND:

```bash
cd /root/LIBERTUS
nohup python3 telegram_bot.py > logs/telegram_bot.log 2>&1 &
echo $! > /tmp/telegram_bot.pid
```

**Parar:**
```bash
kill $(cat /tmp/telegram_bot.pid)
```

---

## 📊 FLUXO:

```
Você (Telegram) → /scan google.com
    ↓
Bot recebe comando
    ↓
Executa LIBERTUS scanner
    ↓
Processa resultado
    ↓
Envia resposta (Telegram)
```

---

## 🎯 PRÓXIMOS UPGRADES:

- [ ] Enviar PDF do relatório
- [ ] Notificações automáticas
- [ ] Comandos admin
- [ ] Multi-usuário
- [ ] Dashboard inline

---

**Bot pronto para controle remoto 24/7.**
