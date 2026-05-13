#!/usr/bin/env python3
"""
LIBERTUS MOTOR DE DECISÃO v2.0 REAL
Sistema de decisão baseado em REGRAS e ESTADO, não em IA generativa
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum


class ActionType(Enum):
    """Tipos de ação que o sistema pode decidir"""
    SCAN_FULL = "scan_full"
    SCAN_QUICK = "scan_quick"
    RESCAN = "rescan"
    ANALYZE_RESULTS = "analyze_results"
    GENERATE_REPORT = "generate_report"
    WAIT = "wait"
    ESCALATE = "escalate"
    MONITOR = "monitor"


class Priority(Enum):
    """Níveis de prioridade"""
    IMMEDIATE = 5
    URGENT = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1


class MotorDecisaoV2:
    """
    Motor de decisão com lógica real
    Decide próximo passo baseado em estado do sistema
    """
    
    def __init__(self):
        # Regras de decisão
        self.decision_rules = self._load_decision_rules()
        
        # Thresholds
        self.thresholds = {
            'critical_vulnerabilities': 1,  # 1+ CRITICAL = ação imediata
            'high_vulnerabilities': 3,      # 3+ HIGH = ação urgente
            'scan_interval_hours': 24,      # Rescan a cada 24h
            'risk_score_critical': 50,      # Score 50+ = crítico
            'risk_score_high': 20,          # Score 20+ = alto
        }
        
        # Estado do sistema
        self.state = {
            'last_scan': None,
            'targets': {},
            'pending_actions': []
        }
    
    def _load_decision_rules(self) -> Dict:
        """
        Matriz de decisão baseada em condições
        Cada regra: condição → ação + prioridade
        """
        return {
            'new_target': {
                'condition': lambda ctx: self._is_new_target(ctx),
                'action': ActionType.SCAN_FULL,
                'priority': Priority.HIGH,
                'reason': 'Novo target nunca escaneado'
            },
            'critical_found': {
                'condition': lambda ctx: self._has_critical_vulns(ctx),
                'action': ActionType.ESCALATE,
                'priority': Priority.IMMEDIATE,
                'reason': 'Vulnerabilidade CRITICAL detectada'
            },
            'high_vulns_found': {
                'condition': lambda ctx: self._has_multiple_high_vulns(ctx),
                'action': ActionType.GENERATE_REPORT,
                'priority': Priority.URGENT,
                'reason': 'Múltiplas vulnerabilidades HIGH encontradas'
            },
            'scan_outdated': {
                'condition': lambda ctx: self._is_scan_outdated(ctx),
                'action': ActionType.RESCAN,
                'priority': Priority.MEDIUM,
                'reason': 'Último scan há mais de 24h'
            },
            'risk_score_critical': {
                'condition': lambda ctx: self._is_risk_critical(ctx),
                'action': ActionType.ESCALATE,
                'priority': Priority.IMMEDIATE,
                'reason': 'Risk score crítico (50+)'
            },
            'risk_score_high': {
                'condition': lambda ctx: self._is_risk_high(ctx),
                'action': ActionType.GENERATE_REPORT,
                'priority': Priority.URGENT,
                'reason': 'Risk score alto (20+)'
            },
            'no_vulns_found': {
                'condition': lambda ctx: self._no_vulns_found(ctx),
                'action': ActionType.MONITOR,
                'priority': Priority.LOW,
                'reason': 'Nenhuma vulnerabilidade encontrada - monitorar'
            },
            'scan_in_progress': {
                'condition': lambda ctx: self._scan_in_progress(ctx),
                'action': ActionType.WAIT,
                'priority': Priority.LOW,
                'reason': 'Scan em progresso'
            }
        }
    
    def decide(self, context: Dict) -> Dict:
        """
        Decide próxima ação baseada em contexto
        
        Args:
            context: {
                'target': str,
                'scan_results': Dict (opcional),
                'last_scan_date': datetime (opcional),
                'state': str (new/scanning/complete)
            }
        
        Returns:
            {
                'action': ActionType,
                'priority': Priority,
                'reason': str,
                'params': Dict
            }
        """
        
        # Avaliar todas as regras
        matched_rules = []
        
        for rule_name, rule in self.decision_rules.items():
            if rule['condition'](context):
                matched_rules.append({
                    'name': rule_name,
                    'action': rule['action'],
                    'priority': rule['priority'],
                    'reason': rule['reason']
                })
        
        # Se nenhuma regra matched, default
        if not matched_rules:
            return {
                'action': ActionType.WAIT,
                'priority': Priority.LOW,
                'reason': 'Nenhuma condição matched - aguardar',
                'params': {}
            }
        
        # Ordenar por prioridade (maior primeiro)
        matched_rules.sort(key=lambda r: r['priority'].value, reverse=True)
        
        # Pegar regra de maior prioridade
        top_rule = matched_rules[0]
        
        # Gerar parâmetros específicos para a ação
        params = self._generate_action_params(
            top_rule['action'],
            context
        )
        
        return {
            'action': top_rule['action'],
            'priority': top_rule['priority'],
            'reason': top_rule['reason'],
            'params': params,
            'matched_rules': len(matched_rules),
            'decision_method': 'RULE_BASED'
        }
    
    # Funções de condição (retornam True/False)
    
    def _is_new_target(self, ctx: Dict) -> bool:
        """Target nunca foi escaneado"""
        return ctx.get('state') == 'new'
    
    def _has_critical_vulns(self, ctx: Dict) -> bool:
        """Tem 1+ vulnerabilidades CRITICAL"""
        results = ctx.get('scan_results', {})
        vulns = results.get('vulnerabilities', [])
        
        critical = len([v for v in vulns if v.get('severity') == 'CRITICAL'])
        return critical >= self.thresholds['critical_vulnerabilities']
    
    def _has_multiple_high_vulns(self, ctx: Dict) -> bool:
        """Tem 3+ vulnerabilidades HIGH"""
        results = ctx.get('scan_results', {})
        vulns = results.get('vulnerabilities', [])
        
        high = len([v for v in vulns if v.get('severity') == 'HIGH'])
        return high >= self.thresholds['high_vulnerabilities']
    
    def _is_scan_outdated(self, ctx: Dict) -> bool:
        """Último scan há mais de 24h"""
        last_scan = ctx.get('last_scan_date')
        
        if not last_scan:
            return True
        
        if isinstance(last_scan, str):
            last_scan = datetime.fromisoformat(last_scan)
        
        age = datetime.now() - last_scan
        return age > timedelta(hours=self.thresholds['scan_interval_hours'])
    
    def _is_risk_critical(self, ctx: Dict) -> bool:
        """Risk score >= 50"""
        results = ctx.get('scan_results', {})
        risk = results.get('risk_score', 0)
        return risk >= self.thresholds['risk_score_critical']
    
    def _is_risk_high(self, ctx: Dict) -> bool:
        """Risk score >= 20"""
        results = ctx.get('scan_results', {})
        risk = results.get('risk_score', 0)
        return risk >= self.thresholds['risk_score_high']
    
    def _no_vulns_found(self, ctx: Dict) -> bool:
        """Zero vulnerabilidades encontradas"""
        results = ctx.get('scan_results', {})
        vulns = results.get('vulnerabilities', [])
        return len(vulns) == 0
    
    def _scan_in_progress(self, ctx: Dict) -> bool:
        """Scan ainda rodando"""
        return ctx.get('state') == 'scanning'
    
    def _generate_action_params(self, action: ActionType, ctx: Dict) -> Dict:
        """Gera parâmetros específicos para cada tipo de ação"""
        
        target = ctx.get('target', 'unknown')
        
        if action == ActionType.SCAN_FULL:
            return {
                'target': target,
                'scan_type': 'comprehensive',
                'modules': ['all'],
                'timeout': 3600
            }
        
        elif action == ActionType.SCAN_QUICK:
            return {
                'target': target,
                'scan_type': 'quick',
                'modules': ['ports', 'headers'],
                'timeout': 300
            }
        
        elif action == ActionType.RESCAN:
            return {
                'target': target,
                'scan_type': 'incremental',
                'modules': ['vulnerabilities'],
                'timeout': 1800
            }
        
        elif action == ActionType.ESCALATE:
            results = ctx.get('scan_results', {})
            return {
                'target': target,
                'severity': results.get('severity', 'CRITICAL'),
                'risk_score': results.get('risk_score', 0),
                'notification_channels': ['email', 'slack'],
                'urgency': 'immediate'
            }
        
        elif action == ActionType.GENERATE_REPORT:
            results = ctx.get('scan_results', {})
            return {
                'target': target,
                'format': 'pdf',
                'include_executive_summary': True,
                'include_technical_details': True,
                'severity': results.get('severity', 'MEDIUM')
            }
        
        elif action == ActionType.MONITOR:
            return {
                'target': target,
                'frequency': 'daily',
                'alert_on_change': True
            }
        
        elif action == ActionType.WAIT:
            return {
                'reason': 'No action required',
                'next_check': datetime.now() + timedelta(hours=1)
            }
        
        else:
            return {}
    
    def evaluate_workflow(self, context: Dict) -> List[Dict]:
        """
        Avalia workflow completo: do scan até relatório
        Retorna lista de ações em ordem de execução
        """
        
        workflow = []
        current_ctx = context.copy()
        
        # Loop até workflow estar completo
        max_steps = 10  # Prevenir loop infinito
        for _ in range(max_steps):
            decision = self.decide(current_ctx)
            workflow.append(decision)
            
            # Se ação é terminal, parar
            if decision['action'] in [
                ActionType.WAIT,
                ActionType.GENERATE_REPORT,
                ActionType.ESCALATE
            ]:
                break
            
            # Simular próximo estado
            current_ctx = self._simulate_next_state(current_ctx, decision)
        
        return workflow
    
    def _simulate_next_state(self, ctx: Dict, decision: Dict) -> Dict:
        """Simula estado após executar ação"""
        
        new_ctx = ctx.copy()
        action = decision['action']
        
        # Simular mudanças de estado
        if action in [ActionType.SCAN_FULL, ActionType.SCAN_QUICK]:
            new_ctx['state'] = 'complete'
            new_ctx['last_scan_date'] = datetime.now()
        
        elif action == ActionType.RESCAN:
            new_ctx['state'] = 'complete'
            new_ctx['last_scan_date'] = datetime.now()
        
        return new_ctx
    
    def update_state(self, target: str, scan_results: Dict):
        """Atualiza estado do sistema com resultados de scan"""
        
        self.state['targets'][target] = {
            'last_scan': datetime.now(),
            'results': scan_results,
            'last_decision': self.decide({
                'target': target,
                'scan_results': scan_results,
                'state': 'complete'
            })
        }
        
        self.state['last_scan'] = datetime.now()
    
    def get_pending_actions(self) -> List[Dict]:
        """Retorna ações pendentes de execução"""
        
        actions = []
        
        for target, data in self.state['targets'].items():
            last_decision = data.get('last_decision', {})
            
            # Se decisão requer ação, adicionar
            if last_decision.get('priority', Priority.LOW).value >= Priority.MEDIUM.value:
                actions.append({
                    'target': target,
                    'action': last_decision.get('action'),
                    'priority': last_decision.get('priority'),
                    'reason': last_decision.get('reason')
                })
        
        # Ordenar por prioridade
        actions.sort(key=lambda a: a['priority'].value, reverse=True)
        
        return actions


# Teste
if __name__ == "__main__":
    motor = MotorDecisaoV2()
    
    print("🎯 LIBERTUS MOTOR DE DECISÃO v2.0 - TESTE")
    print("="*60)
    
    # Teste 1: Novo target
    print("\n1️⃣ Testando: Novo target")
    ctx1 = {
        'target': 'example.com',
        'state': 'new'
    }
    
    decision1 = motor.decide(ctx1)
    print(f"   Ação: {decision1['action'].value}")
    print(f"   Prioridade: {decision1['priority'].name}")
    print(f"   Razão: {decision1['reason']}")
    
    # Teste 2: Vulnerabilidade CRITICAL encontrada
    print("\n2️⃣ Testando: CRITICAL encontrada")
    ctx2 = {
        'target': 'vulnerable.com',
        'state': 'complete',
        'scan_results': {
            'vulnerabilities': [
                {'type': 'SQLi', 'severity': 'CRITICAL'},
                {'type': 'XSS', 'severity': 'HIGH'}
            ],
            'risk_score': 75,
            'severity': 'CRITICAL'
        }
    }
    
    decision2 = motor.decide(ctx2)
    print(f"   Ação: {decision2['action'].value}")
    print(f"   Prioridade: {decision2['priority'].name}")
    print(f"   Razão: {decision2['reason']}")
    print(f"   Params: {decision2['params']}")
    
    # Teste 3: Scan antigo
    print("\n3️⃣ Testando: Scan desatualizado")
    ctx3 = {
        'target': 'old-scan.com',
        'state': 'complete',
        'last_scan_date': datetime.now() - timedelta(hours=48),
        'scan_results': {
            'vulnerabilities': [],
            'risk_score': 5
        }
    }
    
    decision3 = motor.decide(ctx3)
    print(f"   Ação: {decision3['action'].value}")
    print(f"   Prioridade: {decision3['priority'].name}")
    print(f"   Razão: {decision3['reason']}")
    
    # Teste 4: Workflow completo
    print("\n4️⃣ Testando: Workflow completo")
    ctx4 = {
        'target': 'new-site.com',
        'state': 'new'
    }
    
    workflow = motor.evaluate_workflow(ctx4)
    print(f"   Total de passos: {len(workflow)}")
    for i, step in enumerate(workflow, 1):
        print(f"   Passo {i}: {step['action'].value} ({step['priority'].name})")
    
    print("\n" + "="*60)
