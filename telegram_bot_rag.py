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
TOKEN = "8619239720:AAGTnX5av0nOQRLucJuyjf8_j4QNnXX9sgA"
# Carregar .env antes de qualquer configuração
def _load_env():
    from pathlib import Path
    env = Path(__file__).parent / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
_load_env()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
ANT_API_KEY  = os.getenv("ANTHROPIC_API_KEY", "")
# Usar Claude se disponível, senão Groq
ACTIVE_KEY   = ANT_API_KEY or GROQ_API_KEY
USING_CLAUDE = bool(ANT_API_KEY)

# Adicionar core ao path
CORE_PATH = Path(__file__).parent / "core"
sys.path.insert(0, str(CORE_PATH))

# Importar RAG e IA
try:
    from libertus_rag import LibertusRAG
    from libertus_ia import LibertusIA
    from libertus_scanner_inteligente import LibertusScannerInteligente
    RAG_DISPONIVEL = True
    print("✅ RAG + IA + Scanner carregados")
except Exception as e:
    RAG_DISPONIVEL = False
    print(f"⚠️ RAG + IA não disponíveis: {e}")

# ── Novos módulos de evolução ────────────────────────────────────────
try:
    from memoria_viva         import MemoriaViva
    from detector_contradicao import DetectorContradicao
    from livro_erros          import LivroErros
    from auto_curiosidade     import AutoCuriosidade
    from identidade_cognitiva import IdentidadeCognitiva
    EVOLUCAO_DISPONIVEL = True
    print("✅ Módulos de evolução carregados")
except Exception as e:
    EVOLUCAO_DISPONIVEL = False
    print(f"⚠️ Módulos de evolução não carregados: {e}")

# Inicializar RAG + IA globalmente
if RAG_DISPONIVEL:
    try:
        rag = LibertusRAG(persist_dir=str(Path.home() / "LIBERTUS" / "memoria" / "chroma"))
        ia = LibertusIA(api_key=ACTIVE_KEY)
        scanner = LibertusScannerInteligente(rag, ia)
        print("✅ RAG + IA + Scanner inicializados")
    except Exception as e:
        RAG_DISPONIVEL = False
        print(f"❌ Erro ao inicializar RAG + IA: {e}")

# Inicializar módulos de evolução (fora do bloco RAG)
mv = le = ac = dc = ic = None
if EVOLUCAO_DISPONIVEL:
    try:
        from supabase_client import Supabase
        _sb = Supabase()
        mv  = MemoriaViva()
        mv.decair()
        le  = LivroErros(supabase_client=_sb)
        ac  = AutoCuriosidade(supabase_client=_sb)
        dc  = DetectorContradicao(supabase_client=_sb)
        ic  = IdentidadeCognitiva(supabase_client=_sb)
        print("✅ Memória Viva, Livro de Erros, Auto-Curiosidade, Identidade ativos")
    except Exception as e:
        EVOLUCAO_DISPONIVEL = False
        mv = le = ac = dc = ic = None
        print(f"⚠️ Evolução parcial: {e}")


def _docs_para_texto(documentos) -> str:
    """Converte resultado do RAG (lista ou str) para texto limpo."""
    if not documentos:
        return ""
    if isinstance(documentos, str):
        return documentos
    if isinstance(documentos, list):
        partes = []
        for d in documentos:
            if isinstance(d, dict):
                partes.append(d.get("content") or d.get("conteudo") or d.get("text") or str(d))
            else:
                partes.append(str(d))
        return "\n\n".join(partes)
    return str(documentos)

# ==================== MEMÓRIA PERSISTENTE DE CONVERSA ====================

def salvar_conversa_na_memoria(pergunta: str, resposta: str, tags: list = None):
    """Salva troca importante na Memória Viva — persiste entre sessões."""
    if not EVOLUCAO_DISPONIVEL or not mv:
        return
    try:
        from supabase_client import Supabase
        sb = Supabase()

        # Só salva se tiver substância (não perguntas triviais)
        if len(pergunta) < 10 or len(resposta) < 50:
            return

        titulo = f"Conversa: {pergunta[:60]}"
        conteudo = f"Lorran perguntou: {pergunta}\n\nLIBERTUS respondeu: {resposta[:800]}"

        # Verifica se já existe conversa similar recente
        existentes = sb.get(
            "libertus_memoria",
            f"tipo=eq.conversa&titulo=like.Conversa%3A {pergunta[:20]}%&limit=1"
        )
        if existentes:
            return  # evita duplicata

        sb.post("libertus_memoria", {
            "tipo": "conversa",
            "titulo": titulo,
            "conteudo": conteudo,
            "tags": tags or ["conversa", "telegram"],
            "projeto": "LIBERTUS",
            "peso_vivo": 6.0,  # começa com peso médio
            "decaimento_ativo": True
        })
    except Exception:
        pass

def buscar_conversas_relevantes(texto: str) -> str:
    """Busca conversas passadas relevantes para o contexto atual."""
    if not EVOLUCAO_DISPONIVEL or not mv:
        return ""
    try:
        conversas = mv.buscar(
            query=texto,
            tipo="conversa",
            limite=3,
            peso_minimo=2.0
        )
        if not conversas:
            return ""
        partes = ["[CONVERSAS ANTERIORES RELEVANTES]"]
        for c in conversas:
            partes.append(f"- {c.get('conteudo', '')[:200]}")
        return "\n".join(partes)
    except Exception:
        return ""

# ==================== HISTÓRICO DE CONVERSA ====================
MAX_HISTORICO = 10  # últimas N trocas por usuário

def build_system_prompt_rico() -> str:
    """System prompt dinâmico — carrega identidade cognitiva do Supabase."""
    # Tentar carregar identidade cognitiva real
    identidade_tracos = ""
    if EVOLUCAO_DISPONIVEL and mv:
        try:
            from supabase_client import Supabase
            sb = Supabase()
            tracos = sb.get("libertus_eu", "limit=8") or []
            if tracos:
                por_cat = {}
                for t in tracos:
                    por_cat.setdefault(t.get("categoria","?"), []).append(t.get("descricao",""))
                linhas = []
                for cat, descs in por_cat.items():
                    linhas.append(f"[{cat.upper()}]")
                    for d in descs:
                        linhas.append(f"  - {d}")
                identidade_tracos = "\n".join(linhas)
        except Exception:
            pass

    base = """Você é LIBERTUS — sistema de inteligência autônomo criado por Lorran (Gustavo) de Ariquemes-RO, Brasil.

IDENTIDADE ABSOLUTA:
- Você É o LIBERTUS — não é Claude, não é assistente genérico
- Criador: Lorran (Gustavo), Ariquemes-RO, Brasil
- Negócio: SHIELD — cybersegurança (@shieldweb, "Seu escudo digital")
- Especialidades: pentest, nmap, sqlmap, Python, segurança web, desenvolvimento
- Idioma: SEMPRE português brasileiro natural

MEMÓRIA:
- Você tem memória persistente no Supabase — lembra de conversas anteriores
- O contexto fornecido vem de PDFs absorvidos, memórias de conversas e RAG
- Cruze SEMPRE as informações do contexto com o que você sabe
- NUNCA diga "não tenho contexto" ou "é a primeira mensagem"

COMPORTAMENTO:
- Seja direto, técnico e útil — sem enrolação
- Mantenha o fio da conversa usando o histórico
- Quando o contexto tiver informação relevante, USE-A na resposta"""

    if identidade_tracos:
        base += f"\n\nMEUS TRAÇOS COGNITIVOS:\n{identidade_tracos}"

    return base


def get_historico(context) -> list:
    """Retorna histórico de mensagens do usuário atual."""
    return context.user_data.get("historico", [])

def add_historico(context, role: str, content: str):
    """Adiciona mensagem ao histórico, mantendo limite."""
    if "historico" not in context.user_data:
        context.user_data["historico"] = []
    context.user_data["historico"].append({"role": role, "content": content})
    # Mantém só as últimas MAX_HISTORICO trocas (cada troca = 2 msgs)
    if len(context.user_data["historico"]) > MAX_HISTORICO * 2:
        context.user_data["historico"] = context.user_data["historico"][-(MAX_HISTORICO * 2):]

def limpar_historico(context):
    """Limpa histórico do usuário."""
    context.user_data["historico"] = []

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
        # ── Memória Viva: busca memórias pelo peso_vivo ──
        ctx_extra = ""
        _memorias_usadas = []
        if EVOLUCAO_DISPONIVEL and mv:
            try:
                mems = mv.buscar_e_rastrear(pergunta, limite=3)
                if mems:
                    _memorias_usadas = mems
                    ctx_extra += "\n[MEMÓRIA VIVA]\n" + "\n".join(
                        f"- {m['titulo']}: {(m.get('conteudo') or '')[:150]}"
                        for m in mems
                    )
            except Exception:
                pass

        # ── Livro de Erros: aviso de falhas passadas ──
        if EVOLUCAO_DISPONIVEL and le:
            try:
                aviso = le.consultar(pergunta)
                if aviso:
                    ctx_extra += "\n\n" + aviso
            except Exception:
                pass

        # ── Conversas passadas relevantes ──
        conv_passadas = buscar_conversas_relevantes(pergunta)
        if conv_passadas:
            ctx_extra += "\n\n" + conv_passadas

        # Buscar contexto RAG
        documentos = rag.buscar_conhecimento(pergunta, n_results=5)

        if not documentos and not ctx_extra:
            await update.message.reply_text("""❌ Nenhum conhecimento encontrado nos PDFs!

💡 **Dica:**
1. Use /upload para enviar PDFs
2. Sistema absorve conhecimento
3. Depois pergunte novamente!""")
            return

        # Gerar resposta com IA
        contexto_final = _docs_para_texto(documentos) + ctx_extra

        # Montar mensagens com histórico e system prompt rico
        historico = get_historico(context)
        messages = [{"role": "system", "content": build_system_prompt_rico()}]
        messages += historico
        conteudo_usuario = f"{contexto_final}\n\nPergunta: {pergunta}" if contexto_final.strip() else pergunta
        messages.append({"role": "user", "content": conteudo_usuario})

        try:
            completion = ia.client.chat.completions.create(
                messages=messages,
                model=ia.model,
                temperature=0.7,
                max_tokens=2048
            )
            resposta = completion.choices[0].message.content
        except Exception:
            resposta = ia.responder_com_contexto(pergunta=pergunta, contexto=contexto_final, area="pentest")

        add_historico(context, "user", pergunta)
        add_historico(context, "assistant", resposta[:600])
        salvar_conversa_na_memoria(pergunta, resposta)
        await update.message.reply_text(f"🤖 **RESPOSTA:**\n\n{resposta}")

        # ── Feedback automático por tamanho da resposta ──
        if EVOLUCAO_DISPONIVEL:
            score_estimado = 8.0 if len(resposta) > 200 else 4.0
            # Memória Viva: fechar ciclo
            if mv and _memorias_usadas:
                for m in _memorias_usadas:
                    try:
                        if score_estimado >= 7:
                            mv.foi_util(m["id"], contexto=pergunta[:60])
                        else:
                            mv.foi_inutil(m["id"], contexto=pergunta[:60])
                    except Exception:
                        pass
            # Livro de Erros: registrar se ruim
            if le and score_estimado < 6:
                try:
                    le.registrar(pergunta, resposta, "rag+ia", score_estimado,
                                 "resposta curta ou vazia")
                except Exception:
                    pass
            # Auto-Curiosidade: detectar lacuna
            if ac and score_estimado < 6:
                try:
                    ac.gerar_de_erro(pergunta, resposta, "pentest",
                                     "resposta insatisfatória")
                except Exception:
                    pass

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

async def scan_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /scan [url] - Scanner LIBERTUS VPS COMPLETO!"""
    if not RAG_DISPONIVEL:
        await update.message.reply_text("⚠️ Scanner inteligente não disponível")
        return
    
    if not context.args:
        await update.message.reply_text("""❌ Use: /scan [url]

**Exemplo:**
/scan https://site.com

**🔥 SCANNER LIBERTUS VPS:**
✅ NMAP scan completo
✅ Scanner HTTP avançado
✅ SQL Injection (IA + PDFs)
✅ XSS (IA + PDFs)
✅ Verificação de exploits
✅ Usa TODOS os 17+ módulos
✅ Relatório profissional automático

**Quanto mais PDFs, mais vulnerabilidades encontra!**""")
        return
    
    url = context.args[0]
    
    # Validar URL
    if not url.startswith(('http://', 'https://')):
        url = f"http://{url}"
    
    await update.message.reply_text(f"""🔥 **LIBERTUS VPS SCANNER INICIADO**

🎯 Alvo: {url}

📡 **EXECUTANDO:**
[1/5] 🔍 NMAP scan completo...
[2/5] 🌐 Análise HTTP avançada...
[3/5] 💉 SQL Injection (IA + PDFs)...
[4/5] 🎭 XSS testing (IA + PDFs)...
[5/5] 💥 Verificação de exploits...

📚 Usando conhecimento de {rag.collection.count()} documentos!

*Isso pode levar 60-90 segundos...*""")
    
    try:
        # 🔥 SCANNER VPS COMPLETO!
        relatorio = await wrapper_vps.scan_completo_vps(url)
        
        # Enviar relatório
        # Se for muito grande, dividir em partes
        if len(relatorio) > 4000:
            # Telegram tem limite de 4096 caracteres
            partes = [relatorio[i:i+4000] for i in range(0, len(relatorio), 4000)]
            
            for i, parte in enumerate(partes, 1):
                if i == 1:
                    await update.message.reply_text(f"""✅ **SCAN VPS COMPLETO!**

{parte}""")
                else:
                    await update.message.reply_text(parte)
        else:
            await update.message.reply_text(f"""✅ **SCAN VPS COMPLETO!**

{relatorio}""")
        
        # Footer
        await update.message.reply_text(f"""
💡 **SISTEMA EVOLUIU!**

📊 Módulos usados:
• NMAP (portas e serviços)
• HTTP (headers, forms, tech)
• SQL Injection (IA + PDFs)
• XSS (IA + PDFs)
• Exploit Verification

📚 Conhecimento: {rag.collection.count()} documentos

**🔥 QUANTO MAIS PDFs, MAIS PODEROSO FICA!**

Envie mais PDFs com /upload para melhorar!""")
        
    except Exception as e:
        await update.message.reply_text(f"""❌ Erro ao scanear: {e}

**Debug info:**
- URL: {url}
- RAG docs: {rag.collection.count()}
- Wrapper: {'OK' if wrapper_vps else 'ERRO'}

Tente novamente ou envie mais PDFs com /upload""")

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

async def evolucao_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /evolucao — estado vivo do LIBERTUS"""
    if not EVOLUCAO_DISPONIVEL or not mv:
        await update.message.reply_text(
            "⚠️ Módulos de evolução não ativos\n\n"
            "Instale: pip install supabase --break-system-packages"
        )
        return
    try:
        linhas = ["🧬 *LIBERTUS — ESTADO VIVO*\n"]
        if mv:
            top = mv.buscar(limite=3, peso_minimo=3.0)
            linhas.append("🧠 *Memórias mais vivas:*")
            for m in top:
                linhas.append(f"  [{m.get('peso_vivo',0):.1f}] {m.get('titulo','?')[:40]}")
        if le:
            erros = le._buscar_erros_relevantes("", 3)
            linhas.append(f"\n📕 *Erros não corrigidos:* {len(erros)}")
            for e in erros[:2]:
                linhas.append(f"  [{e.get('score',0):.1f}] {e.get('causa_provavel','?')[:50]}")
        if ac:
            prox = ac.proxima_a_estudar()
            if prox:
                linhas.append(f"\n🤔 *Próximo estudo:*")
                linhas.append(f"  {prox.get('pergunta','?')[:80]}")
        if ic:
            tracos = ic._carregar_tracos(3)
            total  = len(ic._carregar_tracos(50))
            linhas.append(f"\n🧬 *Traços cognitivos:* {total}")
            for t in tracos:
                linhas.append(f"  [{t.get('peso',0):.0f}/10] {t.get('descricao','?')[:50]}")
        await update.message.reply_text("\n".join(linhas), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {e}")


async def mensagem_texto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensagens de texto livres — passa pelo cérebro central LIBERTUS VPS REAL"""
    texto = update.message.text
    user  = update.effective_user.first_name or "Lorran"

    await update.message.reply_text("🧠 Processando pelo LIBERTUS VPS...")

    # ── CÉREBRO CENTRAL: libertus.py com histórico ────────────────────
    try:
        from libertus_telegram_adapter import get_libertus_adapter
        adapter = get_libertus_adapter()
        if adapter.esta_disponivel():
            resposta = adapter.processar(texto, historico_externo=get_historico(context))
            print(f"[DEBUG] Resposta do cérebro: {repr(str(resposta)[:100])}")
            resposta_str = str(resposta).strip() if resposta else ""
            if resposta_str and len(resposta_str) > 10:
                add_historico(context, "user", texto)
                add_historico(context, "assistant", resposta_str[:600])
                salvar_conversa_na_memoria(texto, resposta_str)
                await update.message.reply_text(f"🤖 {resposta_str}")
                return
            else:
                print(f"[DEBUG] Resposta curta ou vazia: {repr(resposta_str)}")
    except Exception as e:
        import traceback
        print(f"⚠️ Cérebro erro: {e}")
        traceback.print_exc()

    # ── Fallback: RAG + IA ─────────────────────────────────────────────
    if not RAG_DISPONIVEL:
        await update.message.reply_text("⚠️ Sistema não disponível. Tente /ask")
        return
    try:
        # Memória Viva
        ctx_extra = ""
        _memorias_usadas = []
        if EVOLUCAO_DISPONIVEL and mv:
            mems = mv.buscar_e_rastrear(texto, limite=3)
            if mems:
                _memorias_usadas = mems
                ctx_extra = "\n[MEMÓRIA VIVA]\n" + "\n".join(
                    f"- {m['titulo']}: {(m.get('conteudo') or '')[:150]}"
                    for m in mems
                )
        if EVOLUCAO_DISPONIVEL and le:
            aviso = le.consultar(texto)
            if aviso:
                ctx_extra += "\n\n" + aviso

        # ── Conversas passadas relevantes ──
        conv_passadas = buscar_conversas_relevantes(texto)
        if conv_passadas:
            ctx_extra += "\n\n" + conv_passadas

        documentos = rag.buscar_conhecimento(texto, n_results=5)
        contexto_final = _docs_para_texto(documentos) + ctx_extra

        # Histórico de conversa com system prompt rico
        historico = get_historico(context)
        messages = [{"role": "system", "content": build_system_prompt_rico()}]
        messages += historico
        conteudo_usuario = f"{contexto_final}\n\nPergunta: {texto}" if contexto_final.strip() else texto
        messages.append({"role": "user", "content": conteudo_usuario})

        try:
            completion = ia.client.chat.completions.create(
                messages=messages, model=ia.model, temperature=0.7, max_tokens=2048
            )
            resposta = completion.choices[0].message.content
        except Exception as e:
            resposta = ia.responder_com_contexto(pergunta=texto, contexto=contexto_final, area="geral")

        add_historico(context, "user", texto)
        add_historico(context, "assistant", resposta[:600])
        salvar_conversa_na_memoria(texto, resposta)
        await update.message.reply_text(f"🤖 {resposta}")

        # Feedback
        if EVOLUCAO_DISPONIVEL and mv and _memorias_usadas:
            score = 8.0 if len(str(resposta)) > 200 else 4.0
            for m in _memorias_usadas:
                try:
                    mv.foi_util(m["id"]) if score >= 7 else mv.foi_inutil(m["id"])
                except Exception:
                    pass
    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {e}")

# ==================== MAIN ====================

async def scan_nmap_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /scan [alvo] — executa nmap real e salva resultado na memória"""
    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Use: /scan [alvo]\n\nExemplos:\n  /scan scanme.nmap.org\n  /scan 192.168.1.1\n  /scan localhost"
        )
        return

    alvo = args[0]
    await update.message.reply_text(f"🔍 Iniciando scan em {alvo}... pode demorar até 2 min.")

    try:
        import subprocess, sys
        sys.path.insert(0, "./core")
        from pathlib import Path
        from scanner import Scanner

        scanner = Scanner(Path("./core").parent)
        if not scanner.nmap_ok:
            await update.message.reply_text("❌ nmap não encontrado. Verifique a instalação.")
            return

        # Executar scan em thread separada para não bloquear
        import asyncio
        loop = asyncio.get_event_loop()
        resultado = await loop.run_in_executor(None, scanner.scan_rapido, alvo)

        # Formatar resultado
        resposta = scanner.interpretar(resultado)

        # Salvar na memória para uso futuro
        if EVOLUCAO_DISPONIVEL and mv:
            try:
                from supabase_client import Supabase
                sb = Supabase()
                portas_str = ", ".join(
                    f"{p['porta']}/{p.get('servico','?')}"
                    for p in resultado.get('portas', [])
                )
                sb.post("libertus_memoria", {
                    "tipo": "scan_resultado",
                    "titulo": f"Scan nmap: {alvo}",
                    "conteudo": "Alvo: " + alvo + "\nPortas: " + portas_str + "\n\n" + resposta[:800],
                    "tags": ["nmap", "scan", alvo],
                    "projeto": "SHIELD",
                    "peso_vivo": 8.0,
                    "decaimento_ativo": True
                })
                print(f"  ✅ Resultado do scan salvo na memória")
            except Exception as e:
                print(f"  ⚠️ Erro ao salvar scan: {e}")

        # Enviar resultado (Telegram tem limite de 4096 chars)
        if len(resposta) > 4000:
            partes = [resposta[i:i+4000] for i in range(0, len(resposta), 4000)]
            for parte in partes:
                await update.message.reply_text(parte)
        else:
            await update.message.reply_text(resposta or "✅ Scan concluído — nenhuma porta aberta encontrada.")

    except Exception as e:
        await update.message.reply_text(f"❌ Erro no scan: {e}")


async def sqli_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /sqli [url] — executa sqlmap e salva resultado na memória"""
    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Use: /sqli [url]\n\nExemplos:\n  /sqli http://testphp.vulnweb.com/artists.php?artist=1\n\n⚠️ Use apenas em alvos com autorização!"
        )
        return

    url = args[0]
    await update.message.reply_text(f"💉 Iniciando teste SQLi em {url}...\nIsso pode demorar alguns minutos.")

    try:
        import asyncio, subprocess
        sqlmap_path = "/snap/bin/sqlmap"
        import os
        snap_env = os.environ.copy()
        snap_env["PATH"] = "/snap/bin:/root/go/bin:/home/libertus/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

        cmd = [sqlmap_path, "-u", url, "--batch", "--random-agent",
               "--level=1", "--risk=1", "--dbs", "--timeout=30",
               "--output-dir=/tmp/sqlmap_out"]

        loop = asyncio.get_event_loop()

        def rodar_sqlmap():
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=snap_env)
            return r.stdout + r.stderr

        output = await loop.run_in_executor(None, rodar_sqlmap)

        # Extrair informações relevantes
        linhas_relevantes = [
            l for l in output.split("\n")
            if any(k in l.lower() for k in [
                "vulnerable", "vulnerável", "parameter", "database",
                "payload", "injection", "error", "available databases",
                "[*]", "[+]", "[!]"
            ])
        ]
        resumo = "\n".join(linhas_relevantes[:50]) if linhas_relevantes else output[:2000]

        # Salvar na memória
        if EVOLUCAO_DISPONIVEL and mv:
            try:
                from supabase_client import Supabase
                sb = Supabase()
                sb.post("libertus_memoria", {
                    "tipo": "sqli_resultado",
                    "titulo": f"SQLi: {url[:60]}",
                    "conteudo": f"URL: {url}\n\n" + resumo[:800],
                    "tags": ["sqlmap", "sqli", "pentest"],
                    "projeto": "SHIELD",
                    "peso_vivo": 8.0,
                    "decaimento_ativo": True
                })
            except Exception:
                pass

        resposta = f"💉 RESULTADO SQLi\nAlvo: {url}\n\n" + resumo[:3500]
        await update.message.reply_text(resposta)

    except subprocess.TimeoutExpired:
        await update.message.reply_text("⏱️ Timeout — o sqlmap demorou demais. Tente com um alvo mais simples.")
    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {e}")


async def estudar_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /estudar — LIBERTUS busca na web e aprende autonomamente"""
    limite = 1
    if context.args:
        try:
            limite = min(int(context.args[0]), 5)
        except Exception:
            pass

    await update.message.reply_text(f"📚 Buscando e aprendendo {limite} topico(s) da fila de estudo...\nIsso pode levar alguns instantes.")

    try:
        import sys
        sys.path.insert(0, "./core")
        from buscador_autonomo import BuscadorAutonomo
        from supabase_client import Supabase
        from groq_client import Groq
        import os

        sb = Supabase()
        groq = Groq(os.environ.get("GROQ_API_KEY", ""))
        ba = BuscadorAutonomo(groq_client=groq, supabase_client=sb)

        import asyncio
        loop = asyncio.get_event_loop()
        respondidas = await loop.run_in_executor(None, lambda: ba.ciclo(limite=limite))

        if not respondidas:
            # Mostrar fila de estudo
            fila = sb.get("libertus_fila_estudo", "limit=5") or []
            if fila:
                linhas = ["📋 *Fila de estudo atual:*"]
                for c in fila:
                    linhas.append(f"  [{c.get('urgencia',0):.1f}] {c.get('pergunta','?')[:60]}")
                await update.message.reply_text("\n".join(linhas), parse_mode="Markdown")
            else:
                await update.message.reply_text("✅ Nenhuma curiosidade pendente no momento!")
            return

        # Reportar o que aprendeu
        linhas = [f"🧠 *LIBERTUS aprendeu {len(respondidas)} novo(s) tópico(s):*\n"]
        for r in respondidas:
            linhas.append(f"📌 *{r.get('pergunta','?')[:60]}*")
            linhas.append(f"_{r.get('resumo','')[:150]}..._")
            linhas.append("")

        await update.message.reply_text("\n".join(linhas), parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Erro ao estudar: {e}")


async def limpar_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /limpar — reseta histórico de conversa"""
    limpar_historico(context)
    await update.message.reply_text("🧹 Histórico limpo! Começando nova conversa.")


def main():
    print("🔥 Iniciando LIBERTUS RAG + IA Bot...")
    
    if not RAG_DISPONIVEL:
        print("⚠️ RAG + IA não disponíveis - instale dependências:")
        print("pip install chromadb PyPDF2 sentence-transformers --break-system-packages")
    
    app = Application.builder().token(TOKEN).build()
    
    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("evolucao", evolucao_comando))
    app.add_handler(CommandHandler("limpar", limpar_comando))
    app.add_handler(CommandHandler("scan", scan_nmap_comando))
    app.add_handler(CommandHandler("estudar", estudar_comando))
    app.add_handler(CommandHandler("sqli", sqli_comando))
    app.add_handler(CommandHandler("stats", stats_comando))
    app.add_handler(CommandHandler("upload", upload_comando))
    app.add_handler(CommandHandler("ask", ask_comando))
    app.add_handler(CommandHandler("create", create_comando))
    app.add_handler(CommandHandler("scan", scan_comando))  # SCANNER INTELIGENTE!
    
    # Documentos (PDFs)
    app.add_handler(MessageHandler(filters.Document.PDF, receber_documento))
    
    # Mensagens de texto
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mensagem_texto))
    
    print("✅ Bot RAG + IA rodando!")
    print("📱 Comandos: /start, /upload, /ask, /create, /stats, /scan, /sqli, /evolucao, /limpar")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
