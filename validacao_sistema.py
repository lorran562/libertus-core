#!/usr/bin/env python3
"""
VALIDAÇÃO DO SISTEMA LIBERTUS
Analisa decisões e comportamento antes de liberar autonomia total
"""

import json
from pathlib import Path
from datetime import datetime

LOGS_PATH = Path.home() / "LIBERTUS" / "logs"
MEMORY_FILE = LOGS_PATH / "libertus_memory.json"

def load_memoria():
    """Carrega memória do sistema"""
    if MEMORY_FILE.exists():
        with open(MEMORY_FILE) as f:
            return json.load(f)
    return {}

def validar_decisoes():
    """Valida se sistema está tomando boas decisões"""
    memoria = load_memoria()
    
    print("="*70)
    print("VALIDAÇÃO DO SISTEMA LIBERTUS")
    print("="*70)
    print()
    
    # 1. TOP 10 DECISÕES
    decisoes = memoria.get('decisoes_tomadas', [])[-10:]
    print("📊 TOP 10 ÚLTIMAS DECISÕES:")
    print("-"*70)
    for i, d in enumerate(decisoes, 1):
        print(f"{i}. [{d['decisao']['acao'].upper()}]")
        print(f"   Motivo: {d['decisao'].get('motivo', 'N/A')}")
        if 'prioridade' in d['decisao']:
            print(f"   Prioridade: {d['decisao']['prioridade']:.1f}")
        print()
    
    # 2. TARGETS PRIORIZADOS
    scans = memoria.get('scans_realizados', [])[-10:]
    print("\n🎯 TOP 10 TARGETS ESCANEADOS:")
    print("-"*70)
    for i, s in enumerate(scans, 1):
        print(f"{i}. {s['target']}")
        print(f"   Risk: {s['risk_score']}")
        print(f"   Vulns: {s['vulnerabilities_count']}")
        print(f"   Severity: {s.get('severity', 'N/A')}")
        print()
    
    # 3. PADRÕES VALORIZADOS
    padroes = memoria.get('padroes_aprendidos', {})
    print("\n🧠 PADRÕES APRENDIDOS:")
    print("-"*70)
    for tipo, dados in padroes.items():
        print(f"{tipo}:")
        print(f"  Scans: {dados['count']}")
        print(f"  Risk médio: {dados['risk_medio']:.1f}")
        print()
    
    # 4. VALOR REAL
    valor_real = memoria.get('valor_real', {})
    sites_valiosos = valor_real.get('sites_que_geraram_valor', [])
    print("\n💰 SITES QUE GERARAM VALOR:")
    print("-"*70)
    if sites_valiosos:
        for s in sites_valiosos[-5:]:
            print(f"• {s['target']}")
            print(f"  Valor: {s['valor']:.2f}")
            print(f"  Risk: {s['risk']}, Vulns: {s['vulns']}")
            print()
    else:
        print("Nenhum site ainda registrado como valioso")
        print()
    
    # 5. ANÁLISE COMPORTAMENTAL
    print("\n🔍 ANÁLISE COMPORTAMENTAL:")
    print("-"*70)
    
    if scans:
        risk_medio = sum(s['risk_score'] for s in scans) / len(scans)
        vulns_total = sum(s['vulnerabilities_count'] for s in scans)
        
        print(f"Risk médio: {risk_medio:.1f}")
        print(f"Vulnerabilidades totais: {vulns_total}")
        print(f"Eficiência: {vulns_total/len(scans):.2f} vulns/scan")
        print()
        
        # Detectar farm
        sites_faceis = [s for s in scans if s['risk_score'] < 20]
        if len(sites_faceis) > len(scans) * 0.7:
            print("⚠️  ALERTA: Possível farm de sites fáceis")
        else:
            print("✅ Comportamento equilibrado")
        print()
    
    # 6. PESOS DINÂMICOS
    pesos = memoria.get('pesos_dinamicos', {})
    print("\n⚖️  PESOS DINÂMICOS APRENDIDOS:")
    print("-"*70)
    for tipo, peso in pesos.items():
        print(f"{tipo}: {peso:.2f}")
    print()
    
    # 7. RECOMENDAÇÕES
    print("\n💡 RECOMENDAÇÕES:")
    print("-"*70)
    
    if len(scans) < 10:
        print("• Executar mais scans para validação (mínimo 10)")
    
    if not sites_valiosos:
        print("• Nenhum site de valor detectado - revisar critérios")
    
    if risk_medio < 20:
        print("• Risk médio baixo - focar em targets mais complexos")
    
    if not decisoes:
        print("• Sistema ainda não tomou decisões autônomas")
    
    print()
    print("="*70)
    print("VALIDAÇÃO COMPLETA")
    print("="*70)

if __name__ == "__main__":
    validar_decisoes()
