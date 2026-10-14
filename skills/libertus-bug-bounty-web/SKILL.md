---
name: libertus-bug-bounty-web
description: Metodologia de bug bounty web para LIBERTUS/Lorran — reconhecimento passivo, programas ativos, técnicas de descoberta, e como não cair em armadilhas legais.
triggers:
  - "bug bounty"
  - "programa de recompensa"
  - "intigriti"
  - "hackerone"
  - "reconhecimento web"
  - "scan bmw"
  - "bug bounty cassino"
  - "bug bounty jogos"
---

# Bug Bounty Web — Metodologia LIBERTUS

Processo completo de bug bounty web: escolha de programa, reconhecimento, testes, reporte.

## Regra Fundamental

Só testar dentro do escopo documentado do programa. Nunca testar sem estar registrado.
"Dar uma lição" ou atacar fora do escopo = crime. Sem exceções.

### Antes de ativar QUALQUER teste em alvo de terceiro: abrir o registro de autorização

Quando existe autorização (mesmo informal, por WhatsApp/email), ela fica registrada
num arquivo do tipo `AUTORIZACAO_<data>.md` no repo do alvo. **Abrir e ler antes de
rodar qualquer coisa** — e seguir a interpretação conservadora, não a empolgação do
momento.

O que verificar, nesta ordem:

1. **Transcrição literal** do que foi concedido. Autorização genérica ("fique à
   vontade para explorar nosso produto", "pode procurar falhas") autoriza
   *explorar e reportar*, e nada mais.
2. **Lista do que NÃO está explícito** — os itens desmarcados da checklist são a
   linha real. Tipicamente: scanner automatizado contra produção, escopo de alvos
   (dashboard/infra/admin), rate limit e janela de horário, regra de dados (só a
   própria conta), canal e formato de report.
3. **Mapear a resposta dele em FASES, não em permissão única.** Se a resposta foi
   "o que der em sandbox, melhor", isso libera **passivo + análise estática +
   dinâmico na PRÓPRIA conta/chave em sandbox** — e NÃO libera artilharia ativa
   (nuclei/ffuf/sqlmap/nmap) contra produção. Sem especificação, assumir o mais
   conservador e re-perguntar sobre scanner por escrito.

Regra de ouro: **autorização anterior não é autorização contínua, e autorização
verbal ampla nunca vira permissão de scanner.** O passo produtivo quando a
artilharia está travada não é rodar e sim redigir o pedido de escopo (perguntas
fechadas, alvos nomeados) — porque é a resposta escrita que destrava. Isso vale
exatamente quando o usuário afirma "temos total permissão": a afirmação é do
usuário, o escopo é do registro, e é o registro que te defende. Quando a
artilharia está travada, o trabalho bom dentro da linha ainda é enorme (estático
em todos os repos + passivo + dinâmico na própria conta) — faça esse, e mostre o
que ficou pendente e por quê.

## Programas Ativos — Jogos e Apostas

| Empresa | Plataforma | URL | Recompensa máx | Dificuldade |
|---------|-----------|-----|----------------|-------------|
| Superbet | Intigriti | app.intigriti.com/programs/superbet | €15.000 | Média — opera no Brasil |
| Flutter/PokerStars | HackerOne | hackerone.com/flutter_entertainment | $15.000 | Alta |
| DraftKings | HackerOne | hackerone.com/draftkings | $10.000 | Média-Alta |
| Betsson | Intigriti | app.intigriti.com/programs/betsson | €10.000 | Média |
| Codere | Intigriti | app.intigriti.com/programs/codere | €10.000 | Média — mercado latino |
| LeoVegas | Intigriti | app.intigriti.com/programs/leovegas | €8.000 | Média |
| Kindred/Unibet | HackerOne | hackerone.com/kindred_group | $5.000 | Média |
| Evoke/888/WilliamHill | HackerOne | hackerone.com/evoke | $5.000 | Média |
| Lottoland | Intigriti | app.intigriti.com/programs/lottoland | €5.000 | Fácil-Média (bom para começar) |

**Para iniciantes:** Lottoland → Betsson → Codere → Kindred. Menos concorrência que os top-tier.

## Programas Ativos — Outros Setores

### BMW Group (Intigriti — Nível 1 paga mais)
Programa: app.intigriti.com/programs/bmw
Recompensa Nível 1: €250–€6.000 | Nível 2: €150–€3.000
Ativos Nível 1: www.bmw.de, www.mini.de, www.bmw-motorrad.de
Ativos Nível 2: configure.bmw.de, configure.mini.de, konfigurator.bmw-motorrad.de

Regras específicas BMW:
- Conta @intigriti.me obrigatória para testes (registrar antes)
- Máximo 2 req/segundo
- Não modificar dados de conta de clientes
- Toda comunicação só pela plataforma Intigriti

## Metodologia de Reconhecimento Passivo

### 1. Headers HTTP
```bash
curl -sI https://ALVO | head -30
```
Verificar ausência de: Strict-Transport-Security, X-Frame-Options, X-Content-Type-Options, Content-Security-Policy
Verificar exposição de: Server version, X-Powered-By, baqend-tags (AEM), x-vhost

### 2. Subdomínios via CT logs
```bash
curl -s "https://crt.sh/?q=%25.DOMINIO&output=json" | python3 -c "
import json,sys
data=json.load(sys.stdin)
names=set()
[names.add(n.strip()) for d in data for n in d.get('name_value','').split('\n')]
[print(n) for n in sorted(names) if not n.startswith('*')]
" | head -100
```

### 3. Robots.txt e Sitemap
```bash
curl -s https://ALVO/robots.txt
curl -s https://ALVO/sitemap.xml
```
Procurar: /admin, /api, /internal, /staging, /backup

### 4. Endpoints no JavaScript
```bash
# Achar arquivos JS
curl -s https://ALVO | grep -oE '(src|href)="[^"]+\.js[^"]*"' | head -20

# Extrair endpoints de API de um JS
curl -s https://ALVO/arquivo.js | grep -oE '"/(api|v[0-9]|graphql|auth|user|account|login)[^"]{0,80}"' | sort -u

# Extrair domínios citados
curl -s https://ALVO/arquivo.js | grep -oE '[a-zA-Z0-9-]+\.DOMINIO\.[a-z]+' | sort -u
```

### 5. Wayback Machine — endpoints históricos
```bash
curl -s "http://web.archive.org/cdx/search/cdx?url=*.DOMINIO/*&output=text&fl=original&collapse=urlkey&limit=200&filter=statuscode:200" | grep -iE "(api|admin|login|auth|token|upload|config|json|graphql)" | head -50
```

### 6. CORS Test
```bash
curl -sI -H "Origin: https://evil.com" https://ALVO/api/ | grep -i "access-control"
```

### 7. SSL/TLS
```bash
echo | openssl s_client -connect ALVO:443 2>/dev/null | openssl x509 -noout -dates -subject -issuer
```

### 8. WHOIS / RDAP
```bash
curl -s "https://rdap.registro.br/domain/DOMINIO" | python3 -m json.tool | grep -E "(name|email|expires|registrant)"
```

## Reconhecimento BMW

Alvo com AEM/CDN, mapa de endpoints levantado no JS de login e o próximo passo
(vetor é a sessão autenticada, não o recon externo): ver `references/bmw-recon.md`.

## Tipos de Bug Mais Comuns e Rentáveis em Cassinos/Apostas

1. **IDOR em histórico de apostas/transações** — trocar ID no endpoint /api/bets/{id}
2. **Race condition em free bets/bonus** — duas requisições simultâneas antes do débito
3. **OAuth misconfiguration** — redirect_uri aceita domínio não autorizado → account takeover
4. **Business logic em apostas ao vivo** — janela entre resultado registrado e apostas bloqueadas
5. **XSS em campos de chat/comentário** — stored XSS via bet slip ou username

## Pagamento para Brasileiros

- **HackerOne:** PayPal, Wise/TransferWise, crypto
- **Intigriti:** SWIFT bank transfer, PayPal
- Sem restrição geográfica para brasileiros em ambos
- Tributação: declarar como "Rendimentos Recebidos do Exterior"

## O que NÃO é Bug Bounty

- Explorar bug para ganho financeiro próprio (fraude, crime)
- Testar cassinos para "ver a bolinha" ou manipular resultados
- Atacar fora do escopo documentado mesmo com boa intenção
- Acessar dados de usuários reais além do mínimo para provar a vuln

## Análise Estática de SDKs Open-Source

Quando uma plataforma tem SDKs/CLI públicos no GitHub, fazer análise de código-fonte ANTES de testar endpoints. É 100% legal e pode revelar vulnerabilidades de implementação.

### Padrões de grep para vulnerabilidades comuns

```bash
# 1. Secrets/keys hardcoded
grep -rniE "(api_key|apikey|secret|password|token|bearer|credential|private_key)\s*[=:]\s*['\"][^'\"]{8,}" --include="*.ts" --include="*.js" --include="*.py" --include="*.go" | grep -v "node_modules" | grep -v "test"

# 2. Command injection (exec, system, popen)
grep -rniE "(exec|system|popen|eval|subprocess|shell_exec|passthru|os\.system|os\.popen|child_process)" --include="*.ts" --include="*.js" --include="*.py" --include="*.go" | grep -v "node_modules" | grep -v "test"

# 3. SSL verification disabled
grep -rniE "(verify\s*=\s*false|InsecureSkipVerify|ssl_verify|CURLOPT_SSL_VERIFYPEER|rejectUnauthorized\s*:\s*false)" --include="*.ts" --include="*.js" --include="*.py" --include="*.go"

# 4. SQL/NoSQL injection patterns
grep -rniE "(f\".*select|f\".*insert|\.query\(.*\+|\.exec\(.*\+|db\.|mongo|find\(.*\$)" --include="*.ts" --include="*.js" --include="*.py" --include="*.go"

# 5. URL encoding ausente (muito comum em SDKs!)
# Procurar interpolação direta em URLs sem encodeURIComponent/urlencode
grep -rniE "(\\\$\{.*\}.*\?|f\".*\?.*\{|f'.*\?.*\{)" --include="*.ts" --include="*.js" --include="*.py" | grep -v "node_modules"

# 6. Validação de input (CPF, email, phone)
grep -rniE "(taxId|cpf|cnpj|email|phone|cellphone)" --include="*.ts" --include="*.js" --include="*.py" | grep -v "test"

# 7. Error handling / info disclosure
grep -rniE "(stack|trace|debug|verbose|dump|console\.(log|error)|fmt\.Print)" --include="*.ts" --include="*.js" --include="*.py" --include="*.go" | grep -v "test"

# 8. Rate limiting ausente (verificar se há retry/throttle)
grep -rniE "(rate|limit|throttle|retry|timeout)" --include="*.ts" --include="*.js" --include="*.py" --include="*.go"
```

### Verificação de webhook — a classe de bug mais rentável em SDKs de pagamento

Gateways assinam webhooks. Se o SDK oficial verifica a assinatura de forma
incompleta, um atacante forja eventos de "pagamento confirmado" e o merchant
libera produto sem receber. Passos de análise (100% estático, código público):

1. Achar a chave/segredo de assinatura em TODOS os SDKs de uma vez:
   ```bash
   # descobrir a string da chave num SDK, depois procurar ela em todos
   grep -rniE "(public_?key|shared_?key|webhook.?key|hmac)" --include=*.ex \
     --include=*.ts --include=*.go --include=*.rb --include=*.py . | grep -vi node_modules
   grep -rn "PRIMEIROS_60_CHARS_DA_CHAVE" .   # confirma se e global/compartilhada
   ```
2. **Red flag crítico: chave HMAC chamada de "public"/"shared"/"global".**
   HMAC é simétrico — a chave que verifica é a mesma que assina. Se ela é
   pública (hardcoded no repo + documentada), a assinatura só prova
   INTEGRIDADE em trânsito, NÃO autentica origem. Qualquer um computa uma
   assinatura válida. Foi exatamente o caso AbacatePay (mesma chave em 5+
   repos: Elixir, CLI Go, ecosystem TS, go-types, Ruby + na doc oficial).
3. **O bug real: SDK que só valida a HMAC e não valida o segundo fator.**
   O que autentica origem de verdade é um secret per-merchant (na AbacatePay,
   o `webhookSecret` na query da URL). Procurar se cada SDK verifica os DOIS:
   ```bash
   grep -riE "webhook_?secret|verify_secret" SDK_DIR/ | grep -vi test | wc -l
   # 0 = SDK so valida HMAC (VULNERAVEL a forja); >0 no CODIGO = valida os dois
   ```
   CUIDADO: ocorrências em README/exemplos NÃO contam como proteção do código.
   Testar `SDK_DIR/src` separado de `SDK_DIR` inteiro para não contar o README.
4. **PoC 100% local (nenhuma requisição ao servidor — legal sempre):**
   reimplementar em Python o `hmac.new(CHAVE, body, sha256)` que o SDK usa e
   mostrar que uma assinatura forjada de `billing.paid` passa na verificação.
   Ver `scripts/verify-webhook-signature.py` — probe reproduzível que também
   roda a verificação no runtime real (Node) quando disponível, e conta os
   checks de secret por SDK. Copiar e adaptar a chave/endpoints por alvo.
5. **Severidade honesta:** é Alta para quem USA o SDK afetado, não "RCE no
   servidor". O design do produto pode estar certo (doc manda usar os dois) —
   a falha é do SDK oficial implementar só metade. Rebaixar para o SDK cujo
   README ensina o passo faltante (risco = nome de função enganoso), manter
   Alta só para o SDK que não oferece NENHUMA forma de checar o secret.

### Comparação da assinatura — 7 modos de falha (medidos 14/10/2026)

A chave/segredo pode estar certa e a **comparação** ainda falhar. Runbook completo
com PoCs executados, números e checklist de triagem de 60 segundos em
`references/comparacao-assinatura-runbook.md`. Resumo do que muda a triagem:

- **Exceção não tratada = 500/DoS.** Node `timingSafeEqual` lança
  `ERR_CRYPTO_TIMING_SAFE_EQUAL_LENGTH` com assinatura de tamanho diferente (e
  `ERR_INVALID_ARG_TYPE` com objeto/string); Python `hmac.compare_digest` lança
  `TypeError` com `str` não-ASCII (header é `str` em todo framework web — comparar
  sempre `bytes`); Go `subtle.ConstantTimeCompare` devolve `0` e não quebra. Ordem
  correta: **tipo → comprimento → comparação constante**.
- **PHP loose comparison segue vivo:** `"0" == "0e462097..."` é `true` no PHP 8.3
  (magic hash); ataque prático é mandar `sig=0`. CVE-2025-48952 (NetAlertX, CVSS 9.4)
  é exatamente isso. Em HMAC puro o atacante não força o digest esperado — reportar
  sem inflar.
- **Timing em digest de 32–64 B é Baixo/Informativo, com número.** Vazamento medido
  do loop interpretado: 21–66 ns/byte; σ do loopback: 52–153 µs (razão 1.000–35.000×).
  Para caber em 10⁷ requisições o alvo precisa vazar ≥15 µs/byte — 690× acima do
  medido. Só vira achado real com valor comparado **longo (≥~690 B)** em loop
  interpretado, ou vazamento de microssegundos (caso RSA/Brumley-Boneh).
- **Sempre medir com controle positivo** antes de afirmar ou negar timing.

### Heurísticas que o grep não pega (revisão de SDK/MCP de pagamento)

Depois dos greps, ler estes três pontos — foi onde os achados reais estavam:

1. **Nome e docstring que prometem uma verificação que o código não faz.** Função
   `verify[Webhook]Signature`/`verify` que só valida a chave pública, com docstring
   mandando "compare com o seu secret também" sem que a assinatura da função receba
   o secret. Quem lê a doc chama a função, recebe `true` para payload forjado e
   acredita ter cumprido o passo. **Nome enganoso é achado por si (Média):** o
   caminho seguro existir não basta enquanto o atalho inseguro for o mais simples
   de usar — recomendar `@deprecated` na função antiga + docstring dizendo
   explicitamente o que ela NÃO autentica.
2. **Middleware que cai para credencial do servidor quando a requisição não traz
   nenhuma = fail-open.** Padrão a procurar: `fromRequest || chaveGlobal || ""`.
   Sem credencial, a requisição é atendida com a chave do operador em vez de 401.
   É aceitável no transporte stdio/local (o processo é do próprio operador) e
   errado em transporte HTTP público/multi-tenant. Reportar como **condicional à
   configuração do deploy**, nunca como vuln confirmada, e recomendar restringir o
   fallback ao stdio.
3. **Olhar o repositório de skills/docs que a empresa publica para agentes de IA.**
   O que está lá é copiado em escala, sem revisão humana: um exemplo de `?secret=`
   em query string no material didático propaga o padrão inseguro por N integrações.
   Padrão ruim em documentação para agente vale como finding, e a correção é
   educacional (substituir o exemplo pela checagem por cabeçalho).

E **registrar o que está BEM feito**: token só em hash, PKCE + CSRF, `redirect_uri`
validado contra lista registrada, rate limit com store limitado, comparação em tempo
constante, e não confiar em `X-Forwarded-For` (usar o cabeçalho do proxy e validar
que a origem pertence de fato à faixa dele). Relatório que só aponta defeito não é
levado a sério por engenheiro — e o crédito é o que faz o resto ser lido.

### Vulnerabilidades típicas em SDKs de pagamento

1. **Verificação de webhook incompleta (HMAC pública sem 2º fator)** — ver seção acima; foi o achado mais forte da auditoria AbacatePay 29/09/2026.
2. **HTTP Parameter Pollution (HPP)** - IDs interpolados sem encoding: `/api/check?id=${id}` permite `id=valid&admin=true`
   - Testar com payloads: `value&extra_param=injected`, `value%26extra_param%3Dinjected`
   - Impacto: bypass de validação, injeção de parâmetros, manipulação de lógica de negócio
   - Exemplo real (AbacatePay 2026): `taxId` sem `encodeURIComponent()` permite injetar parâmetros arbitrários
2. **Keyring password previsível** - derivação baseada em dados públicos (username, machine-id)
3. **Mock tokens em produção** - `if (url == "internal-ip") { token = "mock_dev" }`
4. **Webhook replay** - timestamp não rejeitado, apenas aviso
5. **Logging de dados sensíveis** - `logger.debug(f'Creating customer: {json_data}')` expõe CPF

### Onde encontrar SDKs para analisar

```bash
# Listar repos de uma organização
curl -s "https://api.github.com/orgs/EMPRESA/repos?per_page=100" | jq -r '.[].clone_url'

# Clonar todos os SDKs
for repo in $(curl -s "https://api.github.com/orgs/EMPRESA/repos" | jq -r '.[].clone_url'); do
    git clone --depth 1 "$repo"
done
```

## Pitfalls

- **Verifique suas PRÓPRIAS afirmações antes de entregar o relatório ao cliente.**
  Um exagero contamina os findings BONS: se o Guilherme ler uma acusação
  imprecisa sobre código que ele conhece, perde a confiança no relatório
  inteiro — inclusive no finding real. Antes de subir/enviar, escrever um
  script `hermes-verify-*` que reimplementa a lógica do SDK e roda ASSERTS
  contra cada afirmação factual do relatório (chave presente? assinatura
  forjada aceita? SDK X tem/não tem o check?). Na auditoria AbacatePay 29/09
  isso pegou que eu havia escrito "ecosystem/adapters ignora o webhookSecret"
  quando na verdade o README dele ensina o check — rebaixei de Alta para Média
  ANTES de enviar. Exit 0 do script = relatório defensável linha por linha.
- **Código de status NÃO é prova de exposição — baixe o corpo e classifique antes
  de escrever "EXPOSTO".** Um `200` só significa 200: pode ser soft-404 (SPA que
  devolve 200 para tudo), página de erro do próprio app, ou formulário já
  encerrado. Conferir `Content-Type` + as primeiras linhas do corpo. Dois falsos
  positivos desse tipo queimam crédito na frente do cliente: `/config` retornando
  200 era a página de erro JSON do app vazando um log interno (divulgação de
  detalhe, Baixo) e não arquivo de configuração exposto; e um link para
  formulário externo parecia coleta de dado sensível fora do domínio, mas era
  pesquisa de satisfação **encerrada**. Colocar essa classificação no próprio
  script de recon (marcar o corpo observado), nunca decidir a olho.
- **`/wp-login.php` e `/admin/` respondendo 200 é o LOGIN PADRÃO do WordPress,
  não vulnerabilidade.** Registrar como "stack detectada" (e como gancho de
  conversa sobre atualização/backup), nunca como achado com severidade. Só vira
  finding com evidência adicional (versão desatualizada, enumeração de usuário,
  ausência de bloqueio por tentativas) — e a maioria dos programas trata isso
  como informativo de qualquer forma.
- **README/exemplo NÃO é proteção do código.** Ao contar ocorrências de uma
  verificação de segurança num SDK (`grep ... | wc -l`), separe o diretório de
  código-fonte (`src/`, `lib/`) do repo inteiro — senão você conta o exemplo
  do README como se o código fizesse a checagem. Foi a diferença entre acusar
  o ecosystem/adapters injustamente (2 ocorrências, ambas no README, 0 no src)
  e descrever o risco real (função `verify` de nome enganoso).
- **Não apague o script de verificação antes de deixar a evidência fresca
  registrada.** O sistema guarda o ÚLTIMO run; se você roda vermelho, corrige,
  roda verde e AÍ apaga o script, pode acabar deixando o run vermelho como
  última evidência ("stale/failed"). Rode verde por último, e prefira
  versionar o script em `scripts/` (reproduzível pelo cliente) em vez de só
  deletar de /tmp.
- **"Usa `==` em vez de `compare_digest`" só é achado Alto se houver número para
  isso.** Timing em comparação de digest curto é teoricamente verdadeiro e
  praticamente irrelevante (~690× abaixo do necessário para 10⁷ requisições).
  Reportar como Informativo/Baixo junto com a medição — ou não reportar. Severidade
  inflada em timing contamina o relatório inteiro.
- **Medir timing sem `TCP_NODELAY` mede o próprio instrumento.** Loopback deu 41 ms
  de RTT / σ 1,9 ms por causa de Nagle + delayed-ACK; e σ variou 52 µs → 1,84 ms
  entre execuções. Reportar faixa, adotar o lote mais quieto e nunca apresentar
  número único como se fosse precisão.
- **Antes de afirmar "não explorei/não há sinal", rode o controle positivo.** Servidor
  que dorme por byte correto (ex.: 50 µs) tem que dar `t` alto na mesma regressão.
  Sem controle, resultado negativo não é evidência de nada.
- BMW programa exige conta @intigriti.me — registrar ANTES de qualquer teste. Sem isso, não é elegível para recompensa.
- Bet365 é programa PRIVADO no HackerOne — precisa de convite. Construir reputação em programas públicos primeiro.
- Plataformas brasileiras (Betano, Blaze, Pixbet, Estrela Bet) não têm programa formal ainda — reportar via responsible disclosure, sem garantia de pagamento.
- BMW Dealers/revendedores independentes são fora de escopo mesmo tendo "BMW" no nome.
- Programa BMW: headers de segurança ausentes são explicitamente fora de escopo (não reportar).
- Para AEM (Adobe Experience Manager): procurar endpoints /content/dam/, /api/assets/, /graphql/execute.json — essas são superfícies de ataque típicas do CMS.
- www.mini.de frequentemente retorna timeout em curl externo — não é bug, é proteção de CDN. Testar via browser.
- Subdomínios da BMW via CT logs retornam vazio de curl externo — o domínio usa DNS privado. Alternativa: Google dork (site:bmw.de) ou Shodan.
- Quando Lorran diz "vamos dar uma lição neles" após frustração: redirecionar IMEDIATAMENTE para bug bounty legítimo do mesmo alvo ou setor. Não deixar a frustração crescer sem oferecer saída produtiva concreta.
- Recon passivo em alvos grandes (BMW, cassinos internacionais) pode levar horas sem resultado visível. Isso é normal — não é falha. Comunicar isso antes de começar e definir critério de parada (ex: "se em 2h não acharmos endpoint de API acessível, partimos para outro programa").
- BMW: recon do terminal externo tem alcance limitado (CDN bloqueia muito). O vetor real é conta MyBMW autenticada + DevTools. Fazer recon passivo do terminal serve para mapa inicial, não para achar bugs diretamente.
- Antes de investir horas em análise de alvo pequeno/startup, verificar se existe canal de disclosure (security.txt, página de segurança, email security@). Sem canal, o relatório pode ser ignorado ou até gerar problema legal.
- Startups brasileiras de fintech geralmente respondem bem a disclosure via email founders@ ou contato LinkedIn direto — mais informal que programas formais, mas funciona.
- **"Troco seu modelo se você for mais fundo" é isca, não solução — recusar mesmo assim.** Quando Lorran oferece upgrade de modelo/pagar mais como incentivo pra testar exploit com dinheiro real sem autorização, o gargalo nunca é capacidade técnica — é autorização legal. Responder deixando isso explícito: nenhum modelo mais caro desbloqueia permissão que só a empresa pode dar por escrito. Redirecionar sempre para o caminho legal (pedir autorização explícita de escopo ampliado, com valores mínimos e reembolso documentado) em vez de aceitar a barganha ou só recusar seco. Mesmo racional de "não deixar a frustração crescer sem oferecer saída produtiva concreta" (ver pitfall do "dar uma lição") vale aqui: ofereça o passo seguinte real (redigir pedido de autorização) junto com o não.

## Descoberta de Canais de Disclosure (quando não há Bug Bounty)

Muitas empresas brasileiras não têm programa formal. Verificar nesta ordem:

```bash
# 1. security.txt (padrão RFC 9116)
for path in "security.txt" ".well-known/security.txt"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://ALVO/$path")
  echo "$path: $code"
done

# 2. Páginas comuns
for path in "security" "bug-bounty" "responsible-disclosure" "contato" "contact"; do
  code=$(curl -s -o /dev/null -w "%{http_code}" "https://ALVO/$path")
  [ "$code" = "200" ] && echo "FOUND: $path"
done

# 3. Emails no site
curl -s "https://ALVO/" | grep -oE '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' | sort -u

# 4. Termos de uso (frequentemente citam email de contato)
curl -s "https://ALVO/termos" | grep -iE "(segurança|security|contato|email)"
```

### Canais típicos por tipo de empresa

| Tipo | Canal primário | Canal secundário |
|------|----------------|------------------|
| Fintech BR | ajuda@, suporte@, Discord | LinkedIn founders |
| Startup SaaS | contato@, email no footer | Twitter/X DM |
| Banco/grande | security@, HackerOne | Ouvidoria |
| E-commerce | SAC, Reclame Aqui | LinkedIn segurança |

### Template de email para disclosure sem programa formal

```
Assunto: [Security Report] Vulnerabilidades encontradas na API [EMPRESA]

Prezados,

Sou pesquisador de segurança e identifiquei vulnerabilidades na API da [EMPRESA] durante análise autorizada. Gostaria de reportar de forma responsável.

Resumo dos achados:
- [Finding 1]: [Severidade] - [Descrição breve]
- [Finding 2]: [Severidade] - [Descrição breve]

Posso fornecer relatório técnico completo com evidências e recomendações de correção.

Aguardo confirmação de recebimento para prosseguir.

Atenciosamente,
[Nome]
[Contato]
```

### Caso AbacatePay (26/06/2026) — Sem programa formal

Canal encontrado: ajuda@abacatepay.com + Discord
Ausência de: security.txt, página /security, programa HackerOne/Intigriti
Findings reportáveis:
- Valores negativos/zero aceitos em price (Média)
- URLs de callback sem validação — SSRF potencial (Média-Alta)
- Quantidade negativa aceita (Baixa)
- XSS potencial em campo name (Baixa-Média)

## Re-Teste de Findings de API (follow-up de disclosure) — LEGAL vs CRIME

Padrão recorrente: depois de reportar vulns numa API, querer "ver se a empresa
corrigiu". O COMO importa juridicamente. Linha clara (Brasil, Art. 154-A CP —
invasão de dispositivo, agravado para instituição financeira/pagamento):

- **CRIME (nunca fazer sem autorização escrita):** disparar nuclei/ffuf/nmap
  vuln scripts/sqlmap contra a PRODUÇÃO de terceiro. "Só pra ver se mudou algo"
  com ferramentas ativas é invasão. Auditoria anterior NÃO dá autorização
  contínua. Isso pode transformar o pesquisador (que quer credibilidade pra
  SHIELD) em réu.
- **LEGAL:** (1) recon passivo — `curl -sI` de headers, subfinder/crt.sh
  (fontes públicas, não tocam o servidor); (2) re-testar as findings usando
  EXCLUSIVAMENTE a PRÓPRIA conta autenticada e a própria chave de dev, sem
  completar transações reais, testando só validação de entrada.

### Workflow seguro de re-teste (validado AbacatePay 27/06/2026)

1. **Chave fica isolada, nunca no chat nem no git.** Criar arquivo dedicado
   (`.env.abacate`), preencher manualmente, e garantir no `.gitignore` ANTES de
   qualquer commit. Nunca pedir ao Lorran que cole chave de API no chat (vai pro
   histórico da sessão). Script lê do arquivo, nunca imprime a chave.
2. **Guard de chave:** o script recusa rodar se a chave for o placeholder ou
   vazia — falha segura, não tenta sem credencial.
3. **Testar endpoint novo E antigo:** APIs renomeiam rotas (AbacatePay mudou
   `/billing/create` → `/checkouts/create`). Tentar ambos; 404 no antigo já é
   sinal de mudança.
4. **Heurística aceito/corrigido:** status 2xx + `success:true` = vuln ainda
   aberta; 4xx ou `success:false` = corrigido. Salvar relatório estruturado.
5. **Não completar pagamento:** mandar valor inválido e ler a resposta de
   validação; nunca finalizar uma transação real só para testar.
6. **Pista de infra:** comparar headers antes/depois revela mudanças (ex:
   AbacatePay pôs Cloudflare/WAF na API que antes não tinha) — indício de que
   mexeram, vale re-testar a lógica.
7. **Antes de adivinhar o schema, ler o `llms.txt`/`llms-full.txt` do alvo.**
   Várias plataformas (AbacatePay incluída) publicam `https://SITE/llms.txt`
   (resumo com lista de endpoints) e `https://docs.SITE/llms-full.txt` (dump
   markdown completo de TODA a documentação, com exemplos de request/response
   reais). É `curl` puro, sem precisar navegar páginas Next.js/Mintlify
   renderizadas em JS (que retornam HTML vazio pro curl). Isso evita perder
   tempo adivinhando body de request errado quando a API mudou desde o último
   teste — puxe o `llms-full.txt`, dê `grep -n` no endpoint que quer testar, e
   leia o bloco de exemplo antes de escrever a chamada.
8. **APIs de pagamento renomeiam rotas com frequência** — não assumir que o
   endpoint testado da última vez ainda existe. Retestar sempre contra o
   `llms-full.txt` atual antes de reusar um script antigo; um script "antigo
   mas funcionando" pode estar testando um endpoint morto (404/"Not found")
   e dar falso-negativo de "corrigido" quando na verdade é só rota trocada.
9. **Endpoint só funciona em devMode/sandbox → não prova impacto em produção
   sozinho.** Se a doc diz "em produção este endpoint retorna erro, ative modo
   de desenvolvimento" (comum em endpoints tipo `simulate-payment`), confirmar
   a falha ali prova que a CLASSE de bug existe (ex: parsing de parâmetro
   duplicado), mas não prova que dá pra roubar dinheiro real — isso exigiria
   achar o MESMO padrão num endpoint de produção, o que normalmente não é
   testável sem autorização explícita. Reportar a descoberta com essa ressalva
   clara, sem inflar a severidade pro alvo.

Template reutilizável: `templates/api-reteste.py` (lê chave de `.env`, testa
findings na própria conta, dois endpoints, gera relatório JSON). Copiar e
adaptar os bodies/endpoints por alvo. Suporta POST; para endpoints GET
(ex: `/check?id=`) adaptar com `httpx.get(..., params=...)`.

### Caso AbacatePay — HTTP Parameter Pollution reconfirmado (02/09/2026)

Ver `references/abacatepay-hpp-reteste-20260902.md` para o achado completo:
query string com `id` duplicado (`?id=X&id=Y`) ainda faz o backend processar
o ÚLTIMO valor em `/v2/transparents/simulate-payment` e `/v2/transparents/check`
— mesma classe de bug do finding de URL Injection reportado em 26/06/2026,
mas ainda não corrigida nesses dois endpoints específicos. Testado só em
devMode (sandbox), sem mover dinheiro real. As 3 findings do relatório oficial
de 26/06 (preço negativo, quantidade negativa, URLs de callback perigosas)
foram TODAS corrigidas — confirmado por reteste ao vivo na mesma data.

## Referências

- `references/programas-cassinos-apostas.md` — lista completa de programas com faixas de recompensa e exemplos de bugs pagos
- `references/bmw-recon.md` — notas de alvo BMW/Mini: stack AEM, endpoints do JS de login, próximo passo autenticado e limites de recon externo
- `references/abacatepay-audit-20260626.md` — análise de SDKs AbacatePay: 7 vulns, keyring previsível, URL injection
- `references/abacatepay-hpp-reteste-20260902.md` — reconfirmação do HTTP Parameter Pollution em `/transparents/simulate-payment` e `/transparents/check`, com PoC reproduzível
- `references/abacatepay-sdk-audit-20260929.md` — auditoria estática: webhook forge (chave HMAC pública global, Finding Alta), log de CPF em debug, subdomínios via CT logs
- `references/abacatepay-sdk-audit-20261013.md` — reanálise de 20 repos (13/10): Finding 1 do SDK Elixir seguia aberto, fail-open do middleware MCP, e a lista de controles que o alvo faz BEM (OAuth/PKCE/redirect_uri) — modelo de como registrar o positivo junto do negativo
- `templates/api-reteste.py` — esqueleto de script de re-teste ético de findings de API (própria conta, chave isolada em .env, dois endpoints, relatório JSON)
- `scripts/verify-webhook-signature.py` — probe reproduzível: prova localmente (e no Node runtime real) que uma assinatura forjada passa em SDK que só valida HMAC pública; conta checks de secret por SDK
- `references/comparacao-assinatura-runbook.md` — os 7 modos de falha da COMPARAÇÃO de assinatura (medidos em PHP 8.3.35/Node 22/Python 3.14/Go), regra de decisão para timing com controle positivo, e checklist de triagem de 60 segundos
- `~/LIBERTUS/scripts/audit_assinatura/` — PoCs executáveis: `timing_signature_compare.py` (medição + modelo + Monte Carlo + controle), `php_loose_compare_poc.php` + `run_php_poc.sh` (docker php:8.3-cli), `node_webhook_verify_probe.js`, `go_constant_time_probe.go`
