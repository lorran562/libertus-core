# ANÁLISE DE SEGURANÇA — LABORATÓRIO SÃO FRANCISCO

**Alvo:** saofranciscorondonia.com.br + portal de resultados
**Data da análise:** 13/10/2026 (reanálise; primeira análise em maio/2026)
**Metodologia:** reconhecimento passivo — apenas dados públicos (DNS, cabeçalhos HTTP, TLS, HTML e JavaScript publicado). Nenhum teste intrusivo.
**Executado por:** SHIELD Cibersegurança (@shieldweb)

---

## 1. LEIA ISTO PRIMEIRO — o site mudou e o que foi corrigido

Diferente da análise de maio, o site **foi refeito e migrado**. As falhas antigas
**não existem mais**:

| Falha reportada em maio | Situação hoje (13/10/2026) |
|---|---|
| `/.env` acessível publicamente | **CORRIGIDO** — responde 403 (bloqueado) |
| `/.git/` exposto (código-fonte vazando) | **CORRIGIDO** — `/.git/HEAD` e `/.git/config` respondem 403 |
| `/config` exposto | **CORRIGIDO** — responde 404 (não existe mais) |
| `/backup.sql` e `/.DS_Store` | **CORRIGIDO/ausente** — 403 / 404 |

**Consequência prática:** não existe mais o argumento "a falha continua aberta".
Dizer isso ao cliente seria mentira verificável em 10 segundos — e destruiria a
credibilidade da abordagem. Este documento substitui aquele argumento.

Infraestrutura atual: **AWS CloudFront** (server-3-174-59-*.r.cloudfront.net) +
Apache/2.4.68 em Amazon Linux. O site é publicado por plataforma de terceiros
(**W2B** — w2b.com.br).

Nota importante de responsabilidade: mesmo com o site terceirizado, **o
laboratório continua sendo o CONTROLADOR dos dados de paciente perante a LGPD**.
Quem opera é o fornecedor; quem responde pela multa é o controlador.

---

## 2. PONTOS POSITIVOS (crédito onde é devido)

- HTTP redireciona corretamente para HTTPS (sem conteúdo misto).
- TLS 1.3 no site principal, certificado da Amazon válido até 22/01/2027.
- Nenhum cookie sem flag de segurança (`HttpOnly`/`Secure`/`SameSite` presentes).
- **Nenhum dado de paciente guardado no navegador**: `localStorage`,
  `sessionStorage` e `IndexedDB` vazios (verificado).
- Cloudflare Turnstile presente na página.
- Source maps **não** expostos para o código próprio do site.
- Portal de resultados com HSTS e `X-Frame-Options: DENY`.

---

## 3. ACHADOS ABERTOS HOJE

### 3.1 [OBSERVAÇÃO — corrigido] Formulário externo no Google **encerrado**

Verificando o link que aparece no site, ele aponta para um formulário do Google:
```
https://docs.google.com/forms/d/e/1FAIpQLSeSCj0LbSmtCUmq4SRvZnmpiO8Gcj57tQauCzDFKohptg5GcA/viewform
```

Ao abrir: é uma **"Pesquisa de Satisfação de Clientes"** e o formulário está
**ENCERRADO** (redireciona para `/closedform`, não aceita mais respostas).

**Correção de rumo na própria análise:** numa primeira leitura este item parecia
coleta de dado de paciente fora do domínio (risco alto). Conferido o conteúdo, é
apenas uma pesquisa de satisfação **desativada**. Sendo assim:
- não há dado pessoal sendo coletado ali hoje;
- **não** deve ser usado como argumento de venda — seria exagero, e o cliente
  verifica em um clique.

O que sobra é higiene: o site mantém no ar um botão que leva a um formulário
morto. Isso é problema de experiência do cliente, não de segurança.

**O ponto de LGPD que continua valendo** (e é mais forte do que esse) é o
formulário de contato do próprio site, que envia nome, e-mail e telefone sem
registro de consentimento nem aviso de privacidade no ponto de coleta — e o
portal de resultados da seção 3.3, que trata dado de saúde.

### 3.2 [ALTO] Endpoints internos "escondidos" estão em texto claro no JavaScript público

O site tenta esconder o diretório de componentes internos no `robots.txt`:
```
Disallow: /_src/components/
```

Mas os caminhos internos estão publicados no JavaScript aberto da página:
```
/_src/components/v1/inc/ajax/exames.php
/_src/components/v1/inc/ajax/exames_exclusivos.php
```

Isso foi extraído por análise estática de bundle (ferramenta REA), com
**hash SHA-256 dos scripts analisados e registro de evidência** — não é suposição.
O que esconder no robots.txt não protege nada: robots.txt é um pedido a buscadores,
não um controle de acesso.

**Importante:** esses endereços **não foram acessados** nesta análise. Verificar se
eles expõem dados exige **autorização escrita** — e é exatamente o tipo de teste que
compõe um pentest contratado.

### 3.3 [ALTO] Portal de resultados de exames — a superfície de maior risco

```
https://saofranciscorondonia.lab.jalis.net.br:7070/resultado/login?cfg_codigo=hsf_arq
```

Observado (apenas a página pública de login, sem nenhuma tentativa de acesso):
- Sistema de terceiro (**Jalis**), hospedado fora do domínio do laboratório, em
  porta não padrão (7070).
- **Sem captcha** no formulário de login.
- **Sem Content-Security-Policy**.
- Emissor do certificado: GoGetSSL (wildcard `*.lab.jalis.net.br`), TLS 1.2.
- O código do cliente vai na URL (`cfg_codigo=hsf_arq`).

**Leitura honesta:** um portal de resultados na internet não é, por si só, uma
falha — o paciente precisa acessá-lo. O que importa e precisa ser confirmado com o
fornecedor: existe MFA? Existe bloqueio por tentativas repetidas? Onde os
resultados ficam armazenados e por quanto tempo? Há contrato de tratamento de
dados (LGPD art. 39) entre o laboratório e a Jalis?

Isso é **superfície de risco em dado sensível de saúde**, não uma vulnerabilidade
provada. Nada aqui foi testado.

### 3.4 [MÉDIO] Cabeçalhos de segurança ausentes no site principal

| Cabeçalho | Situação | Risco |
|---|---|---|
| `Strict-Transport-Security` | **AUSENTE** | permite downgrade para HTTP |
| `X-Frame-Options` | **AUSENTE** | clickjacking (iframe sobre o site) |
| `X-Content-Type-Options` | **AUSENTE** | navegador "adivinha" tipo de arquivo |
| `Referrer-Policy` | **AUSENTE** | vaza URL de origem para terceiros |
| `Content-Security-Policy` | presente mas **fraca**: permite `'unsafe-inline'` e `'unsafe-eval'` | reduz muito a proteção contra injeção de script |
| CSP — origem interna exposta | `http://w2b-api-v2.localhost` | endereço de desenvolvimento vazado na política pública |

### 3.5 [BAIXO] Bibliotecas antigas de terceiros

`jquery-3.5.1.min.js` (2020), `bootstrap.min.js`, `validator.min.js`,
`owl.carousel.min.js` — versões não declaradas na página, sem política de
atualização visível.

---

## 4. O QUE ESTA ANÁLISE **NÃO** FEZ (e por quê)

- Não chamou os endpoints `exames.php` / `exames_exclusivos.php`.
- Não tentou nenhum acesso ao portal de resultados.
- Não executou nenhum teste de força, injeção ou exploração.

Tudo foi observação de dado público. **Qualquer aprofundamento exige autorização
escrita do laboratório** (e, no caso do portal, também do fornecedor Jalis). Isso
não é burocracia: é o que nos protege e o que dá validade legal ao trabalho.

---

## 5. PROPOSTA

| Serviço | O que inclui | Valor |
|---|---|---|
| **Adequação LGPD + endurecimento** | aviso de privacidade e registro de consentimento no formulário de contato, cabeçalhos de segurança do site, especificação técnica pronta para enviar ao fornecedor W2B | **R$ 497** |
| **Verificação autorizada do portal de resultados** | teste real de autenticação, bloqueio por tentativas repetidas, MFA, exposição de dados — com autorização do lab e da Jalis | **R$ 1.500** |
| **Escudo Mensal** | verificação mensal, relatório, alerta de exposição nova, canal direto | **R$ 297/mês** |

Prazo dos itens 3.4 e 3.5 (dependem do fornecedor do site): **2 dias úteis**.
Item 3.2 depende do fornecedor do site. Item 3.3 depende do fornecedor do sistema.

---

## 6. ABORDAGEM SUGERIDA (mensagem de abertura)

> Bom dia! Aqui é o Lorran, da SHIELD Cibersegurança, aqui de Ariquemes.
> Eu acompanho o site do laboratório desde maio, quando reportei alguns arquivos
> de configuração que estavam expostos publicamente. Fui conferir de novo ontem:
> **vocês corrigiram tudo** — parabéns, pouca gente resolve isso.
> Nessa nova passada sobraram três coisas que valem uma conversa de 10 minutos:
> faltam alguns cabeçalhos de proteção no site, o formulário de contato coleta
> nome e telefone sem aviso de privacidade, e o portal de resultados precisa de
> uma checagem com o fornecedor. Montei um laudo de 3 páginas. Te mando sem custo?

**Por que essa abordagem funciona:** confirma em 5 segundos que somos o cara que
já reportou antes (não é spam), elogia o que foi corrigido (gera rapport, abordagem
consultiva), e entrega um laudo novo com a data de hoje — sem mentir.

---

## 7. BALANÇO HONESTO (leia antes de ligar)

O gancho forte de maio — arquivo de configuração e credencial expostos na internet
— **não existe mais**. Ele foi corrigido. Quem tentar vender em cima disso hoje
vai ser desmentido na hora.

O que sobra é real, mas é mais fraco: cabeçalhos de segurança ausentes (item 3.4),
endpoints internos descobríveis (3.2), bibliotecas antigas (3.5) e a necessidade de
due diligence com os fornecedores (3.3). Nada disso é "você foi invadido".

Traduzindo em estratégia:
- **São Francisco hoje é uma venda de consultoria/adequação, não de emergência.**
  Ticket menor, decisão mais lenta.
- O valor deste trabalho não está no tamanho do achado: está em você chegar com
  informação **correta e datada de hoje**, incluindo o elogio pelo que foi
  corrigido. Isso é o que separa a SHIELD de quem manda spam de "seu site tem
  vulnerabilidades".
- Os leads de MAIO deste mesmo laboratório provavelmente foram esfriados por um
  laudo apocalíptico seguido de silêncio. Agora existe uma segunda conversa
  legítima: "vocês resolveram; olha o que sobrou". Isso reabre porta fechada.

Antes de ligar, reconferir em 2 minutos se algum item mudou (script
`shield/recon_sao_francisco.py` roda inteiro de novo e regenera o JSON).
