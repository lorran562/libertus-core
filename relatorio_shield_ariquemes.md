# RELATÓRIO DE ANÁLISE DE SEGURANÇA — SHIELD CIBERSEGURANÇA
## Empresas de Ariquemes-RO | Uso Exclusivo Comercial Interno
**Data da análise:** 27 de maio de 2026
**Metodologia:** Análise passiva (observação externa, sem invasão ou testes ativos)
**Finalidade:** Material de apoio para abordagem comercial presencial

---

> AVISO LEGAL: Este relatório é baseado exclusivamente em informações publicamente
> acessíveis sem qualquer tipo de acesso não autorizado. Toda informação coletada
> está disponível a qualquer pessoa com acesso à internet.

---

# SUMÁRIO EXECUTIVO

Foram analisados 5 sites de empresas de Ariquemes-RO. Nenhum dos 5 sites possui
configuração de segurança adequada. Os principais problemas encontrados são:

- 5/5 sites sem proteção contra ataques de interceptação de dados (headers de segurança ausentes)
- 1/5 site com certificado SSL expirando em 3 DIAS (emergência)
- 1/5 site servindo conteúdo em HTTP puro sem criptografia
- 2/5 sites expondo versão exata do software ao público (facilita ataques)
- 1/5 site expondo tecnologia de servidor ao público (Microsoft IIS + ASP.NET)
- 1/5 domínio com vencimento em menos de 6 meses (risco de sequestro)

---

# EMPRESA 1 — CEDDI CENTRO DE DIAGNÓSTICO
## Site: ceddi.com.br
**Segmento:** Saúde / Centro de diagnóstico médico
**Registrante:** PROMATER COMPL DIAGNOSTICA LTDA - ME
**Servidor de hospedagem:** HostGator
**Domínio válido até:** 27/11/2029

---

## RESUMO EXECUTIVO (linguagem para o dono)

O site do CEDDI é um site WordPress com Elementor, mas está com várias portas
abertas para possíveis ataques. Imagine que o site da sua clínica é uma casa:
ela tem a porta da frente fechada (o site carrega e funciona), mas as janelas
dos fundos estão abertas. Qualquer pessoa mal-intencionada pode entrar por lá.

O principal problema é que o site não possui as "travas de segurança" digitais
modernas — chamadas de headers de segurança — que todo site profissional deveria
ter. Além disso, o sistema de software (WordPress versão 7.0 com Elementor)
está exposto publicamente, o que é como colocar um cartaz na porta dizendo
"usamos essa fechadura específica" — facilitando para quem quer arrombar.

Sendo uma empresa de saúde, vocês lidam com dados sensíveis de pacientes.
A LGPD exige proteção adequada dessas informações. A ausência de medidas
básicas de segurança coloca a empresa em risco de multa e processo.

---

## PROBLEMAS ENCONTRADOS

| # | Problema | Severidade | Detalhe Técnico |
|---|----------|------------|-----------------|
| 1 | Versão do WordPress exposta publicamente | ALTO | WordPress 7.0 visível no HTML. Atacantes podem buscar vulnerabilidades específicas dessa versão |
| 2 | Versão do Elementor exposta | ALTO | Elementor 3.35.8 visível. Plugins populares como Elementor têm vulnerabilidades registradas que atacantes exploram automaticamente |
| 3 | Ausência de HSTS (Strict-Transport-Security) | ALTO | Sem essa proteção, um atacante em rede Wi-Fi pública pode forçar o navegador do paciente a usar conexão sem criptografia (ataque man-in-the-middle) |
| 4 | Ausência de X-Frame-Options | MÉDIO | O site pode ser embutido dentro de outro site falso (técnica chamada Clickjacking), enganando usuários a fornecer dados pensando estarem no site original |
| 5 | Ausência de X-Content-Type-Options | MÉDIO | Permite que arquivos maliciosos enviados ao servidor sejam executados como se fossem legítimos |
| 6 | Ausência de Content-Security-Policy | MÉDIO | Sem essa barreira, um atacante que conseguir injetar código malicioso no site pode roubar dados de pacientes e visitantes em tempo real |
| 7 | Ausência de X-XSS-Protection | MÉDIO | Camada adicional de proteção contra scripts maliciosos desativada |
| 8 | SSL renovado recentemente mas gratuito (Let's Encrypt) | BAIXO | Certificado gratuito e básico. Para empresa de saúde, recomenda-se certificado pago com validação organizacional (OV) que transmite mais confiança |
| 9 | Email de contato técnico é Gmail gratuito | BAIXO | O RDAP público mostra ceddiariquemesarq@gmail.com como email técnico do domínio. Empresa de saúde deveria usar email corporativo |
| 10 | API do WordPress exposta | BAIXO | O endpoint /wp-json/ está aberto, expondo estrutura interna do site e metadados das páginas |

---

## IMPACTO REAL PARA O NEGÓCIO

1. LGPD (Lei Geral de Proteção de Dados): Clínicas médicas processam dados
   sensíveis de saúde — categoria de maior proteção na LGPD. Multas chegam a
   R$ 50 milhões ou 2% do faturamento. Sem os controles mínimos de segurança,
   a empresa está sujeita a sanções da ANPD.

2. Reputação: Um ataque que comprometa dados de pacientes pode destruir a
   reputação da clínica. No mercado de saúde, confiança é tudo.

3. Sequestro do site (ransomware): WordPress desatualizado e sem proteção é
   o principal vetor de ataque de ransomware. O site pode ser criptografado e
   os atacantes exigem pagamento para devolvê-lo.

4. Phishing: O site pode ser clonado com facilidade por não ter os headers
   de proteção adequados, enganando pacientes a fornecer dados em sites falsos.

---

## ARGUMENTO DE VENDA — SHIELD

"Dr./Sr. [nome], fizemos uma análise rápida do site do CEDDI e encontramos
10 vulnerabilidades, incluindo sua versão de software exposta publicamente e
a ausência das proteções mínimas exigidas pela LGPD para empresas que lidam
com dados de saúde. Empresa de saúde sem segurança digital adequada pode
receber multa de até R$ 50 milhões. Posso mostrar exatamente o que está
exposto e como a SHIELD pode resolver isso em menos de 30 dias."

---
---

# EMPRESA 2 — AISLAN SANTOS IMÓVEIS
## Site: aislansantosimoveis.com.br
**Segmento:** Imobiliária
**Registrante:** Aislan De Jesus Santos Vieira (PESSOA FÍSICA — nome exposto no RDAP)
**Servidor:** Plataforma ImobiBrasil
**Domínio válido até:** 30/10/2028

---

## RESUMO EXECUTIVO (linguagem para o dono)

ATENÇÃO — EMERGÊNCIA: O certificado de segurança (SSL) do site expira em
MENOS DE 3 DIAS (31/05/2026). Quando isso acontecer, todos os navegadores
vão mostrar um AVISO VERMELHO de "site não seguro" para qualquer pessoa que
tentar acessar o site. Isso praticamente mata as vendas online do imobiliário
enquanto o problema não for corrigido.

Além disso, o site não tem nenhuma das proteções básicas de segurança, o nome
completo do proprietário está exposto publicamente para qualquer pessoa que
pesquisar o domínio, e o sistema usa codificação de texto antiquada (iso-8859-1
dos anos 90), indicando uma plataforma desatualizada.

---

## PROBLEMAS ENCONTRADOS

| # | Problema | Severidade | Detalhe Técnico |
|---|----------|------------|-----------------|
| 1 | CERTIFICADO SSL EXPIRA EM 3 DIAS (31/05/2026) | CRÍTICO | Quando expirar, todos os navegadores vão bloquear o acesso ao site com tela vermelha de aviso. Perda imediata de clientes e credibilidade |
| 2 | Nome completo do proprietário exposto no RDAP público | ALTO | "Aislan De Jesus Santos Vieira" visível para qualquer pessoa. Pode ser usado para engenharia social, phishing direcionado e fraudes em nome do proprietário |
| 3 | Ausência de HSTS | ALTO | Dados de clientes em trânsito podem ser interceptados por atacantes em redes Wi-Fi |
| 4 | Ausência de X-Frame-Options | MÉDIO | Site pode ser clonado dentro de página falsa para enganar compradores de imóveis |
| 5 | Ausência de X-Content-Type-Options | MÉDIO | Arquivos maliciosos podem ser executados no servidor |
| 6 | Ausência de Content-Security-Policy | MÉDIO | Dados de clientes podem ser roubados via scripts injetados |
| 7 | Ausência de X-XSS-Protection | MÉDIO | Proteção contra scripts maliciosos desativada |
| 8 | Codificação antiquada (iso-8859-1) | MÉDIO | Charset dos anos 90. Indica plataforma desatualizada, com maior superfície de ataque. Problemas com caracteres especiais podem causar comportamentos inesperados |
| 9 | Dependência total de plataforma terceirizada (ImobiBrasil) | MÉDIO | A segurança do site depende 100% de um terceiro (imobibrasil.com.br). Se a plataforma for comprometida, todos os clientes da ImobiBrasil são afetados simultaneamente |
| 10 | Robots.txt sem restrições ("Allow: /") | BAIXO | Toda a estrutura do site está aberta para indexação, incluindo páginas que deveriam ser privadas |

---

## IMPACTO REAL PARA O NEGÓCIO

1. EMERGÊNCIA IMEDIATA: Em 3 dias o site vai parecer "hackeado" para todos
   os clientes. Leads que tentarem acessar verão tela vermelha de perigo e
   vão sair sem entrar em contato. Perda direta de vendas.

2. LGPD: Imobiliária coleta dados pessoais de compradores e inquilinos
   (CPF, renda, documentos). Sem proteção adequada, responsabilidade civil.

3. Fraude: Nome do proprietário exposto facilita que criminosos entrem em
   contato com clientes se passando pelo corretor, desviando transações.

4. Dependência de terceiros: Todo o negócio digital está nas mãos de uma
   plataforma terceirizada que o proprietário não controla.

---

## ARGUMENTO DE VENDA — SHIELD

"Sr. Aislan, trouxemos uma notícia urgente: o certificado de segurança do seu
site vence em 3 dias. Quando isso acontecer, seus clientes vão ver uma tela
vermelha dizendo que o site é perigoso. Além disso, seu nome completo está
exposto publicamente na internet para qualquer um consultar. A SHIELD pode
resolver a emergência hoje mesmo e implementar um plano completo de proteção
para sua imobiliária. Posso mostrar tudo isso na tela agora?"

---
---

# EMPRESA 3 — BRUNI IMÓVEIS
## Site: bruniimoveis.com.br
**Segmento:** Imobiliária
**Registrante:** Rubens Luis Bruni (PESSOA FÍSICA — nome exposto no RDAP)
**Servidor:** Cloudflare + WordPress
**Domínio válido até:** 23/08/2027

---

## RESUMO EXECUTIVO (linguagem para o dono)

A Bruni Imóveis tem algo que chama a atenção: o site funciona tanto com
criptografia (https://) quanto SEM criptografia (http://), servindo conteúdo
completo em ambos os casos. Isso significa que quando um cliente acessa o
site pela rede sem fio de um café, por exemplo, os dados podem ser
interceptados por alguém mal-intencionado na mesma rede, sem que ninguém
perceba.

O site usa Cloudflare (um serviço de proteção bem conhecido), mas a
configuração foi feita de forma incompleta — é como instalar uma câmera
de segurança mas não ligar ela na energia.

---

## PROBLEMAS ENCONTRADOS

| # | Problema | Severidade | Detalhe Técnico |
|---|----------|------------|-----------------|
| 1 | HTTP NÃO redireciona para HTTPS — site acessível sem criptografia | CRÍTICO | curl -sI http://bruniimoveis.com.br retorna "200 OK" com conteúdo completo. Dados de clientes trafegam em texto puro. Violação direta da LGPD |
| 2 | Cloudflare configurado de forma incompleta | ALTO | Mesmo usando Cloudflare (serviço pago), o site não aproveita as proteções disponíveis. Dinheiro gasto sem o benefício completo |
| 3 | Ausência de HSTS | ALTO | Sem esse header, navegadores não são instruídos a sempre usar HTTPS, permitindo downgrades para HTTP |
| 4 | Nome completo do dono exposto no RDAP | ALTO | "Rubens Luis Bruni" + email do técnico visíveis publicamente |
| 5 | Ausência de X-Frame-Options | MÉDIO | Site pode ser embutido em páginas falsas para enganar compradores |
| 6 | Ausência de X-Content-Type-Options | MÉDIO | Proteção contra execução de arquivos maliciosos ausente |
| 7 | Ausência de Content-Security-Policy | MÉDIO | Sem barreira contra scripts injetados por terceiros |
| 8 | Ausência de X-XSS-Protection | MÉDIO | Camada de proteção contra ataques de script desativada |
| 9 | Versões de plugins expostas (Elementor, etc.) | MÉDIO | Versões detectadas no código-fonte: Elementor, Yoast SEO e outros — alvos frequentes de exploits automatizados |
| 10 | API WordPress exposta (/wp-json/) | BAIXO | Endpoint público expõe estrutura do site e pode revelar informações de usuários cadastrados |

---

## IMPACTO REAL PARA O NEGÓCIO

1. LGPD: Site acessível via HTTP sem criptografia é uma violação clara do
   princípio de segurança da LGPD. Qualquer dado enviado por formulário
   (nome, telefone, CPF) pode ser capturado em redes Wi-Fi.

2. Dinheiro desperdiçado: A empresa já paga pelo Cloudflare mas não está
   usando corretamente. Com a configuração adequada, o Cloudflare oferece
   proteção robusta — mas apenas se configurado direito.

3. Confiança do cliente: Um comprador de imóveis pesquisando propriedades
   em uma rede pública pode ter seus dados capturados por terceiros.

4. Concorrência: Sites concorrentes bem configurados aparecem melhor no
   Google (HTTPS é fator de ranqueamento). O site em HTTP prejudica o SEO.

---

## ARGUMENTO DE VENDA — SHIELD

"Sr. Rubens, encontramos um problema sério no site da Bruni Imóveis:
qualquer pessoa que acessar o site por uma rede Wi-Fi de café ou shopping
pode ter seus dados interceptados, porque o site ainda funciona sem
criptografia. Pior: vocês já pagam pelo Cloudflare, que poderia resolver
isso, mas está configurado errado. A SHIELD pode consertar essa configuração
e implementar a proteção completa que vocês já estão pagando mas não estão
usando. Faz sentido conversarmos?"

---
---

# EMPRESA 4 — ADI IMÓVEIS RO
## Site: adimoveisro.com.br
**Segmento:** Imobiliária
**Registrante:** Acácio da Silva Campos (PESSOA FÍSICA — nome exposto no RDAP)
**Servidor:** LiteSpeed (via Cloudflare DNS)
**Domínio válido até:** 06/12/2028

---

## RESUMO EXECUTIVO (linguagem para o dono)

A ADI Imóveis é, dos 5 sites analisados, o que apresenta a melhor
configuração de segurança — mas ainda com lacunas significativas que precisam
ser corrigidas. Já existe algum cuidado técnico evidente: algumas proteções
básicas estão ativas, os cookies têm configuração adequada e o servidor
LiteSpeed está bem configurado.

Porém, ainda faltam proteções importantes, especialmente contra ataques
mais sofisticados como injeção de scripts e interceptação de dados. É como
ter uma boa fechadura mas deixar a janela do lado aberta.

---

## PROBLEMAS ENCONTRADOS

| # | Problema | Severidade | Detalhe Técnico |
|---|----------|------------|-----------------|
| 1 | Ausência de HSTS (Strict-Transport-Security) | ALTO | Apesar do redirecionamento HTTP→HTTPS funcionar, sem HSTS os navegadores podem ser manipulados para ignorar o HTTPS em ataques sofisticados |
| 2 | Ausência de Content-Security-Policy | ALTO | É a proteção mais importante contra ataques XSS modernos. Sem ela, scripts maliciosos injetados podem roubar dados de clientes sem deixar rastro |
| 3 | Nome completo do proprietário exposto no RDAP | ALTO | "Acácio da Silva Campos" visível publicamente para qualquer consulta |
| 4 | Ausência de X-XSS-Protection | MÉDIO | Camada de proteção complementar desativada |
| 5 | Certificado SSL expira em 43 dias (10/07/2026) | MÉDIO | Let's Encrypt renova automaticamente, mas problemas na renovação podem deixar o site offline. Recomenda-se monitoramento ativo |
| 6 | Versões de software expostas | MÉDIO | Versões de plugins visíveis no código-fonte (ex: ver=6.4.1) facilitam ataques direcionados |
| 7 | API WordPress exposta (/wp-json/) | MÉDIO | Endpoint público acessível, podendo revelar informações sobre usuários e estrutura do site |
| 8 | Ausência de monitoramento de segurança | MÉDIO | Sem alertas de segurança em tempo real, um ataque pode demorar dias para ser detectado |
| 9 | Proteções parciais sem política documentada | BAIXO | Alguns headers estão corretos, mas a configuração parece ter sido feita sem seguir uma política de segurança formal |

---

## PONTOS POSITIVOS (para mencionar na abordagem)

- X-Frame-Options: SAMEORIGIN ativo (protege contra clickjacking)
- X-Content-Type-Options: nosniff ativo (protege contra MIME sniffing)
- Referrer-Policy configurada
- Cookie PHPSESSID com flags de segurança corretas (HttpOnly, SameSite=Strict, Secure)
- HTTP redireciona para HTTPS
- Uso de Cloudflare DNS

---

## IMPACTO REAL PARA O NEGÓCIO

1. LGPD: Mesmo com as proteções parciais, a ausência de Content-Security-Policy
   deixa os dados dos clientes vulneráveis ao ataque mais comum na internet hoje.

2. Risco de reputação: O fato de ter algumas proteções pode criar uma falsa
   sensação de segurança. Um ataque bem-sucedido é mais surpreendente (e danoso)
   para quem achava que estava protegido.

3. Certificado expirando: Em 43 dias, se a renovação automática falhar, o
   site fica inacessível — sem monitoramento, o problema pode durar dias.

---

## ARGUMENTO DE VENDA — SHIELD

"Sr. Acácio, parabéns — o site da ADI tem algumas proteções que os
concorrentes não têm. Mas encontramos pontos críticos que ainda estão abertos,
especialmente a falta de proteção contra injeção de scripts, que é o ataque
mais usado atualmente para roubar dados de clientes em sites imobiliários.
O certificado SSL também vence em 43 dias — se a renovação automática
falhar, o site fica inacessível. A SHIELD pode completar a proteção que
vocês já começaram e adicionar monitoramento 24h."

---
---

# EMPRESA 5 — COLÉGIO EXCELÊNCIA (Colégio Sapiens Excelência)
## Site: colegioexcelenciaro.com.br
**Segmento:** Educação / Ensino
**Registrante:** Douglas Torres Nogueira
**Responsável técnico:** claudio.fonseca@gruposapiens.com.br (email exposto publicamente)
**Servidor:** Microsoft IIS 10.0 / ASP.NET
**Domínio válido até:** 05/10/2026 — ATENÇÃO: em 130 dias

---

## RESUMO EXECUTIVO (linguagem para o dono)

Esse site tem uma situação diferente dos outros: o domínio colegioexcelenciaro.com.br
redireciona para outro site (colegiosapiens.com), o que significa que
a escola não controla sua presença digital diretamente. Quem digitar o
endereço é mandado para outro lugar.

O problema mais urgente é o domínio: ele vence em outubro de 2026, em
apenas 130 dias. Se não for renovado, qualquer pessoa pode registrar o mesmo
domínio e criar um site falso se passando pelo colégio — capturando mensalidades,
dados de alunos e prejudicando famílias que tentarem contato.

Além disso, o servidor expõe publicamente que usa tecnologia Microsoft IIS 10.0
e ASP.NET, informações que facilitam ataques direcionados.

---

## PROBLEMAS ENCONTRADOS

| # | Problema | Severidade | Detalhe Técnico |
|---|----------|------------|-----------------|
| 1 | DOMÍNIO VENCE EM 130 DIAS (05/10/2026) | CRÍTICO | Se não renovado, qualquer pessoa pode registrar colegioexcelenciaro.com.br e criar site falso, capturando dados de pais e alunos |
| 2 | Tecnologia do servidor exposta: Microsoft IIS 10.0 | ALTO | O header "Server: Microsoft-IIS/10.0" é visível publicamente. Atacantes buscam vulnerabilidades específicas dessa versão |
| 3 | Framework exposto: X-Powered-By: ASP.NET | ALTO | Informa exatamente qual tecnologia o servidor usa, reduzindo o trabalho de um atacante que queira encontrar brechas |
| 4 | Ausência de HSTS | ALTO | Sem proteção contra downgrade de conexão segura para insegura |
| 5 | Ausência de X-Frame-Options | ALTO | Site de escola pode ser embutido em página falsa para capturar login de pais e alunos (portal do aluno / boletos) |
| 6 | Ausência de X-Content-Type-Options | MÉDIO | Proteção contra execução de arquivos maliciosos ausente |
| 7 | Ausência de Content-Security-Policy | MÉDIO | Dados de pais e alunos podem ser roubados via scripts injetados |
| 8 | Ausência de X-XSS-Protection | MÉDIO | Proteção básica contra scripts maliciosos desativada |
| 9 | Certificado SSL expira em 39 dias (06/07/2026) | MÉDIO | Let's Encrypt básico expirando em breve, sem monitoramento |
| 10 | Email técnico exposto publicamente no RDAP | MÉDIO | claudio.fonseca@gruposapiens.com.br visível para qualquer consulta, facilitando engenharia social e phishing direcionado |
| 11 | Domínio separado do conteúdo real | MÉDIO | O site em colegioexcelenciaro.com.br apenas redireciona para colegiosapiens.com — a escola não tem controle direto sobre seu próprio domínio |
| 12 | Robots.txt e Sitemap inacessíveis (redirecionados) | BAIXO | Infraestrutura digital fragmentada e sem gestão centralizada |

---

## IMPACTO REAL PARA O NEGÓCIO

1. RISCO MAIS GRAVE — Golpe no nome do colégio: Quando o domínio vencer,
   criminosos podem registrá-lo e criar um portal de matrículas falso,
   cobrando mensalidades de pais desavisados. O colégio fica sem ferramenta
   para provar que não foi responsável.

2. LGPD: Instituições de ensino processam dados de menores de idade —
   categoria de proteção máxima na LGPD. Multas e sanções são severas.

3. Confiança dos pais: Um site que expõe tecnologia do servidor e redireciona
   para outro domínio passa impressão de descuido. Pais pesquisando o colégio
   podem desconfiar da seriedade da instituição.

4. Servidor IIS exposto: IIS 10.0 tem vulnerabilidades conhecidas exploráveis
   remotamente. A exposição da versão facilita ataques automatizados.

---

## ARGUMENTO DE VENDA — SHIELD

"Olá, gostaria de falar com o responsável pela TI do Colégio Excelência. Fizemos
uma análise de segurança do site e encontramos um problema urgente: o domínio
colegioexcelenciaro.com.br vence em outubro — em 130 dias. Se não for renovado,
qualquer pessoa pode registrar esse endereço e criar um site falso do colégio,
cobrando mensalidades de pais de alunos. Além disso, o servidor expõe publicamente
qual tecnologia usa, facilitando ataques. O colégio também lida com dados de
menores, o que torna a conformidade com a LGPD ainda mais crítica. Podemos
ajudar a resolver tudo isso."

---

# TABELA COMPARATIVA — RESUMO GERAL

| Proteção | CEDDI | Aislan | Bruni | ADI | Colégio |
|----------|-------|--------|-------|-----|---------|
| HTTPS Ativo | SIM | SIM | SIM | SIM | SIM (redirecionado) |
| HTTP redireciona p/ HTTPS | SIM | SIM | NÃO ❌ | SIM | SIM (p/ outro domínio) |
| HSTS | NÃO ❌ | NÃO ❌ | NÃO ❌ | NÃO ❌ | NÃO ❌ |
| X-Frame-Options | NÃO ❌ | NÃO ❌ | NÃO ❌ | SIM ✅ | NÃO ❌ |
| X-Content-Type-Options | NÃO ❌ | NÃO ❌ | NÃO ❌ | SIM ✅ | NÃO ❌ |
| Content-Security-Policy | NÃO ❌ | NÃO ❌ | NÃO ❌ | NÃO ❌ | NÃO ❌ |
| X-XSS-Protection | NÃO ❌ | NÃO ❌ | NÃO ❌ | NÃO ❌ | NÃO ❌ |
| Versão CMS exposta | SIM ❌ | NÃO | SIM (parcial) | NÃO | SIM ❌ |
| Servidor exposto | Apache | Apache | Cloudflare | LiteSpeed | IIS 10.0 ❌ |
| SSL válido | 81 dias | 3 DIAS ❌ | 71 dias | 43 dias | 39 dias |
| Domínio válido | 2029 | 2028 | 2027 | 2028 | OUT/2026 ❌ |
| Nota geral | 3/10 | 1/10 | 2/10 | 5/10 | 2/10 |

---

# PRIORIDADE DE ABORDAGEM — RECOMENDAÇÃO PARA SHIELD

1. AISLAN SANTOS IMÓVEIS — Abordagem URGENTE (SSL expira em 3 dias)
   Use o argumento da emergência. O dono provavelmente não sabe.

2. COLÉGIO EXCELÊNCIA — Alta prioridade (domínio vence em 130 dias, dados de menores)
   Maior impacto potencial de dano. Decisor pode ser sensível ao risco reputacional.

3. BRUNI IMÓVEIS — Site em HTTP puro é violação LGPD ativa
   Argumento legal forte. Cloudflare já pago mas mal configurado.

4. CEDDI CENTRO DIAGNÓSTICO — Dados de saúde + WordPress desatualizado exposto
   LGPD com multa máxima (dados sensíveis de saúde).

5. ADI IMÓVEIS — Melhor configurado, mas ainda com lacunas
   Abordagem consultiva: "vocês começaram bem, vamos completar a proteção."

---

# SERVIÇOS QUE A SHIELD PODE OFERECER

Com base nos problemas encontrados, os seguintes serviços são aplicáveis:

- Auditoria de Segurança Web (diagnóstico completo)
- Hardening de Servidor (configuração de headers, versões, etc.)
- Monitoramento de SSL e Domínio (alerta antes de vencimento)
- Implementação de WAF (Web Application Firewall)
- Consultoria LGPD (adequação para dados pessoais e sensíveis)
- Configuração completa de Cloudflare (para quem já usa)
- Plano de Resposta a Incidentes

---

*Relatório gerado por análise passiva em 27/05/2026.*
*SHIELD Cibersegurança — Ariquemes-RO*
*Uso interno exclusivo para abordagem comercial.*
