# UBI: estrutura on-flash e extração de volumes (medido 12/11/2026)

Fonte primária: `drivers/mtd/ubi/ubi-media.h` (kernel Linux). Medido em
`lab/firmware/asus-rt-ac88u/asus_rt-ac88u-openwrt.trx` (OpenWrt bcm53xx).

## TL;DR — regras que evitam erro de diagnóstico

1. SquashFS dentro de UBI **não** se extrai por offset de flash. Extraia o
   **volume** (`scripts/ubi_extract.py` ou `ubireader_extract_images`) e depois
   `unsquashfs`.
2. `LEB size = PEB size - data_offset - data_pad`. Se o arquivo não é múltiplo
   disso, o erro é de mapeamento, não do SquashFS.
3. CRC de header UBI = `zlib.crc32(buf) ^ 0xFFFFFFFF` (JAMCRC). **Não** é
   `zlib.crc32(buf, 0xFFFFFFFF)` — a API do zlib já embute o xorout.
4. `data_size = 0` no VID de volume **dinâmico** é normal (só estático usa).
   Quem lê `data_size` como tamanho joga o volume inteiro fora.
5. `DEADC0DE` no início de um bloco = marcador OpenWrt `FS_DEADCODE`
   (`libfstools/common.c`), padding de imagem; **não** é corrupção.
6. `ec=0` e `sqnum=0` em todos os PEBs ⇒ imagem de build, nunca montada.
   Não conclua nada sobre desgaste/histórico.

## Estruturas (todas big-endian)

### ubi_ec_hdr — 64 B no início de cada PEB

| off | tam | campo |
|---|---|---|
| 0x00 | 4 | magic `UBI#` |
| 0x04 | 1 | version (=1) |
| 0x08 | 8 | ec (erase counter) |
| 0x10 | 4 | vid_hdr_offset |
| 0x14 | 4 | data_offset |
| 0x18 | 4 | image_seq |
| 0x3C | 4 | hdr_crc sobre [0,60) |

### ubi_vid_hdr — 64 B em `peb + vid_hdr_offset`

| off | tam | campo |
|---|---|---|
| 0x00 | 4 | magic `UBI!` |
| 0x05 | 1 | vol_type (1=dynamic, 2=static) |
| 0x06 | 1 | copy_flag |
| 0x08 | 4 | vol_id |
| 0x0C | 4 | lnum |
| 0x14 | 4 | data_size (só estático/cópia) |
| 0x18 | 4 | used_ebs (só estático) |
| 0x1C | 4 | data_pad |
| 0x20 | 4 | data_crc (só estático/cópia) |
| 0x28 | 8 | sqnum |
| 0x3C | 4 | hdr_crc sobre [0,60) |

### ubi_vtbl_record — 172 B, na layout volume (vol_id 0x7FFFEFFF, 2 LEBs redundantes)

| off | tam | campo |
|---|---|---|
| 0x00 | 4 | reserved_pebs (= tamanho do volume em LEBs) |
| 0x04 | 4 | alignment |
| 0x08 | 4 | data_pad |
| 0x0C | 1 | vol_type |
| 0x0D | 1 | upd_marker |
| 0x0E | 2 | name_len |
| 0x10 | 128 | name |
| 0x90 | 1 | flags (bit 0 = AUTORESIZE) |
| 0xA8 | 4 | crc sobre [0,168) |

128 slots = 22.016 B (0x5600) escritos por inteiro; o resto do LEB é `0xFF`.
Slot `0xFF*172` = nunca escrito → ignorar, não invalidar a tabela.

## Algoritmo de reconstrução

```
1. achar primeiro EC íntegro (magic + crc + version=1)
2. PEB size: testar 0x10000/0x20000/0x40000/0x80000/0x100000/0x200000
   exigindo EC válido em base + k*PEB para vários k
3. ler EC de cada PEB -> ec, vid_hdr_offset, data_offset, image_seq
4. ler VID -> (vol_id, lnum) -> PEB físico, sqnum, data_size, data_pad
5. duplicata: maior sqnum vence; copy_flag=1 decide por data_crc
6. LEB = PEB - data_offset - data_pad
7. montar por lnum; buraco = 0xFF * leb (NUNCA deslocar o resto)
8. layout volume -> vtbl -> nomes, reserved_pebs, tipo, flags
9. estático: size = lnum_final*LEB + data_size do último LEB
10. dinâmico: size = reserved_pebs * LEB (volume nunca escrito = 0 bytes)
```

## Ferramenta verificada

```bash
~/LIBERTUS/venv/bin/python3 ~/LIBERTUS/scripts/ubi_extract.py firmware.trx -o out/
~/LIBERTUS/venv/bin/python3 ~/LIBERTUS/scripts/ubi_extract.py ubi.img --json
~/LIBERTUS/venv/bin/python3 ~/LIBERTUS/scripts/tests/test_ubi_extract.py
```

Resultado no ASUS (PEB 0x20000, vid_hdr_offset 0x800, data_offset 0x1000):
`rootfs` 38 LEBs = 4.825.088 B, sha256 `8fb8df46…` **idêntico** ao ubireader;
`rootfs_data` 0 LEBs (overlay não formatado, flags AUTORESIZE).
Volume `rootfs` é SquashFS (1339 inodes, xz, block_size 262144 > LEB 126976),
`unsquashfs` → 1013 arquivos.

## Por que `dd` falha (números)

| item | valor |
|---|---|
| PEB | 131.072 B |
| header por PEB | 4.096 B |
| LEB | 126.976 B |
| volume 38 LEBs | 4.825.088 B |
| espaço físico | 4.980.736 B |
| desperdício | 155.648 B (3,12%) |

Cada 131.072 B lidos contêm 4.096 B de EC/VID → todo conteúdo após o primeiro
PEB fica deslocado; `unsquashfs` morre lendo ponteiro de id_table em lixo.

## Limitações declaradas

- **Fastmap não suportado** (magic SB `0x7B11D69F`); neste firmware não existe.
- Sem tratamento de bad block de NAND real.
- `ec`/`sqnum` medidos só em imagem de build, não em dump de campo.

Análise completa: `~/LIBERTUS/evolucao/analise_2026-11-12_ubi-internals.md`.
