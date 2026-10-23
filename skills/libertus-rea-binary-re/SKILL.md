---
name: libertus-rea-binary-re
description: "Reverse binaries/firmware with REA + Ghidra here."
version: 1.0.0
author: LIBERTUS
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [reverse-engineering, ghidra, binwalk, firmware, mcp, rea, decompile]
    related_skills: [firmware-analysis, native-mcp, hermes-agent]
---

# REA no LIBERTUS (integração local)

## When to Use

- Analisar um binário/artefato JÁ COMPILADO (ELF, PE, ASAR/Electron, APK,
  firmware, WASM, EVM, SQLite) — não código-fonte.
- Precisa de decompilação/pseudocódigo, xrefs, strings, call graph ou PGP de
  função: REA + Ghidra é o caminho aqui.
- Investigar firmware/roteador além da extração: pegar binário ARM/MIPS do
  rootfs e provar comportamento.
- Comparar duas versões de um app empacotado.
- Perguntas do tipo "como esse app faz X?" quando só existe o artefato.

Não use: análise de repositório-fonte normal (git/grep/leitura de código), nem
quando a resposta já está em código disponível.

Este skill é a camada LOCAL do REA (morluto/rea) na máquina do Lorran: caminhos,
variáveis, o que já está pronto e as armadilhas medidas. O workflow genérico de
investigação (roteamento por tipo de alvo, Evidence, contratos) é do skill que o
próprio REA instala em `~/.hermes/skills/reverse-engineer-anything/` — leia esse
para decidir COMO investigar; use este para saber O QUE funciona aqui.

**Regra dura:** não editar `~/.hermes/skills/reverse-engineer-anything/` à mão —
`rea setup` reescreve esse diretório e apaga customização. Conhecimento local
vive AQUI.

## O que já está instalado e verificado (13/10/2026)

| Peça | Caminho / estado |
|---|---|
| CLI `rea` 6.4.0 (npm global) | `~/.hermes/node/bin/rea` |
| MCP no Hermes | `mcp_servers.rea` em `~/.hermes/config.yaml` com `env:` já preenchido |
| Ghidra 12.1.4 | `~/tools/ghidra_12.1.4_PUBLIC` (`GHIDRA_INSTALL_DIR`) |
| JDK 21 Temurin (full, com javac) | `~/tools/jdk-21.0.12.1+1` (`JAVA_HOME`) |
| Binwalk 3.1.0 (Rust, ReFirmLabs) | `~/.cargo/bin/binwalk` (`REA_BINWALK_COMMAND`) |
| Binwalk 2.4.3 OSPG (fork antigo) | `~/.local/bin/binwalk` — **REA NÃO aceita** (ver armadilhas) |
| Python do venv LIBERTUS | `~/LIBERTUS/venv/bin/python3` |

Env exportado em `~/.bashrc` (bloco `# ==== REA / Ghidra ====`) e também dentro do
`env:` do registro MCP — o servidor MCP roda como filho do gateway e **não herda**
seu shell, por isso a duplicação é intencional.

## Comandos de verificação

```bash
export PATH="$HOME/.hermes/node/bin:$PATH"   # se o shell não for interativo
rea --version
rea doctor --client hermes --json      # registro MCP + skill
rea doctor --provider ghidra --json    # engine de decompilação
```

Sucesso esperado no doctor: `ghidra`, `ghidra-version` (12.1.4), `ghidra-installation`,
`ghidra-headless`, `ghidra-native_decompiler`, `ghidra-java` todos OK.
Falhas de `registration:claude_code` / `claude_desktop` / `hopper` / `ida` são ruído:
são clientes/engines que não usamos.

## Uso (CLI, testado)

```bash
# overview com decompilação via Ghidra
rea analyze /caminho/alvo --provider ghidra --json

# procurar funções (retorna lista em normalized_result)
rea search /caminho/alvo . --kind procedures --mode regex --provider ghidra --json

# decompilar pelo endereço observado
rea decompile /caminho/alvo 0x101000 --provider ghidra --json

# regiões de firmware (exige REA_BINWALK_COMMAND)
rea inspect-firmware-regions firmware.trx --json
```

As respostas são registros de Evidence: `evidence_id`, `normalized_result`,
`limitations`, `locations`. **Sempre leia `limitations`** e cite o `evidence_id` —
é a assinatura de honestidade do REA (observação ≠ inferência ≠ desconhecido).

## Armadilhas medidas (não repetir)

1. **Cada chamada CLI re-importa o binário.** O projeto Ghidra é efêmero
   (`-readOnly -deleteProject`), então `analyze` + `search` + `decompile` = 3
   imports. Medido: ELF pequeno (`/bin/true`) ≈ 14 s por chamada; busybox ARM
   32-bit de 417 KB ≈ 44 s. Para investigação multi-etapa, use a sessão MCP
   (uma sessão, um import) em vez de encadear CLI.
2. **Ferramentas MCP só aparecem depois de reiniciar a sessão.** O Hermes lê
   `mcp_servers` na partida; registrar no meio da conversa não injeta as 170
   tools na sessão viva. Verificação barata sem reiniciar: rodar o handshake
   (`rea mcp` + `initialize` + `tools/list`) ou usar o CLI.
3. **Binwalk 2.x NÃO é aceito.** O REA exige Binwalk 3.1.x (o fork Rust) ou
   Unblob 26.6.x, por linha de major.minor. O binwalk do OSPG (2.4.3) que já
   existia nesta máquina falha com
   `code: execution_failure` mesmo com `REA_BINWALK_COMMAND` apontando para ele.
   Use `REA_BINWALK_COMMAND=$HOME/.cargo/bin/binwalk`.
4. **`capability_unavailable` sem a variável.** `inspect-firmware-regions` exige
   caminho ABSOLUTO: sem `REA_BINWALK_COMMAND` ele nem tenta, devolve
   `requires Linux and an absolute REA_BINWALK_COMMAND path`.
5. **Ferramentas que não precisam de engine** (funcionam mesmo com Ghidra fora):
   JavaScript/Electron/ASAR, SQLite, WASM, EVM bytecode, PE resources, archives,
   `inspect_binary_layout` (offline ELF — exige pwntools via
   `REA_PWNTOOLS_PYTHON`), Android (exige apktool/JADX próprios).
8. **Docs do repo main ≠ pacote npm.** `docs/go-binaries.md` e
   `docs/rust-binaries.md` do GitHub descrevem `inspect_go_binary` /
   `inspect_rust_binary`, mas o 6.4.0 publicado **não** expõe essas tools
   (confirmado em `tools/list` e no `dist/`). O próprio skill do REA avisa:
   "a skill installed from repository main may describe capabilities absent
   from an older npm release". Confira capacidade contra `tools/list` do seu
   servidor, nunca contra a doc do main.
6. **`rea setup` não instala Java, Ghidra, binwalk nem nada.** Ele só registra e
   grava env. Instalar engine continua sendo trabalho manual (foi o que fizemos).
7. **Sudo não é opcional-por-acaso:** esta máquina pede senha de sudo, então
   engine e JDK foram para `~/tools` por tarball, nunca por apt.

## Como reconstruir o Binwalk 3.1 sem sudo (receita verificada)

O `cargo install binwalk` puro **falha** nesta máquina: `plotters` → `font-kit`
→ `yeslogic-fontconfig-sys` chama `pkg-config` e exige `libfontconfig1-dev`
(ausentes; `sudo apt` pede senha). Saída: a crate tem escape de dlopen.

```bash
RUST_FONTCONFIG_DLOPEN=1 ~/.cargo/bin/cargo install binwalk --version 3.1.0 --locked
~/.cargo/bin/binwalk --version    # precisa imprimir: binwalk 3.1.0
```

`RUST_FONTCONFIG_DLOPEN` faz o build pular o probe de link e dlopnar a
fontconfig em runtime. Build levou ~1m15s. Se um dia o tarball binário oficial
existir, prefira ele — o REA só confere o banner de versão (`3.1.x`).

## SquashFS: detectar ≠ validar (medido 21/10/2026)

O binwalk (v2 **e** v3) serve para **localizar** SquashFS, não para validar.
O v2 decide com 4 bytes de magic + `s_major`/`s_minor` (1..10) + id de
compressão (1..6): aceita um falso positivo de 10 bytes e esconde assinatura
válida quando `bytes_used` estoura o arquivo (visível só com `-I`). Regras,
matriz de 8 casos medidos e armadilhas (LZO rotulado como "gzip non-standard",
`{jump}` do UBI escondendo o interior, magic de vendor) em
`references/squashfs-deteccao-e-validacao.md`.

Validador sem dependência do binwalk: `python3 ~/LIBERTUS/scripts/sqfs_probe.py <arquivo>`
— checa superblock como o `read_super` do squashfs-tools, valida o primeiro
bloco de metadados da inode/id table e imprime `dd` + `unsquashfs` prontos.

## TRX/HDR0: o v3 valida CRC, o v2 não (medido 23/10/2026)

Em TRX o v3 **é** validador estrutural: ele só aceita a assinatura se o dry-run
de extração passar, e o dry-run exige o CRC. O v2 lista qualquer coisa com
`HDR0` + versão 1/2, inclusive imagem com 1 byte corrompido ou `len` mentindo.

O CRC é **CRC-32/JAMCRC** (init 0xFFFFFFFF, **sem** xorout final) sobre
`[0x0C, len)` — não é o `zlib.crc32` e não começa em 0x1C. TRXv2 ainda exige a
máscara de 8 bytes em `offsets[3]+22` (contadores do bin header → 0xFF) antes de
calcular; o v3 **não** aplica essa máscara, então rejeita TRXv2 bem construído
(falso negativo medido em sintético). Matriz de 12 casos, fontes do trx.c e do
`trx.rs`, e o caso dos blobs `brcmfmac*.bin` (mesmo HDR0+JAMCRC, offsets de
outro formato) em `references/trx-crc-e-validacao.md`.

Ferramenta: `python3 ~/LIBERTUS/scripts/trx_probe.py firmware.trx` (veredito +
candidatos de CRC) e `--fix` para recalcular `crc32`/`len` in-place (testado em
firmware real de 9.5 MB com byte corrompido: v3 voltou a listar).

## Verificação end-to-end (rode isto depois de mexer)

`scripts/verify-rea-mcp.py` (neste skill) sobe o servidor MCP **com o env exato
do registro** e checa com asserts: registro no config, handshake, 170 tools,
chamada real de `inspect_firmware_regions` no TRX do ASUS, `open_binary` +
`binary_overview` via Ghidra num ELF, e `binary_session`. Precisa de PyYAML:
rode com `~/LIBERTUS/venv/bin/python3`. Resultado esperado: `TODOS OS CHECKS
PASSARAM` (exit 0).

## Análise de site/app web com REA (recon passivo de verdade)

O REA não aceita URL solta: ele observa um navegador via CDP. Receita verificada
(13/10/2026, alvo: saofranciscorondonia.com.br):

```bash
# 1. navegador headless com CDP (background=True no terminal do Hermes)
rm -rf /tmp/rea-chrome && mkdir -p /tmp/rea-chrome
google-chrome --headless=new --remote-debugging-port=9222 --no-first-run \
  --user-data-dir=/tmp/rea-chrome "https://ALVO/"

# 2. alvos (endpoint é POSICIONAL, não existe --endpoint)
rea list-browser-targets http://127.0.0.1:9222 --json

# 3. bundle estático: o que realmente acha coisas
rea analyze-web-bundle http://127.0.0.1:9222 <targetId> --fetch-source-maps --json

# 4. observação da página: storage, console, formas de JSON
rea inspect-web-page http://127.0.0.1:9222 <targetId> --observation-ms 3000 \
  --include-console-text --include-json-body-shapes --include-storage-keys --json
```

Para encerrar sem se matar: `pkill -f "remote-debugging-por[t]=9222"` — o padrão
SEM o truque do colchete casa com o próprio shell e mata o comando.

**O que o `analyze-web-bundle` entrega que grep no HTML não entrega:** ele baixa
todos os scripts, tira SHA-256 de cada um, percorre a AST (no teste: 77.359 nós em
10 scripts) e devolve um registro de Evidence com `capture`, `observations`,
`inferences`, `unknowns`, `completeness` e `limitations`. No alvo testado ele
extraiu endpoints AJAX internos que estavam em texto claro dentro do JS publicado
(`/_src/components/v1/inc/ajax/*.php`) — num diretório que o `robots.txt` do
próprio site tentava esconder. Achado real, verificável e datado, impossível de
provar com um scan de cabeçalhos.

**Limite que não se cruza:** os endpoints descobertos NÃO são chamados. Apontar a
existência é observação; acessar é teste, e teste exige autorização escrita. Isso
não é frescura: é o que mantém o achado válido como peça de venda em vez de virar
problema jurídico.

## Atualizar

```bash
rea upgrade                                   # atualiza o pacote npm global
rea setup --client hermes --yes --json        # re-registra MCP + skill do REA
# antes de aplicar, revise: rea setup --client hermes --dry-run --json
```

`rea setup` preserva o resto do `config.yaml` e faz backup em
`~/.hermes/config.yaml.rea.backup`. Mesmo assim, copie o config antes.

## Sinergia com o fluxo de firmware que já existe

O pipeline `firmware-analysis` (TRX→UBI→SquashFS com binwalk OSPG + ubireader)
continua sendo o extrator. O REA entra DEPOIS e em paralelo: pegar um binário
ARM/MIPS já extraído do rootfs e **decompilar com Ghidra** para provar
vulnerabilidade (ex.: NVRAM Broadcom, scripts de init, binários de `sbin/`).
Exemplo real validado: `busybox` ARM 32-bit extraído de
`~/LIBERTUS/lab/firmware/asus-rt-ac88u/extracted/rootfs/bin/busybox`
→ `rea analyze ... --provider ghidra --json` retornou 4 segmentos
(`0x10000`–`0x7a508`, `EXTERNAL` incluído) em 44 s.
