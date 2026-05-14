#!/usr/bin/env python3
"""
LIBERTUS OBJETIVO SYSTEM
Sistema de objetivos autônomos com aprendizado direcionado
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional


class ObjetivoSystem:
    """
    Sistema de objetivos para LIBERTUS
    - Define objetivos claros
    - Mede progresso
    - Direciona aprendizado
    - Evolui autonomamente
    """
    
    def __init__(self):
        self.objetivo_dir = os.path.expanduser("~/LIBERTUS/objetivos")
        os.makedirs(self.objetivo_dir, exist_ok=True)
        
        self.objetivo_ativo = self._load_objetivo_ativo()
    
    def _load_objetivo_ativo(self) -> Optional[Dict]:
        """Carrega objetivo ativo"""
        
        objetivo_file = os.path.join(self.objetivo_dir, "objetivo_ativo.json")
        
        if os.path.exists(objetivo_file):
            with open(objetivo_file, "r") as f:
                return json.load(f)
        
        return None
    
    def definir_objetivo(
        self, 
        titulo: str, 
        descricao: str, 
        metricas: List[Dict],
        topicos_aprendizado: List[str]
    ) -> Dict:
        """Define novo objetivo"""
        
        objetivo = {
            "id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "titulo": titulo,
            "descricao": descricao,
            "data_inicio": datetime.now().isoformat(),
            "metricas": metricas,
            "topicos_aprendizado": topicos_aprendizado,
            "progresso": {
                "papers_lidos": 0,
                "vulnerabilidades_descobertas": 0,
                "scans_realizados": 0,
                "conhecimento_adquirido": []
            },
            "status": "ativo"
        }
        
        # Salvar objetivo ativo
        objetivo_file = os.path.join(self.objetivo_dir, "objetivo_ativo.json")
        with open(objetivo_file, "w") as f:
            json.dump(objetivo, f, indent=2)
        
        # Histórico
        historico_file = os.path.join(
            self.objetivo_dir, 
            f"objetivo_{objetivo['id']}.json"
        )
        with open(historico_file, "w") as f:
            json.dump(objetivo, f, indent=2)
        
        self.objetivo_ativo = objetivo
        
        return objetivo
    
    def atualizar_progresso(self, metrica: str, valor: int) -> Dict:
        """Atualiza progresso de uma métrica"""
        
        if not self.objetivo_ativo:
            return {"error": "Nenhum objetivo ativo"}
        
        if metrica in self.objetivo_ativo["progresso"]:
            self.objetivo_ativo["progresso"][metrica] += valor
        
        # Salvar
        objetivo_file = os.path.join(self.objetivo_dir, "objetivo_ativo.json")
        with open(objetivo_file, "w") as f:
            json.dump(self.objetivo_ativo, f, indent=2)
        
        return self.objetivo_ativo
    
    def adicionar_conhecimento(self, topico: str, fonte: str) -> Dict:
        """Registra conhecimento adquirido"""
        
        if not self.objetivo_ativo:
            return {"error": "Nenhum objetivo ativo"}
        
        conhecimento = {
            "topico": topico,
            "fonte": fonte,
            "timestamp": datetime.now().isoformat()
        }
        
        self.objetivo_ativo["progresso"]["conhecimento_adquirido"].append(conhecimento)
        
        # Salvar
        objetivo_file = os.path.join(self.objetivo_dir, "objetivo_ativo.json")
        with open(objetivo_file, "w") as f:
            json.dump(self.objetivo_ativo, f, indent=2)
        
        return conhecimento
    
    def calcular_progresso_geral(self) -> Dict:
        """Calcula progresso geral do objetivo"""
        
        if not self.objetivo_ativo:
            return {"error": "Nenhum objetivo ativo"}
        
        metricas = self.objetivo_ativo["metricas"]
        progresso = self.objetivo_ativo["progresso"]
        
        total_metricas = len(metricas)
        metricas_atingidas = 0
        
        detalhes = []
        
        for metrica in metricas:
            nome = metrica["nome"]
            meta = metrica["meta"]
            atual = progresso.get(nome, 0)
            
            percentual = min(100, (atual / meta * 100)) if meta > 0 else 0
            atingida = atual >= meta
            
            if atingida:
                metricas_atingidas += 1
            
            detalhes.append({
                "metrica": nome,
                "meta": meta,
                "atual": atual,
                "percentual": percentual,
                "atingida": atingida
            })
        
        progresso_geral = (metricas_atingidas / total_metricas * 100) if total_metricas > 0 else 0
        
        return {
            "objetivo": self.objetivo_ativo["titulo"],
            "progresso_geral": progresso_geral,
            "metricas_atingidas": f"{metricas_atingidas}/{total_metricas}",
            "detalhes": detalhes,
            "status": "completo" if progresso_geral >= 100 else "em_progresso"
        }
    
    def get_proximo_topico_aprendizado(self) -> Optional[str]:
        """Retorna próximo tópico para aprender"""
        
        if not self.objetivo_ativo:
            return None
        
        topicos = self.objetivo_ativo["topicos_aprendizado"]
        conhecimento = self.objetivo_ativo["progresso"]["conhecimento_adquirido"]
        
        # Tópicos já estudados
        estudados = {c["topico"] for c in conhecimento}
        
        # Próximo não estudado
        for topico in topicos:
            if topico not in estudados:
                return topico
        
        # Se todos estudados, retornar primeiro (revisão)
        return topicos[0] if topicos else None
    
    def gerar_relatorio(self) -> str:
        """Gera relatório de progresso"""
        
        if not self.objetivo_ativo:
            return "❌ Nenhum objetivo ativo"
        
        progresso = self.calcular_progresso_geral()
        
        relatorio = f"""
═══════════════════════════════════════════════
🎯 RELATÓRIO DE OBJETIVO - LIBERTUS v10.0
═══════════════════════════════════════════════

📌 OBJETIVO: {progresso['objetivo']}

📊 PROGRESSO GERAL: {progresso['progresso_geral']:.1f}%
✅ Métricas Atingidas: {progresso['metricas_atingidas']}
📈 Status: {progresso['status'].upper()}

📋 DETALHAMENTO:
"""
        
        for detalhe in progresso['detalhes']:
            status = "✅" if detalhe['atingida'] else "⏳"
            relatorio += f"""
{status} {detalhe['metrica']}
   Meta: {detalhe['meta']}
   Atual: {detalhe['atual']}
   Progresso: {detalhe['percentual']:.1f}%
"""
        
        conhecimento = self.objetivo_ativo["progresso"]["conhecimento_adquirido"]
        
        relatorio += f"""
🧠 CONHECIMENTO ADQUIRIDO: {len(conhecimento)} tópicos

"""
        
        for c in conhecimento[-5:]:  # Últimos 5
            relatorio += f"   • {c['topico']} ({c['fonte']})\n"
        
        return relatorio


# Objetivos pré-definidos para SHIELD
OBJETIVOS_PREDEFINIDOS = {
    "bug_bounty_hunter": {
        "titulo": "Bug Bounty Hunter Profissional",
        "descricao": "Tornar-se especialista em Bug Bounty com foco em OWASP Top 10",
        "metricas": [
            {"nome": "papers_lidos", "meta": 50},
            {"nome": "vulnerabilidades_descobertas", "meta": 100},
            {"nome": "scans_realizados", "meta": 200}
        ],
        "topicos_aprendizado": [
            "SQL Injection advanced techniques",
            "XSS bypass WAF",
            "SSRF exploitation",
            "Authentication bypass",
            "XXE vulnerabilities",
            "Insecure Deserialization",
            "IDOR exploitation",
            "CSRF advanced",
            "Security misconfiguration",
            "Path traversal"
        ]
    },
    "shield_specialist": {
        "titulo": "Especialista SHIELD - Vendas de Segurança",
        "descricao": "Dominar detecção de vulnerabilidades em sites empresariais brasileiros",
        "metricas": [
            {"nome": "papers_lidos", "meta": 30},
            {"nome": "vulnerabilidades_descobertas", "meta": 50},
            {"nome": "scans_realizados", "meta": 100}
        ],
        "topicos_aprendizado": [
            "WordPress vulnerabilities",
            "E-commerce security",
            "Brazilian payment gateway security",
            "LGPD compliance scanning",
            "Small business web security",
            "Common CMS vulnerabilities",
            "Basic SQL injection",
            "XSS in forms",
            "Outdated software detection"
        ]
    },
    "waf_bypass_master": {
        "titulo": "Mestre em WAF Bypass",
        "descricao": "Especializar em bypass de Web Application Firewalls",
        "metricas": [
            {"nome": "papers_lidos", "meta": 40},
            {"nome": "vulnerabilidades_descobertas", "meta": 80},
            {"nome": "scans_realizados", "meta": 150}
        ],
        "topicos_aprendizado": [
            "WAF bypass techniques",
            "CloudFlare bypass",
            "ModSecurity bypass",
            "Encoding techniques",
            "Protocol smuggling",
            "HTTP parameter pollution",
            "Race conditions",
            "Logic flaws"
        ]
    }
}


if __name__ == "__main__":
    # Teste
    sistema = ObjetivoSystem()
    
    # Definir objetivo
    objetivo = OBJETIVOS_PREDEFINIDOS["shield_specialist"]
    sistema.definir_objetivo(
        titulo=objetivo["titulo"],
        descricao=objetivo["descricao"],
        metricas=objetivo["metricas"],
        topicos_aprendizado=objetivo["topicos_aprendizado"]
    )
    
    print(sistema.gerar_relatorio())
    
    # Próximo tópico
    proximo = sistema.get_proximo_topico_aprendizado()
    print(f"\n🎓 Próximo tópico: {proximo}")
