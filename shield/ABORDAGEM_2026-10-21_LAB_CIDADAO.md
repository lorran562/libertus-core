# PACOTE DE VENDA — LABORATÓRIO CIDADÃO (Ariquemes/RO)
**Verificado por LIBERTUS em 21/10/2026, 13h10 (-05)**

Alvo: **Laboratório Cidadão Ariquemes** · `exameslaboratoriocidadao.com.br`
Canal escrito: WhatsApp (69) 99294-6971 · e-mail `labcidadao@gmail.com`
Vertical: laboratório de análises clínicas → **dado de saúde = LGPD art. 5º, II
(categoria especial)**, a multa mais alta por dado tratado.

## Por que este é o lead que dá dinheiro

Não é "falta de header". É o paciente digitando **código e senha de acesso ao
resultado do exame** numa página **sem HTTPS**, e o endereço seguro do site
entregando o **painel de login do servidor** no lugar do laboratório. Os dois
fatos são verificáveis pelo dono em 30 segundos, no celular dele.

## Achados (todos reverificados hoje, com requisição direta)

### 1. ALTO — Código e senha de resultado do exame trafegam sem criptografia
- `http://exameslaboratoriocidadao.com.br/` → **200**, e **não redireciona** para HTTPS.
- A página inicial (servida em HTTP) contém o formulário de resultados:
  `<form method="post" action="https://portal.worklabweb.com.br/resultados/1157">`
  com os campos `tbCodigo` e `tbSenha`.
- Ou seja: a **página** onde o paciente digita o código e a senha do exame é
  entregue sem TLS. Em Wi-Fi público (lanchonete, aeroporto, hospital, rede
  aberta de terceiro) esses campos trafegam legíveis.
- LGPD: dado de saúde + credencial de acesso a dado de saúde. Art. 46 (medidas
  de segurança) e art. 5º, II.

### 2. ALTO — O endereço HTTPS do laboratório entrega o painel do provedor
- `https://exameslaboratoriocidadao.com.br/` → 303 → `/login.php` → 303 →
  `/login_up.php` → **200, título "Plesk Obsidian 18.0.80"**.
- O paciente que digita `https://` vê **tela de login do painel de hospedagem**,
  não o site do laboratório. Exposição de superfície administrativa do servidor
  na raiz do domínio, além do dano de imagem.

### 3. MÉDIO — Certificado do servidor não é do domínio
- Certificado apresentado no 443: `CN = *.hospedagemdesites.ws`
  (GlobalSign AlphaSSL, válido até 28/11/2026). Não cobre o domínio do
  laboratório → aviso de segurança no navegador do paciente.

### 4. MÉDIO — Canal de contato em Gmail para dado de saúde
- Único e-mail no site: `labcidadao@gmail.com`. Não é achado técnico, é
  governança: canal pessoal para dado sensível, sem registro de operador.

## O que NÃO dizer (para não perder credibilidade)

- Não dizer "seu site foi invadido". Não houve invasão observada — foi
  observação pública.
- Não dizer "seus exames vazaram". Não há evidência de vazamento; há **risco**
  de interceptação. Exagerar aqui é mentira que o cliente desmente.
- Não cobrar por "achado de header". O que se vende aqui é a **exposição de
  credencial de paciente em canal aberto** e o **endereço seguro fora do ar**.

## Mensagem de abertura — WhatsApp (copiar e colar)

> Bom dia, tudo bem? Aqui é o Lorran, da SHIELD — cibersegurança aqui em Ariquemes.
>
> Conferi hoje de manhã o site do Laboratório Cidadão olhando só o que qualquer
> navegador vê, nada invasivo, e achei duas coisas que valem sua atenção:
>
> 1) O site abre sem o cadeado (http). E é justamente nessa página que fica o
> campo onde o paciente digita o código e a senha pra ver o resultado do exame.
> Numa rede Wi-Fi pública, esse código e essa senha passam sem proteção nenhuma.
> É dado de saúde, a categoria mais sensível da LGPD.
>
> 2) Quando alguém digita https://exameslaboratoriocidadao.com.br não abre o
> laboratório: cai na tela de login do painel do seu provedor de hospedagem.
> O paciente vê uma tela de servidor no lugar do site de vocês.
>
> Montei um laudo curto, de 4 páginas, com o que achei e o passo a passo pra
> resolver. Te mando sem custo, só pra você avaliar? Posso mandar aqui mesmo.

## Mensagem de abertura — e-mail (se o WhatsApp não responder em 2 dias)

Assunto: `Site do Laboratório Cidadão — código de resultado de exame sem proteção`

> Olá, bom dia.
>
> Meu nome é Lorran, sou analista de segurança da informação aqui em Ariquemes
> (SHIELD). Faço análise apenas com informação pública — o que qualquer
> navegador enxerga — e não acesso nada interno sem autorização.
>
> Ao conferir o site de vocês hoje encontrei dois pontos:
>
> 1. A página inicial é servida em HTTP (sem cadeado). Nela está o formulário
>    onde o paciente informa código e senha para consultar o resultado do
>    exame. Em rede Wi-Fi pública, esses dados trafegam sem criptografia.
>    Como se trata de dado de saúde (LGPD art. 5º, II), o risco jurídico é o
>    mais alto da lei.
> 2. O endereço com https:// não abre o site: entrega o painel de login do
>    provedor de hospedagem (Plesk). Testei agora, 21/10/2026, às 13h10.
>
> Preparei um laudo de 4 páginas com os achados, a exposição legal e a ordem de
> correção. Envio sem custo — basta responder este e-mail.
>
> Lorran Gustavo — SHIELD Cibersegurança, Ariquemes/RO

## Oferta (quando ele responder)

1. **Diagnóstico Express + Laudo LGPD — R$ 497** (o laudo que ele já viu de
   graça vira o documento formal com nome da empresa, severidade e plano).
2. **Correção técnica — a combinar** (forçar HTTPS com redirect 301, corrigir
   vhost/certificado, tirar o Plesk da raiz do domínio). Faixa realista:
   R$ 400–900 dependendo do acesso à hospedagem.
3. **Escudo Mensal — R$ 297/mês** (verificação mensal + alerta de certificado
   vencendo + WhatsApp direto). Este é o que paga as contas.
