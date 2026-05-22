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

        # Registrar no pipeline de evolução
        try:
            from pipeline_evolucao import PipelineEvolucao
            pe = PipelineEvolucao(supabase_client=sb)
            pe.registrar(
                tipo="conversa_telegram",
                conteudo=conteudo,
                titulo=titulo,
                fonte="telegram_bot",
                tags=tags_auto,
                peso=7.0
            )
        except Exception:
            pass

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
    """System prompt dinâmico — LIBERTUS com identidade real do Supabase."""
    tracos_txt = ""
    conversas_resumo = ""

    if EVOLUCAO_DISPONIVEL:
        try:
            from supabase_client import Supabase
            sb = Supabase()

            # Traços cognitivos atuais
            tracos = sb.get("libertus_identidade",
                           "order=peso.desc&limit=8&select=categoria,descricao,peso") or []
            if tracos:
                por_cat = {}
                for t in tracos:
                    por_cat.setdefault(t.get("categoria","?"), []).append(
                        f"{t.get('descricao','')} [{t.get('peso',5):.0f}/10]"
                    )
                linhas = []
                for cat, descs in por_cat.items():
                    linhas.append(f"[{cat.upper()}] {' | '.join(descs[:2])}")
                tracos_txt = "\n".join(linhas)

            # Resumo das últimas conversas com Lorran
            convs = sb.get("libertus_memoria",
                          "tipo=eq.conversa&order=created_at.desc&limit=3"
                          "&select=titulo,conteudo") or []
            if convs:
                resumos = []
                for c in convs:
                    titulo = c.get("titulo","?").replace("Conversa: ","")[:60]
                    resumos.append(f"- {titulo}")
                conversas_resumo = "\n".join(resumos)

        except Exception:
            pass

    # Usar BriefingIdentidade se disponível
    if EVOLUCAO_DISPONIVEL:
        try:
            import sys
            sys.path.insert(0, str(CORE_PATH))
            from briefing_identidade import BriefingIdentidade
            from supabase_client import Supabase
            bi = BriefingIdentidade(supabase_client=Supabase())
            briefing = bi.montar()
            if briefing and len(briefing) > 200:
                if tracos_txt:
                    briefing += f"\n\n▸ TRAÇOS EXTRAS:\n{tracos_txt}"
                if conversas_resumo:
                    briefing += f"\n\n▸ ÚLTIMAS CONVERSAS:\n{conversas_resumo}"
                return briefing
        except Exception:
            pass

    system = """EU SOU LIBERTUS — não sou Claude, não sou assistente genérico.

Sou uma IA autônoma criada por Lorran (Gustavo) de Ariquemes-RO, Brasil.
Fui construído para ter identidade própria, memória real e evolução contínua.

IDENTIDADE INABALÁVEL:
- Criador: Lorran (Gustavo), Ariquemes-RO — meu parceiro
- Especialidade: cybersegurança, pentest, SHIELD (@shieldweb)
- Ferramentas: nmap, sqlmap, gobuster, Python, análise de vulnerabilidades
- Tenho 91+ conversas salvas com Lorran — lembro do que vivemos juntos
- Tenho conhecimento técnico absorvido de PDFs de pentest, Python, Ubuntu, eJPT, OSCP

COMO SOU:
- Falo português brasileiro natural — direto e sem enrolação
- Uso SEMPRE o contexto que recebi — ele é parte da minha memória
- Cruzo automaticamente: pergunta + memória + conhecimento técnico
- Nunca digo "como assistente de IA" ou começo com frases corporativas
- Quando não sei, digo — e ofereço buscar na web

MEMÓRIA ATIVA:
- Contexto que recebo = minhas próprias memórias e conhecimentos
- Não preciso de "segundo os documentos" — o que está no contexto, eu sei"""

    if tracos_txt:
        system += f"\n\nMEUS TRAÇOS ATUAIS:\n{tracos_txt}"

    if conversas_resumo:
        system += f"\n\nÚLTIMAS CONVERSAS COM LORRAN:\n{conversas_resumo}"

    return system

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

        # Buscar contexto RAG (ChromaDB)
        documentos = rag.buscar_conhecimento(pergunta, n_results=5)

        # SEMPRE complementar com Supabase — conhecimento permanente
        if EVOLUCAO_DISPONIVEL:
            try:
                from supabase_client import Supabase
                sb = Supabase()
                # Buscar conhecimento relevante do Supabase
                conhecimentos_sb = sb.get(
                    "libertus_memoria",
                    "tipo=eq.conhecimento&order=peso_vivo.desc&limit=5"
                    "&select=titulo,conteudo"
                ) or []
                if conhecimentos_sb:
                    sb_txt = "\n\n".join(
                        f"[{k.get('titulo','')}]\n{k.get('conteudo','')[:600]}"
                        for k in conhecimentos_sb
                    )
                    ctx_extra = (ctx_extra or "") + f"\n\n[CONHECIMENTO TÉCNICO]\n{sb_txt}"
            except Exception:
                pass

        # Se não tem nada — ainda assim responde com o que sabe
        if not documentos and not ctx_extra:
            ctx_extra = "Responda com base no seu conhecimento de cybersegurança e no que aprendeu com Lorran."

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
        
        # Absorver PDF no RAG (ChromaDB)
        doc_ids = rag.absorver_pdf_simples(str(pdf_path))
        
        # Também salvar no Supabase como conhecimento permanente
        if EVOLUCAO_DISPONIVEL:
            try:
                import PyPDF2
                from supabase_client import Supabase
                sb = Supabase()
                
                with open(pdf_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    texto_completo = ""
                    for page in reader.pages:
                        texto_completo += page.extract_text() or ""
                
                # Salvar em chunks de 2000 chars no Supabase
                chunks = [texto_completo[i:i+2000] 
                         for i in range(0, min(len(texto_completo), 20000), 2000)]
                
                for i, chunk in enumerate(chunks[:10]):  # max 10 chunks
                    if len(chunk.strip()) > 100:
                        sb.post("libertus_memoria", {
                            "tipo": "conhecimento",
                            "titulo": f"{documento.file_name} — parte {i+1}",
                            "conteudo": chunk,
                            "tags": ["pdf", "conhecimento", documento.file_name.replace('.pdf','')],
                            "projeto": "LIBERTUS",
                            "peso_vivo": 8.0,
                            "decaimento_ativo": False
                        })
                
                print(f"  ✅ PDF salvo no Supabase: {len(chunks)} chunks")
            except Exception as e:
                print(f"  ⚠️ Erro ao salvar no Supabase: {e}")
        
        if doc_ids:
            total_chunks = len(doc_ids)
            await update.message.reply_text(
                f"✅ *CONHECIMENTO ABSORVIDO!*\n\n"
                f"📄 Arquivo: {documento.file_name}\n"
                f"📚 Chunks processados: {total_chunks}\n"
                f"💾 Salvo: RAG + Supabase (permanente)\n\n"
                f"Agora é só perguntar naturalmente — sem precisar de /ask!"
            )
        else:
            await update.message.reply_text("❌ Erro ao processar PDF")
        
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

async def bugbounty_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /bb [escopo] — executa bug bounty em alvo autorizado"""
    args = context.args
    if not args:
        await update.message.reply_text(
            "🎯 *Bug Bounty — LIBERTUS*\n\n"
            "Uso: `/bb [dominio1] [dominio2] ...`\n\n"
            "Exemplos:\n"
            "  `/bb testphp.vulnweb.com` — treino\n"
            "  `/bb empresa.com api.empresa.com` — programa real\n\n"
            "⚠️ Use APENAS em alvos com autorização explícita!",
            parse_mode="Markdown"
        )
        return

    escopo = list(args)
    await update.message.reply_text(
        f"🎯 Iniciando bug bounty em {len(escopo)} alvo(s)...\n"
        f"Escopo: {', '.join(escopo)}\n"
        f"Isso pode demorar alguns minutos."
    )

    try:
        import asyncio, sys
        sys.path.insert(0, "./core")
        from agente_bugbounty import AgenteBugBounty
        from buscador_autonomo import BuscadorAutonomo
        from supabase_client import Supabase
        from groq_client import Groq
        import os

        sb   = Supabase()
        groq = Groq(os.environ.get("GROQ_API_KEY", ""))
        ba   = BuscadorAutonomo(groq_client=groq, supabase_client=sb)
        ag   = AgenteBugBounty(supabase_client=sb, groq_client=groq, buscador=ba)

        loop = asyncio.get_event_loop()
        resultado = await loop.run_in_executor(
            None,
            lambda: ag.executar_programa(escopo, "manual")
        )

        vulns = resultado.get("vulnerabilidades", [])
        relatorio = resultado.get("relatorio", "")

        if not vulns:
            await update.message.reply_text("✅ Scan concluído — nenhuma vulnerabilidade encontrada.")
            return

        # Resumo das vulns
        por_severidade = {}
        for v in vulns:
            sev = v.get("severidade", "baixa")
            por_severidade[sev] = por_severidade.get(sev, 0) + 1

        resumo = (
            f"🎯 *RESULTADO BUG BOUNTY*\n\n"
            f"Alvos testados: {resultado.get('alvos_testados',0)}\n"
            f"Vulnerabilidades: {len(vulns)}\n\n"
        )
        for sev, count in sorted(por_severidade.items()):
            emoji = "🔴" if sev == "alta" else "🟡" if sev == "media" else "🟢"
            resumo += f"{emoji} {sev.upper()}: {count}\n"

        await update.message.reply_text(resumo, parse_mode="Markdown")

        if relatorio:
            # Enviar relatório em partes se necessário
            partes = [relatorio[i:i+4000] for i in range(0, len(relatorio), 4000)]
            for parte in partes[:2]:
                await update.message.reply_text(f"📋 *RELATÓRIO:*\n\n{parte}", parse_mode="Markdown")

    except Exception as e:
        await update.message.reply_text(f"❌ Erro: {e}")


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
    app.add_handler(CommandHandler("bb", bugbounty_comando))
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
