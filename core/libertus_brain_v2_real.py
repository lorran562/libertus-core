#!/usr/bin/env python3
"""
LIBERTUS BRAIN v2.0 REAL
Sistema de inteligência baseado em LÓGICA, não em geração de texto.
"""

from typing import Dict, List, Optional
from datetime import datetime


class LibertusBrainV2:
    """
    Brain real com lógica de decisão
    Não depende de API para funcionar
    """
    
    def __init__(self):
        # Base de conhecimento de vulnerabilidades
        self.vulnerability_knowledge = self._load_vulnerability_db()
        
        # Matriz de severidade
        self.severity_weights = {
            'CRITICAL': 10,
            'HIGH': 5,
            'MEDIUM': 2,
            'LOW': 1
        }
        
        # Matriz de impacto comercial
        self.business_impact = {
            'data_exposure': {
                'severity_multiplier': 3.0,
                'industries': ['healthcare', 'finance', 'ecommerce'],
                'avg_cost': 150000  # USD
            },
            'auth_bypass': {
                'severity_multiplier': 2.5,
                'industries': ['all'],
                'avg_cost': 80000
            },
            'injection': {
                'severity_multiplier': 2.8,
                'industries': ['all'],
                'avg_cost': 120000
            },
            'xss': {
                'severity_multiplier': 1.5,
                'industries': ['all'],
                'avg_cost': 40000
            },
            'security_misconfiguration': {
                'severity_multiplier': 1.2,
                'industries': ['all'],
                'avg_cost': 25000
            }
        }
    
    def _load_vulnerability_db(self) -> Dict:
        """Base de conhecimento de vulnerabilidades"""
        return {
            'SQL Injection': {
                'category': 'injection',
                'owasp_rank': 3,
                'exploitation_difficulty': 'medium',
                'typical_impact': ['data_breach', 'data_manipulation', 'authentication_bypass'],
                'fix_complexity': 'medium',
                'fix_time_hours': 8,
                'requires_testing': True
            },
            'Cross-Site Scripting (XSS)': {
                'category': 'xss',
                'owasp_rank': 7,
                'exploitation_difficulty': 'low',
                'typical_impact': ['session_hijacking', 'credential_theft', 'defacement'],
                'fix_complexity': 'low',
                'fix_time_hours': 4,
                'requires_testing': True
            },
            'Missing Security Header': {
                'category': 'security_misconfiguration',
                'owasp_rank': 5,
                'exploitation_difficulty': 'easy',
                'typical_impact': ['clickjacking', 'mime_sniffing', 'mitm'],
                'fix_complexity': 'very_low',
                'fix_time_hours': 1,
                'requires_testing': False
            },
            'Weak Password Hash': {
                'category': 'data_exposure',
                'owasp_rank': 2,
                'exploitation_difficulty': 'medium',
                'typical_impact': ['credential_theft', 'account_takeover'],
                'fix_complexity': 'high',
                'fix_time_hours': 16,
                'requires_testing': True
            },
            'Exposed API Key': {
                'category': 'data_exposure',
                'owasp_rank': 2,
                'exploitation_difficulty': 'easy',
                'typical_impact': ['service_abuse', 'data_access', 'financial_loss'],
                'fix_complexity': 'medium',
                'fix_time_hours': 4,
                'requires_testing': True
            },
            'Exposed AWS Key': {
                'category': 'data_exposure',
                'owasp_rank': 2,
                'exploitation_difficulty': 'easy',
                'typical_impact': ['infrastructure_takeover', 'data_breach', 'crypto_mining'],
                'fix_complexity': 'high',
                'fix_time_hours': 8,
                'requires_testing': True
            }
        }
    
    def analyze_vulnerability(self, vuln: Dict) -> Dict:
        """
        Analisa vulnerabilidade com LÓGICA REAL
        Retorna análise estruturada baseada em regras
        """
        
        vuln_type = vuln.get('type', 'Unknown')
        severity = vuln.get('severity', 'MEDIUM')
        
        # Buscar conhecimento na base
        knowledge = self.vulnerability_knowledge.get(vuln_type, {})
        
        # Calcular risk score
        base_score = self.severity_weights.get(severity, 2)
        category = knowledge.get('category', 'security_misconfiguration')
        impact_data = self.business_impact.get(category, {})
        
        risk_score = base_score * impact_data.get('severity_multiplier', 1.0)
        
        # Determinar urgência
        urgency = self._calculate_urgency(severity, knowledge)
        
        # Calcular custo estimado
        cost_estimate = self._calculate_cost(severity, impact_data, knowledge)
        
        # Gerar recomendação de correção
        fix_recommendation = self._generate_fix_recommendation(vuln_type, knowledge, vuln)
        
        # Análise de impacto
        business_impact_text = self._analyze_business_impact(vuln_type, severity, impact_data)
        
        return {
            'vulnerability_type': vuln_type,
            'severity': severity,
            'risk_score': round(risk_score, 2),
            'urgency': urgency,
            'owasp_rank': knowledge.get('owasp_rank', 'N/A'),
            'exploitation_difficulty': knowledge.get('exploitation_difficulty', 'unknown'),
            'business_impact': business_impact_text,
            'estimated_fix_cost': cost_estimate,
            'fix_complexity': knowledge.get('fix_complexity', 'unknown'),
            'fix_time_estimate_hours': knowledge.get('fix_time_hours', 0),
            'requires_testing': knowledge.get('requires_testing', False),
            'fix_recommendation': fix_recommendation,
            'typical_impact': knowledge.get('typical_impact', []),
            'analysis_method': 'RULE_BASED_LOGIC'
        }
    
    def _calculate_urgency(self, severity: str, knowledge: Dict) -> str:
        """Calcula urgência baseada em severidade e dificuldade de exploração"""
        
        difficulty = knowledge.get('exploitation_difficulty', 'medium')
        
        # Matriz de decisão
        if severity == 'CRITICAL':
            if difficulty in ['easy', 'low']:
                return 'IMMEDIATE'  # Fix in 24h
            else:
                return 'URGENT'  # Fix in 72h
        
        elif severity == 'HIGH':
            if difficulty in ['easy', 'low']:
                return 'URGENT'  # Fix in 72h
            else:
                return 'HIGH_PRIORITY'  # Fix in 1 week
        
        elif severity == 'MEDIUM':
            return 'MEDIUM_PRIORITY'  # Fix in 2 weeks
        
        else:
            return 'LOW_PRIORITY'  # Fix in 1 month
    
    def _calculate_cost(self, severity: str, impact_data: Dict, knowledge: Dict) -> Dict:
        """Calcula custo estimado de correção vs custo de exploração"""
        
        # Custo de correção (baseado em horas)
        fix_hours = knowledge.get('fix_time_hours', 4)
        hourly_rate = 150  # USD/hour developer rate
        fix_cost = fix_hours * hourly_rate
        
        # Custo de exploração (média da categoria)
        exploitation_cost = impact_data.get('avg_cost', 50000)
        
        # Adicionar custo de testes se necessário
        if knowledge.get('requires_testing', False):
            fix_cost += 500  # QA/testing cost
        
        return {
            'fix_cost_usd': fix_cost,
            'exploitation_cost_usd': exploitation_cost,
            'roi': round((exploitation_cost / fix_cost), 2) if fix_cost > 0 else 0,
            'cost_benefit': 'HIGH' if exploitation_cost / fix_cost > 10 else 'MEDIUM' if exploitation_cost / fix_cost > 5 else 'LOW'
        }
    
    def _generate_fix_recommendation(self, vuln_type: str, knowledge: Dict, vuln: Dict) -> Dict:
        """Gera recomendação de correção específica"""
        
        # Base de soluções
        fixes = {
            'SQL Injection': {
                'immediate': 'Implementar prepared statements/parametrized queries',
                'code_example': 'cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))',
                'validation': 'Input validation + whitelist',
                'long_term': 'Implementar WAF + code review automático'
            },
            'Cross-Site Scripting (XSS)': {
                'immediate': 'Sanitizar output + encoding HTML',
                'code_example': 'output = html.escape(user_input)',
                'validation': 'Content Security Policy (CSP)',
                'long_term': 'Framework com auto-escape + security headers'
            },
            'Missing Security Header': {
                'immediate': f"Adicionar header: {vuln.get('header', 'N/A')}",
                'code_example': self._get_header_fix(vuln.get('header', '')),
                'validation': 'Verificar com securityheaders.com',
                'long_term': 'Automatizar via servidor web config'
            },
            'Weak Password Hash': {
                'immediate': 'Migrar para bcrypt com cost 12+',
                'code_example': 'bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))',
                'validation': 'Force password reset para todos usuários',
                'long_term': 'Password policy + 2FA'
            },
            'Exposed API Key': {
                'immediate': 'Revogar key + regenerar + mover para env vars',
                'code_example': 'API_KEY = os.getenv("API_KEY")  # Never hardcode',
                'validation': 'Git history cleanup + secrets scanning',
                'long_term': 'CI/CD secret scanning + rotation automática'
            }
        }
        
        fix = fixes.get(vuln_type, {
            'immediate': 'Consultar documentação OWASP',
            'code_example': 'N/A',
            'validation': 'Security testing',
            'long_term': 'Security training + code review'
        })
        
        return {
            'immediate_action': fix.get('immediate'),
            'code_example': fix.get('code_example'),
            'validation_step': fix.get('validation'),
            'long_term_solution': fix.get('long_term'),
            'estimated_hours': knowledge.get('fix_time_hours', 4)
        }
    
    def _get_header_fix(self, header: str) -> str:
        """Retorna exemplo de correção para header específico"""
        
        examples = {
            'X-Frame-Options': 'X-Frame-Options: DENY',
            'X-Content-Type-Options': 'X-Content-Type-Options: nosniff',
            'Strict-Transport-Security': 'Strict-Transport-Security: max-age=31536000; includeSubDomains',
            'Content-Security-Policy': "Content-Security-Policy: default-src 'self'"
        }
        
        return examples.get(header, f'{header}: <value>')
    
    def _analyze_business_impact(self, vuln_type: str, severity: str, impact_data: Dict) -> str:
        """Analisa impacto comercial baseado em regras"""
        
        avg_cost = impact_data.get('avg_cost', 50000)
        
        impacts = {
            'CRITICAL': f"Risco extremo. Custo médio de exploração: ${avg_cost:,}. Pode resultar em: perda de dados sensíveis, violação de compliance (LGPD/GDPR), dano reputacional grave, processos judiciais.",
            
            'HIGH': f"Risco alto. Custo médio de exploração: ${avg_cost:,}. Pode resultar em: acesso não autorizado, manipulação de dados, interrupção de serviço.",
            
            'MEDIUM': f"Risco médio. Custo médio de exploração: ${avg_cost:,}. Pode resultar em: exposição de informações, vulnerabilidade a ataques secundários.",
            
            'LOW': f"Risco baixo. Custo médio de exploração: ${avg_cost:,}. Impacto limitado mas ainda requer correção."
        }
        
        return impacts.get(severity, 'Impacto não determinado')
    
    def prioritize_vulnerabilities(self, vulnerabilities: List[Dict]) -> List[Dict]:
        """
        Prioriza vulnerabilidades baseado em risk score
        Retorna lista ordenada com análise
        """
        
        analyzed = []
        
        for vuln in vulnerabilities:
            analysis = self.analyze_vulnerability(vuln)
            
            # Combinar vulnerability original com análise
            combined = {**vuln, 'brain_analysis': analysis}
            analyzed.append(combined)
        
        # Ordenar por risk score (maior primeiro)
        analyzed.sort(key=lambda x: x['brain_analysis']['risk_score'], reverse=True)
        
        return analyzed
    
    def generate_executive_summary(self, analyzed_vulns: List[Dict]) -> Dict:
        """Gera sumário executivo baseado em análise"""
        
        total = len(analyzed_vulns)
        
        by_severity = {
            'CRITICAL': len([v for v in analyzed_vulns if v.get('severity') == 'CRITICAL']),
            'HIGH': len([v for v in analyzed_vulns if v.get('severity') == 'HIGH']),
            'MEDIUM': len([v for v in analyzed_vulns if v.get('severity') == 'MEDIUM']),
            'LOW': len([v for v in analyzed_vulns if v.get('severity') == 'LOW'])
        }
        
        by_urgency = {}
        total_fix_cost = 0
        total_risk_cost = 0
        
        for vuln in analyzed_vulns:
            analysis = vuln.get('brain_analysis', {})
            urgency = analysis.get('urgency', 'UNKNOWN')
            by_urgency[urgency] = by_urgency.get(urgency, 0) + 1
            
            cost = analysis.get('estimated_fix_cost', {})
            total_fix_cost += cost.get('fix_cost_usd', 0)
            total_risk_cost += cost.get('exploitation_cost_usd', 0)
        
        # Decisão: CRÍTICO ou não
        overall_status = 'CRITICAL' if by_severity['CRITICAL'] > 0 else \
                        'HIGH' if by_severity['HIGH'] > 0 else \
                        'MEDIUM' if by_severity['MEDIUM'] > 0 else 'LOW'
        
        return {
            'total_vulnerabilities': total,
            'by_severity': by_severity,
            'by_urgency': by_urgency,
            'overall_status': overall_status,
            'estimated_total_fix_cost_usd': total_fix_cost,
            'estimated_total_risk_cost_usd': total_risk_cost,
            'roi': round(total_risk_cost / total_fix_cost, 2) if total_fix_cost > 0 else 0,
            'recommendation': self._get_overall_recommendation(overall_status, by_urgency),
            'analysis_method': 'RULE_BASED_LOGIC'
        }
    
    def _get_overall_recommendation(self, status: str, urgency_breakdown: Dict) -> str:
        """Recomendação geral baseada em status"""
        
        immediate = urgency_breakdown.get('IMMEDIATE', 0)
        urgent = urgency_breakdown.get('URGENT', 0)
        
        if status == 'CRITICAL':
            return f"AÇÃO IMEDIATA REQUERIDA. {immediate + urgent} vulnerabilidades críticas devem ser corrigidas nas próximas 24-72 horas. Sistema apresenta risco grave de exploração."
        
        elif status == 'HIGH':
            return f"Alta prioridade. {urgent} vulnerabilidades devem ser corrigidas na próxima semana. Sistema vulnerável a ataques direcionados."
        
        elif status == 'MEDIUM':
            return "Prioridade média. Correções devem ser agendadas nas próximas 2 semanas. Sistema apresenta vulnerabilidades exploráveis mas com menor impacto."
        
        else:
            return "Prioridade baixa. Correções podem ser agendadas no próximo ciclo de manutenção. Sistema apresenta vulnerabilidades menores."


# Teste
if __name__ == "__main__":
    brain = LibertusBrainV2()
    
    # Teste com vulnerabilidades
    test_vulns = [
        {
            'type': 'SQL Injection',
            'severity': 'CRITICAL',
            'url': 'https://example.com/search?q=test',
            'payload': "' OR '1'='1"
        },
        {
            'type': 'Missing Security Header',
            'severity': 'MEDIUM',
            'header': 'X-Frame-Options'
        }
    ]
    
    print("🧠 LIBERTUS BRAIN v2.0 - TESTE")
    print("="*60)
    
    # Analisar cada uma
    for vuln in test_vulns:
        print(f"\n📊 Analisando: {vuln['type']}")
        analysis = brain.analyze_vulnerability(vuln)
        
        print(f"   Risk Score: {analysis['risk_score']}")
        print(f"   Urgency: {analysis['urgency']}")
        print(f"   Fix Cost: ${analysis['estimated_fix_cost']['fix_cost_usd']}")
        print(f"   ROI: {analysis['estimated_fix_cost']['roi']}x")
    
    # Priorizar
    print(f"\n\n🎯 PRIORIZANDO VULNERABILIDADES...")
    prioritized = brain.prioritize_vulnerabilities(test_vulns)
    
    for i, vuln in enumerate(prioritized, 1):
        print(f"\n{i}. {vuln['type']} (Score: {vuln['brain_analysis']['risk_score']})")
    
    # Sumário executivo
    print(f"\n\n📊 SUMÁRIO EXECUTIVO:")
    summary = brain.generate_executive_summary(prioritized)
    print(f"   Status: {summary['overall_status']}")
    print(f"   Total Fix Cost: ${summary['estimated_total_fix_cost_usd']}")
    print(f"   Total Risk: ${summary['estimated_total_risk_cost_usd']}")
    print(f"   ROI: {summary['roi']}x")
    print(f"\n   {summary['recommendation']}")
