#!/usr/bin/env python3
"""
LIBERTUS GERADOR DE RELATÓRIOS v2.0 REAL
Geração 100% automática de relatórios profissionais
Baseado SOMENTE em dados reais de scan
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from jinja2 import Template


class GeradorRelatorioV2:
    """
    Gerador de relatórios profissionais
    100% baseado em dados reais
    """
    
    def __init__(self):
        self.template_md = self._load_markdown_template()
    
    def _load_markdown_template(self) -> str:
        """Template Markdown para relatório"""
        
        return """# 🛡️ RELATÓRIO DE SEGURANÇA

**Cliente:** {{ client_name }}  
**Target:** {{ target }}  
**Data do Scan:** {{ scan_date }}  
**Scanner:** {{ scanner_version }}

---

## 📊 SUMÁRIO EXECUTIVO

### Status Geral
- **Severidade:** {{ severity }}
- **Risk Score:** {{ risk_score }}/100
- **Total de Vulnerabilidades:** {{ total_vulnerabilities }}

### Distribuição por Severidade
- 🔴 **CRITICAL:** {{ critical_count }}
- 🟠 **HIGH:** {{ high_count }}
- 🟡 **MEDIUM:** {{ medium_count }}
- 🟢 **LOW:** {{ low_count }}

### Análise de Risco
{{ executive_summary }}

---

## 🔍 RECONHECIMENTO

### Subdomínios Descobertos
{% if subdomains %}
Total: {{ subdomains|length }}

{% for subdomain in subdomains[:10] %}
- {{ subdomain }}
{% endfor %}
{% if subdomains|length > 10 %}
... e mais {{ subdomains|length - 10 }} subdomínios
{% endif %}
{% else %}
Nenhum subdomínio descoberto.
{% endif %}

### Portas Abertas
{% if open_ports %}
{% for port in open_ports %}
- **Porta {{ port.port }}:** {{ port.state }}
{% endfor %}
{% else %}
Nenhuma porta aberta detectada.
{% endif %}

### Tecnologias Detectadas
{% if technologies %}
{% for tech in technologies %}
- {{ tech }}
{% endfor %}
{% else %}
Nenhuma tecnologia detectada.
{% endif %}

### APIs Descobertas
{% if apis %}
Total: {{ apis|length }} endpoints

{% for api in apis[:15] %}
- `{{ api }}`
{% endfor %}
{% if apis|length > 15 %}
... e mais {{ apis|length - 15 }} endpoints
{% endif %}
{% else %}
Nenhuma API descoberta.
{% endif %}

---

## 🚨 VULNERABILIDADES DETECTADAS

{% for vuln in vulnerabilities %}
### {{ loop.index }}. {{ vuln.type }} {% if vuln.severity == 'CRITICAL' %}🔴{% elif vuln.severity == 'HIGH' %}🟠{% elif vuln.severity == 'MEDIUM' %}🟡{% else %}🟢{% endif %}

**Severidade:** {{ vuln.severity }}  
**Validação:** {{ vuln.validation }}

{% if vuln.brain_analysis %}
**Risk Score:** {{ vuln.brain_analysis.risk_score }}  
**Urgência:** {{ vuln.brain_analysis.urgency }}  
**OWASP Rank:** #{{ vuln.brain_analysis.owasp_rank }}

#### Impacto Comercial
{{ vuln.brain_analysis.business_impact }}

#### Exploração
- **Dificuldade:** {{ vuln.brain_analysis.exploitation_difficulty }}
- **Impactos Típicos:**
{% for impact in vuln.brain_analysis.typical_impact %}
  - {{ impact }}
{% endfor %}

#### Custo Estimado
- **Correção:** ${{ vuln.brain_analysis.estimated_fix_cost.fix_cost_usd }}
- **Exploração:** ${{ vuln.brain_analysis.estimated_fix_cost.exploitation_cost_usd }}
- **ROI:** {{ vuln.brain_analysis.estimated_fix_cost.roi }}x
- **Custo-Benefício:** {{ vuln.brain_analysis.estimated_fix_cost.cost_benefit }}

#### Correção Recomendada
**Ação Imediata:**
```
{{ vuln.brain_analysis.fix_recommendation.immediate_action }}
```

**Exemplo de Código:**
```
{{ vuln.brain_analysis.fix_recommendation.code_example }}
```

**Validação:**
{{ vuln.brain_analysis.fix_recommendation.validation_step }}

**Solução de Longo Prazo:**
{{ vuln.brain_analysis.fix_recommendation.long_term_solution }}

**Tempo Estimado:** {{ vuln.brain_analysis.fix_recommendation.estimated_hours }} horas

{% endif %}

{% if vuln.url %}
**URL Afetada:**
```
{{ vuln.url }}
```
{% endif %}

{% if vuln.payload %}
**Payload Utilizado:**
```
{{ vuln.payload }}
```
{% endif %}

{% if vuln.evidence %}
**Evidência:**
```
{{ vuln.evidence }}
```
{% endif %}

{% if vuln.context %}
**Contexto:**
```
{{ vuln.context[:200] }}...
```
{% endif %}

---

{% endfor %}

## 💰 ANÁLISE FINANCEIRA

### Custos de Correção
{% if brain_summary %}
- **Total de Correções:** ${{ brain_summary.estimated_total_fix_cost_usd }}
- **Risco Total de Exploração:** ${{ brain_summary.estimated_total_risk_cost_usd }}
- **ROI da Correção:** {{ brain_summary.roi }}x

### Priorização
{% for urgency, count in brain_summary.by_urgency.items() %}
- **{{ urgency }}:** {{ count }} vulnerabilidades
{% endfor %}

### Recomendação
{{ brain_summary.recommendation }}
{% endif %}

---

## 📋 PLANO DE AÇÃO

### Prioridade Imediata (24-72h)
{% for vuln in vulnerabilities %}
{% if vuln.brain_analysis and vuln.brain_analysis.urgency in ['IMMEDIATE', 'URGENT'] %}
- [ ] **{{ vuln.type }}** - {{ vuln.brain_analysis.fix_recommendation.immediate_action }}
{% endif %}
{% endfor %}

### Alta Prioridade (1 semana)
{% for vuln in vulnerabilities %}
{% if vuln.brain_analysis and vuln.brain_analysis.urgency == 'HIGH_PRIORITY' %}
- [ ] **{{ vuln.type }}** - {{ vuln.brain_analysis.fix_recommendation.immediate_action }}
{% endif %}
{% endfor %}

### Média Prioridade (2 semanas)
{% for vuln in vulnerabilities %}
{% if vuln.brain_analysis and vuln.brain_analysis.urgency == 'MEDIUM_PRIORITY' %}
- [ ] **{{ vuln.type }}** - {{ vuln.brain_analysis.fix_recommendation.immediate_action }}
{% endif %}
{% endfor %}

---

## 📈 MÉTRICAS TÉCNICAS

### Análise Crypto
{% if crypto_analysis %}
- **Módulo:** {{ crypto_analysis.module }}
- **Hashes Encontrados:** {{ crypto_analysis.hashes_found|length if crypto_analysis.hashes_found else 0 }}
{% endif %}

### Análise Reverse
{% if reverse_analysis %}
- **Módulo:** {{ reverse_analysis.module }}
- **Secrets Encontrados:** {{ reverse_analysis.secrets_found }}
{% endif %}

---

## 🔐 COMPLIANCE

### LGPD / GDPR
{% if severity in ['CRITICAL', 'HIGH'] %}
⚠️ **ATENÇÃO:** As vulnerabilidades detectadas podem resultar em:
- Exposição de dados pessoais
- Violação de compliance LGPD/GDPR
- Multas de até 2% do faturamento (máx R$ 50 milhões)
- Processos judiciais de titulares
- Dano reputacional grave
{% else %}
✅ Nível de risco atual é compatível com requisitos básicos de segurança.
{% endif %}

---

## 📞 PRÓXIMOS PASSOS

1. **Revisar este relatório** com equipe técnica
2. **Priorizar correções** conforme urgência indicada
3. **Implementar correções** seguindo recomendações
4. **Validar correções** através de novo scan
5. **Documentar mudanças** para auditoria

---

## 📄 INFORMAÇÕES TÉCNICAS

**Método de Análise:** {{ analysis_method }}  
**Gerado em:** {{ generation_date }}  
**Válido até:** {{ expiration_date }}

---

*Relatório gerado automaticamente por LIBERTUS v9.0*  
*Todos os dados são baseados em scan real executado em {{ scan_date }}*
"""
    
    def generate_report(self, 
                       scan_results: Dict,
                       brain_analysis: Dict,
                       client_name: str = "Cliente",
                       output_format: str = "markdown") -> str:
        """
        Gera relatório completo
        
        Args:
            scan_results: Resultados do scanner v9.0
            brain_analysis: Análise do Brain v2.0 com priorização
            client_name: Nome do cliente
            output_format: 'markdown' ou 'json'
        
        Returns:
            String do relatório ou path do arquivo
        """
        
        # Preparar dados do template
        template_data = self._prepare_template_data(
            scan_results,
            brain_analysis,
            client_name
        )
        
        if output_format == "markdown":
            return self._generate_markdown(template_data)
        elif output_format == "json":
            return self._generate_json(template_data)
        else:
            raise ValueError(f"Formato não suportado: {output_format}")
    
    def _prepare_template_data(self, scan_results: Dict, brain_analysis: Dict, client_name: str) -> Dict:
        """Prepara dados para o template"""
        
        # Dados básicos
        data = {
            'client_name': client_name,
            'target': scan_results.get('target', 'Unknown'),
            'scan_date': scan_results.get('scan_date', datetime.now().isoformat()),
            'scanner_version': scan_results.get('scanner_version', 'LIBERTUS v9.0'),
            'severity': scan_results.get('severity', 'MEDIUM'),
            'risk_score': scan_results.get('risk_score', 0),
            'analysis_method': 'RULE_BASED_LOGIC',
            'generation_date': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'expiration_date': (datetime.now().replace(day=1, month=datetime.now().month+1) if datetime.now().month < 12 else datetime.now().replace(day=1, month=1, year=datetime.now().year+1)).strftime('%d/%m/%Y')
        }
        
        # Reconhecimento
        recon = scan_results.get('reconnaissance', {})
        data['subdomains'] = recon.get('subdomains', [])
        data['open_ports'] = recon.get('open_ports', [])
        data['technologies'] = recon.get('technologies', [])
        data['apis'] = recon.get('apis', [])
        
        # Vulnerabilidades (já analisadas pelo Brain)
        vulnerabilities = brain_analysis.get('analyzed_vulnerabilities', [])
        data['vulnerabilities'] = vulnerabilities
        data['total_vulnerabilities'] = len(vulnerabilities)
        
        # Contar por severidade
        data['critical_count'] = len([v for v in vulnerabilities if v.get('severity') == 'CRITICAL'])
        data['high_count'] = len([v for v in vulnerabilities if v.get('severity') == 'HIGH'])
        data['medium_count'] = len([v for v in vulnerabilities if v.get('severity') == 'MEDIUM'])
        data['low_count'] = len([v for v in vulnerabilities if v.get('severity') == 'LOW'])
        
        # Sumário do Brain
        data['brain_summary'] = brain_analysis.get('executive_summary', {})
        data['executive_summary'] = brain_analysis.get('executive_summary', {}).get('recommendation', '')
        
        # Crypto/Reverse
        data['crypto_analysis'] = scan_results.get('crypto_analysis', {})
        data['reverse_analysis'] = scan_results.get('reverse_analysis', {})
        
        return data
    
    def _generate_markdown(self, data: Dict) -> str:
        """Gera relatório em Markdown"""
        
        template = Template(self.template_md)
        return template.render(**data)
    
    def _generate_json(self, data: Dict) -> str:
        """Gera relatório em JSON"""
        
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    def save_report(self, 
                   report_content: str,
                   target: str,
                   output_dir: str = "/root/LIBERTUS/relatorios",
                   format: str = "markdown") -> str:
        """
        Salva relatório em arquivo
        
        Returns:
            Path do arquivo salvo
        """
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_target = target.replace('.', '_').replace('/', '_')
        
        ext = 'md' if format == 'markdown' else 'json'
        filename = f"relatorio_{safe_target}_{timestamp}.{ext}"
        
        filepath = output_path / filename
        
        # Salvar
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(filepath)


# Integração completa: Scanner + Brain + Relatório
async def generate_complete_report(target: str, client_name: str = "Cliente"):
    """
    Workflow completo:
    1. Scan com Scanner v9.0
    2. Análise com Brain v2.0
    3. Geração de relatório
    """
    
    from libertus_scanner_v9_real import LibertusScannerV9
    from libertus_brain_v2_real import LibertusBrainV2
    
    print(f"🎯 WORKFLOW COMPLETO - {target}")
    print("="*70)
    
    # 1. SCAN
    print("\n1️⃣ Executando scan...")
    scanner = LibertusScannerV9(target)
    scan_results = await scanner.scan_complete()
    
    # 2. BRAIN ANALYSIS
    print("\n2️⃣ Analisando com Brain v2.0...")
    brain = LibertusBrainV2()
    
    vulnerabilities = scan_results.get('vulnerabilities', [])
    
    if vulnerabilities:
        analyzed = brain.prioritize_vulnerabilities(vulnerabilities)
        summary = brain.generate_executive_summary(analyzed)
        
        brain_analysis = {
            'analyzed_vulnerabilities': analyzed,
            'executive_summary': summary
        }
    else:
        brain_analysis = {
            'analyzed_vulnerabilities': [],
            'executive_summary': {
                'recommendation': 'Nenhuma vulnerabilidade detectada. Sistema apresenta boa postura de segurança.'
            }
        }
    
    # 3. RELATÓRIO
    print("\n3️⃣ Gerando relatório...")
    gerador = GeradorRelatorioV2()
    
    report_md = gerador.generate_report(
        scan_results,
        brain_analysis,
        client_name
    )
    
    # Salvar
    filepath = gerador.save_report(report_md, target)
    
    print(f"\n✅ Relatório salvo: {filepath}")
    print(f"📊 Total de vulnerabilidades: {len(vulnerabilities)}")
    print(f"⚠️  Severidade: {scan_results.get('severity', 'LOW')}")
    
    return filepath


# Teste
if __name__ == "__main__":
    import asyncio
    
    # Teste com dados de exemplo
    test_scan = {
        'scanner_version': 'LIBERTUS v9.0 REAL',
        'scan_date': datetime.now().isoformat(),
        'target': 'example.com',
        'reconnaissance': {
            'subdomains': ['www.example.com', 'api.example.com'],
            'open_ports': [{'port': 80, 'state': 'open'}, {'port': 443, 'state': 'open'}],
            'apis': ['/api/v1/users', '/api/v1/auth'],
            'technologies': ['nginx', 'PHP']
        },
        'vulnerabilities': [
            {
                'type': 'Missing Security Header',
                'severity': 'MEDIUM',
                'header': 'X-Frame-Options',
                'validation': 'CONFIRMED'
            }
        ],
        'risk_score': 8,
        'severity': 'MEDIUM',
        'crypto_analysis': {'module': 'ULTRA v2.0', 'hashes_found': {}},
        'reverse_analysis': {'module': 'ULTRA v2.0', 'secrets_found': 0}
    }
    
    # Brain analysis
    from libertus_brain_v2_real import LibertusBrainV2
    brain = LibertusBrainV2()
    analyzed = brain.prioritize_vulnerabilities(test_scan['vulnerabilities'])
    summary = brain.generate_executive_summary(analyzed)
    
    test_brain = {
        'analyzed_vulnerabilities': analyzed,
        'executive_summary': summary
    }
    
    # Gerar
    gerador = GeradorRelatorioV2()
    report = gerador.generate_report(test_scan, test_brain, "Empresa Teste LTDA")
    
    # Salvar
    filepath = gerador.save_report(report, 'example.com')
    
    print("✅ TESTE COMPLETO!")
    print(f"📄 Relatório: {filepath}")
    print("\nPRIMEIRAS 50 LINHAS:")
    print(report[:2000])
