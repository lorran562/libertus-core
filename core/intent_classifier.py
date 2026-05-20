"""
intent_classifier.py — Classificador de Intenção do Libertus
Converte linguagem natural em ações reais nos módulos corretos.
Sem este módulo o Libertus é manual. Com ele, é autônomo.

Integração: chamado pelo orquestrador ANTES de qualquer outra decisão.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Intencao:
    tipo: str           # pentest | recon | scan | wordlist | analisar | skill | conversa | evolucao | absorver
    confianca: float    # 0.0 a 1.0
    alvo: str           # URL, IP, arquivo, domínio
    parametros: Dict    # parâmetros extras detectados
    acoes: List[str]    # sequência de ações a executar
    autonomo: bool      # True = executa sem confirmação


class IntentClassifier:
    """
    Classifica intenção e define sequência de ações automáticas.
    
    Exemplo:
        clf = IntentClassifier()
        intent = clf.classificar("analisa o site cassino.com e me dá um relatório de falhas")
        # intent.tipo = "pentest_completo"
        # intent.alvo = "cassino.com"
        # intent.acoes = ["recon", "scan", "pentest", "relatorio"]
    """

    # Padrões de intenção — ordem importa (mais específico primeiro)
    PADROES = [
        # ── PENTEST / SEGURANÇA ───────────────────────────────────────────
        {
            "tipo": "pentest_completo",
            "triggers": [
                r"analisa.*(site|sistema|servidor|domínio|dominio|url|ip).*falha",
                r"(encontra|encontre|acha|ache|detecta|detecte).*(falha|vulnerabilidade|vuln|brecha|problema)",
                r"(testa|teste|verifica|verifique).*(segurança|seguranca|pentest|hack)",
                r"(relatório|relatorio|report).*(segurança|seguranca|vuln|falha)",
                r"pentest\s+\S+",
                r"(quais|que).*(falha|vulnerabilidade|brecha).*(site|sistema|servidor)",
                r"(site|sistema|servidor).*(segur|vuln|falha|brecha|hack)",
                r"o que.*(errado|inseguro|vulnerável|vulneravel).*(site|sistema)",
            ],
            "acoes": ["recon", "scan_web", "scan_portas", "pentest", "relatorio"],
            "autonomo": True,
            "confianca_base": 0.92,
        },
        # ── RECONHECIMENTO ────────────────────────────────────────────────
        {
            "tipo": "recon",
            "triggers": [
                r"(recon|reconnaissance|osint).*(de|em|sobre|no|na)\s+\S+",
                r"(informações|informacoes|info|dados).*(sobre|de|do|da).*(site|domínio|dominio|empresa)",
                r"(descobre|descubra|mapeia|mapeie).*(subdomínio|subdomain|email|dns|servidor)",
                r"(quem|qual|onde).*(dono|proprietário|proprietario|host|servidor|registrado)",
                r"whois|dns\s+(lookup|enum)|zone.?transfer",
            ],
            "acoes": ["recon"],
            "autonomo": True,
            "confianca_base": 0.88,
        },
        # ── SCAN DE REDE ──────────────────────────────────────────────────
        {
            "tipo": "scan",
            "triggers": [
                r"(scan|escaneia|escanear|varre|varrer|sonda|sondar)\s+\S+",
                r"(porta|port|serviço|servico).*(aberta|aberto|open|rodando|ativo)",
                r"(quais|que).*(porta|serviço|servico).*(aberta|aberto|open|exposta|exposto)",
                r"nmap\s+\S+",
                r"(descobre|descubra).*(porta|serviço|servico)",
            ],
            "acoes": ["scan_portas"],
            "autonomo": True,
            "confianca_base": 0.90,
        },
        # ── WORDLIST ──────────────────────────────────────────────────────
        {
            "tipo": "wordlist",
            "triggers": [
                r"(gera|cria|faz).*(wordlist|lista.*(senha|password|diretório|diretorio|subdomínio))",
                r"(senha|password).*(prováve|provave|possíve|possive|comum|padrão|padrao)",
                r"wordlist.*(para|do|da|de)\s+\S+",
            ],
            "acoes": ["wordlist"],
            "autonomo": True,
            "confianca_base": 0.88,
        },
        # ── ANÁLISE DE CÓDIGO / ENG. REVERSA ─────────────────────────────
        {
            "tipo": "analisar_codigo",
            "triggers": [
                r"(analisa|analyze|revisa|revise|lê|le|leia).*(código|codigo|script|arquivo|arquivo\.py|\.js|\.gd)",
                r"(o que|como).*(código|codigo|script|função|funcao).*(faz|funciona|significa)",
                r"(melhora|melhore|refatora|refatore|otimiza|otimize).*(código|codigo|script|função|funcao)",
                r"engenharia.?reversa",
                r"(encontra|encontre|detecta|detecte).*(bug|erro|problema).*(código|codigo)",
            ],
            "acoes": ["eng_reversa"],
            "autonomo": True,
            "confianca_base": 0.87,
        },
        # ── EVOLUÇÃO DO SISTEMA ───────────────────────────────────────────
        {
            "tipo": "evolucao",
            "triggers": [
                r"(evolui|evolu|melhora|melhore).*(sistema|libertus|você|voce)",
                r"(analisa|verifique|checa).*(estado|status|saúde|saude).*(sistema|libertus)",
                r"(o que|oque).*(pode|falta|melhorar|evoluir).*(sistema|libertus)",
                r"ciclo.*(evolução|evolucao)",
            ],
            "acoes": ["evolucao"],
            "autonomo": True,
            "confianca_base": 0.85,
        },
        # ── ABSORVER DOCUMENTO ────────────────────────────────────────────
        {
            "tipo": "absorver",
            "triggers": [
                r"(absorve|absorva|aprende|aprenda|lê|le|leia|processa|processe).*(arquivo|documento|pdf|\.txt|\.md)",
                r"(ensina|ensine).*(partir|de|com|usando).*(arquivo|documento|pdf)",
                r"/absorver\s+\S+",
            ],
            "acoes": ["absorver"],
            "autonomo": True,
            "confianca_base": 0.90,
        },
        # ── CRIAR SKILL ───────────────────────────────────────────────────
        {
            "tipo": "criar_skill",
            "triggers": [
                r"(cria|crie|salva|salve|registra|registre).*(skill|habilidade|automação|automacao)",
                r"(aprende|aprenda|memoriza|memorize).*(como|a).+(sempre|toda vez|automaticamente)",
                r"(faz|faça).*(isso|esse|esta).*(sempre|automaticamente|sozinho)",
            ],
            "acoes": ["criar_skill"],
            "autonomo": False,
            "confianca_base": 0.83,
        },
    ]

    # Extratores de alvo por tipo
    EXTRATORES_ALVO = [
        # URL completa
        r"https?://[\w\-\.]+(?:/[\w\-\./]*)?",
        # Domínio com TLD
        r"\b[\w\-]+\.(?:com|net|org|io|br|co|gov|edu|br|casino|bet)(?:\.\w+)?\b",
        # IP
        r"\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b",
        # Caminho de arquivo
        r"(?:/[\w\-\./]+\.(?:py|js|ts|gd|txt|md|pdf))",
        # Windows path
        r"[A-Za-z]:\\[\w\\\-\. ]+",
    ]

    def classificar(self, texto: str) -> Intencao:
        """
        Classifica a intenção do texto e retorna ação estruturada.
        """
        texto_l = texto.lower().strip()

        # 1. Tenta cada padrão
        melhor = None
        melhor_score = 0.0

        for padrao in self.PADROES:
            score = self._avaliar_padrao(texto_l, padrao["triggers"])
            if score > melhor_score:
                melhor_score = score
                melhor = padrao

        # 2. Se confiança alta o suficiente, usa o padrão
        if melhor and melhor_score >= 0.5:
            alvo = self._extrair_alvo(texto)
            confianca = min(1.0, melhor["confianca_base"] * melhor_score)
            return Intencao(
                tipo=melhor["tipo"],
                confianca=confianca,
                alvo=alvo,
                parametros=self._extrair_parametros(texto, melhor["tipo"]),
                acoes=melhor["acoes"],
                autonomo=melhor["autonomo"] and bool(alvo),
            )

        # 3. Fallback: conversa
        return Intencao(
            tipo="conversa",
            confianca=1.0,
            alvo="",
            parametros={},
            acoes=["groq"],
            autonomo=True,
        )

    def _avaliar_padrao(self, texto: str, triggers: List[str]) -> float:
        """Avalia quanto o texto corresponde aos triggers."""
        matches = 0
        for trigger in triggers:
            if re.search(trigger, texto, re.IGNORECASE | re.DOTALL):
                matches += 1
        return matches / len(triggers) if triggers else 0

    def _extrair_alvo(self, texto: str) -> str:
        """Extrai o alvo (URL, IP, domínio, arquivo) do texto."""
        for padrao in self.EXTRATORES_ALVO:
            m = re.search(padrao, texto, re.IGNORECASE)
            if m:
                return m.group(0).strip()
        # Tenta extrair palavra após preposições comuns
        # Palavras-chave de alvo seguidas de hostname
        m = re.search(
            r"(?:site|domínio|dominio|servidor|ip|url|arquivo|sistema|em|no|na|alvo)\s+(?:do|da|de|em|no|na)?\s*([\w\-\.\/\\:]+)",
            texto, re.IGNORECASE
        )
        if m:
            return m.group(1).strip()
        # Preposição seguida de alvo: "em localhost", "no servidor"
        m = re.search(r"\bem\s+([\w\-\.]+)\b", texto, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        # Última palavra que parece um alvo
        palavras = texto.split()
        for palavra in reversed(palavras):
            if palavra.lower() in ("localhost", "127.0.0.1"):
                return palavra
            if "." in palavra and len(palavra) > 4:
                return palavra.strip(".,!?")
        return ""

    def _extrair_parametros(self, texto: str, tipo: str) -> Dict:
        """Extrai parâmetros adicionais baseado no tipo de intenção."""
        params = {}

        if tipo == "pentest_completo":
            if re.search(r"(relatório|relatorio|report)", texto, re.IGNORECASE):
                params["gerar_relatorio"] = True
            if re.search(r"(completo|full|tudo|toda)", texto, re.IGNORECASE):
                params["modo"] = "completo"
            else:
                params["modo"] = "rapido"

        elif tipo == "wordlist":
            if re.search(r"(senha|password)", texto, re.IGNORECASE):
                params["tipo"] = "senhas"
            elif re.search(r"(diretório|diretorio|dir|pasta)", texto, re.IGNORECASE):
                params["tipo"] = "diretorios"
            elif re.search(r"(subdomínio|subdomain)", texto, re.IGNORECASE):
                params["tipo"] = "subdominios"
            else:
                params["tipo"] = "completa"

        elif tipo == "analisar_codigo":
            if re.search(r"(melhora|refatora|otimiza)", texto, re.IGNORECASE):
                params["modo"] = "melhorias"
            else:
                params["modo"] = "completo"

        return params

    def resumo(self, intent: Intencao) -> str:
        """Gera descrição legível da intenção detectada."""
        if intent.tipo == "conversa":
            return "💬 Conversa"
        emoji = {
            "pentest_completo": "🔐",
            "recon": "🔍",
            "scan": "📡",
            "wordlist": "📝",
            "analisar_codigo": "🔬",
            "evolucao": "🧬",
            "absorver": "📚",
            "criar_skill": "⚡",
        }.get(intent.tipo, "🤖")

        alvo_str = f" → {intent.alvo}" if intent.alvo else ""
        conf_str = f" ({int(intent.confianca * 100)}%)"
        auto_str = " [AUTO]" if intent.autonomo else " [CONFIRMAR]"
        return f"{emoji} {intent.tipo}{alvo_str}{conf_str}{auto_str}"
