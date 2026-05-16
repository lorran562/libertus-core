"""
LIBERTUS TELEGRAM BOT - VERSÃO LOCAL
Rode no SEU COMPUTADOR (não no servidor)
"""

import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8619239720:AAGxEQx1rLtdPV8vmVj4HYFMerctFIOoFY"
LIBERTUS_API = "http://SEU_IP_UBUNTU:5000"  # Configurar depois

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ LIBERTUS Scanner Bot\n\n"
        "Comandos:\n"
        "/scan <url> - Escanear site\n"
        "/status - Ver status\n"
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /scan <url>")
        return
    
    target = context.args[0]
    await update.message.reply_text(f"🔍 Escaneando {target}...")
    
    # Chamar API LIBERTUS
    try:
        response = requests.post(
            f"{LIBERTUS_API}/scan",
            json={"target": target},
            timeout=300
        )
        
        if response.status_code == 200:
            data = response.json()
            await update.message.reply_text(
                f"✅ Scan completo!\n"
                f"Risk: {data['risk']}/100\n"
                f"Vulns: {data['vulns']}"
            )
        else:
            await update.message.reply_text("❌ Erro no scan")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan))
    print("🤖 Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
