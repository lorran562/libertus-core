# Programas de Bug Bounty — Cassinos, Apostas e BMW

Pesquisa realizada em 27/05/2026. Programas ativos e verificados.

## Cassinos e Apostas — Ordenados por Recompensa Máxima

| Empresa | Plataforma | URL | Max USD | Para iniciante |
|---------|-----------|-----|---------|---------------|
| Superbet | Intigriti | app.intigriti.com/programs/superbet | ~$16.500 | Não |
| Flutter/PokerStars | HackerOne | hackerone.com/flutter_entertainment | $15.000 | Não |
| DraftKings | HackerOne | hackerone.com/draftkings | $10.000 | Talvez |
| Betsson | Intigriti | app.intigriti.com/programs/betsson | ~$11.000 | SIM |
| Codere | Intigriti | app.intigriti.com/programs/codere | ~$11.000 | SIM (América Latina) |
| LeoVegas | Intigriti | app.intigriti.com/programs/leovegas | ~$8.800 | SIM |
| Kindred/Unibet | HackerOne | hackerone.com/kindred_group | $5.000 | SIM |
| Evoke/888/WilliamHill | HackerOne | hackerone.com/evoke | $5.000 | SIM |
| Lottoland | Intigriti | app.intigriti.com/programs/lottoland | ~$5.500 | SIM (melhor para começar) |

## BMW Group — Intigriti

Programa: app.intigriti.com/programs/bmw (público)
Requisito: conta @intigriti.me obrigatória
Rate limit: máx 2 req/segundo

| Ativo | Nível | Max |
|-------|-------|-----|
| www.bmw.de | 1 | €6.000 |
| www.mini.de | 1 | €6.000 |
| www.bmw-motorrad.de | 1 | €6.000 |
| configure.bmw.de | 2 | €3.000 |
| configure.mini.de | 2 | €3.000 |

Achados técnicos (27/05/2026):
- CMS: Adobe Experience Manager (AEM/CRX3) — header baqend-tags revela
- CDN: Akamai em bmw.de/mini.de, CloudFront AWS em configure.bmw.de
- APIs no JS (/static/login/flyout.js): /api/b2b/refresh, /api/b2b/validate, /api/gcdm/refresh, /api/flyout/data, /api/business-partner/preferred-sales-agent
- Todas retornam 404 sem autenticação — precisam conta MyBMW logada
- Fora de escopo: headers de segurança ausentes, banner grabbing, subdomínios de dealers

Estratégia recomendada:
1. Criar conta bmw.de com email @intigriti.me
2. Logar no MyBMW portal
3. DevTools F12 → Network → capturar requisições autenticadas
4. Procurar IDOR em IDs de veículos, perfil, pedidos

## Exemplos Reais de Bugs Pagos (cassinos)

- OAuth2 misconfiguration PokerStars → account takeover: $8.000
- SQL injection API Betsson: €8.000
- Business logic free bets (race condition): $5.000
- Race condition apostas ao vivo Unibet: $3.000
- IDOR histórico contas 888 Holdings: $1.200
- Stored XSS DraftKings: $500

## Plataformas Brasileiras — Status

- Betano: responsible disclosure apenas, sem programa formal
- Blaze.com: sem programa
- Pixbet: sem programa
- Estrela Bet: sem programa
- Sportingbet: coberta pelo programa Evoke (verificar se sportingbet.com.br está explicitamente em escopo)

## Pagamento para Brasileiros

- HackerOne: PayPal, Wise, crypto
- Intigriti: SWIFT, PayPal
- Sem restrição geográfica
- Tributação BR: declarar como "Rendimentos Recebidos do Exterior"
