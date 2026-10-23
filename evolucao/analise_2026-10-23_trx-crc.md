# TRX: o CRC que ninguém checava — e o falso negativo do binwalk v3

**Data:** 23/10/2026 · **Contexto:** pipeline de firmware (TRX → UBI → SquashFS), labs ASUS RT-AC88U e Netgear R7000
**Ferramentas medidas:** binwalk 3.1.0 (Rust, `~/.cargo/bin`), binwalk 2.4.3 OSPG (`~/.local/bin`), fonte `firmware-utils/src/trx.c`, fonte `binwalk-3.1.0/src/{structures,extractors,signatures}/trx.rs`

---

## 1. A pergunta (que era uma dívida)

A análise de 21/10 terminou com um gap explícito:

> o CRC32 do header TRX **não confere** nos dois firmwares do lab […] hipótese: o campo não foi recalculado no repack. **Não verificado**.

Isso está errado — e o erro era meu, não do firmware. Pergunta desta noite: **qual CRC o TRX usa de verdade, sobre quais bytes, e quem valida isso?**

Resposta curta: CRC-32/**JAMCRC** (tabela refletida `0xEDB88320`, init `0xFFFFFFFF`, **sem** inversão final) sobre os bytes `[0x0C, len)`. O binwalk v3 valida; o v2 nunca valida. E o v3 tem um falso negativo em TRXv2.

---

## 2. A fonte da verdade (lida, não deduzida)

`firmware-utils/src/trx.c`, no fim do arquivo:

```c
#define UPDC32(octet,crc) (crc_32_tab[((crc) ^ (octet)) & 0xff] ^ ((crc) >> 8))

uint32_t crc32buf(char *buf, size_t len)
{
      uint32_t crc;
      crc = 0xFFFFFFFF;
      for ( ; len; --len, ++buf)
            crc = UPDC32(*buf, crc);
      return crc;                 /* sem ~crc */
}
```

E a chamada:

```c
/* for TRXv2 set bin-header Flags to 0xFF for CRC calculation like CFE does */
if (trx_version == 2) {
        memcpy(binheader, buf + LOAD32_LE(p->offsets[3]), sizeof(binheader));
        memset(buf + LOAD32_LE(p->offsets[3]) + 22, 0xFF, 8);
}

p->crc32 = crc32buf((char *) &p->flag_version,
                    ((fsmark)?fsmark:cur_len) - offsetof(struct trx_header, flag_version));
p->len   = STORE32_LE((fsmark) ? fsmark : cur_len);
```

`flag_version` está em `0x0C`. `cur_len` está alinhado a `0x1000` antes disso. Logo:

- **polinômio:** `0xEDB88320` (refletido, o mesmo do zlib)
- **init:** `0xFFFFFFFF`
- **xorout:** `0x00000000` ← é aqui que todo mundo erra
- **cobertura:** `[0x0C, len)`
- **v2:** 8 bytes em `offsets[3]+22` valem `0xFF` durante o cálculo

`zlib.crc32()` aplica o xorout final. `zlib.crc32(d) ^ 0xFFFFFFFF` é o valor certo.

### 2.1 Prova nos dois firmwares reais

```
== asus-rt-ac88u/asus_rt-ac88u-openwrt.trx size=9568256
 magic=0x30524448 len=9568256 (0x920000) crc_field=0x5efbb12f ver=1 flags=0
 offs=['0x1c', '0x400000', '0x0', '0x100005d']
  [12:len]       jamcrc=0x5efbb12f zlib=0xa1044ed0 <== MATCH
  [12:eof]       jamcrc=0x5efbb12f zlib=0xa1044ed0 <== MATCH

== netgear-r7000/r7000.trx size=7340032
 magic=0x30524448 len=7340032 (0x700000) crc_field=0x16492303 ver=1 flags=0
 offs=['0x1c', '0x400000', '0x0', '0x100005d']
  [12:len]       jamcrc=0x16492303 zlib=0xe9b6dcfc <== MATCH
```

Os dois batem. O "gap" de 21/10 tinha duas causas somadas: **convenção** (zlib em vez de JAMCRC) e **offset inicial** (`[28:]` em vez de `[12:]`).

---

## 3. O que o binwalk v3 faz (fonte, não impressão)

`src/structures/trx.rs` — parser: 4 offsets sempre lidos; `version` precisa ser 1 ou 2; `total_size > 28`; `p1,p2,p3 <= total_size`; para v1 `header_size = 28`.

`src/extractors/trx.rs` — e aqui está o que ninguém documenta:

```rust
const CRC_DATA_START_OFFSET: usize = 12;
...
let crc_data_start = offset + CRC_DATA_START_OFFSET;
let crc_data_end   = crc_data_start + trx_header.total_size - CRC_DATA_START_OFFSET;
if let Some(crc_data) = file_data.get(crc_data_start..crc_data_end) {
    if trx_crc32(crc_data) == trx_header.checksum {
        result.success = true;
...
fn trx_crc32(crc_data: &[u8]) -> usize {
    (crc32(crc_data) ^ 0xFFFFFFFF) as usize
}
```

`common::crc32` é `crc32_v2::crc32(0, data)`, e o `crc32-v2` faz `crc ^= 0xFFFFFFFF` na entrada e `crc ^ 0xFFFFFFFF` na saída — ou seja, zlib padrão. Logo `zlib ^ 0xFFFFFFFF` = **JAMCRC**, exatamente o `crc32buf`. O v3 implementa a convenção do trx.c corretamente.

Consequência estrutural: `src/signatures/trx.rs` chama a extração em **dry-run** e só aceita a assinatura se `dry_run.success` — e o dry-run exige o CRC. Portanto, ao contrário do que acontece com SquashFS, **em TRX o binwalk v3 é validador, não só localizador**.

O v2 (`magic/firmware`, linhas 105-119) é só:

```
0  string  HDR0  TRX firmware header, little endian,
>4  lelong  <1    {invalid}
>4  ulelong x     image size: %d bytes,
>8  ulelong x     CRC32: 0x%X,
>14 uleshort !1
>>14 uleshort !2  {invalid}
```

Magic, `len >= 1`, versão ∈ {1,2}. O CRC é **impresso** e nunca conferido.

---

## 4. Matriz medida (12 casos, gerados e rodados nesta máquina)

Sintéticos construídos byte a byte; "ACEITA" = o binwalk v3 imprime `TRX firmware image`; "lista" = o v2 imprime a linha.

| caso | v2 | v3 |
|---|---|---|
| v1 com JAMCRC correto | lista | **ACEITA** |
| v1 com CRC estilo zlib (xorout) | lista | rejeita |
| v1 com 1 byte do corpo alterado (CRC não recalculado) | lista | rejeita |
| v1 `len` > tamanho do arquivo | lista | rejeita |
| v1 `len` não múltiplo de 0x1000 | lista | ACEITA (não checa alinhamento) |
| v1 `offsets[0]=0x30` (header real = 0x1C) | lista | ACEITA (não checa) |
| v1 offset > `len` | lista | rejeita |
| v1 + 4 KiB de lixo depois de `len` | lista | ACEITA (CRC cobre `len`) |
| TRX embutido em offset 0x200 | lista em 0x200 | ACEITA em 0x200 |
| magic trocado (`HDR1`) | silêncio | rejeita |
| **v2 com máscara do bin header (construção correta)** | lista | **rejeita** |
| v2 com CRC calculado sem máscara | lista | ACEITA |

Saídas que sustentam as linhas mais importantes:

```
$ binwalk v1_zlib.trx                  # CRC com xorout, resto perfeito
Analyzed 1 file for 85 file signatures (187 magic patterns) in 1.0 milliseconds

$ binwalk v2_masked.trx                # TRXv2 construído como o trx.c manda
Analyzed 1 file for 85 file signatures (187 magic patterns) in 1.0 milliseconds

$ binwalk v2_unmasked.trx              # mesmo arquivo, CRC "errado" pelo CFE
0  0x0  TRX firmware image, version 2, partition count: 3, header size: 32 bytes, total size: 8192 bytes
```

---

## 5. Achado 1 — o v3 rejeita TRXv2 válido

O `extractors/trx.rs` calcula o CRC sobre os bytes crus. Não existe no código do
v3 nada equivalente ao `memset(..., 8, 0xFF)` do trx.c. Em TRXv2 os bytes
`[offsets[3]+22, +30)` são contadores de boot/flash do bin header: o CFE os zera
ou incrementa, e o CRC do arquivo é calculado **como se fossem 0xFF**. Como eles
praticamente nunca são `0xFF` no arquivo em repouso, o CRC cru nunca fecha →
**falso negativo sistemático em TRXv2 de fabricante**.

O que foi de fato medido: sintético v2 com contadores em `0x00` → máscara muda o
CRC → v3 rejeita; o mesmo arquivo com o CRC "sem máscara" → v3 aceita. O que
**não** foi medido: um TRXv2 real de fabricante (não tenho amostra v2 no lab —
ASUS e R7000 daqui são v1). A predição é forte, mas é predição.

Consequência prática: **não use "o binwalk v3 não listou" como prova de imagem
inválida em TRXv2.** Rode `trx_probe.py`, que testa as duas convenções.

---

## 6. Achado 2 — "TRX firmware image" também é blobo de WiFi Broadcom

Varrendo o rootfs extraído do ASUS, dois arquivos de firmware de rádio começam
com `HDR0`:

```
./firmware/asus-rt-ac88u/extracted/rootfs/lib/firmware/brcm/brcmfmac43143.bin  size=397312 len=397312 ver=1 crc=0x4d392f9e
./firmware/asus-rt-ac88u/extracted/rootfs/lib/firmware/brcm/brcmfmac43236b.bin  size=348160 len=348160 ver=1 crc=0xa1f165eb
```

`trx_probe.py` nos dois:

```
crc     : 0x4d392f9e
offsets : ['0x609bc', '0x81', '0x31c', '0x0']
   OK  jamcrc[12:len]               0x4d392f9e
PROBLEMAS:
   ! offsets[0]=0x609bc != header_size 0x1c
   ! offsets fora de ordem: ['0x609bc', '0x81', '0x31c']
```

O CRC é o mesmo JAMCRC — então **HDR0 + JAMCRC é a assinatura do container
Broadcom**, não do firmware de roteador. A semântica dos offsets é outra
(`offsets[0]` aponta quase para o fim, `offsets[1]/[2]` são 0x81/0x31C).

O v3 lista os dois como `TRX firmware image, version 1, partition count: 3`
porque só compara cada offset com `total_size`, sem ordem. Na extração ele falha
limpo:

```
[-] Extraction of trx data at offset 0x0 failed!
```

Regra: antes de chamar offset de partição, **ordene** e compare `offsets[0]` com
o header (28/32). Nenhum dos dois binwalks faz isso.

---

## 7. `scripts/trx_probe.py` (novo)

Lê o header, valida magic/versão/len/alinhamento/ordem/`offsets[0]`, testa as
convenções de CRC (jamcrc e zlib, com e sem cobertura até EOF, com e sem máscara
do bin header v2) e diz qual bate. `--fix` recalcula `crc32` e `len` in-place com
backup `.bak`.

Teste end-to-end em firmware real de 9,5 MB com **1 byte corrompido em 0x100000**:

```
== antes do fix (v3): 0 linhas  (silêncio total)
== probe:
   ! CRC 0x5efbb12f nao bate com nenhuma convencao testada
== fix:
regravado: len=9568256 crc=0x2ff7ea41 (backup em asus_corrupt.trx.bak)
== depois (v3):
0  0x0  TRX firmware image, version 1, partition count: 2, header size: 28 bytes, total size: 9568256 bytes
```

Ou seja: imagem com CRC quebrado não é imagem morta — o v3 só fica calado, e o
`--fix` devolve a validação sem tocar nos dados.

---

## 8. Regras que passam a valer

1. **Localizar** TRX: `binwalk` v2 (lista mesmo com CRC quebrado) ou `grep -abo HDR0`.
2. **Validar** TRX: binwalk v3 ou `trx_probe.py`. O v2 nunca valida CRC.
3. CRC "não confere": testar JAMCRC sobre `[12, len)` **antes** de acusar corrupção.
4. `len <= filesize` e `len % 0x1000 == 0` são sanity de graça — o v2 não faz e o v3 não reclama de alinhamento.
5. TRXv2 de fabricante rejeitado pelo v3 = limitação do v3, não do arquivo.
6. `HDR0` + JAMCRC em blob de rádio: container Broadcom, não partição de firmware. Ordem e `offsets[0]` decidem.
7. Imagem reparada/repackada manualmente: rodar `--fix` antes de extrair, não depois de reclamar que "não abre".

---

## 9. Gap honesto

- **TRXv2 real não testado.** A máscara do bin header foi medida só em sintético. Falta baixar um `.trx` v2 de fabricante e medir.
- **`offsets[1]/[2]` dos `brcmfmac*.bin` (0x81, 0x31C) não decodifiquei.** Não afirmo o que são; só que não são partições no sentido do trx.c.
- **Não li o `trx.rs` do binwalk v2** (é magic, não código) — a conclusão de que o v2 não valida CRC é por leitura do magic + pelos 6 casos em que ele lista arquivo corrompido.

---

## 10. Artefatos

- `scripts/trx_probe.py` — leitor/validador/reparador de TRX, testado em 12 sintéticos, 2 firmwares reais e 2 blobs Broadcom.
- Referência: skill `libertus-rea-binary-re` → `references/trx-crc-e-validacao.md`.
- Correção registrada no artefato de 21/10 (`analise_2026-10-21_squashfs-binwalk.md`, §9).
