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
    print("   libertus scan <URL>          # Scanner completo")
    print("   libertus exploit <URL>       # Scanner avançado (validação)")
    print()
    print("🧠 MEMÓRIA:")
    print("   libertus memory <query>      # Busca conhecimento")
    print("   libertus memories            # Lista todas memórias")
    print()
    print("📊 STATUS:")
    print("   libertus status              # Status do daemon")
    print("   libertus stats               # Estatísticas")
    print()
    print("📚 APRENDIZADO:")
    print("   libertus learn <topic>       # Força aprendizado")
    print()
    print("EXEMPLOS:")
    print("   libertus scan https://exemplo.com")
    print("   libertus exploit https://vulnsite.com")
    print("   libertus memory sql injection")
    print()

async def cmd_scan(url):
    """Scanner completo."""
    print(f"\n🔍 Iniciando scan completo de: {url}\n")
    scanner = LibertusScanner(url)
    await scanner.run_full_scan()

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
    
    else:
        print(f"❌ Comando desconhecido: {command}")
        print("   Use 'libertus help' para ver comandos disponíveis")


if __name__ == "__main__":
    main()
