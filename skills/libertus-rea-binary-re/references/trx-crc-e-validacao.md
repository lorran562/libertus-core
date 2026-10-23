# TRX (Broadcom HDR0): qual CRC, qual cobertura, o que cada binwalk valida

Medido em 23/10/2026 nesta máquina: binwalk v2.4.3 OSPG (`~/.local/bin`),
binwalk 3.1.0 Rust (`~/.cargo/bin`), fonte `firmware-utils/src/trx.c` (OpenWrt)
e `binwalk-3.1.0/src/{structures,extractors,signatures}/trx.rs`.

## Formato

```
0x00 u32 magic   "HDR0" = 0x30524448 (little endian)
0x04 u32 len     tamanho total incluindo header, alinhado a 0x1000
0x08 u32 crc32   CRC de flag_version até o fim
0x0C u16 flags
0x0E u16 version (1 ou 2)
0x10 u32 offsets[4]   v1 usa 3 → header 28 bytes; v2 usa 4 → 32 bytes
```

## O CRC certo: JAMCRC, não zlib

`crc32buf()` no trx.c: tabela refletida `0xEDB88320`, **init 0xFFFFFFFF,
sem inversão final**. Isso é CRC-32/JAMCRC. `zlib.crc32()` faz o xorout final e
dá outro valor — foi exatamente esse erro que produziu o "CRC não confere" de
21/10 (agravado por começar em 0x1C em vez de 0x0C).

```python
jam = lambda d: zlib.crc32(d) ^ 0xFFFFFFFF      # correto
cobertura = buf[12:h["len"]]                     # NÃO [28:], NÃO [:eof]
```

Fonte, trx.c: `p->crc32 = crc32buf((char *)&p->flag_version, ((fsmark)?fsmark:cur_len) - offsetof(struct trx_header, flag_version))`.
Como `flag_version` está em 0x0C, a cobertura é `[0x0C, len)`.

### TRXv2: máscara obrigatória no cálculo

Antes de calcular, o trx.c grava `0xFF` em 8 bytes de `buf[offsets[3] + 22]`
(contadores `stable` / `try1..3` do bin header, mascarados pelo CFE), calcula o
CRC e restaura. Quem valida um TRXv2 de fabricante **tem** que aplicar a mesma
máscara, senão o CRC nunca fecha (os contadores mudam a cada boot).

## O que cada binwalk faz de fato

| | binwalk v2 (magic) | binwalk v3 (parser Rust) |
|---|---|---|
| magic | sim | sim |
| version ∈ {1,2} | sim | sim |
| `len >= 1` / `len > 28` | sim | sim |
| **CRC-32** | **nunca** (só imprime o campo) | **sim** (`crc32(data)^0xFFFFFFFF`) |
| offsets ≤ total_size | não | sim (p1..p3) |
| offsets[0] == header_size | não | não |
| offsets em ordem | não | não |
| máscara bin header v2 | não | **não** (bug → falso negativo) |

Cadeia do v3: `extractors/trx.rs` usa `CRC_DATA_START_OFFSET = 12`,
`crc_data_end = offset + 12 + total_size - 12`, e
`trx_crc32 = crc32(data) ^ 0xFFFFFFFF`; `common::crc32` é
`crc32_v2::crc32(0, data)` — que aplica init/final xor internamente, ou seja,
zlib padrão. Logo `^ 0xFFFFFFFF` devolve exatamente o JAMCRC do trx.c. A
assinatura do v3 só é aceita se o **dry-run de extração** passar, e esse dry-run
exige o CRC.

## Matriz medida (sintéticos + reais)

| caso | v2 | v3 |
|---|---|---|
| v1 com JAMCRC correto | lista | ACEITA |
| v1 com CRC estilo zlib (xorout) | lista | rejeita |
| v1 com 1 byte do corpo alterado (CRC não recalculado) | lista | rejeita |
| v1 `len` > tamanho do arquivo | lista | rejeita |
| v1 `len` não múltiplo de 0x1000 | lista | ACEITA (não checa alinhamento) |
| v1 `offsets[0]=0x30` (≠ header 0x1C) | lista | ACEITA (não checa) |
| v1 offset > len | lista | rejeita |
| v1 com 4 KiB de lixo depois de `len` | lista | ACEITA (CRC cobre `len`, não EOF) |
| TRX em offset 0x200 (embutido) | lista em 0x200 | ACEITA em 0x200 |
| magic trocado (HDR1) | silêncio | rejeita |
| **v2 com máscara do bin header (construção correta)** | lista | **rejeita** |
| v2 com CRC sem máscara | lista | ACEITA |

Reais do lab: `asus_rt-ac88u-openwrt.trx` 0x5EFBB12F e `netgear-r7000/r7000.trx`
0x16492303 — os dois batem com `jamcrc[12:len]`. Nenhum dos dois é v2, então o
falso negativo do v3 em TRXv2 é medido só em sintético (predição, não observação
de vendor).

## Broadcom HDR0 não é só firmware de roteador

Blobs de WiFi do próprio rootfs extraído casam a mesma convenção:
`lib/firmware/brcm/brcmfmac43143.bin` (0x4D392F9E) e `brcmfmac43236b.bin`
(0xA1F165EB) batem `jamcrc[12:len]` e o v3 os lista como "TRX firmware image".
Mas a semântica de offsets é outra (`offsets[0]=0x609BC`, `0x54404` — fim do
arquivo, e `offsets[1]/[2]` = 0x81/0x31C), fora de ordem. O v3 aceita porque só
compara cada offset com `total_size`; a extração falha limpa:
`[-] Extraction of trx data at offset 0x0 failed!`.

Regra: **HDR0 + JAMCRC = container Broadcom**, não necessariamente TRX de
roteador. Ordene os offsets e compare `offsets[0]` com o header antes de chamar
qualquer coisa de partição.

## Ferramenta

```bash
python3 ~/LIBERTUS/scripts/trx_probe.py firmware.trx          # veredito + candidatos de CRC
python3 ~/LIBERTUS/scripts/trx_probe.py --fix copia.trx       # recalcula CRC e len (backup .bak)
python3 ~/LIBERTUS/scripts/trx_probe.py --json firmware.trx   # para script
```

`--fix` testado em firmware real de 9.5 MB com 1 byte corrompido: antes o v3
ficava silencioso, depois do fix listou
`TRX firmware image, version 1, partition count: 2 ... total size: 9568256`.

## Checklist

1. Localizar: `binwalk` v2 (lista mesmo com CRC quebrado) ou `grep -abo HDR0`.
2. Validar: `binwalk` v3 **ou** `trx_probe.py` — o v2 nunca valida CRC.
3. CRC "não confere" em arquivo do fabricante: testar antes a convenção JAMCRC
   sobre `[12, len)`; só depois suspeitar de corrupção.
4. TRXv2 de fabricante rejeitado pelo v3: não é arquivo inválido — é o v3 sem a
   máscara do bin header. Conferir com `trx_probe.py` (ele testa as duas).
5. Antes de extrair: `len <= filesize`, offsets crescentes, `offsets[0]` ==
   header (28/32). O v3 não checa os dois últimos.
6. Imagem com data/hora de boot ou contador de flash quebrado → CRC quebrado é
   esperado; `--fix` antes de extrair, nunca depois de reclamar que "não abre".
