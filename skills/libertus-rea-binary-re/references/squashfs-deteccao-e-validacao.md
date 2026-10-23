# SquashFS em firmware: detectar ≠ validar (medido 21/10/2026)

Regra central: **binwalk localiza, não valida.** Veredito de validade é
`python3 scripts/sqfs_probe.py <arquivo>` + `unsquashfs` de verdade.

## O que o binwalk v2.4.3 (OSPG) confere numa assinatura `hsqs`

Só isto (magic/filesystems):

- `hsqs` nos 4 primeiros bytes (ou `sqsh`/`sqlz`/`qshs`/`tqsh`/`hsqt`/`shsq`);
- `s_major` (offset 28) e `s_minor` (offset 30) entre 1 e 10;
- `compression` (offset 20) entre 1 e 6 — **só é checado quando s_major > 3**;
- `{size:%d}` = `bytes_used` (offset 40 no v4): se estourar o arquivo, a
  assinatura é marcada inválida e **escondida** (só aparece com `-I`).

Não confere `block_size`, `block_log`, coerência das tabelas, `root_inode`.

## Matriz medida (imagens geradas com mksquashfs + mutação de 1 campo)

| caso | binwalk v2 | unsquashfs extrai | sqfs_probe.py |
|---|---|---|---|
| v4 xz/gzip/zstd/lz4 normal | ok | ok | VALIDO |
| v4 lzo | ok, mas rotula `gzip (non-standard type definition)` | ok | VALIDO + aviso |
| magic vendor `hsqt`/`shsq` | ok | **não** (magic ≠ hsqs) | VALIDO_magic_vendor + patch |
| `sqlz`/`qshs`/`tqsh` sobre imagem LE | não (lê BE) | não | INVALIDO |
| `hsqs` + versão 4.0 + compression=4 (10 bytes forjados) | **sim** ("size: 0 bytes, blocksize: 0") | não | INVALIDO |
| s_major = 99 | escondido (só com `-I`) | não | INVALIDO |
| bytes_used = 0x7FFFFFFF (> EOF) | escondido por padrão, visível com `-I` | não | INVALIDO |
| block_size 131072 vs block_log 5 | ok | `FATAL: Block size and block_log do not match` | INVALIDO |

## Armadilhas operacionais

1. **`unsquashfs -s` não valida**: imprime `Found a valid SQUASHFS 4:0 superblock`
   e lista campos; a extração real pode falhar em seguida. Só `unsquashfs -d` conta.
2. **compressão id 3 em v4 = LZO.** Se o binwalk disser `gzip (non-standard type
   definition)` numa imagem v4, é LZO (o rótulo é herança do SquashFS 3.x).
3. **Antes de dizer "não tem SquashFS"**: `binwalk -I <f>` e busca crua
   `binwalk -R '\x68\x73\x71\x73' <f>` (ou `grep -abo hsqs <f>`).
4. **`{jump}` de container esconde o miolo.** O magic do UBI (`UBI\x23`) tem
   `{jump:0}` e `plugins/ubivalid.py` faz `result.jump = self.peb_size` (PEB =
   erase block). Resultado medido: TRX real do ASUS tem `hsqs` em 0x441000 e o
   scan padrão do v2 reporta **zero** squashfs; a busca crua acha.
5. **SquashFS dentro de UBI não é extraível direto**: os PEBs intercalam EC
   header + VID header + padding, então os offsets internos apontam para lixo.
   Sintoma: `read_block: failed to read block @0x...`. Extraia o **volume**
   antes (`ubireader_extract_images`), nunca `dd` no offset do flash.
6. **Magic de vendor**: extrair o range e sobrescrever os 4 bytes por `hsqs`
   (`printf 'hsqs' | dd of=vol.sqfs bs=1 seek=0 conv=notrunc`); depois
   `unsquashfs` monta normal (validado com `hsqt`).

## O que o unsquashfs valida (read_super, squashfs-tools)

magic == 0x73717368; s_major == 4 e s_minor <= 0; compressor suportado;
block_size entre 4096 e 1 MiB; `block_size == (1 << block_log)`; bytes_used >= 0;
id/xattr/lookup table starts dentro de bytes_used. Depois: inode table, diretório,
id table.

## binwalk v3 (3.1.0, `~/.cargo/bin/binwalk`)

- Parser em `src/signatures/squashfs.rs`: checa `image_size <= available_data`,
  que `id_table_start` aponte para dentro da imagem, e que o primeiro `u64` do
  índice da UID table seja plausível; só então reporta (CONFIDENCE_HIGH).
- Rejeita o falso positivo de 10 bytes e o `block_log` incoerente; lê o label
  de compressão certo (`lzo`).
- 7 magics: `sqsh`, `hsqs`, `sqlz`, `qshs`, `tqsh`, `hsqt`, `shsq`.
- **Extração é de um nível por execução** (TRX → `partition_0.bin`,
  `partition_1.bin`); não recursa. Rodar de novo em cada partição.
- Scan é "limpo": não despeja lixo tipo JBOOT STAG no meio do kernel (o v2 despeja).

## Ferramenta do repo

`scripts/sqfs_probe.py` (sem dependência do binwalk):

```bash
python3 scripts/sqfs_probe.py firmware.bin          # humano
python3 scripts/sqfs_probe.py firmware.bin --json    # máquina
```

- varre os 7 magics byte a byte; checa superblock como o `read_super` + valida o
  primeiro bloco de metadados da inode table e o índice da id table;
- imprime `dd if=... iflag=skip_bytes,count_bytes skip=OFF count=BYTES` e o
  `unsquashfs` prontos, mais o patch quando o magic é de vendor;
- exit 0 = achou extraível, 1 = só suspeitas, 2 = nenhum candidato.
