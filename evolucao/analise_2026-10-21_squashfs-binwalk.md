# SquashFS em firmware: o que o binwalk realmente valida (medido, não suposto)

**Data:** 21/10/2026 · **Contexto:** pipeline de firmware (TRX → UBI → SquashFS) dos labs ASUS RT-AC88U e Netgear R7000
**Ferramentas medidas:** binwalk v2.4.3+ce6c706 (fork OSPG, `~/.local/bin`), binwalk 3.1.0 (Rust, `~/.cargo/bin`), squashfs-tools 4.x (`unsquashfs`), `ubireader`

---

## 1. A pergunta

O pipeline atual usa `binwalk` para decidir "isto é SquashFS, em tal offset, com tal tamanho".
Se essa decisão estiver errada, todo o resto (dd → unsquashfs → análise) herda o erro.

Pergunta da noite: **quanto de validação existe de fato atrás da frase "Squashfs filesystem" do binwalk v2 — e onde ela mente?**

Método: 9 imagens construídas com `mksquashfs` (todos os compressores) e mutações cirúrgicas campo a campo, mais 2 firmwares reais do lab. Cada caso rodado nas três ferramentas.

---

## 2. O que o binwalk v2 confere (lido no magic, não deduzido)

`~/.local/lib/python3.12/site-packages/binwalk/magic/filesystems`, regra little-endian:

```
0   string  hsqs  Squashfs filesystem, little endian,
>28 leshort >10   {invalid}        # s_major   (offset 28)
>28 leshort <1    {invalid}
>30 leshort >10   {invalid}        # s_minor   (offset 30)
>28 leshort x     version %d.
>30 leshort x     \b%d,
>28 leshort >3    compression:
>>20 leshort 1    \bgzip,          # compression id (offset 20)
>>20 leshort 2    \blzma,
>>20 leshort 3    \bgzip (non-standard type definition),   <-- ver §4.1
>>20 leshort 4    \bxz,
>>20 leshort 5    \blz4,
>>20 leshort 6    \bzstd,
>>20 leshort 0    \b{invalid},
>>20 leshort >6   \b{invalid},
>28 leshort >3
>>40 bequad  x    size: %ld bytes,   # bytes_used (offset 40) só no v4
```

Tradução: **4 bytes de magic + s_major/s_minor em 1..10 + id de compressão em 1..6. Mais nada.**
`block_size`, `block_log`, `bytes_used` coerente com o arquivo, `id_table_start`, `root_inode`: não são checados.

O `{size:%d}` é "smart keyword": se o valor passado em `{size:%d}` estoura o arquivo, o binwalk **marca a assinatura como inválida e a esconde** (aparece só com `-I`).

---

## 3. Matriz medida

Legenda: ✅ detecta/aceita · ❌ rejeita · ⚠️ aceita errado (rótulo ou plausibilidade)

| caso (mutação) | binwalk v2 | binwalk v3 | `unsquashfs` extrai? | `sqfs_probe.py` |
|---|---|---|---|---|
| v4 xz (normal) | ✅ | ✅ | ✅ | ✅ VALIDO |
| v4 gzip / zstd / lz4 | ✅ | ✅ | ✅ | ✅ VALIDO |
| v4 lzo | ⚠️ rotula "gzip (non-standard type definition)" | ✅ "lzo" | ✅ | ✅ VALIDO (avisa o rótulo errado) |
| magic de vendor `hsqt` / `shsq` | ✅ | ✅ | ❌ (magic não é `hsqs`) | ✅ VALIDO_magic_vendor + comando de patch |
| `sqlz`/`qshs`/`tqsh` sobre imagem LE | ❌ (lê como big-endian: lixo) | — | ❌ | ❌ INVALIDO (v1024.0) |
| falso positivo: `hsqs` + versão 4.0 + compression=4 (10 bytes) | ⚠️ **"Squashfs ... size: 0 bytes, blocksize: 0"** | ❌ | ❌ | ❌ INVALIDO (5 motivos) |
| s_major = 99 | ❌ invisível (só com `-I`) | ❌ | ❌ | ❌ INVALIDO (v99.0) |
| bytes_used = 0x7FFFFFFF (> EOF) | ⚠️ invisível por padrão, visível com `-I` | ❌ | ❌ | ❌ INVALIDO (além do EOF) |
| block_size=131072, block_log=5 | ⚠️ aceita como normal | ❌ | ❌ ("Block size and block_log do not match") | ❌ INVALIDO (block_log) |

Saídas brutas que sustentam a tabela:

```
$ binwalk fp_min.bin            # 4096 bytes de zeros, só 10 bytes de header forjado
0  0x0  Squashfs filesystem, little endian, version 4.0, compression:xz, size: 0 bytes, 0 inodes, blocksize: 0 bytes, created: 1970-01-01 00:00:00

$ binwalk t7_huge.bin           # bytes_used = 0x7FFFFFFF
(nenhuma linha de squashfs)

$ binwalk -I t7_huge.bin
0  0x0  Squashfs filesystem, little endian, version 4.0, compression:xz, size: 2147483647 bytes, 6 inodes, blocksize: 131072 bytes, ...

$ unsquashfs t5_badlog.bin      # block_log incoerente
FATAL ERROR: Block size and block_log do not match.  File system is corrupt.
```

Duas armadilhas práticas caem daqui:

1. **`unsquashfs -s` não valida.** No caso `t5_badlog` ele imprimiu `Found a valid SQUASHFS 4:0 superblock` e listou os campos; a extração de verdade falhou. `-s` só lê o superbloco.
2. **"não achei SquashFS" ≠ "não tem SquashFS".** `binwalk -I` e busca crua (`binwalk -R '\x68\x73\x71\x73'` ou `grep -abo hsqs`) são obrigatórios antes de concluir ausência.

---

## 4. Três defeitos concretos do v2

### 4.1 O id 3 é LZO, não "gzip non-standard"

Em SquashFS **v4** os ids são: 1 gzip, 2 lzma, 3 **lzo**, 4 xz, 5 lz4, 6 zstd.
A string `gzip (non-standard type definition)` é herança do SquashFS 3.x (onde o id 3 significava outra coisa) e ficou no magic do v2. Confirmado:

```
$ binwalk img_lzo.sqfs
0  0x0  Squashfs ... compression:gzip (non-standard type definition), size: 200361 ...
$ unsquashfs -s img_lzo.sqfs
Compression lzo
$ ~/.cargo/bin/binwalk img_lzo.sqfs     # v3
SquashFS file system, ... compression: lzo, inode count: 6, block size: 131072, image size: 200361
```

Consequência: se o relatório diz "gzip non-standard" numa imagem v4, é **LZO** — e a extração precisa de `unsquashfs` com LZO compilado (não é o caso de um binário sem `liblzo2`).

### 4.2 Falso positivo com 10 bytes

`hsqs` + `s_major=4` + `s_minor=0` + `compression=4` e o resto zeros → o v2 chama de SquashFS. O v3 tem um *parser* (`src/signatures/squashfs.rs`) que, além do header, exige:

- `image_size <= available_data`;
- que `id_table_start` aponte para dentro da imagem **e** que o primeiro `u64` desse índice seja um ponteiro plausível;
- (aí sim) o bloco de metadados do UID.

Por isso o v3 rejeita o caso de 10 bytes. Não é "v3 mais moderno por moda": é validação estrutural.

### 4.3 `{jump}` de container esconde o conteúdo — o caso UBI

No firmware real isso morde forte. `magic/filesystems`:

```
0 string UBI\x23 UBI erase count header, ...
>20      ubyte  x  {jump:0}      # dummy jump - valor real vem do UBIValidPlugin
```

e `plugins/ubivalid.py`:

```python
if self.peb_size:
    result.jump = self.peb_size     # salta um PEB inteiro (EC header -> EC header)
```

Ou seja: achou um EC header válido (CRC sobre os 60 primeiros bytes, guardado em `[60:64]`), o binwalk **salta de erase block em erase block** e nunca varre o miolo dos PEBs — exatamente onde ficam os volumes UBI.

Medido no firmware real (ASUS RT-AC88U, build OpenWrt):

```
$ binwalk asus_rt-ac88u-openwrt.trx | grep -ci squashfs
0
$ binwalk -R '\x68\x73\x71\x73' asus_rt-ac88u-openwrt.trx
4460544  0x441000  Raw signature (\x68\x73\x71\x73)
$ grep -abo hsqs asus_rt-ac88u-openwrt.trx
4460544:hsqs
```

Existe um SquashFS em 0x441000 e o scan padrão do v2 não mostra. Não é bug de versão do magic: é o modelo "interpretador de containers" funcionando como projetado.

---

## 5. O que o `unsquashfs` valida (a régua de verdade)

`read_fs.c` → `read_super()`:

- `s_magic == 0x73717368`;
- `s_major == 4` e `s_minor <= 0`;
- compressor suportado pelo binário;
- `block_size <= SQUASHFS_FILE_MAX_SIZE` e `block_log <= SQUASHFS_FILE_MAX_LOG`;
- `block_size >= 4096`;
- **`block_size == (1 << block_log)`**;
- `bytes_used >= 0`;
- `xattr_id_table_start`, `id_table_start`, `lookup_table_start` dentro de `bytes_used`.

Depois disso ainda valida inode table, diretórios, id table — é por isso que imagem "válida no superbloco" pode morrer na extração.

---

## 6. Caso real: SquashFS dentro de UBI não é SquashFS extraível

No ASUS RT-AC88U do lab: `TRX (LE, v1, header 28 B) → UBI em 0x400000 → volume rootfs.ubifs`.
O `hsqs` em 0x441000 (dentro do volume UBI) passa por **todas** as checagens de superbloco: v4.0, xz, `block_size=262144`, `bytes_used=4730822`, 1339 inodes.

Extraindo e montando:

```
$ dd if=...trx of=real.sqfs bs=1M iflag=skip_bytes,count_bytes skip=4460544 count=4730822
$ unsquashfs -d root real.sqfs
Lseek failed because Invalid argument
read_block: failed to read block @0x34afec2c7f40a833
read_id_table: failed to read id table block
FATAL ERROR: File system corruption detected
```

Motivo: o volume UBI não é contíguo no flash — a cada PEB (128 KiB) existem EC header, VID header e padding no meio do "arquivo". Os offsets internos do SquashFS (relativos ao início do volume) apontam para lixo.

O `sqfs_probe.py` criado nesta sessão **previu exatamente esse endereço de falha** sem extrair nada, lendo o primeiro bloco de metadados da `id_table`:

```
[INVALIDO] offset 4460544 (0x441000)
    v4.0 | xz | block_size 262144 | bytes_used 4730822 | inodes 1339
    ! inode_table legível: tamanho de bloco implausível (8764)
    ! id_table legível: primeiro ponteiro do índice = 0x34AFEC2C7F40A833 (fora da imagem)
```

`0x34AFEC2C7F40A833` é byte a byte o endereço que o `unsquashfs` reclamou depois. Regra: **valide a tabela, não só o header.**

Regra derivada: se o SquashFS está dentro de UBI, extraia o **volume** primeiro (`ubireader_extract_images`), nunca o offset do flash.

---

## 7. Receita verificada nesta máquina

```bash
# 1. binwalk v3 extrai o container UM nível por execução (TRX -> partições)
~/.cargo/bin/binwalk -e firmware.trx
#    extractions/firmware.trx.extracted/0/partition_0.bin  (kernel LZMA)
#    extractions/firmware.trx.extracted/0/partition_1.bin  (UBI image, 5242880 bytes)

# 2. UBI -> volumes
ubireader_extract_images -o out partition_1.bin
#    out/partition_1.bin/img-..._vol-rootfs.ubifs

# 3a. volume UBIFS -> arquivos
ubireader_extract_files -o rootfs out/.../img-..._vol-rootfs.ubifs

# 3b. volume SquashFS -> validar, cortar, montar
python3 scripts/sqfs_probe.py <arquivo_ou_volume>
#    imprime: dd if=... skip=<off> count=<bytes_used> + unsquashfs -d ...
```

Detalhe medido: o v3 **não recursa**. Ele extrai TRX → `partition_*.bin` e para; é preciso rodar de novo em cada partição (foi assim que o UBI apareceu). O v2 faz o contrário: lista tudo que casa, inclusive falso positivo (no ASUS real ele reportou um "JBOOT STAG header" com `image size: 496046238 bytes` no meio do kernel LZMA).

---

## 8. Checklist para o pipeline (o que passa a valer)

1. `binwalk` (v2 ou v3) serve para **localizar**, não para **validar**. Veredito de validade: `sqfs_probe.py` → `unsquashfs` de verdade.
2. Antes de dizer "não tem SquashFS": `binwalk -I` + busca crua (`-R '\x68\x73\x71\x73'`, `grep -abo hsqs`).
3. `bytes_used > tamanho do arquivo` → assinatura escondida: dump truncado ou campo em escala de flash. Ver `-I`.
4. `compression` id 3 em v4 = **LZO** (o v2 chama de "gzip non-standard").
5. Magic de vendor (`hsqt`, `shsq`): extrair e sobrescrever os 4 bytes por `hsqs` antes do `unsquashfs` (validado: extrai normal depois do patch).
6. SquashFS dentro de UBI → extrair o volume com `ubireader`, nunca `dd` no offset do flash.
7. `unsquashfs -s` não valida estrutura: só imprime o superbloco.
8. Se `block_log` e `block_size` não batem, a imagem é corrupta mesmo que todos os outros campos estejam bons.

---

## 9. Gap honesto desta sessão

O CRC32 do header TRX **não confere** nos dois firmwares do lab:

| arquivo | campo CRC | `crc32(corpo[28:])` |
|---|---|---|
| asus_rt-ac88u-openwrt.trx | 0x5EFBB12F | 0x77FDFF70 |
| netgear-r7000/r7000.trx | 0x16492303 | 0x6440B534 |

Também não confere com CRC do arquivo inteiro, nem do arquivo com o campo zerado. Os dois arquivos passaram por repack no lab (OpenWrt TRX + extração de CHK), então a hipótese mais provável é que o campo não foi recalculado. **Não verificado** — fica como tarefa: pegar um `.trx` original do fabricante e testar as três convenções.

> **Correção (23/10/2026):** o CRC **confere** nos dois arquivos. A convenção do TRX é CRC-32/**JAMCRC** (init `0xFFFFFFFF`, **sem** xorout final) sobre `[0x0C, len)` — e eu havia medido com `zlib.crc32` (que aplica xorout) a partir de `0x1C`. Medido: ASUS `0x5EFBB12F` e R7000 `0x16492303` batem byte a byte. Detalhes, matriz de 12 casos e o falso negativo do binwalk v3 em TRXv2 em `analise_2026-10-23_trx-crc.md`. O trecho abaixo sobre o v3 continua válido apenas em parte: o `trx.rs` do v3 valida a **tabela de offsets** *e* o **CRC** (o dry-run exige os dois).

Sobre o v3 no TRX, o que foi medido: ele **reportou** os dois TRX reais (`TRX firmware image, version 1, partition count: 2`) e ficou calado nos meus TRX sintéticos — inclusive num com CRC correto. Como o meu sintético tinha tabela de partições implausível (`loader=0x1C`, `kernel=0x0`), a hipótese é que o parser do v3 valide a **tabela de offsets**, não o CRC; mas isso eu **não** confirmei lendo o `trx.rs`. Não afirmar sem ler.


---

## 10. Artefatos

- `scripts/sqfs_probe.py` — scanner/validador independente do binwalk: 7 magics, checagens do `read_super` + tabela de metadados, veredito por campo, comandos `dd`/patch/`unsquashfs` prontos. Testado nos 9 casos sintéticos + 2 firmwares reais.
- Referência condensada na skill `libertus-rea-binary-re` (`references/squashfs-deteccao-e-validacao.md`).
