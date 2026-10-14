# BMW / Mini — programa Intigriti (notas de alvo)

Depth de alvo específico. As regras sempre-válidas do programa estão no SKILL.md.

## Stack confirmada

- Adobe Experience Manager (AEM/CRX3) — evidência: cabeçalho `baqend-tags: crx3composite`
  em todas as respostas
- CDN: Akamai (bmw.de / mini.de) e CloudFront AWS (configure.bmw.de)

A presença de AEM muda o mapa de superfície: procurar `/content/dam/`,
`/api/assets/`, `/graphql/execute.json` — são as superfícies típicas desse CMS.

## Endpoints levantados no JS de login (`/static/login/flyout.js`)

```
/api/b2b/refresh
/api/b2b/validate
/api/gcdm/refresh          # BMW Global Customer Data Management
/api/flyout/data
/api/business-partner/preferred-sales-agent
/account
```

Todos retornam 404 sem autenticação — ficam ativos com conta MyBMW logada. Isso é
comportamento esperado, não achado.

## Próximo passo real (o vetor é a sessão autenticada)

1. Criar conta em bmw.de com email `@intigriti.me` (obrigatório para elegibilidade).
2. Logar no MyBMW e capturar requisições reais da API autenticada via DevTools
   (F12 → Network).
3. Foco: IDOR em IDs de veículo, pedido, dados de perfil.

## Limites de recon observados

- `www.mini.de` costuma dar timeout em `curl` externo — é proteção de CDN, não bug.
- Subdomínios via CT logs voltam vazios de `curl` externo (o domínio usa DNS
  privado). Alternativa: Google dork (`site:bmw.de`) ou Shodan.
- Recon de terminal externo tem alcance limitado (CDN bloqueia muito). Serve para
  mapa inicial, não para achar bug direto. Definir critério de parada antes de
  começar (ex: sem endpoint acessível em 2h, trocar de programa).
