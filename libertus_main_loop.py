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

# Importar Core
from libertus_core_interface import get_core

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
        
        # SISTEMA DE OBJETIVOS
        self.objetivos = [
            {'nome': 'encontrar_vulnerabilidades_criticas', 'prioridade': 10, 'peso': 1.0},
            {'nome': 'mapear_padroes', 'prioridade': 7, 'peso': 0.8},
            {'nome': 'identificar_oportunidades_comerciais', 'prioridade': 8, 'peso': 0.9},
            {'nome': 'otimizar_eficiencia', 'prioridade': 6, 'peso': 0.7}
        ]
        
        logger.info("="*70)
        logger.info("LIBERTUS MAIN LOOP - INICIANDO")
        logger.info("Sistema autônomo adaptativo")
        logger.info("="*70)
        logger.info("OBJETIVOS ATIVOS:")
        for obj in sorted(self.objetivos, key=lambda x: x['prioridade'], reverse=True):
            logger.info(f"  [{obj['prioridade']}] {obj['nome']}")
    
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
        
        # Salvar decisão na memória
        self.memoria['decisoes_tomadas'].append({
            'timestamp': time.time(),
            'data': datetime.now().isoformat(),
            'decisao': decisao
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
        """Aprende padrões com base no scan"""
        # Identificar tipo de site
        if 'wordpress' in target.lower():
            tipo = 'wordpress'
        elif 'shopify' in target.lower():
            tipo = 'shopify'
        else:
            tipo = 'generico'
        
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
