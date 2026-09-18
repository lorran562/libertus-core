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

### 2. KLABIN IMÓVEIS — klabinimoveis.com.br — PRIORIDADE ALTA
Servidor: gocache | SSL expira: 09/11/2026
Faltando: TODOS os 5 headers.

### 3. CHEIDITH IMÓVEIS — apartamentosavendanachacaraklabin.com — PRIORIDADE ALTA
Servidor: Cloudflare (mas mal configurado — mesmo padrão do Bruni Imóveis em
Ariquemes: paga proteção e não usa) | SSL expira: 06/11/2026
Faltando: TODOS os 5 headers, apesar do Cloudflare ativo.
Maior volume de avaliações (1000+) do grupo — imobiliária de peso na região.

### 4. REMAX SQUARE — remax.com.br/square — PRIORIDADE ALTA
Servidor: Cloudflare (mesmo padrão: mal configurado) | SSL expira: 07/11/2026
Faltando: TODOS os 5 headers.
Marca REMAX é franquia internacional — abordagem tem que ser mais formal/cuidadosa
(provavelmente há política de marca a respeitar), mas achado técnico é real.

### 5. MODAELLI ADVOGADOS — modaelliadvogados.com — PRIORIDADE ALTA
Servidor: Apache | SSL expira: 06/11/2026
Faltando: TODOS os 5 headers.
Escritório em endereço nobre (Av. Paulista, 807), processa dados sigilosos de
clientes — argumento de confidencialidade profissional (OAB) é forte aqui.

### 6. SQUIAPATI.LAW — squiapati.law — PRIORIDADE ALTA
Servidor: Apache | SSL expira: 03/01/2027
Faltando: TODOS os 5 headers.

### 7. ODONTO PINHEIROS — odontopinheiros.com.br — PRIORIDADE MÉDIA-ALTA
HTTPS não respondeu na varredura direta (checar manualmente — pode ser CDN
bloqueando IP do datacenter, não necessariamente erro real do site).
HTTP redireciona certo para HTTPS. SSL expira 09/09/2026 — checar de novo,
pode estar próximo do vencimento quando for abordar.
Dado de saúde (odontologia) = LGPD sensível.

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

## PRÓXIMO PASSO
Escolher 2-3 da lista PRIORIDADE ALTA pra montar o relatório completo em PDF
(igual fizemos em Ariquemes) e definir abordagem (e-mail formal, mais indicado
pra porte SP do que WhatsApp direto).
