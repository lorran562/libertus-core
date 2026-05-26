# GHOST — Global Hostile OSINT Surface Tracker

> "Não basta encontrar subdomínios. Você precisa entender o que eles significam."

---

## O Problema Real

O mercado de segurança ofensiva tem ferramentas para cada etapa — mas nenhuma que conecte todas as etapas de forma autônoma, com contexto e score de risco.

| Ferramenta | O que faz | O que NÃO faz |
|------------|-----------|---------------|
| Shodan/Censys | Escaneia IPs e portas | Não correlaciona com subdomínios, não analisa abandono |
| Subfinder/Amass | Encontra subdomínios | Não analisa risco, não detecta takeover, não faz fingerprint |
| Nuclei | Testa vulnerabilidades | Precisa de input manual, não faz discovery |
| Wayback Machine | Histórico de URLs | Não correlaciona com superfície atual |
| SecurityTrails | Histórico de DNS | Caro, fechado, não analisa risco |

**A lacuna:** nenhuma ferramenta une CT logs + DNS + Wayback + fingerprint + CVE + score em um pipeline zero-clique.

---

## O Que é o GHOST

GHOST é um motor de reconhecimento de superfície de ataque web **totalmente autônomo**.

Dado apenas um domínio raiz (`empresa.com.br`), o GHOST:

1. **Mapeia a superfície completa** sem tocar no alvo diretamente
   - Certificate Transparency via crt.sh (subdomínios reais emitidos em certs SSL)
   - DNS brute-force leve com wordlist curada
   - Wayback Machine para URLs históricas e endpoints mortos

2. **Faz fingerprinting inteligente** de cada host vivo
   - Stack tecnológico (PHP, Laravel, WordPress, Django, Node.js...)
   - Headers que vazam versões
   - Cookies de sessão que revelam frameworks
   - Correlação automática com CVEs conhecidos

3. **Detecta o que as outras ferramentas ignoram** — ativos esquecidos
   - Subdomain takeover (CNAME apontando para serviços mortos)
   - Buckets S3/GCS/Azure públicos
   - APIs sem autenticação (/swagger, /graphql, /api/v1)
   - Painéis admin acessíveis (/admin, /wp-admin, /phpmyadmin)
   - Arquivos críticos expostos (.env, .git/HEAD, config.json, id_rsa)

4. **Calcula um score de exposição 0-100** ponderado por categoria
   - Infraestrutura
   - Credenciais/Segredos
   - Ativos abandonados
   - Versões vulneráveis
   - Disclosure de informações

5. **Gera relatórios profissionais** em JSON (para integração) e Markdown (para cliente)

---

## Por Que É Revolucionário

### 1. Pipeline End-to-End Zero-Clique
O pentester executa um comando. O GHOST faz o trabalho de 4 ferramentas diferentes, correlaciona os dados e entrega um relatório profissional. Nenhuma ferramenta faz isso hoje.

### 2. Inteligência sobre Ativos Mortos
O insight mais valioso em segurança ofensiva não está nos ativos que estão vivos — está nos que ESTAVAM vivos. Um subdomínio `dev.empresa.com` com CNAME para `empresa.github.io` que não existe mais pode ser tomado por qualquer um em minutos. O GHOST detecta isso automaticamente.

### 3. Contexto de Risco, Não Apenas Dados
Outras ferramentas despejam listas de subdomínios. O GHOST responde: "Este subdomínio está vivo, roda PHP 7.2 com CVE-2019-11043, tem /phpmyadmin/ acessível e expõe o header X-Powered-By. Score: 78/100 [HIGH]."

### 4. Sem Dependências Pesadas
Python puro + requests. Sem Docker obrigatório, sem banco de dados, sem instalação complexa. Roda em qualquer máquina com Python 3.

### 5. Passivo por Default
Todo o reconhecimento da Fase 1 é 100% passivo — consultamos APIs públicas (crt.sh, Wayback Machine) sem tocar no alvo. Isso é eticamente defensável e legalmente mais seguro.

---

## Casos de Uso

### Red Team / Penteste
- Reconhecimento inicial de um cliente em minutos
- Identificar superfície de ataque antes de qualquer interação direta
- Encontrar os "frutos baixos" (subdomínios esquecidos, painéis admin, secrets expostos)

### Bug Bounty
- Mapear scope completo de um programa rapidamente
- Priorizar alvos pelo score de exposição
- Encontrar subdomínios que outros caçadores ignoram

### Security Assessment
- Deliverable profissional com relatório Markdown pronto para cliente
- Score de risco objetivo para comunicar impacto para C-Level
- Baseline de segurança para comparação futura

### Blue Team / Defesa
- Auditoria proativa da própria superfície de ataque
- Detectar subdomínios esquecidos antes que um atacante os encontre
- Monitoramento contínuo (cron job semanal)

---

## Como Monetizar Via SHIELD

### GHOST como Produto Standalone
- **GHOST Community:** Open source, gratuito, construir reputação/comunidade
- **GHOST Pro:** $49/mês — rate limits maiores, mais wordlists, mais CVEs, exportação PDF
- **GHOST Enterprise:** $299/mês — API REST, webhooks, integração com Slack/Jira, histórico de scans

### GHOST Como Motor do SHIELD

O SHIELD é a plataforma de segurança gerenciada da LIBERTUS. O GHOST seria o **motor de reconhecimento contínuo** do SHIELD:

```
SHIELD PLATFORM
├── GHOST Engine (reconhecimento contínuo)
│   ├── Scan semanal automático de todos os clientes
│   ├── Alertas em tempo real: novo subdomínio detectado
│   ├── Diff de superfície: "3 novos hosts apareceram esta semana"
│   └── Alerta de takeover: "CRÍTICO: subdomain takeover detectado"
│
├── SENTINEL (monitoramento de ameaças)
├── SHADOW (análise de malware)
└── Dashboard unificado para gestores
```

### Modelo de Receita SHIELD com GHOST

| Tier | Público | Preço | Inclui |
|------|---------|-------|--------|
| Starter | PMEs | R$ 997/mês | 1 domínio, scan semanal, relatório mensal |
| Growth | Médias empresas | R$ 2.997/mês | 5 domínios, scan diário, alertas, relatório executivo |
| Enterprise | Grandes corporações | R$ 8.997/mês | Domínios ilimitados, API, integração SIEM, SLA |

### LTV Estimado
- 50 clientes Starter = R$ 49.850/mês
- 20 clientes Growth = R$ 59.940/mês
- 5 clientes Enterprise = R$ 44.985/mês
- **Total: ~R$ 154.775/mês (~$30k USD)**

---

## Roadmap

### v1.0 (atual)
- CT logs + DNS brute-force + Wayback
- Fingerprinting + CVE correlation
- Abandoned asset detection
- Exposure score + report JSON/MD

### v1.5
- GitHub leaks (buscar chaves de API em repos públicos relacionados ao domínio)
- Shodan integration (enriquecer com dados de portas abertas)
- Slack/email notification
- Rate limiting inteligente

### v2.0
- Monitoramento contínuo (daemon mode)
- Diff engine: "novo subdomínio detectado desde último scan"
- API REST para integração com SHIELD
- Plugin para Burp Suite

### v3.0
- ML-based risk scoring (treinar com dados históricos de breaches)
- Integração com HaveIBeenPwned para email de domínio
- Correlation com threat intelligence feeds

---

## Filosofia

> O GHOST não ataca. Ele vê o que um atacante veria antes de você.

Segurança não é sobre ter todas as ferramentas. É sobre ter a perspectiva certa.
O GHOST dá ao defensor os olhos do atacante — automaticamente, de forma contínua, sem falsos positivos excessivos.

---

*GHOST foi concebido e construído por LIBERTUS como arma central do arsenal SHIELD.*
