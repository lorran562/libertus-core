#!/usr/bin/env python3
"""
LIBERTUS TELEGRAM BOT - Integrado ao Scanner
Rodando em paralelo com production_daemon_v2_shadow_intelligent.py
"""

import asyncio
import logging
import sys
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuração
TOKEN = "8619239720:AAGxEQx1rLtdPV8vmVj4HYFMerctFIOoFY"
LIBERTUS_PATH = Path.home() / "LIBERTUS" / "core"
LOG_PATH = Path.home() / "LIBERTUS" / "logs" / "telegram_bot.log"

# Adicionar LIBERTUS ao path
sys.path.insert(0, str(LIBERTUS_PATH))

# Importar módulos inteligentes
try:
    from motor_decisao import MotorDecisao
    from shadow_analyzer import ShadowAnalyzer
    from inteligencia_comercial import InteligenciaComercial
    from logic_engine import LogicEngine
    MODULOS_INTELIGENTES = True
    logger_temp = logging.getLogger(__name__)
    logger_temp.info("✅ Módulos inteligentes carregados")
except Exception as e:
    MODULOS_INTELIGENTES = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"⚠️ Módulos inteligentes não disponíveis: {e}")

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Inicializar módulos inteligentes (se disponíveis)
if MODULOS_INTELIGENTES:
    try:
        motor_decisao = MotorDecisao()
        shadow_analyzer = ShadowAnalyzer()
        inteligencia_comercial = InteligenciaComercial()
        logic_engine = LogicEngine()
        logger.info("✅ Motores inteligentes inicializados")
    except Exception as e:
        MODULOS_INTELIGENTES = False
        logger.error(f"❌ Erro ao inicializar motores: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    comandos = (
        "🛡️ *LIBERTUS Scanner Bot*\n\n"
        "Comandos disponíveis:\n"
        "━━━━━━━━━━━━━━━━━\n"
        "📍 /scan <url> - Escanear site\n"
        "📊 /status - Status do sistema\n"
    )
    
    if MODULOS_INTELIGENTES:
        comandos += "🧠 /ask <pergunta> - Consultar IA\n"
    
    comandos += (
        "❓ /help - Ajuda\n\n"
        "Sistema 24/7 operacional"
    )
    
    await update.message.reply_text(comandos, parse_mode='Markdown')

async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /scan <url>"""
    if not context.args:
        await update.message.reply_text(
            "❌ Uso incorreto\n\n"
            "Correto: /scan <url>\n"
            "Exemplo: /scan google.com"
        )
        return
    
    target = context.args[0]
    
    # Validar URL básica
    if not target or len(target) < 3:
        await update.message.reply_text("❌ URL inválida")
        return
    
    # Adicionar http se necessário
    if not target.startswith(('http://', 'https://')):
        target = f"https://{target}"
    
    user = update.effective_user.username or update.effective_user.first_name
    logger.info(f"Scan solicitado por {user}: {target}")
    
    await update.message.reply_text(
        f"🔍 *Iniciando scan...*\n\n"
        f"🎯 Target: `{target}`\n"
        f"⏱️ Aguarde 30-60 segundos...",
        parse_mode='Markdown'
    )
    
    try:
        # Importar scanner
        from libertus_scanner_final import LibertusScannerFinal
        
        # Executar scan com timeout
        scanner = LibertusScannerFinal(target)
        scan_result = await asyncio.wait_for(
            scanner.scan_complete(),
            timeout=120  # 2 min timeout
        )
        
        # Extrair resultados
        risk_score = scan_result.get('risk_score', 0)
        severity = scan_result.get('severity', 'UNKNOWN')
        vulnerabilities = scan_result.get('vulnerabilities', [])
        vuln_count = len(vulnerabilities)
        
        # Contar por severidade
        critical = len([v for v in vulnerabilities if v.get('severity') == 'CRITICAL'])
        high = len([v for v in vulnerabilities if v.get('severity') == 'HIGH'])
        medium = len([v for v in vulnerabilities if v.get('severity') == 'MEDIUM'])
        low = len([v for v in vulnerabilities if v.get('severity') == 'LOW'])
        
        # Emoji por severidade
        severity_emoji = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢',
            'UNKNOWN': '⚪'
        }
        
        # Montar resposta
        response = (
            f"✅ *Scan Completo*\n\n"
            f"🎯 *Target:* `{target}`\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📊 *Risk Score:* {risk_score}/100\n"
            f"{severity_emoji.get(severity, '⚪')} *Severity:* {severity}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"⚠️ *Vulnerabilidades:* {vuln_count}\n"
        )
        
        if vuln_count > 0:
            response += f"\n📋 *Breakdown:*\n"
            if critical > 0:
                response += f"  🔴 CRITICAL: {critical}\n"
            if high > 0:
                response += f"  🟠 HIGH: {high}\n"
            if medium > 0:
                response += f"  🟡 MEDIUM: {medium}\n"
            if low > 0:
                response += f"  🟢 LOW: {low}\n"
        
        # ANÁLISE INTELIGENTE (se disponível)
        if MODULOS_INTELIGENTES:
            try:
                # Shadow Analyzer
                analysis = shadow_analyzer.analyze_comparison(
                    prod_risk=risk_score,
                    router_risk=risk_score,  # Usando mesmo valor (modo standalone)
                    target=target,
                    vulnerabilities=vulnerabilities
                )
                
                # Motor de Decisão
                decision_data = {
                    'risk_score': risk_score,
                    'severity': severity,
                    'vulnerabilities': vulnerabilities,
                    'target': target
                }
                
                # Inteligência Comercial
                comercial_assessment = inteligencia_comercial.avaliar_lead({
                    'url': target,
                    'risk': risk_score,
                    'vulns': vuln_count
                })
                
                # Adicionar análise inteligente
                response += f"\n━━━━━━━━━━━━━━━━━\n"
                response += f"🧠 *Análise Inteligente:*\n"
                
                # Prioridade de ação
                if critical > 0:
                    response += f"🚨 URGENTE: {critical} falhas críticas\n"
                elif high > 0:
                    response += f"⚠️ ATENÇÃO: {high} falhas graves\n"
                elif risk_score > 50:
                    response += f"⚠️ Risco elevado detectado\n"
                else:
                    response += f"✅ Risco controlável\n"
                
                # Potencial comercial
                if comercial_assessment and isinstance(comercial_assessment, dict):
                    potencial = comercial_assessment.get('potencial', 'MÉDIO')
                    response += f"\n💰 *Potencial:* {potencial}\n"
                
            except Exception as e:
                logger.error(f"Erro na análise inteligente: {e}")
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
        logger.info(f"Scan completo: {target} - Risk: {risk_score}")
    
    except asyncio.TimeoutError:
        await update.message.reply_text(
            "⏱️ *Timeout*\n\n"
            "Scan demorou muito (>2 min)\n"
            "Tente novamente ou escolha outro target",
            parse_mode='Markdown'
        )
        logger.error(f"Timeout no scan: {target}")
    
    except Exception as e:
        error_msg = str(e)[:200]
        await update.message.reply_text(
            f"❌ *Erro no scan*\n\n"
            f"`{error_msg}`",
            parse_mode='Markdown'
        )
        logger.error(f"Erro no scan {target}: {e}", exc_info=True)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status"""
    try:
        import json
        
        # Verificar daemon
        import subprocess
        result = subprocess.run(
            ["pgrep", "-f", "production_daemon"],
            capture_output=True
        )
        daemon_status = "✅ Rodando" if result.returncode == 0 else "❌ Parado"
        
        # Verificar métricas shadow
        metrics_file = Path.home() / "LIBERTUS" / "logs" / "shadow_metrics.json"
        
        if metrics_file.exists():
            with open(metrics_file) as f:
                metrics = json.load(f)
            
            total = metrics.get('total_comparisons', 0)
            router_better = metrics.get('router_better', 0)
            
            response = (
                f"📊 *LIBERTUS Status*\n\n"
                f"🤖 Daemon: {daemon_status}\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"🔬 *Shadow Mode:*\n"
                f"  Comparações: {total}/10\n"
                f"  Router melhor: {router_better}"
            )
        else:
            response = (
                f"📊 *LIBERTUS Status*\n\n"
                f"🤖 Daemon: {daemon_status}\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ Métricas não disponíveis"
            )
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    except Exception as e:
        await update.message.reply_text(
            f"❌ Erro ao verificar status\n\n`{str(e)}`",
            parse_mode='Markdown'
        )

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ask - Perguntas para IA"""
    if not MODULOS_INTELIGENTES:
        await update.message.reply_text(
            "❌ Módulos inteligentes não disponíveis\n\n"
            "Use /scan para análise básica"
        )
        return
    
    if not context.args:
        await update.message.reply_text(
            "❓ *Como usar /ask:*\n\n"
            "Faça perguntas sobre segurança, clientes ou estratégia\n\n"
            "*Exemplos:*\n"
            "• `/ask vale a pena prospectar clínicas pequenas?`\n"
            "• `/ask como precificar serviço de pentest?`\n"
            "• `/ask qual melhor abordagem para vender?`",
            parse_mode='Markdown'
        )
        return
    
    pergunta = " ".join(context.args)
    user = update.effective_user.username or update.effective_user.first_name
    logger.info(f"Pergunta de {user}: {pergunta}")
    
    await update.message.reply_text(
        f"🧠 *Processando pergunta...*\n\n"
        f"`{pergunta}`",
        parse_mode='Markdown'
    )
    
    try:
        # Usar inteligência comercial para responder
        resposta = inteligencia_comercial.responder_pergunta(pergunta)
        
        if resposta:
            await update.message.reply_text(
                f"🧠 *LIBERTUS IA*\n\n"
                f"{resposta}",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "🤔 Não tenho dados suficientes para responder essa pergunta.\n\n"
                "Tente perguntas sobre:\n"
                "• Prospecção de clientes\n"
                "• Precificação de serviços\n"
                "• Estratégia de vendas"
            )
    
    except Exception as e:
        logger.error(f"Erro no /ask: {e}", exc_info=True)
        await update.message.reply_text(
            f"❌ Erro ao processar pergunta\n\n"
            f"`{str(e)[:200]}`",
            parse_mode='Markdown'
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    help_text = (
        "🛡️ *LIBERTUS Scanner Bot*\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "📖 *Comandos:*\n\n"
        "📍 */scan* <url>\n"
        "Escanear um site\n"
        "Exemplo: `/scan google.com`\n\n"
        "📊 */status*\n"
        "Ver status do sistema\n\n"
    )
    
    if MODULOS_INTELIGENTES:
        help_text += (
            "🧠 */ask* <pergunta>\n"
            "Consultar inteligência artificial\n"
            "Exemplo: `/ask vale a pena clínicas pequenas?`\n\n"
        )
    
    help_text += (
        "❓ */help*\n"
        "Mostrar esta ajuda\n\n"
        "━━━━━━━━━━━━━━━━━\n"
        "🔒 Sistema 24/7 operacional\n"
        "⚡ Shadow Mode ativo"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler global de erros"""
    logger.error(f"Update causou erro: {context.error}", exc_info=context.error)

def main():
    """Main - Iniciar bot"""
    logger.info("Iniciando LIBERTUS Telegram Bot...")
    
    # Criar aplicação
    application = Application.builder().token(TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("scan", scan))
    application.add_handler(CommandHandler("status", status))
    
    # Comando /ask (se módulos inteligentes disponíveis)
    if MODULOS_INTELIGENTES:
        application.add_handler(CommandHandler("ask", ask))
        logger.info("✅ Comando /ask registrado")
    
    application.add_handler(CommandHandler("help", help_command))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("🤖 Bot Telegram iniciado e rodando")
    logger.info("Aguardando comandos...")
    
    # Rodar bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
