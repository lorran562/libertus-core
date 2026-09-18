# LISTA DE PROSPECÇÃO — SÃO PAULO (SP) — 18/09
Fonte: Google Maps (nome, endereço, telefone confirmados — DDD 11 verificado).
NÃO verificado ainda: site institucional de cada uma, headers, SSL, CNPJ.
Antes de abordar QUALQUER uma, rodar a mesma análise passiva que fizemos em
Ariquemes (headers, SSL, WHOIS, CMS exposto) pra ter argumento real na mão —
sem isso, é só nome de empresa, não é proposta.

## POR QUE ESSES SEGMENTOS
Imobiliária, advocacia e clínica são os 3 tipos de negócio que mais aparecem
com vulnerabilidade real nas nossas análises anteriores (Ariquemes) — sites
institucionais feitos por agência barata, sem CSP/HSTS, às vezes WordPress
desatualizado. Advocacia e clínica também lidam com dado sensível (sigilo
profissional / LGPD saúde), o que fortalece o argumento comercial.

## IMOBILIÁRIAS — VILA MARIANA / SÃO PAULO
1. REMAX Square — Imobiliária Vila Mariana
   R. Humberto I, 115 - Sl 209 | (11) 91336-3191
2. Lello Imóveis Vila Mariana
   R. Domingos de Morais, 3014 | (11) 3387-0000
3. Dom Paiva Imóveis
   R. Dr. Tirso Martins, 100 - Cjto 211 | (11) 5549-0088
4. Klabin Imóveis
   R. Bartolomeu de Gusmão, 329 | (11) 5575-6988
5. Cheidith Imóveis — Chácara Klabin, Vila Mariana
   R. João Luís Vives, 130 | (11) 3232-1250

## ESCRITÓRIOS DE ADVOCACIA — AV. PAULISTA
6. Squiapati.law
   Av. Paulista, 37 - 4º Andar | (11) 2502-6621
7. Modaelli Advogados Associados
   Av. Paulista, 807 - 14º Andar, CJ 1416/1417 | (11) 94281-9611
8. Onesti Advogados
   Av. Paulista, 91 - 1º andar, 101 | (11) 3262-4647
9. MF Advocacia | Consultoria & Assessoria Jurídica
   Av. Paulista, 726 | (11) 98694-4365
10. Vilhena Silva Advogados
    Av. Paulista, 1294 | (11) 3256-1283

## CLÍNICAS ODONTOLÓGICAS — PINHEIROS
11. Odonto Pinheiros
    R. Teodoro Sampaio, 1020 - Conj 903 | (11) 3081-9404
12. Nipodonto
    R. Teodoro Sampaio, 744 - Conj 131 | (11) 3061-5567
13. Clínica Flúor
    R. Teodoro Sampaio, 744 - Conj. 148 | (11) 3375-0875

---

## PRÓXIMO PASSO OBRIGATÓRIO ANTES DE MANDAR QUALQUER MENSAGEM
Não mandar mensagem só com "oi, oferecemos segurança" — isso sem prova
concreta parece spam/golpe e vai pro lixo. Pra cada empresa que Lorran
decidir priorizar:

1. Descobrir o site institucional real (varia por empresa — nem todo
   contato do Maps tem site próprio ligado).
2. Rodar a mesma checagem passiva feita nos sites de Ariquemes:
   headers HTTP, SSL/TLS, WHOIS, CMS exposto, redirect HTTP->HTTPS.
3. Só abordar com achado real na mão (igual fizemos com o Lab São Francisco).
4. Ligar ou mandar e-mail formal — não WhatsApp de número pessoal pra
   empresa de porte médio/grande de capital, o tom tem que ser mais formal
   que em Ariquemes.

## SOBRE ESCALA E CRÉDITO (resposta à sua pergunta de fazer 100% só em quem
fechar negócio)
Faz sentido economizar: a ANÁLISE PASSIVA (headers, SSL, WHOIS) é barata e
rápida — pode ser feita pra todos os 13 antes de qualquer contato, sem gasto
de crédito relevante, porque são poucos comandos curl/openssl por site.
O que deve ser reservado só pra quem fechar é o WORK PESADO: pentest ativo,
scan completo (nmap, nuclei, sqlmap), relatório técnico completo em PDF.
Ou seja: reconhecimento passivo em todos, esforço ativo só em quem pagar.
