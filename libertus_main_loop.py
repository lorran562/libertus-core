#!/usr/bin/env python3
"""
LIBERTUS MAIN LOOP - CORAÇÃO DO SISTEMA
Sistema autônomo que roda 24/7 independente de interfaces
"""

import asyncio
import logging
import json
import time
from pathlib import Path
from datetime import datetime

# Setup
LIBERTUS_PATH = Path.home() / "LIBERTUS"
CORE_PATH = LIBERTUS_PATH / "core"
LOGS_PATH = LIBERTUS_PATH / "logs"
MEMORY_FILE = LOGS_PATH / "libertus_memory.json"
TARGETS_FILE = LOGS_PATH / "targets.json"

import sys
sys.path.insert(0, str(CORE_PATH))

# Importar Core
try:
    from core.libertus_core_interface import get_core
except ImportError:
    print("ERRO: Módulo libertus_core_interface não encontrado")
    print(f"Tentando importar de: {CORE_PATH}")
    sys.exit(1)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [LIBERTUS] - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_PATH / "main_loop.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LibertusMainLoop:
    """
    Loop central do LIBERTUS
    Sistema vivo que decide e age autonomamente
    """
    
    def __init__(self):
        self.core = get_core()
        self.memoria = self._load_memoria()
        self.targets = self._load_targets()
        self.running = True
        
        # SISTEMA DE OBJETIVOS (agora dinâmico)
        self.objetivos = self.memoria.get('objetivos_ativos', [
            {'nome': 'encontrar_vulnerabilidades_criticas', 'prioridade': 10, 'peso': 1.0, 'resultado_acumulado': 0},
            {'nome': 'mapear_padroes', 'prioridade': 7, 'peso': 0.8, 'resultado_acumulado': 0},
            {'nome': 'identificar_oportunidades_comerciais', 'prioridade': 8, 'peso': 0.9, 'resultado_acumulado': 0},
            {'nome': 'otimizar_eficiencia', 'prioridade': 6, 'peso': 0.7, 'resultado_acumulado': 0}
        ])
        
        # PESOS DINÂMICOS (aprendidos, não fixos)
        self.pesos_dinamicos = self.memoria.get('pesos_dinamicos', {
            'wordpress': 1.0,
            'shopify': 1.0,
            'laravel': 1.0,
            'generico': 1.0
        })
        
        # MÉTRICAS DE PERFORMANCE
        self.meta_metricas = self.memoria.get('meta_metricas', {
            'scans_ultimos_30': 0,
            'vulnerabilidades_encontradas': 0,
            'risk_medio_global': 0,
            'eficiencia': 0,
            'ultima_revisao': None
        })
        
        # VALOR REAL (não só técnico)
        self.valor_real = self.memoria.get('valor_real', {
            'sites_que_geraram_valor': [],
            'tipos_mais_lucrativos': {},
            'nichos_prioritarios': [],
            'estrategias_que_funcionaram': []
        })
        
        logger.info("="*70)
        logger.info("LIBERTUS MAIN LOOP - VALOR REAL")
        logger.info("Sistema com noção de valor composto")
        logger.info("="*70)
        logger.info("OBJETIVOS ATIVOS:")
        for obj in sorted(self.objetivos, key=lambda x: x['prioridade'], reverse=True):
            logger.info(f"  [{obj['prioridade']}] {obj['nome']} (resultado: {obj['resultado_acumulado']})")
        logger.info("PESOS DINÂMICOS:")
        for tipo, peso in self.pesos_dinamicos.items():
            logger.info(f"  {tipo}: {peso:.2f}")
    
    def _load_memoria(self):
        """Carrega memória persistente"""
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE) as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'scans_realizados': [],
            'padroes_aprendidos': {},
            'decisoes_tomadas': [],
            'estado_atual': 'inicializando'
        }
    
    def _load_targets(self):
        """Carrega lista de targets"""
        if TARGETS_FILE.exists():
            try:
                with open(TARGETS_FILE) as f:
                    return json.load(f)
            except:
                pass
        
        # Targets padrão para teste
        return [
            {'url': 'https://google.com', 'prioridade': 'baixa', 'intervalo_horas': 24},
            {'url': 'https://github.com', 'prioridade': 'baixa', 'intervalo_horas': 24}
        ]
    
    def _save_memoria(self):
        """Salva memória persistente"""
        try:
            MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(MEMORY_FILE, 'w') as f:
                json.dump(self.memoria, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar memória: {e}")
    
    def _save_targets(self):
        """Salva targets"""
        try:
            TARGETS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(TARGETS_FILE, 'w') as f:
                json.dump(self.targets, f, indent=2)
        except Exception as e:
            logger.error(f"Erro ao salvar targets: {e}")
    
    async def decidir_proxima_acao(self):
        """
        Motor de decisão autônomo ADAPTATIVO
        Decide baseado em objetivos + contexto + aprendizado
        """
        contexto = {
            'hora': datetime.now().hour,
            'targets': self.targets,
            'ultima_execucao': self.memoria.get('ultima_execucao'),
            'scans_hoje': len([s for s in self.memoria['scans_realizados'] 
                              if s.get('data', '').startswith(datetime.now().strftime('%Y-%m-%d'))]),
            'padroes': self.memoria.get('padroes_aprendidos', {})
        }
        
        logger.info("[DECISÃO] Analisando contexto adaptativo...")
        logger.info(f"  Hora: {contexto['hora']}h")
        logger.info(f"  Targets: {len(contexto['targets'])}")
        logger.info(f"  Scans hoje: {contexto['scans_hoje']}")
        logger.info(f"  Padrões conhecidos: {len(contexto['padroes'])}")
        
        # PRIORIZAÇÃO INTELIGENTE DE TARGETS
        targets_priorizados = self._priorizar_targets(contexto)
        
        # DECISÃO 1: Escanear target prioritário
        if targets_priorizados:
            target = targets_priorizados[0]
            return {
                'acao': 'scan',
                'target': target['url'],
                'prioridade': target['prioridade_calculada'],
                'motivo': target['motivo']
            }
        
        # DECISÃO 2: Analisar padrões (objetivo: mapear_padroes)
        if len(self.memoria['scans_realizados']) >= 5:
            objetivo_padroes = next(o for o in self.objetivos if o['nome'] == 'mapear_padroes')
            if objetivo_padroes['prioridade'] >= 7:
                return {
                    'acao': 'analisar_padroes',
                    'motivo': f"Objetivo '{objetivo_padroes['nome']}' prioridade {objetivo_padroes['prioridade']}"
                }
        
        # DECISÃO 3: Ajustar estratégia (se performance ruim)
        if self._deve_ajustar_estrategia():
            return {
                'acao': 'ajustar_estrategia',
                'motivo': 'Performance abaixo do esperado'
            }
        
        # DECISÃO 4: Dormir
        return {
            'acao': 'dormir',
            'tempo': 300,
            'motivo': 'Nada prioritário no momento'
        }
    
    def _priorizar_targets(self, contexto):
        """
        Priorização INTELIGENTE baseada em:
        - Risk anterior (alto = prioridade alta)
        - Tipo de site (padrões aprendidos)
        - Intervalo desde último scan
        - Objetivos ativos
        """
        targets_com_prioridade = []
        
        for target in self.targets:
            url = target['url']
            intervalo_config = target.get('intervalo_horas', 24)
            prioridade_base = target.get('prioridade', 'media')
            
            # Verificar último scan
            ultimo_scan = self._get_ultimo_scan(url)
            
            if ultimo_scan:
                horas_desde = (time.time() - ultimo_scan['timestamp']) / 3600
                
                # Não escanear se intervalo não atingido
                if horas_desde < intervalo_config:
                    continue
                
                # PRIORIZAÇÃO BASEADA EM RISK ANTERIOR
                risk_anterior = ultimo_scan.get('risk_score', 0)
                
                if risk_anterior >= 70:
                    prioridade = 'CRÍTICA'
                    peso = 10
                elif risk_anterior >= 50:
                    prioridade = 'ALTA'
                    peso = 8
                elif risk_anterior >= 30:
                    prioridade = 'MEDIA'
                    peso = 5
                else:
                    prioridade = 'BAIXA'
                    peso = 2
            else:
                # Primeiro scan - prioridade média
                prioridade = 'MEDIA'
                peso = 5
                risk_anterior = 0
            
            # AJUSTAR PESO BASEADO EM PADRÕES APRENDIDOS
            tipo_site = self._identificar_tipo_site(url)
            if tipo_site in contexto['padroes']:
                risk_medio_tipo = contexto['padroes'][tipo_site].get('risk_medio', 0)
                
                if risk_medio_tipo > 50:
                    peso *= 1.5  # Aumentar prioridade para tipos problemáticos
                    logger.info(f"  [APRENDIZADO] {tipo_site} tem risk médio {risk_medio_tipo:.1f} - prioridade aumentada")
            
            # AJUSTAR POR OBJETIVO
            objetivo_vulns = next(o for o in self.objetivos if 'vulnerabilidades_criticas' in o['nome'])
            if risk_anterior >= 70:
                peso *= objetivo_vulns['peso']
            
            targets_com_prioridade.append({
                'url': url,
                'prioridade_calculada': peso,
                'prioridade_label': prioridade,
                'risk_anterior': risk_anterior,
                'tipo': tipo_site,
                'motivo': f"{prioridade} (risk anterior: {risk_anterior}, tipo: {tipo_site})"
            })
        
        # Ordenar por prioridade calculada
        targets_com_prioridade.sort(key=lambda x: x['prioridade_calculada'], reverse=True)
        
        # FILTRO ANTI-FARM: Evitar targets fáceis
        targets_com_prioridade = self._evitar_targets_faceis(targets_com_prioridade)
        
        if targets_com_prioridade:
            logger.info(f"[PRIORIZAÇÃO] Top 3 targets:")
            for t in targets_com_prioridade[:3]:
                logger.info(f"  {t['prioridade_label']} ({t['prioridade_calculada']:.1f}): {t['url']}")
        
        return targets_com_prioridade
    
    def _identificar_tipo_site(self, url):
        """Identifica tipo de site por URL"""
        url_lower = url.lower()
        if 'wordpress' in url_lower or 'wp-' in url_lower:
            return 'wordpress'
        elif 'shopify' in url_lower:
            return 'shopify'
        elif 'laravel' in url_lower:
            return 'laravel'
        else:
            return 'generico'
    
    def _deve_ajustar_estrategia(self):
        """Decide se deve ajustar estratégia baseado em performance"""
        scans_recentes = self.memoria['scans_realizados'][-10:]
        
        if len(scans_recentes) < 5:
            return False
        
        # Se últimos scans tiveram risk muito baixo, ajustar
        risk_medio = sum(s.get('risk_score', 0) for s in scans_recentes) / len(scans_recentes)
        
        return risk_medio < 15  # Muito baixo = targets não interessantes
    
    async def executar_acao(self, decisao):
        """Executa a ação decidida ADAPTATIVAMENTE"""
        acao = decisao['acao']
        
        logger.info(f"[AÇÃO] {acao.upper()}")
        logger.info(f"  Motivo: {decisao['motivo']}")
        if 'prioridade' in decisao:
            logger.info(f"  Prioridade: {decisao['prioridade']:.1f}")
        
        if acao == 'scan':
            await self._executar_scan(decisao['target'])
        
        elif acao == 'analisar_padroes':
            self._analisar_padroes()
        
        elif acao == 'ajustar_estrategia':
            self._ajustar_estrategia()
        
        elif acao == 'dormir':
            logger.info(f"  Aguardando {decisao['tempo']}s...")
            await asyncio.sleep(decisao['tempo'])
        
        # Salvar decisão na memória COM EXPLICAÇÃO
        self.memoria['decisoes_tomadas'].append({
            'timestamp': time.time(),
            'data': datetime.now().isoformat(),
            'decisao': decisao,
            'explicacao': self._explicar_decisao(decisao)
        })
        
        self._save_memoria()
    
    def _ajustar_estrategia(self):
        """Ajusta estratégia baseado em performance"""
        logger.info("[ESTRATÉGIA] Ajustando comportamento...")
        
        scans_recentes = self.memoria['scans_realizados'][-10:]
        risk_medio = sum(s.get('risk_score', 0) for s in scans_recentes) / len(scans_recentes)
        
        logger.info(f"  Risk médio recente: {risk_medio:.1f}")
        
        # Se risk muito baixo, focar em tipos mais problemáticos
        if risk_medio < 15:
            logger.info("  [AJUSTE] Aumentando foco em tipos com maior risk")
            
            # Aumentar prioridade do objetivo de encontrar vulnerabilidades
            for obj in self.objetivos:
                if 'vulnerabilidades' in obj['nome']:
                    obj['prioridade'] = min(10, obj['prioridade'] + 1)
                    logger.info(f"    Objetivo '{obj['nome']}' → prioridade {obj['prioridade']}")
        
        # Salvar ajuste
        self.memoria.setdefault('ajustes_estrategicos', []).append({
            'timestamp': time.time(),
            'data': datetime.now().isoformat(),
            'motivo': f'Risk médio baixo ({risk_medio:.1f})',
            'acao': 'Aumentar foco em vulnerabilidades'
        })
        
        self._save_memoria()
    
    async def _executar_scan(self, target):
        """Executa scan de um target"""
        logger.info(f"[SCAN] Iniciando → {target}")
        
        try:
            # DELEGAR AO CORE
            resultado = await self.core.handle_scan(target, user="loop_autonomo")
            
            if resultado['success']:
                risk = resultado['risk_score']
                vulns = len(resultado['vulnerabilities'])
                
                logger.info(f"[SCAN] ✅ Completo")
                logger.info(f"  Risk: {risk}/100")
                logger.info(f"  Vulns: {vulns}")
                
                # Salvar na memória
                scan_data = {
                    'timestamp': time.time(),
                    'data': datetime.now().isoformat(),
                    'target': target,
                    'risk_score': risk,
                    'vulnerabilities_count': vulns,
                    'severity': resultado.get('severity', 'UNKNOWN')
                }
                
                self.memoria['scans_realizados'].append(scan_data)
                self.memoria['ultima_execucao'] = time.time()
                
                # Aprender com resultado
                self._aprender_com_scan(target, scan_data)
                
                self._save_memoria()
            else:
                logger.error(f"[SCAN] ❌ Falhou: {resultado.get('error')}")
        
        except Exception as e:
            logger.error(f"[SCAN] ❌ Erro: {e}", exc_info=True)
    
    def _aprender_com_scan(self, target, scan_data):
        """Aprende padrões com base no scan + META-ADAPTAÇÃO + VALOR REAL"""
        # Identificar tipo de site
        tipo = self._identificar_tipo_site(target)
        
        # Atualizar padrões
        if tipo not in self.memoria['padroes_aprendidos']:
            self.memoria['padroes_aprendidos'][tipo] = {
                'count': 0,
                'risk_medio': 0,
                'vulns_comum': []
            }
        
        padroes = self.memoria['padroes_aprendidos'][tipo]
        padroes['count'] += 1
        
        # Calcular média de risk
        padroes['risk_medio'] = (
            (padroes['risk_medio'] * (padroes['count'] - 1) + scan_data['risk_score']) 
            / padroes['count']
        )
        
        logger.info(f"[APRENDIZADO] Padrão atualizado: {tipo}")
        logger.info(f"  Risk médio: {padroes['risk_medio']:.1f}")
        
        # VALOR REAL: Calcular valor composto
        valor_real = self._calcular_valor_real(target, scan_data)
        
        # Registrar se gerou valor
        self._registrar_valor_real(target, scan_data, valor_real)
        
        # META-ADAPTAÇÃO: Ajustar pesos automaticamente
        self._ajustar_pesos_automaticamente(tipo, scan_data)
        
        # META-ADAPTAÇÃO: Atualizar resultado de objetivos
        if scan_data['risk_score'] >= 70:
            self._atualizar_resultado_objetivo('vulnerabilidades_criticas', 1)
        
        if scan_data['vulnerabilities_count'] > 0:
            self._atualizar_resultado_objetivo('mapear_padroes', 1)
        
        # Valor real alto = objetivo comercial cumprido
        if valor_real >= 0.7:
            self._atualizar_resultado_objetivo('oportunidades_comerciais', 1)
        
        # META-ADAPTAÇÃO: A cada 10 scans, auto-avaliar
        if len(self.memoria['scans_realizados']) % 10 == 0:
            self._avaliar_performance_global()
    
    def _analisar_padroes(self):
        """Analisa padrões aprendidos"""
        logger.info("[ANÁLISE] Padrões aprendidos:")
        
        for tipo, dados in self.memoria['padroes_aprendidos'].items():
            logger.info(f"  {tipo}:")
            logger.info(f"    Scans: {dados['count']}")
            logger.info(f"    Risk médio: {dados['risk_medio']:.1f}")
    
    def _get_ultimo_scan(self, url):
        """Retorna último scan de uma URL"""
        scans = [s for s in self.memoria['scans_realizados'] if s['target'] == url]
        return scans[-1] if scans else None
    

    # ==================== META-ADAPTAÇÃO ====================
    
    def _avaliar_performance_global(self):
        """
        AUTO-AVALIAÇÃO DE PERFORMANCE
        Sistema mede a si mesmo
        """
        logger.info("[META] Auto-avaliação de performance...")
        
        scans = self.memoria['scans_realizados']
        
        if len(scans) < 3:
            logger.info("  Scans insuficientes para avaliação")
            return
        
        # Últimos 10 scans
        recentes = scans[-10:]
        
        # Calcular métricas
        risk_medio = sum(s.get('risk_score', 0) for s in recentes) / len(recentes)
        vulns_total = sum(s.get('vulnerabilities_count', 0) for s in recentes)
        
        # Atualizar meta-métricas
        self.meta_metricas.update({
            'scans_ultimos_30': len(recentes),
            'vulnerabilidades_encontradas': vulns_total,
            'risk_medio_global': risk_medio,
            'eficiencia': vulns_total / len(recentes) if len(recentes) > 0 else 0,
            'ultima_revisao': datetime.now().isoformat()
        })
        
        logger.info(f"  Risk médio: {risk_medio:.1f}")
        logger.info(f"  Vulnerabilidades: {vulns_total}")
        logger.info(f"  Eficiência: {self.meta_metricas['eficiencia']:.2f} vulns/scan")
        
        # DECISÃO META: Estratégia atual funciona?
        if risk_medio < 20:
            logger.info("  [META-DECISÃO] Performance BAIXA - Revisão necessária")
            self._revisar_estrategia_completa()
        elif risk_medio > 60:
            logger.info("  [META-DECISÃO] Performance ALTA - Manter estratégia")
        
        self.memoria['meta_metricas'] = self.meta_metricas
        self._save_memoria()
    
    def _ajustar_pesos_automaticamente(self, tipo_site, resultado_scan):
        """
        AJUSTE AUTOMÁTICO DE PESOS
        Não usa valores fixos - aprende com resultados
        """
        risk = resultado_scan.get('risk_score', 0)
        vulns = resultado_scan.get('vulnerabilities_count', 0)
        
        # Peso atual
        peso_atual = self.pesos_dinamicos.get(tipo_site, 1.0)
        
        # APRENDIZADO: Aumentar peso se gera resultados
        if risk >= 50 or vulns >= 5:
            novo_peso = min(3.0, peso_atual * 1.2)  # Aumentar 20%
            logger.info(f"[META-PESO] {tipo_site}: {peso_atual:.2f} → {novo_peso:.2f} (AUMENTADO - bons resultados)")
        
        # APRENDIZADO: Reduzir peso se não gera resultados
        elif risk < 15 and vulns == 0:
            novo_peso = max(0.3, peso_atual * 0.8)  # Reduzir 20%
            logger.info(f"[META-PESO] {tipo_site}: {peso_atual:.2f} → {novo_peso:.2f} (REDUZIDO - poucos resultados)")
        
        else:
            novo_peso = peso_atual  # Manter
        
        self.pesos_dinamicos[tipo_site] = novo_peso
        self.memoria['pesos_dinamicos'] = self.pesos_dinamicos
        self._save_memoria()
    
    def _revisar_objetivos(self):
        """
        REVISÃO DE OBJETIVOS
        Detecta objetivos que não geram resultado e substitui
        """
        logger.info("[META-OBJETIVO] Revisando objetivos...")
        
        for obj in self.objetivos:
            resultado = obj.get('resultado_acumulado', 0)
            
            # Objetivo não gera resultado há muito tempo?
            if resultado < 5 and len(self.memoria['scans_realizados']) > 20:
                logger.info(f"  [REVISAR] '{obj['nome']}' com baixo resultado ({resultado})")
                
                # DECISÃO META: Substituir objetivo
                if 'vulnerabilidades' in obj['nome']:
                    # Trocar foco de "críticas" para "padrões recorrentes"
                    obj['nome'] = 'encontrar_padroes_recorrentes'
                    obj['prioridade'] = 9
                    logger.info(f"    → SUBSTITUÍDO por '{obj['nome']}'")
                
                elif 'eficiencia' in obj['nome']:
                    # Trocar por foco em nichos específicos
                    obj['nome'] = 'focar_nichos_especificos'
                    obj['prioridade'] = 8
                    logger.info(f"    → SUBSTITUÍDO por '{obj['nome']}'")
                
                obj['resultado_acumulado'] = 0  # Reset
        
        self.memoria['objetivos_ativos'] = self.objetivos
        self._save_memoria()
    
    def _criar_novo_objetivo(self, padrão_descoberto):
        """
        CRIAÇÃO DE NOVOS OBJETIVOS
        Sistema cria objetivos baseado em padrões descobertos
        """
        logger.info(f"[META-CRIAÇÃO] Novo padrão descoberto: {padrão_descoberto}")
        
        # Verificar se já existe objetivo similar
        for obj in self.objetivos:
            if padrão_descoberto['tipo'] in obj['nome']:
                logger.info("  Objetivo similar já existe")
                return
        
        # CRIAR NOVO OBJETIVO
        novo_objetivo = {
            'nome': f"explorar_{padrão_descoberto['tipo']}_vulnerabilidades",
            'prioridade': 7,
            'peso': 1.0,
            'resultado_acumulado': 0,
            'criado_automaticamente': True,
            'data_criacao': datetime.now().isoformat()
        }
        
        self.objetivos.append(novo_objetivo)
        
        logger.info(f"  [NOVO OBJETIVO] '{novo_objetivo['nome']}' criado")
        logger.info(f"    Prioridade: {novo_objetivo['prioridade']}")
        
        self.memoria['objetivos_ativos'] = self.objetivos
        self._save_memoria()
    
    def _revisar_estrategia_completa(self):
        """
        REVISÃO ESTRATÉGICA COMPLETA
        Sistema questiona e modifica a própria caixa
        """
        logger.info("[META-ESTRATÉGIA] Revisão estratégica completa...")
        
        # 1. Avaliar performance
        self._avaliar_performance_global()
        
        # 2. Revisar objetivos
        self._revisar_objetivos()
        
        # 3. Analisar padrões descobertos
        padroes = self.memoria.get('padroes_aprendidos', {})
        
        for tipo, dados in padroes.items():
            risk_medio = dados.get('risk_medio', 0)
            
            # Padrão MUITO problemático? Criar objetivo específico
            if risk_medio > 70:
                self._criar_novo_objetivo({
                    'tipo': tipo,
                    'risk_medio': risk_medio
                })
        
        logger.info("[META-ESTRATÉGIA] Revisão completa")
    
    def _atualizar_resultado_objetivo(self, objetivo_nome, valor):
        """Atualiza resultado acumulado de um objetivo"""
        for obj in self.objetivos:
            if objetivo_nome in obj['nome']:
                obj['resultado_acumulado'] = obj.get('resultado_acumulado', 0) + valor
                break
    
    # ==================== VALOR REAL ====================
    
    def _calcular_valor_real(self, target, scan_data):
        """
        EIXO DE VALOR COMPOSTO
        Não só "risk" - valor REAL considerando múltiplos fatores
        """
        risk = scan_data.get('risk_score', 0)
        vulns = scan_data.get('vulnerabilities_count', 0)
        tipo = self._identificar_tipo_site(target)
        
        # COMPONENTE 1: Impacto técnico (risk)
        impacto_tecnico = risk / 100.0  # 0-1
        
        # COMPONENTE 2: Potencial comercial (tipo de site, nicho)
        potencial_comercial = self._calcular_potencial_comercial(target, tipo)
        
        # COMPONENTE 3: Raridade (não só frequência)
        raridade = self._calcular_raridade(tipo, vulns)
        
        # COMPONENTE 4: Complexidade (evitar targets fáceis demais)
        complexidade = self._calcular_complexidade(scan_data)
        
        # VALOR REAL = média ponderada
        valor_real = (
            impacto_tecnico * 0.3 +
            potencial_comercial * 0.4 +
            raridade * 0.2 +
            complexidade * 0.1
        )
        
        logger.info(f"[VALOR REAL] {target}")
        logger.info(f"  Impacto técnico: {impacto_tecnico:.2f}")
        logger.info(f"  Potencial comercial: {potencial_comercial:.2f}")
        logger.info(f"  Raridade: {raridade:.2f}")
        logger.info(f"  Complexidade: {complexidade:.2f}")
        logger.info(f"  → VALOR TOTAL: {valor_real:.2f}")
        
        return valor_real
    
    def _calcular_potencial_comercial(self, target, tipo):
        """
        Potencial comercial do site
        Não é só "risk alto" - é "site que vale a pena"
        """
        # Nichos prioritários (baseado em SHIELD)
        nichos_alto_valor = ['clinica', 'medic', 'hospital', 'contabil', 'advoca', 'law', 'finance']
        
        potencial = 0.5  # Base
        
        # Nicho prioritário
        for nicho in nichos_alto_valor:
            if nicho in target.lower():
                potencial += 0.3
                logger.info(f"    [COMERCIAL] Nicho alto valor: {nicho}")
                break
        
        # Tipo conhecido lucrativo
        if tipo in self.valor_real['tipos_mais_lucrativos']:
            taxa_conversao = self.valor_real['tipos_mais_lucrativos'][tipo]
            potencial += taxa_conversao * 0.2
        
        return min(1.0, potencial)
    
    def _calcular_raridade(self, tipo, vulns):
        """
        Raridade do padrão
        Não é "frequente = importante"
        É "raro E impactante = importante"
        """
        padroes = self.memoria.get('padroes_aprendidos', {})
        
        if tipo not in padroes:
            return 0.8  # Novo = interessante
        
        count = padroes[tipo]['count']
        
        # Muito comum = menos raro
        if count > 20:
            raridade = 0.3
        elif count > 10:
            raridade = 0.5
        else:
            raridade = 0.7
        
        # Mas se gera vulnerabilidades, aumenta
        if vulns > 5:
            raridade += 0.2
        
        return min(1.0, raridade)
    
    def _calcular_complexidade(self, scan_data):
        """
        Complexidade do target
        PENALIZAR baixa complexidade + baixo impacto (evitar farm)
        VALORIZAR alta complexidade + alto impacto
        """
        risk = scan_data.get('risk_score', 0)
        vulns = scan_data.get('vulnerabilities_count', 0)
        
        # Heurística de complexidade
        if risk < 20 and vulns < 2:
            # Fácil E baixo impacto = RUIM
            return 0.2
        
        elif risk >= 70 and vulns >= 5:
            # Difícil E alto impacto = BOM
            return 0.9
        
        else:
            # Médio
            return 0.5
    
    def _registrar_valor_real(self, target, scan_data, valor_calculado):
        """
        Registra sites que geraram VALOR REAL
        Não só vulnerabilidades
        """
        if valor_calculado >= 0.7:
            self.valor_real['sites_que_geraram_valor'].append({
                'target': target,
                'valor': valor_calculado,
                'timestamp': time.time(),
                'data': datetime.now().isoformat(),
                'risk': scan_data.get('risk_score', 0),
                'vulns': scan_data.get('vulnerabilities_count', 0)
            })
            
            logger.info(f"[VALOR REAL] Site registrado como valioso: {target}")
            
            # Atualizar tipos mais lucrativos
            tipo = self._identificar_tipo_site(target)
            if tipo not in self.valor_real['tipos_mais_lucrativos']:
                self.valor_real['tipos_more_lucrativos'][tipo] = 0
            
            self.valor_real['tipos_mais_lucrativos'][tipo] += 0.1  # Incrementar
        
        self.memoria['valor_real'] = self.valor_real
        self._save_memoria()
    
    def _evitar_targets_faceis(self, targets_priorizados):
        """
        FILTRO ANTI-FARM
        Remove targets fáceis demais com baixo impacto
        """
        filtrados = []
        
        for target in targets_priorizados:
            risk_anterior = target.get('risk_anterior', 0)
            tipo = target.get('tipo', 'generico')
            
            # Target muito fácil?
            if risk_anterior < 15:
                # Só aceitar se for nicho prioritário
                if any(nicho in target['url'].lower() for nicho in ['clinica', 'medic', 'contabil', 'advoca']):
                    filtrados.append(target)
                    logger.info(f"  [ANTI-FARM] Aceito (nicho prioritário): {target['url']}")
                else:
                    logger.info(f"  [ANTI-FARM] Ignorado (fácil + baixo valor): {target['url']}")
            else:
                filtrados.append(target)
        
        return filtrados

    
    def _explicar_decisao(self, decisao):
        """Explica por que uma decisão foi tomada"""
        acao = decisao['acao']
        
        if acao == 'scan':
            return f"Escaneando {decisao['target']} com prioridade {decisao.get('prioridade', 'N/A'):.1f}"
        
        elif acao == 'analisar_padroes':
            return "Analisando padrões aprendidos para ajustar comportamento"
        
        elif acao == 'ajustar_estrategia':
            return "Performance abaixo do esperado - ajustando estratégia"
        
        elif acao == 'dormir':
            return "Nada prioritário no momento - aguardando"
        
        return "Decisão desconhecida"


    async def run(self):
        """Loop principal"""
        logger.info("[LOOP] Sistema ativo")
        self.memoria['estado_atual'] = 'rodando'
        
        while self.running:
            try:
                # 1. DECIDIR
                decisao = await self.decidir_proxima_acao()
                
                # 2. EXECUTAR
                await self.executar_acao(decisao)
                
                # 3. Pequeno delay entre ciclos
                await asyncio.sleep(10)
            
            except KeyboardInterrupt:
                logger.info("[LOOP] Interrompido pelo usuário")
                self.running = False
            
            except Exception as e:
                logger.error(f"[LOOP] Erro: {e}", exc_info=True)
                await asyncio.sleep(60)  # Espera 1 min em caso de erro
        
        self.memoria['estado_atual'] = 'parado'
        self._save_memoria()
        logger.info("[LOOP] Sistema encerrado")

def main():
    """Entry point"""
    loop_sistema = LibertusMainLoop()
    asyncio.run(loop_sistema.run())

if __name__ == "__main__":
    main()
    
