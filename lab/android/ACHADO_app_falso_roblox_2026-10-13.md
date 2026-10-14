# ACHADO — APP REPACKAGED SE PASSANDO POR ROBLOX EM LOJA PÚBLICA

**Pesquisador:** Lorran Gustavo — LIBERTUS / SHIELD Cibersegurança
**Data:** 13/10/2026
**Origem:** detecção acidental durante pipeline de análise Android (buscávamos o APK oficial)
**Método:** 100% análise estática de artefato público. Nada foi executado, nada foi instalado.
**Pacote:** `com.roblox.client` · versão declarada `1010.0-wv` · código `1010`
**Distribuição observada:** Aptoide (link de download público via API da própria loja)
**SHA-256 do artefato:** _(ver `analise.json` no diretório da análise)_

---

## 1. RESUMO

O arquivo analisado se declara **`com.roblox.client`** (o identificador oficial do
app da Roblox) mas **não é o cliente da Roblox**. É um invólucro WebView genérico
— o próprio `BuildConfig` se identifica como `FLAVOR = "wv"` ("webview") — cuja
única função é carregar uma página de monetização por afiliado.

| Fato observado | Evidência |
|---|---|
| Só **6 classes** no pacote do app | `search-android-classes` → BuildConfig, LockerConfig, MainActivity, R, SplashActivity, TabsActivity |
| **Zero código nativo** (nenhum `.so`) | inspeção do conteúdo do APK |
| **Zero funcionalidade Roblox** | nenhuma classe, string ou recurso da Roblox no APK |
| Apenas **2 domínios** no APK inteiro | `play.google.com` (link de avaliação) e `mobi4games.com` |
| Única tela = WebView apontando para oferta de afiliado | `MainActivity.loadStartUrl()` → `LOCKER_URL` |

```java
// LockerConfig.java — a "configuração" inteira do app
LOCKER_URL = "https://mobi4games.com/mts/?month=oct2026&aff_sub4=" + strLastSegment + "&aff_sub5=dga";
SUB5 = "dga";
```

`aff_sub4` / `aff_sub5` são parâmetros de rastreio de afiliado. O `aff_sub4` é
preenchido com o último segmento do application id — neste caso, a palavra
`client`, tirada de `com.roblox.client`.

---

## 2. PARA ONDE O APP MANDA O USUÁRIO

Cadeia observada (só o primeiro salto — parei aqui de propósito):

```
app "Roblox" (com.roblox.client)
   └─> https://mobi4games.com/mts/?month=oct2026&aff_sub4=client&aff_sub5=dga
          título: "Loading..." · sem formulário · sem marca Roblox
          carrega script de rastreio: https://mobi4games.com/st/public/t.js
          └─> https://appsave.online/cl/i/lnxlw     <-- destino da oferta
```

Sobre `mobi4games.com`: domínio registrado em **30/06/2021**, expira em
**30/06/2027**, servindo por nameservers próprios (`NS1/NS2.MOBI4GAMES.COM`). A
página respondeu **200** com `text/html`, 3.703 bytes, `last-modified`
**25/09/2026** (mantida ativamente).

**O que eu NÃO fiz:** não fui além do primeiro salto. `appsave.online` é uma página
de oferta/instalação, e perseguir essa cadeia significaria baixar artefatos cuja
natureza eu não controlo. Caracterizar o encaminhamento já é suficiente para o
achado; entrar na oferta seria risco sem ganho.

---

## 3. POR QUE ISSO IMPORTA (e o que não é)

**O que é:** uso indevido do identificador de pacote de terceiro para distribuir
um app de monetização. Quem procura "Roblox" numa loja alternativa instala algo
que se identifica como Roblox, ocupa a tela com uma WebView e empurra o usuário
para uma cadeia de ofertas de terceiros. Não há Roblox no app — há o **nome** da
Roblox.

**O que agrava:** a configuração da WebView nesse app:

| Configuração encontrada | Valor | Por que importa |
|---|---|---|
| `setJavaScriptEnabled` | `true` | esperado em WebView, mas junto com o resto… |
| `setMixedContentMode` | **`0` = MIXED_CONTENT_ALWAYS_ALLOW** | aceita recurso HTTP dentro de página HTTPS — permite injeção/downgrade no conteúdo que o usuário vê |
| `setAcceptThirdPartyCookies` | `true` | rastreio entre sites dentro de um app rotulado Roblox |
| `android:usesCleartextTraffic` | `true` | tráfego sem TLS permitido no manifesto |
| `setDatabaseEnabled` + `setDomStorageEnabled` | `true` | armazenamento local ativo |

Ou seja: o conteúdo servido por um terceiro (`mobi4games.com` → `appsave.online`)
é renderizado dentro de um app que o usuário acredita ser a Roblox, em uma WebView
que **aceita conteúdo não criptografado**. Quem controla aquela cadeia controla o
que aparece na tela do usuário.

**O que NÃO é (para não inflar):** não há formulário, não há marca Roblox na
página e não há coleta de credencial no trecho que analisei. Não é phishing de
login comprovado. É apropriação de identidade + redirecionamento de monetização.

**O que eu não posso afirmar:** o conteúdo das telas seguintes da cadeia de
oferta. Parei no primeiro salto, conforme declarado acima.

---

## 4. ENCAMINHAMENTO

1. **Aptoide** — o app viola política da loja ao usar identificador de pacote de
   outra publicadora. Caminho: denúncia de app / violação de propriedade
   intelectual. Evidência: package, versão, hash, e o código do `LockerConfig`.
2. **Roblox** — abuso de marca e de identificador de pacote atingindo usuários
   deles. Caminho: canal de segurança/trust & safety da Roblox. **Expectativa
   calibrada:** o programa de bug bounty da Roblox cobre ATIVOS da Roblox; um app
   falso em loja de terceiros provavelmente não é elegível a recompensa. Vale
   enviar mesmo assim — é informação que eles tratam, e serve de portfólio.
3. **Registro para reuso:** este caso é o modelo de um serviço vendável — ver
   `shield/PRODUTO_BRAND_PROTECTION.md`.

---

## 5. O QUE ESTE CASO VALIDOU (o pipeline funcionou)

A detecção saiu de um pipeline construído hoje, do zero, nesta máquina:

```
APK público
  ├─ apktool 3.0.3 ............. decodifica recursos e manifest
  ├─ jadx 1.5.6 ................ reconstrói o código
  ├─ jadx-headless-mcp 0.7.1 ... engine que o REA consome (SHA-256 conferido)
  ├─ REA 6.4.0 ................. inventário, classes, decompilação de método,
  │                              tudo com registro de Evidence (hash + endereços)
  └─ analise_apk.py ............ camada própria: componente exportado, deeplink,
                                 permissão perigosa, flag de manifest, padrão de risco
```

Tempo medido: inventário do pacote em **7,3 s**; busca de classes em **7,5 s**;
decompilação de um método em **1,4 s**. O achado veio da decompilação de um único
método (`MainActivity.onCreate`) — não de força bruta.

**Lacuna honesta que continua aberta:** obter o APK **oficial atual** por script.
APKMirror bloqueia (Cloudflare), APKPure devolve 403, Uptodown não expõe link no
DOM, Aptoide serve versão obsoleta, e `apkeep` exige `libssl-dev` (sudo). O que se
resolve com uma linha — ver `shield/ESTADO_PIPELINE_ANDROID.md`.
