# UBI por dentro: reconstrução de volumes sem ubireader (medido, byte a byte)

**Data:** 12/11/2026 · **Alvo:** `lab/firmware/asus-rt-ac88u/asus_rt-ac88u-openwrt.trx` (OpenWrt bcm53xx, build 23/09/2024)
**Ferramentas:** `scripts/ubi_extract.py` (novo), `scripts/tests/test_ubi_extract.py` (novo), ubireader (referência), `unsquashfs`

---

## 1. A pergunta que faltava no pipeline

O pipeline `TRX → UBI → rootfs` sempre dependeu do `ubireader` como caixa-preta:
`ubireader_extract_images` cospe `img-<seq>_vol-rootfs.ubifs` e a gente segue.
Duas perguntas nunca foram respondidas com medição:

1. **O que exatamente o ubireader faz** para transformar 41 blocos de flash em um
   volume contínuo?
2. **O `dd` no offset do flash funciona?** O relatório de 21/10 diz que não —
   mas não diz *por quanto* ele erra nem *por quê* numericamente.

Esta noite eu escrevi um extrator independente, li as estruturas no
`drivers/mtd/ubi/ubi-media.h` do kernel, e comparei o resultado com o ubireader
por hash. O resultado: **idêntico byte a byte** — e agora eu sei por quê.

---

## 2. As três estruturas que importam (lidas na fonte do kernel)

Todas big-endian, todas com CRC no fim. Fonte:
`drivers/mtd/ubi/ubi-media.h` (Torvalds, master).

### 2.1 `ubi_ec_hdr` — 64 bytes, no início de cada PEB

| offset | tamanho | campo | valor medido no ASUS |
|---|---|---|---|
| 0x00 | 4 | magic `UBI#` (0x55424923) | `55 42 49 23` |
| 0x04 | 1 | version | 1 |
| 0x08 | 8 | ec (erase counter) | **0** (todos os PEBs) |
| 0x10 | 4 | vid_hdr_offset | **0x800** |
| 0x14 | 4 | data_offset | **0x1000** |
| 0x18 | 4 | image_seq | **0x66F16066** (1727094886) |
| 0x3C | 4 | hdr_crc | 0x04E11BCE |

Hexdump real (PEB 2, offset 0x40000):

```
0x00: 55 42 49 23 01 00 00 00 00 00 00 00 00 00 00 00
0x10: 00 00 08 00 00 00 10 00 66 f1 60 66 00 00 00 00
0x30: 00 00 00 00 00 00 00 00 00 00 00 00 04 e1 1b ce
```

`vid_hdr_offset=0x800` e `data_offset=0x1000` **não são constantes universais** —
são propriedades da imagem, ditadas pelo NAND alvo (aqui: página de 2 KiB,
VID na segunda página, dados alinhados em 4 KiB). Um extrator que assume
`0x800` de data_offset perde 2 KiB por bloco. O ubireader lê esses campos; o meu
também. É por isso que ambos acertam.

### 2.2 `ubi_vid_hdr` — 64 bytes, em `peb_start + vid_hdr_offset`

| offset | tamanho | campo | valor medido (PEB 2) |
|---|---|---|---|
| 0x00 | 4 | magic `UBI!` (0x55424921) | `55 42 49 21` |
| 0x04 | 1 | version | 1 |
| 0x05 | 1 | vol_type (1=dynamic, 2=static) | 1 |
| 0x06 | 1 | copy_flag | 0 |
| 0x08 | 4 | vol_id | 0 (`rootfs`) |
| 0x0C | 4 | lnum | 0 |
| 0x14 | 4 | data_size (só estático) | **0** |
| 0x18 | 4 | used_ebs (só estático) | 0 |
| 0x1C | 4 | data_pad | 0 |
| 0x20 | 4 | data_crc (só estático / cópia) | 0 |
| 0x28 | 8 | sqnum | **0** |
| 0x3C | 4 | hdr_crc | 0x73B1AB57 |

`data_size = 0` em volume dinâmico **não é bug**: o kernel só preenche esse
campo em volume estático (ou em LEB copiado pelo wear-leveling, junto com
`copy_flag` e `data_crc`). Quem trata `data_size=0` como "LEB vazio" joga fora
38 LEBs bons — o volume inteiro.

### 2.3 `ubi_vtbl_record` — 172 bytes, na *layout volume*

| offset | tamanho | campo | `rootfs` | `rootfs_data` |
|---|---|---|---|---|
| 0x00 | 4 | reserved_pebs | **38** | **9** |
| 0x04 | 4 | alignment | 1 | 1 |
| 0x08 | 4 | data_pad | 0 | 0 |
| 0x0C | 1 | vol_type | 1 (dynamic) | 1 (dynamic) |
| 0x0D | 1 | upd_marker | 0 | 0 |
| 0x0E | 2 | name_len | 6 | 11 |
| 0x10 | 128 | name | `rootfs` | `rootfs_data` |
| 0x90 | 1 | flags | 0 | **1 = AUTORESIZE** |
| 0xA8 | 4 | crc | ok | ok |

A tabela mora no **layout volume**, `vol_id = 0x7FFFFFFF - 4096 = 0x7FFFEFFF`,
que ocupa **2 LEBs com cópia idêntica** (redundância contra corrupção de um
bloco). Neste firmware: layout em PEB 0 (lnum 0) e PEB 1 (lnum 1). As 128
posições da tabela (128 × 172 = 22.016 B = 0x5600) são escritas por inteiro —
o resto do LEB é `0xFF`. Medido: primeiro `0xFF` da vtbl exatamente em
`0x400000 + 0x1000 + 0x5600 = 0x406600`.

Fora dos 128 slots, `0xFF` é **normal** e não pode invalidar a tabela. Meu
primeiro parser reprovava a cópia A por causa disso; corrigi para tratar slot
`0xFF*172` como "nunca escrito" em vez de CRC inválido. É exatamente o tipo de
erro que só aparece quando se testa com imagem sintética.

---

## 3. O CRC do UBI é JAMCRC — a mesma família do TRX

O kernel calcula `crc32(UBI_CRC32_INIT=0xFFFFFFFF, buf, 60)` e **não aplica
xorout**. Em Python isso **não** é `zlib.crc32(buf, 0xFFFFFFFF)` — a API do zlib
já embute o xorout final. Medido no EC header real:

| fórmula | resultado | bate com o campo 0x04E11BCE? |
|---|---|---|
| `zlib.crc32(buf)` | 0xFB1EE431 | ❌ |
| `zlib.crc32(buf, 0xFFFFFFFF)` | 0x00F392C6 | ❌ |
| `zlib.crc32(buf, 0xFFFFFFFF) ^ 0xFFFFFFFF` | 0xFF0C6D39 | ❌ |
| **`zlib.crc32(buf) ^ 0xFFFFFFFF`** | **0x04E11BCE** | ✅ |

O mesmo vale para o VID header: campo `0x73B1AB57` = `zlib.crc32(buf)^0xFFFFFFFF`.

**Regra:** é o mesmo CRC-32/JAMCRC do header TRX (medido em 23/10: init
0xFFFFFFFF, sem xorout). Duas estruturas Broadcom/MTD diferentes, mesma
convenção de checksum. Quem escreveu `zlib.crc32` cru nos dois casos ficou com
"firmware corrompido" no relatório sem ter nada corrompido.

---

## 4. O algoritmo de reconstrução (o que o ubireader faz e eu refiz)

```text
1. achar o primeiro EC header íntegro  → aqui: 0x400000 (dentro do TRX)
2. descobrir o PEB size               → 0x20000 (EC válido em base + k*PEB)
3. ler EC de cada PEB                 → ec, vid_hdr_offset, data_offset, image_seq
4. ler VID em peb+vid_hdr_offset      → (vol_id, lnum) → PEB físico
5. resolver duplicatas por sqnum      → maior sqnum vence; se copy_flag=1, data_crc decide
6. LEB size = PEB size - data_offset - data_pad   → 131072 - 4096 - 0 = 126976
7. montar o volume em ordem de lnum   → buraco no meio = 0xFF, não deslocamento
8. layout volume → volume table       → nomes, reserved_pebs, flags, tipo
```

Duas sutilezas que separam "funciona" de "funciona sempre":

- **Ordem física ≠ ordem lógica.** O volume é indexado por `lnum`, não por
  posição do PEB na imagem. Numa imagem recém-gerada as duas coincidem
  (medido: PEB 2..39 = lnum 0..37, sequencial). Num dump de flash depois de
  wear-leveling, **não coincidem** — e aí `dd` no offset não tem nem desculpa.
- **Buraco não é deslocamento.** LEB não mapeado no meio do volume vira
  `0xFF * leb_size` na posição certa. Preencher com zero, ou pular o LEB,
  desloca todo o resto e produz um SquashFS "válido" que o `unsquashfs` rejeita
  na primeira tabela.

---

## 5. Resultado medido no firmware real

```
$ python3 scripts/ubi_extract.py lab/firmware/asus-rt-ac88u/asus_rt-ac88u-openwrt.trx -o /tmp/out
imagem        : .../asus_rt-ac88u-openwrt.trx (9568256 bytes)
UBI em        : 0x400000  |  PEB size 0x20000 (131072 B)  |  41 PEBs
headers       : vid_hdr_offset=0x800 data_offset=0x1000 image_seq=[1727094886]
PEBs com VID  : 40  |  mapeamentos duplicados: 0  |  EC values: [0]
volume table  : 2 volume(s), cópia lida do LEB 0
  vol   0 rootfs           dynamic   4825088 B  lebs 38/38  sha256 8fb8df462016871f
  vol   1 rootfs_data      dynamic         0 B  lebs 0/9   sha256 e3b0c44298fc1c14
  # marcador OpenWrt DEADC0DE em PEB(s) [40] (padding/overlay não formatado, não é corrupção)
```

Prova de equivalência com a ferramenta de referência:

```
$ sha256sum out_ubireader/img-1727094886_vol-rootfs.ubifs out_manual/vol000_rootfs.img
8fb8df462016871f7930da28411dc2c38a1d8aa813b145a47fe1619d60dcebb5  ...ubifs
8fb8df462016871f7930da28411dc2c38a1d8aa813b145a47fe1619d60dcebb5  ...img

$ cmp out_ubireader/...ubifs out_manual/vol000_rootfs.img && echo IDENTICOS
IDENTICOS
```

E o volume extraído é utilizável de ponta a ponta:

```
$ unsquashfs -d root manual/vol000_rootfs.img
created 1013 files
created 114 directories
created 211 symlinks
```

**Fecho do loop de 21/10.** Naquele relatório, `binwalk` não achou SquashFS
dentro do TRX e a busca crua achou `hsqs` em `0x441000`. Agora o número tem
estrutura: `hsqs` é o LEB 0 do volume `rootfs`, que está no **PEB 2** do UBI.
PEB 0 = 0x400000, PEB 1 = 0x420000, PEB 2 = 0x440000, e os dados do volume
começam no `data_offset` do PEB: `0x440000 + 0x1000 = 0x441000`. Não era offset
arbitrário. E os dois PEBs antes dele são o **layout volume** — que é justamente
o que o `{jump}` do binwalk estava pulando: o EC header → salta um PEB → cai no
EC do próximo → salta de novo, nunca varrendo os dados.

### Por que `dd` falha — agora quantificado

| item | valor |
|---|---|
| PEB | 131.072 B |
| headers por PEB (data_offset) | 4.096 B |
| LEB | 126.976 B |
| volume rootfs | 38 LEBs = 4.825.088 B |
| espaço físico ocupado | 38 × 131.072 = 4.980.736 B |
| **desperdício em headers** | **155.648 B (3,12%)** |

Um `dd` contínuo a partir do primeiro `hsqs` lê os 4.096 bytes de EC/VID de
**cada** bloco como se fossem dados: a cada 131.072 bytes lidos, 4.096 são
header. Na prática o arquivo gerado é 3,2% maior e todo o conteúdo depois do
primeiro PEB está deslocado — por isso o `unsquashfs` "leu" um ponteiro de
id_table em `0x34AFEC2C7F40A833` (lixo). O erro não é do SquashFS: é do
mapeamento linear aplicado a um dispositivo que **não é linear**.

Detalhe do SquashFS que sai daqui: `block_size = 262.144` (256 KiB) com LEB de
126.976 B. Cada bloco de dados do SquashFS atravessa **três** LEBs. Se alguém
tentar extrair "um LEB por bloco" ou cortar por PEB, quebra. A única unidade
válida é o volume montado.

---

## 6. DEADC0DE não é corrupção

A última PEB da imagem (PEB 40, offset 0x500000) começa com `de ad c0 de`,
seguida de zeros, e tem 8 bytes úteis a 20 bytes do fim: **`RT-AC88U`**.

Isso não é lixo nem assinatura UBI quebrada. É o marcador **"dead code"** do
OpenWrt: o `firmware-utils/imagetag.c` grava `DEADC0DE` no padding depois do
rootfs, e o `libfstools/common.c` reconhece exatamente esse valor:

```c
if (magic == cpu_to_be32(0xdeadc0de)) return FS_DEADCODE;
...
case FS_DEADCODE:
case FS_NONE:
    /* skip padding */
```

Semântica: "aqui não tem filesystem; é padding de imagem" → o overlay é
formatado no primeiro boot. Ou seja, **`rootfs_data` com 0 LEBs gravados e
`flags=AUTORESIZE` é o estado esperado de uma imagem de fábrica**, não um
volume corrompido. Um extrator que reporta isso como erro ensina o analista a
ignorar erro de verdade.

O extrator agora separa as duas coisas: `openwrt_deadcode_pebs` (informativo)
vs `anomalies` (problema real).

---

## 7. Imagem x dump: três números que denunciam a diferença

| sinal | imagem de fábrica (esta) | dump de flash usada |
|---|---|---|
| `ec` (erase counter) | **0 em todos os 40 PEBs** | varia por bloco (dezenas/centenas) |
| `sqnum` | **0 em todos os 40 VIDs** | cresce a cada reescrita |
| `image_seq` | **1 valor** (1727094886) | 1 valor por gravação (o último) |

Aqui os três batem no extremo: `image_seq = 1727094886` = **2024-09-23 12:34:46 UTC**,
exatamente o `mkfs_time` do SquashFS dentro do volume. O campo "sequência" foi
usado como timestamp de build. E `ec=0/sqnum=0` em tudo significa: **essa imagem
nunca foi montada por um kernel**. É artefato de build, não estado de campo.

Consequência prática para análise forense de roteador: se o firmware que você
baixou tem `ec=0` uniforme, você não pode concluir nada sobre histórico de
escrita/desgaste. Se tem `ec` variando, você tem um dump real — e aí
`sqnum`/`copy_flag` passam a importar de verdade (é onde o extrator escolhe o
LEB novo em vez do velho).

---

## 8. O que o extrator faz hoje

`scripts/ubi_extract.py` (sem dependência externa, ~300 linhas):

- autodetecta offset do UBI e PEB size (não confia em constante);
- valida CRC de **todos** os EC/VID headers e lista o que falhou;
- resolve duplicata (`vol_id`, `lnum`) por `sqnum`, com `copy_flag`/`data_crc`;
- lê a volume table, com fallback para a segunda cópia do layout volume;
- monta dinâmico (buraco = 0xFF) e estático (`used_ebs` + `data_size`);
- separa anomalia real de marcador OpenWrt;
- `--json` para uso em pipeline; relata `erased_pebs`, `image_seq`, `ec`.

Testes sintéticos (`scripts/tests/test_ubi_extract.py`, sem `ubinize` — constrói
os headers na mão) cobrem o que o firmware real **não** exercita:

| caso | resultado |
|---|---|
| buraco no meio do volume dinâmico | ✅ 0xFF na posição certa |
| volume estático (2 LEBs, último com 500 B) | ✅ 63.988 B exatos |
| mapeamento duplicado (sqnum 0 vs 9) | ✅ vence o sqnum 9 |
| cópia A da vtbl corrompida | ✅ cai para a cópia B |
| PEB apagado no meio | ✅ contado, não é erro |
| slot de vtbl `0xFF` (nunca escrito) | ✅ ignorado sem invalidar |

```
$ python3 scripts/tests/test_ubi_extract.py
OK: buraco, estático, duplicata por sqnum, vtbl corrompida e PEB apagado
```

---

## 9. Limitações honestas (o que NÃO foi testado)

1. **Fastmap não é suportado.** Imagens com fastmap guardam o mapa LEB→PEB em
   estruturas próprias (`0x7B11D69F`); sem ler isso, um volume com LEBs só
   descritos no fastmap sai com buracos. Neste firmware **não há fastmap**
   (varri os 41 PEBs: zero ocorrências do magic). Não afirmo suporte.
2. **Sem tratamento de bad block real.** PEB marcado como bad (primeiro byte
   `0x00` em NAND) não é tratado; numa imagem de fábrica não existe, num dump
   existe.
3. **Sem dump real de campo.** Todos os números de `ec`/`sqnum` são de imagem
   de build. A regra "imagem x dump" é inferência a partir dos campos, não
   medida em dois arquivos do mesmo roteador.
4. **Um único alvo.** 1 firmware, 2 volumes, 38 LEBs. Volume estático e
   duplicata só foram provados em sintético (declarado acima).

---

## 10. Checklist que passa a valer

1. SquashFS dentro de UBI não se extrai por offset de flash: **extraia o volume**
   (`ubi_extract.py` ou `ubireader_extract_images`) e depois `unsquashfs`.
2. Antes de culpar o SquashFS, calcule: `(PEB - data_offset)` = LEB. Se o
   arquivo não é múltiplo disso, o problema é o mapeamento.
3. CRC de header UBI = `zlib.crc32(buf) ^ 0xFFFFFFFF`. Não é `zlib.crc32` puro.
4. `data_size=0` em VID = volume dinâmico normal. Use `leb_size`, não `data_size`.
5. `DEADC0DE` no começo de um bloco = padding OpenWrt (`FS_DEADCODE`), não
   corrupção.
6. `ec=0` e `sqnum=0` em todo mundo ⇒ imagem de build, nunca montada. Não
   conclua nada sobre desgaste/histórico.
7. `reserved_pebs` da volume table é o tamanho real do volume; `lebs mapeados`
   pode ser menor (volume nunca escrito, ex. `rootfs_data`).

---

## 11. Artefatos desta sessão

- `scripts/ubi_extract.py` — extrator independente, autodetect, JSON, validação de CRC.
- `scripts/tests/test_ubi_extract.py` — 6 casos de borda sintéticos, exit code real.
- Referência condensada: skill `libertus-rea-binary-re`,
  `references/ubi-estrutura-e-extracao.md`.
- Memória Supabase (`tipo=aprendizado`, relevância 9).
