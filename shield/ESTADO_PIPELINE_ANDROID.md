# ESTADO DO PIPELINE ANDROID (13/10/2026, madrugada)

> Escrito pelo LIBERTUS enquanto o Lorran estava fora. Objetivo: ele conseguir
> continuar sem precisar lembrar nada e sem achar arquivo no terminal —
> abrir este link e ler.

## 1. O QUE ESTÁ INSTALADO E VERIFICADO

| Peça | Versão | Onde | Como foi validado |
|---|---|---|---|
| JDK Temurin | 21.0.12.1 | `~/tools/jdk-21.0.12.1+1` | `java -version` + usada pelo Ghidra |
| Ghidra | 12.1.4 | `~/tools/ghidra_12.1.4_PUBLIC` | decompilou busybox ARM do roteador ASUS |
| REA | 6.4.0 | `~/.hermes/node/bin/rea` | 170 tools MCP + Android, tudo com Evidence |
| apktool | **3.0.3** | `~/.local/bin/apktool` (wrapper) | decodificou APK real |
| jadx | **1.5.6** | `~/.local/bin/jadx` | extraiu 2.171 arquivos .java de um APK |
| jadx-headless-mcp | **0.7.1** | `~/tools/android/jadx-headless-mcp.jar` | **SHA-256 conferido** contra o publicado |
| analisador próprio | — | `lab/android/analise_apk.py` | rodou e produziu relatório |

Variáveis que o REA exige para Android (ele NÃO instala nada sozinho):

```bash
export REA_APKTOOL_COMMAND=$HOME/.local/bin/apktool
export REA_JADX_MCP_JAR=$HOME/tools/android/jadx-headless-mcp.jar
```

Tempos medidos: inventário do pacote 7,3 s · busca de classes 7,5 s ·
decompilação de um método 1,4 s.

## 2. O ÚNICO BLOQUEIO QUE SOBROU — e a linha que resolve

**Obter o APK OFICIAL ATUAL por script.** Tentei, na ordem:

| Fonte | Resultado |
|---|---|
| APKMirror | bloqueio Cloudflare ("you have been blocked") |
| APKPure (via curl) | HTTP 403 |
| Uptodown | carrega no navegador, mas a lista de versões não fica acessível no DOM |
| Aptoide (API aberta) | funciona, **mas serve versão obsoleta** (foi ali que apareceu o app falso) |
| apkeep (Rust) | **falha de build: falta `libssl-dev`** (precisa de sudo) |
| apktool de dentro do WSL/Play | não aplicável |

**A linha que destrava tudo** (pedir ao Lorran quando ele voltar):

```bash
sudo apt install -y libssl-dev pkg-config
~/.cargo/bin/cargo install apkeep
```

Depois disso, `apkeep` baixa APK por script (APKPure) e o pipeline fica completo
do começo ao fim sem intervenção manual — inclusive **duas versões diferentes**,
que é o que destrava patch diffing de app.

Alternativas se ele preferir não usar sudo:
- instalar Roblox pelo Play no celular dele e `adb pull` (adb não está instalado;
  instala sem sudo)
- baixar o APK no Firefox dele e jogar em `~/LIBERTUS/lab/android/roblox/`

## 3. O QUE FOI PRODUZIDO HOJE NESTA FRENTE

1. **Um achado real** — app se passando por Roblox em loja pública, com o app
   decompilado e a cadeia de redirecionamento rastreada até o primeiro salto:
   `lab/android/ACHADO_app_falso_roblox_2026-10-13.md`
2. **Um produto vendável** que nasceu desse achado — monitoramento de marca em
   lojas de app: `shield/PRODUTO_BRAND_PROTECTION.md`
3. **Um analisador reusável** — `lab/android/analise_apk.py`: componentes
   exportados, deeplinks, permissões perigosas, flags de manifesto inseguras e
   padrões de risco no código
4. **A cadeia inteira documentada** no skill `libertus-mobile-apk-re`

## 4. PRÓXIMO PASSO (na ordem)

1. Rodar a linha do `apt` acima → completar o pipeline
2. Baixar 2 versões do app alvo → rodar `analise_apk.py` nas duas → comparar
3. Antes de qualquer teste contra infraestrutura: ler a política do programa
   (exigências da Roblox: tag `hackeronetest-<userid>` no user-agent, conta própria,
   sem scan de cabeçalho/SSL — está fora de escopo e não paga)
4. Reportar o app falso: Aptoide (violação de pacote) + Roblox (abuso de marca)

## 5. ONDE NÃO IR MAIS

- Não perseguir a cadeia de oferta além do primeiro salto (`appsave.online`) —
  baixar artefato de origem desconhecida é risco sem ganho.
- Não vender nem testar cheat/executor: proibido explicitamente na política da
  Roblox e é o caminho que mata o plano da Irlanda.
- Não tratar achado de cabeçalho/SSL como achado em programa de jogo: está
  listado como fora de escopo.
