#!/usr/bin/env python3
"""
LIBERTUS CLI - Interface de Comunicação
Permite usar Libertus sem depender do Claude

Comandos:
- libertus scan <URL>        # Scanner completo
- libertus exploit <URL>     # Scanner avançado com validação
- libertus memory <query>    # Busca nas memórias
- libertus status            # Status do sistema
- libertus learn <topic>     # Força aprendizado
"""

import sys
import asyncio
import json
from pathlib import Path

# Importa módulos do Libertus
sys.path.insert(0, '/root/LIBERTUS')
sys.path.insert(0, '/root/LIBERTUS/core')

from libertus_scanner import LibertusScanner
from libertus_advanced_scanner import AdvancedScanner

BANNER = """
╔════════════════════════════════════════════════════════════╗
║                  LIBERTUS v10 CLI                          ║
║            Autonomous Cybersecurity System                 ║
╚════════════════════════════════════════════════════════════╝
"""

def show_help():
    """Mostra ajuda."""
    print(BANNER)
    print("COMANDOS DISPONÍVEIS:\n")
    print("🔍 SCANNING:")
    print("   libertus scan <URL> [--pdf]  # Scanner completo (opcional: gera PDF)")
    print("   libertus exploit <URL>       # Scanner avançado (validação)")
    print()
    print("📄 RELATÓRIOS:")
    print("   libertus report <json> <empresa>  # Gera PDF de scan")
    print("   libertus analyze <empresa> <url>  # Análise comercial completa")
    print()
    print("🧠 MEMÓRIA:")
    print("   libertus memory <query>      # Busca conhecimento")
    print("   libertus memories            # Lista todas memórias")
    print()
    print("📊 STATUS:")
    print("   libertus status              # Status do daemon")
    print("   libertus stats               # Estatísticas")
    print()
    print("EXEMPLOS:")
    print("   libertus scan https://exemplo.com --pdf")
    print("   libertus analyze \"HBB Contabilidade\" https://hbb.com.br")
    print("   libertus report scan_resultado.json \"Marques Imóveis\"")
    print()

async def cmd_scan(url):
    """Scanner completo."""
    gerar_pdf = '--pdf' in sys.argv
    
    print(f"\n🔍 Iniciando scan completo de: {url}\n")
    scanner = LibertusScanner(url)
    resultado = await scanner.run_full_scan()
    
    vulns = len(resultado.get('vulnerabilities', []))
    print(f"\n✅ Scan concluído! {vulns} vulnerabilidades detectadas")
    
    # Gera PDF se solicitado
    if gerar_pdf and vulns > 0:
        print("\n📄 Gerando relatório PDF...")
        try:
            from relatorio_profissional import RelatorioProfissional
            
            gerador = RelatorioProfissional()
            empresa = url.split("//")[1].split("/")[0].split(".")[0].title()
            
            pdf_path = gerador.gerar_relatorio_completo(
                resultado,
                empresa,
                "Empresa"
            )
            print(f"✅ PDF gerado: {pdf_path}")
        except Exception as e:
            print(f"❌ Erro ao gerar PDF: {e}")

async def cmd_exploit(url):
    """Scanner avançado com validação."""
    print(f"\n🔥 Iniciando scan avançado de: {url}\n")
    scanner = AdvancedScanner(url)
    await scanner.run_advanced_scan()

def cmd_memory(query):
    """Busca nas memórias."""
    print(f"\n🧠 Buscando: '{query}' nas memórias...\n")
    
    conhecimento_dir = Path("/root/LIBERTUS/memoria/conhecimento")
    if not conhecimento_dir.exists():
        print("❌ Diretório de memórias não encontrado")
        return
    
    results = []
    query_lower = query.lower()
    
    for mem_file in conhecimento_dir.glob("*.json"):
        try:
            mem_data = json.loads(mem_file.read_text())
            
            # Busca em título, conteúdo e tags
            titulo = mem_data.get("titulo", "").lower()
            conteudo = mem_data.get("conteudo", "").lower()
            tags = " ".join(mem_data.get("tags", [])).lower()
            
            if query_lower in titulo or query_lower in conteudo or query_lower in tags:
                results.append(mem_data)
        except:
            pass
    
    if not results:
        print(f"❌ Nenhuma memória encontrada para '{query}'")
        return
    
    print(f"✅ {len(results)} memória(s) encontrada(s):\n")
    for i, mem in enumerate(results[:5], 1):  # Top 5
        print(f"[{i}] {mem.get('titulo')}")
        print(f"    Tags: {', '.join(mem.get('tags', []))}")
        preview = mem.get('conteudo', '')[:200]
        print(f"    Preview: {preview}...")
        print()

def cmd_memories():
    """Lista todas as memórias."""
    conhecimento_dir = Path("/root/LIBERTUS/memoria/conhecimento")
    
    if not conhecimento_dir.exists():
        print("❌ Diretório de memórias não encontrado")
        return
    
    memorias = list(conhecimento_dir.glob("*.json"))
    
    print(f"\n📚 Total de memórias: {len(memorias)}\n")
    
    # Agrupa por tipo
    tipos = {}
    for mem_file in memorias:
        try:
            mem_data = json.loads(mem_file.read_text())
            tipo = mem_data.get("tipo", "unknown")
            tipos[tipo] = tipos.get(tipo, 0) + 1
        except:
            pass
    
    print("📊 Por tipo:")
    for tipo, count in tipos.items():
        print(f"   • {tipo}: {count}")
    print()

def cmd_status():
    """Mostra status do daemon."""
    print("\n📊 LIBERTUS STATUS:\n")
    
    heartbeat_file = Path("/root/LIBERTUS/memory/heartbeat.json")
    
    if not heartbeat_file.exists():
        print("❌ Daemon não está rodando (sem heartbeat)")
        return
    
    try:
        hb = json.loads(heartbeat_file.read_text())
        
        print(f"✅ Daemon ATIVO")
        print(f"   Timestamp: {hb.get('timestamp')}")
        print(f"   Uptime: {hb.get('uptime_horas'):.2f} horas")
        print(f"   Ticks: {hb.get('ticks')}")
        print()
        print("📈 Estatísticas:")
        for key, value in hb.get('stats', {}).items():
            print(f"   • {key}: {value}")
        print()
        
    except Exception as e:
        print(f"❌ Erro ao ler heartbeat: {e}")

def cmd_stats():
    """Estatísticas detalhadas."""
    cmd_status()
    cmd_memories()

def cmd_report(json_path, empresa):
    """Gera PDF de um scan."""
    print(f"\n📄 Gerando relatório PDF para {empresa}...")
    
    scan_file = Path(json_path)
    if not scan_file.exists():
        print(f"❌ Arquivo não encontrado: {json_path}")
        return
    
    try:
        from relatorio_profissional import RelatorioProfissional
        
        scan_data = json.loads(scan_file.read_text())
        gerador = RelatorioProfissional()
        
        pdf_path = gerador.gerar_relatorio_completo(
            scan_data,
            empresa,
            "Empresa"
        )
        
        print(f"✅ PDF gerado: {pdf_path}")
        print(f"📁 Localização: {pdf_path.parent}")
        
    except Exception as e:
        print(f"❌ Erro ao gerar PDF: {e}")

def cmd_analyze(empresa, url):
    """Análise comercial completa."""
    print(f"\n🧠 Analisando {empresa}...")
    print(f"🔍 URL: {url}\n")
    
    try:
        # Escaneia primeiro
        print("📊 Fase 1: Escaneando vulnerabilidades...")
        scanner = LibertusScanner(url)
        resultado = asyncio.run(scanner.run_full_scan())
        
        # Analisa comercialmente
        print("💼 Fase 2: Análise comercial...")
        from inteligencia_comercial import InteligenciaComercial
        
        intel = InteligenciaComercial()
        analise = intel.calcular_score_lead(
            empresa=empresa,
            url=url,
            vulnerabilidades=resultado.get('vulnerabilities', []),
            tamanho_estimado="medio"
        )
        
        # Mostra resultados
        print(f"\n" + "="*60)
        print(f"📊 ANÁLISE COMERCIAL - {empresa}")
        print("="*60)
        print(f"\n🏢 Tipo de Empresa: {analise['tipo'].upper()}")
        print(f"📈 Score: {analise['score']}/100")
        print(f"💰 Probabilidade Conversão: {analise['probabilidade_conversao']}%")
        print(f"💵 Valor Estimado: R$ {analise['valor_estimado_min']}-{analise['valor_estimado_max']}")
        print(f"⚠️  Urgência LGPD: {analise['urgencia_lgpd']}/10")
        print(f"\n🚨 Vulnerabilidades:")
        print(f"   • Críticas: {analise['vulnerabilidades']['criticas']}")
        print(f"   • Altas: {analise['vulnerabilidades']['altas']}")
        print(f"   • Médias: {analise['vulnerabilidades']['medias']}")
        print(f"   • Total: {analise['vulnerabilidades']['total']}")
        print(f"\n💡 Recomendação:")
        print(f"   {analise['recomendacao_acao']}")
        print(f"\n📋 Dados Sensíveis em Risco:")
        print(f"   {analise['dados_sensiveis']}")
        print("="*60 + "\n")
        
        # Gera argumentos de venda
        args = intel.gerar_argumentos_venda(
            analise['tipo'],
            resultado.get('vulnerabilities', [])
        )
        
        print("💬 ARGUMENTOS DE VENDA:")
        print(f"   Urgência: {args['urgencia']}")
        print(f"   Call-to-Action: {args['call_to_action']}")
        print()
        
    except Exception as e:
        print(f"❌ Erro na análise: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Função principal."""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(0)
    
    command = sys.argv[1].lower()
    
    if command in ['help', '-h', '--help']:
        show_help()
    
    elif command == 'scan':
        if len(sys.argv) < 3:
            print("❌ Uso: libertus scan <URL>")
            sys.exit(1)
        url = sys.argv[2]
        asyncio.run(cmd_scan(url))
    
    elif command == 'exploit':
        if len(sys.argv) < 3:
            print("❌ Uso: libertus exploit <URL>")
            sys.exit(1)
        url = sys.argv[2]
        asyncio.run(cmd_exploit(url))
    
    elif command == 'memory':
        if len(sys.argv) < 3:
            print("❌ Uso: libertus memory <query>")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        cmd_memory(query)
    
    elif command == 'memories':
        cmd_memories()
    
    elif command == 'status':
        cmd_status()
    
    elif command == 'stats':
        cmd_stats()
    
    elif command == 'report':
        if len(sys.argv) < 4:
            print("❌ Uso: libertus report <json> <empresa>")
            sys.exit(1)
        json_path = sys.argv[2]
        empresa = sys.argv[3]
        cmd_report(json_path, empresa)
    
    elif command == 'analyze':
        if len(sys.argv) < 4:
            print("❌ Uso: libertus analyze <empresa> <url>")
            sys.exit(1)
        empresa = sys.argv[2]
        url = sys.argv[3]
        cmd_analyze(empresa, url)
    
    else:
        print(f"❌ Comando desconhecido: {command}")
        print("   Use 'libertus help' para ver comandos disponíveis")


if __name__ == "__main__":
    main()
