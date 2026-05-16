"""
LIBERTUS TELEGRAM BOT
Controle remoto do scanner via Telegram
"""

import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import subprocess
import sys
from pathlib import Path

# Configuração
TOKEN = "8619239720:AAGxEQx1rLtdPV8vmVj4HYFMerctFIOoFY"  # @BotFather
LIBERTUS_PATH = Path.home() / "LIBERTUS" / "core"

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    await update.message.reply_text(
        "🛡️ LIBERTUS Scanner Bot\n\n"
        "Comandos:\n"
        "/scan <url> - Escanear site\n"
        "/status - Ver status do sistema\n"
        "/help - Ajuda"
    )

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /scan <url>"""
    if not context.args:
        await update.message.reply_text("❌ Uso: /scan <url>\nExemplo: /scan google.com")
        return
    
    target = context.args[0]
    
    # Validar URL
    if not target:
        await update.message.reply_text("❌ URL inválida")
        return
    
    await update.message.reply_text(f"🔍 Iniciando scan de {target}...")
    
    try:
        # Executar scanner
        result = subprocess.run(
            [
                sys.executable,
                str(LIBERTUS_PATH / "libertus_scanner_final.py"),
                target
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 min timeout
        )
        
        # Processar resultado
        if result.returncode == 0:
            output = result.stdout
            
            # Extrair risk score
            risk_line = [l for l in output.split('\n') if 'Risk Score:' in l]
            risk = risk_line[0] if risk_line else "Desconhecido"
            
            # Extrair vulnerabilidades
            vuln_line = [l for l in output.split('\n') if 'Vulnerabilidades:' in l]
            vulns = vuln_line[0] if vuln_line else "0"
            
            await update.message.reply_text(
                f"✅ Scan completo!\n\n"
                f"🎯 Target: {target}\n"
                f"📊 {risk}\n"
                f"⚠️ {vulns}\n\n"
                f"Relatório completo em /status"
            )
        else:
            await update.message.reply_text(
                f"❌ Erro no scan:\n{result.stderr[:500]}"
            )
    
    except subprocess.TimeoutExpired:
        await update.message.reply_text("⏱️ Timeout - scan demorou muito")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {str(e)}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status"""
    try:
        # Verificar se daemon está rodando
        result = subprocess.run(
            ["pgrep", "-f", "production_daemon"],
            capture_output=True
        )
        
        if result.returncode == 0:
            status_msg = "✅ Daemon RODANDO"
        else:
            status_msg = "❌ Daemon PARADO"
        
        # Verificar últimas comparações
        metrics_file = Path.home() / "LIBERTUS" / "logs" / "shadow_metrics.json"
        
        if metrics_file.exists():
            import json
            with open(metrics_file) as f:
                metrics = json.load(f)
            
            total = metrics.get('total_comparisons', 0)
            router_better = metrics.get('router_better', 0)
            
            await update.message.reply_text(
                f"📊 LIBERTUS Status\n\n"
                f"{status_msg}\n"
                f"Comparações: {total}/10\n"
                f"Router melhor: {router_better}"
            )
        else:
            await update.message.reply_text(
                f"📊 LIBERTUS Status\n\n"
                f"{status_msg}\n"
                f"Métricas: Não disponíveis"
            )
    
    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {str(e)}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    await update.message.reply_text(
        "🛡️ LIBERTUS Scanner Bot\n\n"
        "📖 Comandos disponíveis:\n\n"
        "/scan <url> - Escanear um site\n"
        "Exemplo: /scan google.com\n\n"
        "/status - Ver status do sistema\n"
        "/help - Mostrar esta ajuda\n\n"
        "🔒 Sistema 24/7 operacional"
    )

def main():
    """Main - Iniciar bot"""
    # Criar aplicação
    application = Application.builder().token(TOKEN).build()
    
    # Adicionar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("scan", scan))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("help", help_command))
    
    # Rodar bot
    print("🤖 Bot Telegram iniciado")
    application.run_polling()

if __name__ == "__main__":
    main()
