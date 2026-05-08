#!/usr/bin/env python3
"""
LIBERTUS v10 - INTELIGÊNCIA COMERCIAL
Analisa empresas e prioriza leads baseado em probabilidade de conversão
"""

from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime

class InteligenciaComercial:
    """Analisa contexto de empresas para otimizar vendas"""
    
    # Base de conhecimento: tipos de empresa e características
    TIPOS_EMPRESA = {
        "clinica": {
            "keywords": ["clinica", "consultorio", "medic", "saude", "hospital", "laboratorio"],
            "valor_medio": 1500,
            "probabilidade_base": 75,
            "urgencia_lgpd": 10,  # Multiplier
            "dados_sensiveis": "prontuários médicos, exames, CPF de pacientes"
        },
        "contabilidade": {
            "keywords": ["contabil", "contador", "assessoria", "fiscal"],
            "valor_medio": 1800,
            "probabilidade_base": 70,
            "urgencia_lgpd": 9,
            "dados_sensiveis": "dados fiscais, CPF/CNPJ de clientes, salários"
        },
        "imobiliaria": {
            "keywords": ["imoveis", "imobiliaria", "corretor", "imovel"],
            "valor_medio": 1200,
            "probabilidade_base": 65,
            "urgencia_lgpd": 7,
            "dados_sensiveis": "CPF/RG, comprovantes de renda, contratos"
        },
        "ecommerce": {
            "keywords": ["loja", "shop", "store", "commerce", "venda"],
            "valor_medio": 1000,
            "probabilidade_base": 60,
            "urgencia_lgpd": 8,
            "dados_sensiveis": "dados de cartão, endereços, pedidos"
        },
        "advocacia": {
            "keywords": ["advogado", "juridic", "advocacia", "oab"],
            "valor_medio": 1500,
            "probabilidade_base": 68,
            "urgencia_lgpd": 9,
            "dados_sensiveis": "processos sigilosos, dados de clientes"
        },
        "generico": {
            "keywords": [],
            "valor_medio": 800,
            "probabilidade_base": 50,
            "urgencia_lgpd": 5,
            "dados_sensiveis": "dados de clientes e usuários"
        }
    }
    
    # Pesos para cálculo de prioridade
    PESO_VULNERABILIDADES = 30
    PESO_TIPO_EMPRESA = 25
    PESO_TAMANHO = 20
    PESO_RESPOSTA = 15
    PESO_TEMPO = 10
    
    def __init__(self):
        self.historico = []
        
    def identificar_tipo_empresa(self, nome: str, url: str = "") -> str:
        """Identifica tipo de empresa pelo nome/URL"""
        
        texto = f"{nome} {url}".lower()
        
        for tipo, info in self.TIPOS_EMPRESA.items():
            for keyword in info["keywords"]:
                if keyword in texto:
                    return tipo
        
        return "generico"
    
    def calcular_score_lead(self, 
                           empresa: str,
                           url: str,
                           vulnerabilidades: List[Dict],
                           respondeu: bool = False,
                           tempo_resposta: int = 0,
                           tamanho_estimado: str = "medio") -> Dict:
        """
        Calcula score de qualidade do lead
        
        Args:
            empresa: Nome da empresa
            url: URL do site
            vulnerabilidades: Lista de vulnerabilidades detectadas
            respondeu: Se a empresa já respondeu contato
            tempo_resposta: Tempo em horas até resposta
            tamanho_estimado: pequeno/medio/grande
            
        Returns:
            Dict com score, probabilidade, valor estimado, etc
        """
        
        # 1. Identifica tipo
        tipo = self.identificar_tipo_empresa(empresa, url)
        info_tipo = self.TIPOS_EMPRESA[tipo]
        
        # 2. Score por vulnerabilidades
        criticas = len([v for v in vulnerabilidades if v.get('severity') == 'CRÍTICA'])
        altas = len([v for v in vulnerabilidades if v.get('severity') == 'ALTA'])
        medias = len([v for v in vulnerabilidades if v.get('severity') == 'MÉDIA'])
        
        score_vulns = 0
        if criticas > 0:
            score_vulns = 100
        elif altas >= 3:
            score_vulns = 85
        elif altas >= 1:
            score_vulns = 70
        elif medias >= 2:
            score_vulns = 50
        else:
            score_vulns = 30
        
        # 3. Score por tipo de empresa
        score_tipo = info_tipo["probabilidade_base"]
        
        # 4. Score por tamanho
        score_tamanho = {
            "pequeno": 50,
            "medio": 75,
            "grande": 90
        }.get(tamanho_estimado, 70)
        
        # 5. Score por resposta
        score_resposta = 0
        if respondeu:
            if tempo_resposta <= 2:  # Respondeu em até 2h
                score_resposta = 100
            elif tempo_resposta <= 12:  # Até 12h
                score_resposta = 80
            elif tempo_resposta <= 24:  # Até 1 dia
                score_resposta = 60
            else:
                score_resposta = 40
        
        # 6. Score por tempo desde contato
        score_tempo = 100  # Default (primeiro contato)
        
        # Calcula score final (média ponderada)
        score_final = (
            score_vulns * self.PESO_VULNERABILIDADES +
            score_tipo * self.PESO_TIPO_EMPRESA +
            score_tamanho * self.PESO_TAMANHO +
            score_resposta * self.PESO_RESPOSTA +
            score_tempo * self.PESO_TEMPO
        ) / 100
        
        # Probabilidade de conversão
        probabilidade = min(95, score_final)  # Cap em 95%
        
        # Valor estimado
        valor_base = info_tipo["valor_medio"]
        
        # Ajusta valor por tamanho
        multiplicador_tamanho = {
            "pequeno": 0.8,
            "medio": 1.0,
            "grande": 1.3
        }.get(tamanho_estimado, 1.0)
        
        # Ajusta valor por número de vulnerabilidades
        multiplicador_vulns = 1.0
        if criticas > 0:
            multiplicador_vulns = 1.3
        elif altas >= 3:
            multiplicador_vulns = 1.2
        
        valor_estimado = int(valor_base * multiplicador_tamanho * multiplicador_vulns)
        
        # Urgência LGPD
        urgencia_lgpd = info_tipo["urgencia_lgpd"]
        
        return {
            "empresa": empresa,
            "url": url,
            "tipo": tipo,
            "score": round(score_final, 1),
            "probabilidade_conversao": round(probabilidade, 1),
            "valor_estimado_min": int(valor_estimado * 0.8),
            "valor_estimado_max": int(valor_estimado * 1.2),
            "urgencia_lgpd": urgencia_lgpd,
            "dados_sensiveis": info_tipo["dados_sensiveis"],
            "vulnerabilidades": {
                "criticas": criticas,
                "altas": altas,
                "medias": medias,
                "total": len(vulnerabilidades)
            },
            "recomendacao_acao": self._gerar_recomendacao(
                score_final, respondeu, criticas, altas
            )
        }
    
    def _gerar_recomendacao(self, 
                           score: float, 
                           respondeu: bool,
                           criticas: int,
                           altas: int) -> str:
        """Gera recomendação de ação baseada no score"""
        
        if score >= 80:
            if respondeu:
                return "🔥 LEAD QUENTE! Enviar relatório AGORA e follow-up em 1h"
            else:
                return "🎯 ALTA PRIORIDADE! Contatar URGENTE com foco em LGPD"
        
        elif score >= 65:
            if criticas > 0 or altas >= 3:
                return "⚠️ BOM LEAD! Enfatizar vulnerabilidades críticas"
            else:
                return "✅ BOM LEAD! Contato profissional com relatório grátis"
        
        elif score >= 50:
            return "📋 LEAD MÉDIO! Esperar resposta ou follow-up em 24h"
        
        else:
            return "⏰ LEAD FRIO! Follow-up em 48-72h ou buscar novos leads"
    
    def priorizar_leads(self, leads: List[Dict]) -> List[Dict]:
        """
        Ordena lista de leads por prioridade
        
        Args:
            leads: Lista de dicts com dados dos leads
            
        Returns:
            Lista ordenada por score (maior primeiro)
        """
        
        leads_com_score = []
        
        for lead in leads:
            score_data = self.calcular_score_lead(
                empresa=lead.get("empresa", ""),
                url=lead.get("url", ""),
                vulnerabilidades=lead.get("vulnerabilidades", []),
                respondeu=lead.get("respondeu", False),
                tempo_resposta=lead.get("tempo_resposta", 0),
                tamanho_estimado=lead.get("tamanho", "medio")
            )
            
            leads_com_score.append({
                **lead,
                **score_data
            })
        
        # Ordena por score (maior primeiro)
        leads_com_score.sort(key=lambda x: x["score"], reverse=True)
        
        return leads_com_score
    
    def gerar_argumentos_venda(self, tipo_empresa: str, vulnerabilidades: List[Dict]) -> Dict:
        """Gera argumentos de venda personalizados"""
        
        info_tipo = self.TIPOS_EMPRESA.get(tipo_empresa, self.TIPOS_EMPRESA["generico"])
        
        criticas = len([v for v in vulnerabilidades if v.get('severity') == 'CRÍTICA'])
        altas = len([v for v in vulnerabilidades if v.get('severity') == 'ALTA'])
        
        # Argumento principal (LGPD)
        argumento_lgpd = f"""
Com as vulnerabilidades detectadas, os seguintes dados estão em risco:
{info_tipo['dados_sensiveis']}

Isso coloca sua empresa em NÃO CONFORMIDADE com a LGPD.

Multa potencial: até R$ 50 milhões
Processos civis: Responsabilidade por danos causados
"""
        
        # Urgência
        if criticas > 0:
            urgencia = f"⚠️ CRÍTICO: {criticas} vulnerabilidade(s) permitindo acesso IMEDIATO aos dados"
        elif altas >= 3:
            urgencia = f"⚠️ URGENTE: {altas} vulnerabilidades ALTAS detectadas"
        else:
            urgencia = "⚠️ Vulnerabilidades detectadas requerem correção"
        
        # Benefícios da correção
        beneficios = [
            "Conformidade total com LGPD",
            "Proteção de dados de clientes",
            "Evita processos e multas",
            "Certificado de segurança",
            "Tranquilidade e reputação preservada"
        ]
        
        return {
            "argumento_lgpd": argumento_lgpd.strip(),
            "urgencia": urgencia,
            "beneficios": beneficios,
            "dados_em_risco": info_tipo['dados_sensiveis'],
            "call_to_action": f"Correção urgente: R$ {info_tipo['valor_medio']} (desconto 20% se fechar hoje)"
        }


# === TESTE ===
if __name__ == "__main__":
    intel = InteligenciaComercial()
    
    # Testa análise de lead
    resultado = intel.calcular_score_lead(
        empresa="Clínica Duran",
        url="https://clinicaduran.com.br",
        vulnerabilidades=[
            {"severity": "ALTA", "type": "File Exposure"},
            {"severity": "ALTA", "type": "Git Exposed"},
            {"severity": "ALTA", "type": "Config Exposed"}
        ],
        respondeu=True,
        tempo_resposta=2,
        tamanho_estimado="medio"
    )
    
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
