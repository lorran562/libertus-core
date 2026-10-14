# LEADS ARIQUEMES — O QUE É REAL (verificado um por um, 13/10/2026)

> Este arquivo é o material de abordagem. Regra dele: só entra o que foi
> **reverificado individualmente** com requisição direta. Falso positivo aqui =
> você perde o lead e a credibilidade na mesma frase.
>
> **Três achados foram RETIRADOS hoje por não se sustentarem.** Estão listados na
> seção 4 pra você não usá-los por engano.

---

## 1. ABORDAGEM MAIS FORTE DA LISTA (não é técnica)

| Empresa | Fato | Por que é a melhor porta |
|---|---|---|
| **Laboratório São José** | **O site está fora do ar.** DNS resolve (`45.167.178.79`, hospedado em `cl-web04.odara.com.br`), mas HTTPS não conecta e HTTP não completa | Não precisa de achado de segurança. "Bom dia, seu site não está abrindo" abre qualquer conversa — e é problema de negócio, não de TI |

---

## 2. ACHADOS TÉCNICOS QUE SE SUSTENTAM

### CEDDI Centro de Diagnóstico — `ceddi.com.br`
- **WordPress detectado**, com `/admin/` e `/wp-login.php` acessíveis (200).
  **Não é vulnerabilidade por si só** — é a tela de login padrão do WordPress.
- **O que dá venda aqui não é o login: é o contexto.** É centro de diagnóstico —
  dado de saúde é categoria especial na LGPD (art. 5º, II). A conversa certa é
  adequação e responsabilidade do controlador, não "seu site está invadido".
- **Verificado:** WordPress presente · TLS OK · sem achado explorável observado
  sem autorização.

### AD Imóveis — `adimoveisro.com.br`
- **WordPress detectado** (`/admin/` e `/wp-login.php` = 200), mesma leitura do CEDDI.
- **Verificado:** sem arquivo sensível exposto; sem achado explorável passivo.

### Marques Imóveis — `marquesimoveisro.com.br`
- **Endpoint `/config` devolve página de erro da aplicação em JSON**, com detalhe
  interno exposto: `"Curl failed with error #22: The requested URL returned error: 401 Unauthorized"`.
  Severidade **BAIXA** (vazamento de detalhe de erro). **Não** é arquivo de
  configuração exposto — a leitura correta é essa, e é o que você deve dizer.
- TLS **1.2** (o resto da lista está em 1.3).
- Cabeçalhos de segurança ausentes: HSTS, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy.
- **Verificado:** redireciona HTTP→HTTPS corretamente (301).

### Bruni Imóveis — `bruniimoveis.com.br`
- **Único da lista que serve conteúdo por HTTP sem redirecionar.** `http://` devolve
  200 com a página inteira, em texto claro.
- O formulário do site já posta em `https://` e **não tem campo de senha** — então
  o risco não é roubo de credencial, é **manipulação de conteúdo por quem estiver
  no meio do caminho** (rede Wi-Fi, provedor, proxy). Severidade **BAIXA-MÉDIA**.
- Cabeçalhos ausentes: os mesmos 6.

### Oikos Assessoria — `oikosassessoria.com.br`
- Site rodando em **Wix**. Redireciona HTTP→HTTPS corretamente.
- Sem achado técnico explorável observado passivamente.
- **Leitura honesta:** se a plataforma é Wix, quase nada que aparecer é do cliente
  — ele não controla. Vender correção aqui é vender o que ele não pode fazer.

### Imobiliária Aislan Santos — `aislansantosimoveis.com.br`
- Redireciona HTTP→HTTPS corretamente. Sem achado explorável observado.
- Cabeçalhos de segurança ausentes (6).

### Laboratório São Francisco — `saofranciscorondonia.com.br`
- **Laudo completo já produzido:** `shield/LAUDO_SAO_FRANCISCO_2026-10-13.md`
- Resumo: as falhas de maio **foram corrigidas**. Hoje: cabeçalhos ausentes,
  CSP fraca (`unsafe-inline`/`unsafe-eval`) com origem de dev vazada
  (`http://w2b-api-v2.localhost`), endpoints internos descobertos no JS público,
  portal de resultados de terceiro sem captcha/CSP.

---

## 3. O QUE ISSO SIGNIFICA NA HORA DE VENDER (leitura fria)

1. **Nenhum dos leads tem "você foi invadido" pra vender.** O gancho forte de maio
   morreu. Quem tentar usar vai ser desmentido.
2. **O que sobrou é honestamente fraco em quase todos:** cabeçalhos ausentes e um
   vazamento de erro. Programa sério de bug bounty (a Roblox, por exemplo) lista
   "cabeçalho ausente sem vulnerabilidade direta" como **fora de escopo** — porque
   não paga mesmo.
3. **Onde há conversa real:** São José (site fora), CEDDI (dado de saúde + LGPD),
   São Francisco (segunda conversa com quem te conhece; laudo pronto).
4. **Onde não há:** Oikos (Wix — ele não controla), Aislan e Bruni (só cabeçalho).
   Abordar esses com achado fraco queima a empresa inteira na cidade.

**Conclusão honesta que eu prefiro te dar agora do que você descobrir no telefone:**
perseguir os 7 leads de Ariquemes com esses achados rende menos que **um** contato
bem feito com o São José (site fora) e **um** com o CEDDI (LGPD + dado de saúde).
Volume de abordagem fraca não compensa ticket baixo — e ainda gasta sua reputação
na cidade onde você vai viver.

---

## 4. ACHADOS RETIRADOS HOJE (não usar — foram desmentidos)

| Retirado | Por quê |
|---|---|
| "Marques: arquivo de configuração exposto" | O `/config` devolve página de erro do app, não arquivo de config. Verificado abrindo o conteúdo |
| "Marques: não redireciona para HTTPS" | **Redireciona (301).** O flag do meu script estava errado; confirmei com requisição direta |
| "São Francisco: coleta dado de paciente no Google Forms" | É **pesquisa de satisfação encerrada**. Não coleta nada. Verificado abrindo o formulário |
| "AD Imóveis / CEDDI: login do WordPress = vulnerabilidade" | É a tela padrão do WordPress. Só vira achado com senha fraca ou plugin vulnerável — e isso exige autorização pra testar |

Os três primeiros foram pegos **antes** de virarem mensagem. Fica o registro
porque o padrão se repete: script acha, **verificação humana desmente**. A etapa
de conferir item por item não é opcional.
