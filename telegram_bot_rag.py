#!/usr/bin/env python3
"""
LIBERTUS TELEGRAM BOT - RAG + IA COMPLETO
Sistema de conhecimento inteligente via Telegram
"""

import os
import sys
import asyncio
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configuração
TOKEN = "8619239720:AAGxEQx1rLtdPV8vmVj4HYFMerctFIOoFY"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")

# Adicionar core ao path
CORE_PATH = Path(__file__).parent / "core"
sys.path.insert(0, str(CORE_PATH))

# Importar RAG e IA
try:
    from libertus_rag import LibertusRAG
    from libertus_ia import LibertusIA
    RAG_DISPONIVEL = True
    print("✅ RAG + IA carregados")
except Exception as e:
    RAG_DISPONIVEL = False
    print(f"⚠️ RAG + IA não disponíveis: {e}")

# Inicializar RAG + IA globalmente
if RAG_DISPONIVEL:
    try:
        rag = LibertusRAG(persist_dir=str(Path.home() / "LIBERTUS" / "memoria" / "chroma"))
        ia = LibertusIA(api_key=GROQ_API_KEY)
        print("✅ RAG + IA inicializados")
    except Exception as e:
        RAG_DISPONIVEL = False
        print(f"❌ Erro ao inicializar RAG + IA: {e}")

# ==================== COMANDOS ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    texto = """🔥 LIBERTUS - Sistema de Conhecimento Inteligente

📚 **COMANDOS:**
/upload - Enviar PDF para absorver conhecimento
/ask [pergunta] - Fazer pergunta baseada nos PDFs
/create [objetivo] - Criar solução inovadora
/stats - Ver estatísticas do sistema
/status - Status do sistema

💡 **EXEMPLO:**
1. /upload → Enviar PDF de hacking
2. /ask como funciona SQL injection
3. IA responde baseado no PDF!

**Sistema pronto para aprender!** 🧠"""
    
    await update.message.reply_text(texto)

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status"""
    if not RAG_DISPONIVEL:
        await update.message.reply_text("⚠️ RAG + IA não disponíveis\n\nInstale dependências:\npip install chromadb PyPDF2")
        return
    
    await update.message.reply_text("✅ Sistema funcionando!\n🧠 RAG + IA operacionais\n📊 Pronto para absorver conhecimento")

async def stats_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /stats"""
    if not RAG_DISPONIVEL:
        await update.message.reply_text("⚠️ RAG não disponível")
        return
    
    try:
        stats = rag.stats()
        fontes = stats.get('fontes', [])
        total = stats.get('total_documentos', 0)
        
        texto = f"""📊 **ESTATÍSTICAS DO SISTEMA**

📚 Documentos absorvidos: {total}
📁 Fontes: {len(fontes)}

**Fontes:**
"""
        for fonte in fontes[:10]:
            texto += f"  • {fonte}\n"
        
        if len(fontes) > 10:
            texto += f"\n  ... e mais {len(fontes) - 10} fontes"
        
        await update.message.reply_text(texto)
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao obter stats: {e}")

async def upload_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /upload"""
    await update.message.reply_text("""📤 **UPLOAD DE PDF**

**Como usar:**
1. Envie o arquivo PDF diretamente no chat
2. Sistema vai absorver o conhecimento
3. Depois use /ask para fazer perguntas!

**Exemplo:**
Envie PDF de pentest → Sistema absorve → /ask como explorar XSS

**Aguardando PDF...** 📄""")

async def ask_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ask [pergunta]"""
    if not RAG_DISPONIVEL:
        await update.message.reply_text("⚠️ RAG + IA não disponíveis")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Use: /ask [sua pergunta]\n\nExemplo: /ask como funciona SQL injection")
        return
    
    pergunta = " ".join(context.args)
    await update.message.reply_text(f"🔍 Buscando conhecimento sobre: {pergunta}...")
    
    try:
        # Buscar contexto relevante
        documentos = rag.buscar_conhecimento(pergunta, n_results=5)
        
        if not documentos:
            await update.message.reply_text("""❌ Nenhum conhecimento encontrado nos PDFs!

💡 **Dica:**
1. Use /upload para enviar PDFs
2. Sistema absorve conhecimento
3. Depois pergunte novamente!""")
            return
        
        # Gerar resposta com IA
        resposta = ia.responder_com_contexto(
            pergunta=pergunta,
            contexto=documentos,
            area="pentest"  # TODO: detectar área automaticamente
        )
        
        await update.message.reply_text(f"🤖 **RESPOSTA:**\n\n{resposta}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao processar: {e}")

async def create_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /create [objetivo]"""
    if not RAG_DISPONIVEL:
        await update.message.reply_text("⚠️ RAG + IA não disponíveis")
        return
    
    if not context.args:
        await update.message.reply_text("""❌ Use: /create [seu objetivo]

**Exemplos:**
/create antibiótico com menos resistência bacteriana
/create exploit para SQL injection em PHP
/create braço robótico para cirurgia""")
        return
    
    objetivo = " ".join(context.args)
    await update.message.reply_text(f"🔬 Analisando conhecimento para criar: {objetivo}...")
    
    try:
        # Buscar conhecimento relevante
        documentos = rag.buscar_conhecimento(objetivo, n_results=10)
        
        if not documentos:
            await update.message.reply_text("❌ Preciso de mais conhecimento! Envie PDFs relacionados com /upload")
            return
        
        # IA analisa e CRIA
        criacao = ia.analisar_e_criar(
            objetivo=objetivo,
            contexto=documentos,
            area="pentest"  # TODO: detectar área
        )
        
        await update.message.reply_text(f"💡 **CRIAÇÃO:**\n\n{criacao}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao criar: {e}")

async def receber_documento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processar PDFs enviados"""
    if not RAG_DISPONIVEL:
        await update.message.reply_text("⚠️ RAG não disponível")
        return
    
    documento = update.message.document
    
    if not documento.file_name.endswith('.pdf'):
        await update.message.reply_text("❌ Envie apenas arquivos PDF!")
        return
    
    await update.message.reply_text(f"📥 Recebendo: {documento.file_name}...")
    
    try:
        # Baixar PDF
        file = await context.bot.get_file(documento.file_id)
        
        # Salvar temporariamente
        pdf_dir = Path.home() / "LIBERTUS" / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / documento.file_name
        
        await file.download_to_drive(pdf_path)
        
        await update.message.reply_text(f"🧠 Absorvendo conhecimento de {documento.file_name}...")
        
        # Absorver PDF
        doc_ids = rag.absorver_pdf_simples(str(pdf_path))
        
        if doc_ids:
            await update.message.reply_text(f"""✅ **CONHECIMENTO ABSORVIDO!**

📄 Arquivo: {documento.file_name}
📚 Páginas processadas: {len(doc_ids)}

💡 Agora você pode:
• /ask [pergunta] - Fazer perguntas
• /create [objetivo] - Criar soluções
• /stats - Ver estatísticas""")
        else:
            await update.message.reply_text(f"❌ Erro ao processar PDF")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {e}")

async def mensagem_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensagens de texto normais"""
    texto = update.message.text
    
    if not RAG_DISPONIVEL:
        await update.message.reply_text(f"Você disse: {texto}\n\n⚠️ RAG + IA não disponíveis ainda!")
        return
    
    # Resposta padrão
    await update.message.reply_text(f"""💬 Recebi: "{texto}"

💡 **USE OS COMANDOS:**
/ask {texto} - Fazer pergunta
/upload - Enviar PDF
/create [objetivo] - Criar solução""")

# ==================== MAIN ====================

def main():
    print("🔥 Iniciando LIBERTUS RAG + IA Bot...")
    
    if not RAG_DISPONIVEL:
        print("⚠️ RAG + IA não disponíveis - instale dependências:")
        print("pip install chromadb PyPDF2 sentence-transformers --break-system-packages")
    
    app = Application.builder().token(TOKEN).build()
    
    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("stats", stats_comando))
    app.add_handler(CommandHandler("upload", upload_comando))
    app.add_handler(CommandHandler("ask", ask_comando))
    app.add_handler(CommandHandler("create", create_comando))
    
    # Documentos (PDFs)
    app.add_handler(MessageHandler(filters.Document.PDF, receber_documento))
    
    # Mensagens de texto
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensagem_texto))
    
    print("✅ Bot RAG + IA rodando!")
    print("📱 Comandos: /start, /upload, /ask, /create, /stats")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
