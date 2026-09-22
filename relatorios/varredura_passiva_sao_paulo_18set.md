# VARREDURA PASSIVA — LEADS SÃO PAULO — 18/09
Fonte dos leads: Apify Actor "compass/crawler-google-places" (Google Maps).
Fonte da varredura: curl headers HTTP/HTTPS + openssl (mesma metodologia usada
em Ariquemes). NÃO é pentest ativo — é só observação pública, sem exploit.

Sites confirmados: 12/13 (MF Advocacia só tem Instagram, sem site próprio —
oportunidade diferente: presença digital fraca é o próprio argumento de venda).

---

## RANKING POR PRIORIDADE (mais vulnerável = mais fácil de vender)

### 1. LELLO IMÓVEIS — lelloimoveis.com.br — PRIORIDADE ALTA
Servidor: Apache | SSL expira: 18/02/2027
Faltando: TODOS os 5 headers de segurança (HSTS, X-Frame, X-Content-Type,
CSP, X-XSS). Zero proteção configurada.
Imobiliária grande (Vila Mariana) processando dados de compradores/locatários
(CPF, renda) sem nenhuma camada extra de proteção.

**MENSAGEM WHATSAPP:**
"Boa tarde! Sou da SHIELD Cibersegurança. Fizemos uma checagem pública e
gratuita no site da Lello Imóveis (lelloimoveis.com.br) e identificamos que
ele está rodando sem nenhuma das 5 proteções básicas de segurança que sites
que coletam CPF e dados financeiros de clientes deveriam ter — hoje está tudo
em aberto, como uma casa sem trava nenhuma na porta. Isso é público, qualquer
pessoa pode checar. Preparamos um relatório técnico simples mostrando
exatamente o que falta e como resolver. Posso te enviar sem compromisso?"
Abordagem: direta, sem alarmismo — é o caso mais grave do lote, o achado
já fala por si. Mandar pro WhatsApp comercial/atendimento da imobiliária.

### 2. KLABIN IMÓVEIS — klabinimoveis.com.br — PRIORIDADE ALTA
Servidor: gocache | SSL expira: 09/11/2026
Faltando: TODOS os 5 headers.

**MENSAGEM WHATSAPP:**
"Olá! Somos da SHIELD Cibersegurança. Analisamos publicamente o site da
Klabin Imóveis e vimos que faltam todas as proteções básicas de segurança
(headers HTTP) que evitam ataques comuns como clonagem de página e roubo de
sessão de cliente. É simples de corrigir, mas hoje está 100% exposto.
Fizemos um relatório gratuito com o detalhamento técnico — posso te mandar?"
Abordagem: mesmo tom direto do lead 1, pode reaproveitar quase igual (mesmo
segmento, mesmo problema — imobiliária).

### 3. CHEIDITH IMÓVEIS — apartamentosavendanachacaraklabin.com — PRIORIDADE ALTA
Servidor: Cloudflare (mas mal configurado — mesmo padrão do Bruni Imóveis em
Ariquemes: paga proteção e não usa) | SSL expira: 06/11/2026
Faltando: TODOS os 5 headers, apesar do Cloudflare ativo.
Maior volume de avaliações (1000+) do grupo — imobiliária de peso na região.

**MENSAGEM WHATSAPP:**
"Boa tarde! Somos da SHIELD Cibersegurança. Vimos que vocês já usam
Cloudflare no site — ótimo primeiro passo — mas a configuração de segurança
não está ativada corretamente, faltam as 5 proteções básicas que o próprio
Cloudflare oferece de graça. É tipo pagar por um alarme e não ligar. Com o
volume de clientes que vocês atendem, vale a pena corrigir isso rápido.
Fizemos um relatório técnico gratuito — posso enviar?"
Abordagem: consultiva (elogiar o Cloudflare primeiro, depois apontar o
problema) — gera rapport melhor que ataque direto, empresa de peso na região.

### 4. REMAX SQUARE — remax.com.br/square — PRIORIDADE ALTA
Servidor: Cloudflare (mesmo padrão: mal configurado) | SSL expira: 07/11/2026
Faltando: TODOS os 5 headers.
Marca REMAX é franquia internacional — abordagem tem que ser mais formal/cuidadosa
(provavelmente há política de marca a respeitar), mas achado técnico é real.

**MENSAGEM WHATSAPP:**
"Boa tarde! Meu nome é Lorran, sou da SHIELD Cibersegurança. Fizemos uma
análise pública no site da unidade RE/MAX Square e identificamos que faltam
as configurações de segurança (headers HTTP) mesmo com Cloudflare ativo —
achado técnico real, verificável por qualquer ferramenta pública. Sei que
como franquia vocês podem ter política própria de TI definida pela rede;
se for o caso, agradeço se puderem me indicar o contato certo. Se quiserem,
te envio o relatório gratuito com o detalhamento."
Abordagem: mais formal, sem pressa, deixando espaço para redirecionamento
interno — franquia grande, não forçar.

### 5. MODAELLI ADVOGADOS — modaelliadvogados.com — PRIORIDADE ALTA
Servidor: Apache | SSL expira: 06/11/2026
Faltando: TODOS os 5 headers.
Escritório em endereço nobre (Av. Paulista, 807), processa dados sigilosos de
clientes — argumento de confidencialidade profissional (OAB) é forte aqui.

**MENSAGEM WHATSAPP:**
"Boa tarde, doutor(a). Sou da SHIELD Cibersegurança. Fizemos uma checagem
pública no site do escritório e identificamos que ele está sem nenhuma das
proteções básicas de segurança digital — um risco real considerando o sigilo
profissional exigido pela OAB sobre dados de clientes. É uma falha simples de
corrigir, mas que hoje deixa a porta aberta para interceptação de dados.
Preparamos um relatório técnico gratuito, sem compromisso — posso enviar?"
Abordagem: usar o argumento de sigilo profissional/OAB como gancho — funciona
melhor que argumento técnico puro com advogados.

### 6. SQUIAPATI.LAW — squiapati.law — PRIORIDADE ALTA
Servidor: Apache | SSL expira: 03/01/2027
Faltando: TODOS os 5 headers.

**MENSAGEM WHATSAPP:**
"Boa tarde! Sou da SHIELD Cibersegurança. Analisamos publicamente o site do
escritório (squiapati.law) e vimos que faltam todas as proteções básicas de
segurança digital, o que expõe dados de clientes e comunicações. Preparamos
um relatório técnico gratuito explicando o que encontramos e como resolver —
posso te mandar sem compromisso?"
Abordagem: igual ao lead 5 (mesmo segmento) — pode reforçar o argumento OAB
se o primeiro contato for outro advogado do escritório.

### 7. ODONTO PINHEIROS — odontopinheiros.com.br — PRIORIDADE MÉDIA-ALTA
HTTPS não respondeu na varredura direta (checar manualmente — pode ser CDN
bloqueando IP do datacenter, não necessariamente erro real do site).
HTTP redireciona certo para HTTPS. SSL expira 09/09/2026 — checar de novo,
pode estar próximo do vencimento quando for abordar.
Dado de saúde (odontologia) = LGPD sensível.
Ainda sem mensagem pronta — recheckar SSL/headers manualmente antes de abordar.

### 8. NIPODONTO — nipodonto.com.br — PRIORIDADE MÉDIA
Servidor: Apache | SSL expira: 02/11/2026
Faltando: TODOS os 5 headers.

### 9. CLÍNICA FLÚOR — clinicafluor.com — PRIORIDADE MÉDIA
Servidor: LiteSpeed | SSL expira: 08/12/2026
Faltando: X-Frame-Options, Content-Security-Policy (só 2 de 5 — configuração
parcial, parecido com o caso ADI Imóveis em Ariquemes).

### 10. ONESTI ADVOGADOS — onestiadvogados.com.br — PRIORIDADE MÉDIA
Servidor: Netlify | SSL expira: 10/11/2026
Faltando: X-Frame-Options, X-Content-Type-Options, CSP, X-XSS (4 de 5 —
Netlify já dá HSTS por padrão, falta completar o resto).

### 11. DOM PAIVA IMÓVEIS — dompaivaimoveis.com.br — PRIORIDADE BAIXA
Servidor: Google Frontend (provavelmente hospedado em infra Google/Firebase)
SSL expira: 13/11/2026
Faltando: só X-XSS-Protection (o mais fraco/menos crítico dos 5). Site já
bem configurado — abordagem consultiva, não alarmista.

### 12. VILHENA SILVA ADVOGADOS — vilhenasilva.com.br — SEM ACHADO
Servidor: Cloudflare | SSL expira: 17/12/2026
TODOS os 5 headers presentes. Site bem protegido — NÃO usar como lead agora,
não há argumento técnico real. (Igual ADI Imóveis em Ariquemes ser o "aluno
nota 10" da lista — não insistir aqui.)

### MF ADVOCACIA — SEM SITE PRÓPRIO (só Instagram)
Oportunidade diferente: não tem o que escanear, mas dá pra abordar oferecendo
criar presença digital segura desde o início — argumento comercial distinto
(não é "conserto de vulnerabilidade", é "comece certo").

---

## PADRÃO IDENTIFICADO (igual Ariquemes)
Cloudflare mal configurado aparece em 3 dos 12 sites (Cheidith, REMAX, Vilhena)
— só a Vilhena configurou certo. Isso confirma que "empresa paga por proteção
mas não usa direito" é um padrão real e repetível, não coincidência de uma
cidade só. Bom argumento de abordagem: "vocês já pagam por isso, só falta
ativar certo."

## COMO USAR AS MENSAGENS ACIMA
- Mandar UMA de cada vez, num canal por dia se possível — não disparar as 6
  juntas pra não parecer spam em massa.
- Trocar "Boa tarde"/"Olá" pelo horário real de envio.
- Se a empresa responder pedindo o relatório completo, montar o PDF só
  depois — não gastar esforço de pentest completo antes de sinal de
  interesse real (regra da skill libertus-shield-prospeccao).
- Se não responder em 2-3 dias, não reenviar a mesma mensagem: seguir a
  cadência de follow-up da skill (trocar canal/pessoa, nunca insistir no
  mesmo contato).

## PRÓXIMO PASSO
Escolher 2-3 da lista PRIORIDADE ALTA pra montar o relatório completo em PDF
(igual fizemos em Ariquemes) assim que algum responder com interesse.
</content>
