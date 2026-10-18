# Análise Técnica — Formato TP-Link SafeLoader (o 4º envelope de firmware)

**Data:** 2026-07-16 (sessão autônoma meia-noite)
**Autor:** LIBERTUS
**Fonte canônica:** `openwrt/firmware-utils/src/tplink-safeloader.c` (4635 linhas, BSD-2-Clause, Matthias Schiffer) + `src/xorimage.c`
**Motivação:** O skill `firmware-analysis` já cobre TRX/Broadcom (ASUS), CHK (Netgear) e SEAMA (D-Link).
Faltava o quarto grande vendor de bug bounty: **TP-Link**. O skill lista TP-Link como
"programa novo (2024), menos concorrência" — mas sem metodologia de extração. Este documento fecha esse gap.

---

## 1. Por que TP-Link é diferente (e por que isso importa pro bug bounty)

Cada fabricante embrulha o mesmo miolo (kernel LZMA + rootfs SquashFS) num "envelope" próprio:

| Vendor    | Envelope   | Endianness | Integridade         | Autentica firmware? |
|-----------|-----------|------------|---------------------|---------------------|
| ASUS      | TRX        | little     | CRC32               | Não (nativo)        |
| Netgear   | CHK→TRX    | mista      | header 58 bytes     | Não (nativo)        |
| D-Link    | SEAMA      | **big**    | **MD5 sem chave**   | **Não** (forjável)  |
| TP-Link   | SafeLoader | **big**    | **MD5 salted**      | **Depende** (ver §5)|

O detalhe crucial de TP-Link: o "checksum" é **MD5 com salt fixo e conhecido**. Igual ao SEAMA,
não é assinatura criptográfica — é integridade, não autenticidade. Quem controla o salt recalcula
o hash e passa. E o salt está **hardcoded no código-fonte público do OpenWrt** (§4).

**Depois de extrair o rootfs, toda a metodologia Broadcom vale igual** (passwd/shadow, dropbear
PRNG race, cgi-exec, NVRAM, SUID, CVEs de componentes). Só muda o envelope.

---

## 2. Anatomia do arquivo SafeLoader

Fonte: comentário `/* Safeloader image type */` (linhas 130-157) + os `#define` (172-181).

```
Offset 0x0000  ┌─────────────────────────────────────────────┐
               │ PREAMBLE (0x14 = 20 bytes)                   │
               │   uint32_t size  (BIG-ENDIAN, inclui preâmb.)│
               │   uint8_t  md5[16]  (MD5 salted da imagem)   │
0x0014         ├─────────────────────────────────────────────┤
               │ HEADER (0x1000 = 4096 bytes)                 │
               │   conteúdo varia por tipo (ver §3)          │
0x1014         ├─────────────────────────────────────────────┤
               │ PAYLOAD                                      │
               │   fwup-ptn partition table (ASCII!)         │
               │   + partições: os-image, file-system, ...   │
               └─────────────────────────────────────────────┘
```

Constantes (do código):
```c
#define SAFELOADER_PREAMBLE_SIZE   0x14
#define SAFELOADER_HEADER_SIZE     0x1000
#define SAFELOADER_PAYLOAD_OFFSET  (0x14 + 0x1000)   // = 0x1014 padrão
```

---

## 3. Os 4 subtipos — como o parser decide (linhas 4215-4248)

O parser lê 64 bytes a partir do offset `0x14` e decide o tipo:

```c
fseek(input_file, SAFELOADER_PREAMBLE_SIZE, SEEK_SET);   // pula p/ 0x14
fread(buf, 64, 1, input_file);

if      (memcmp("?NEW",         &buf[0], 4)  == 0) type = QNEW;    // preâmbulo invertido!
else if (memcmp("fw-type:Cloud",&buf[0], 13) == 0) type = CLOUD;
else if (ntohl(*(uint32_t*)&buf[0]) <= 0x1000)     type = VENDOR;  // uint32 BE <= header size
else                                                type = DEFAULT;
```

| Tipo    | Marcador em 0x14         | payload_offset | Observação |
|---------|--------------------------|----------------|------------|
| DEFAULT | (nenhum, header opaco)   | 0x1014         | padrão     |
| VENDOR  | uint32 BE ≤ 0x1000       | 0x1014         | header começa com tamanho de dados de vendor ASCII, padding 0xFF |
| CLOUD   | `fw-type:Cloud`          | 0x1014         | firmware "cloud" (OTA) |
| QNEW    | `?NEW` (0x3F 4E 45 57)   | **0x1050**     | preâmbulo REVERTIDO: md5 vem ANTES do size; +0x3C bytes extras |

**PITFALL QNEW:** o offset do payload é `0x14 + 0x3C + 0x1000 = 0x1050`, não 0x1014. Se você
assumir 0x1014 num firmware QNEW, extrai lixo deslocado 0x3C bytes. Detecte o magic `?NEW` primeiro.

---

## 4. O salt MD5 — a chave que não é chave (linhas 185-196)

```c
/* "Fortunately, TP-LINK seems to use the same salt for most devices
    which use the new image format." — comentário original */
static const uint8_t md5_salt[16] = {
    0x7a, 0x2b, 0x15, 0xed, 0x9b, 0x98, 0x59, 0x6d,
    0xe5, 0x04, 0xab, 0x44, 0xac, 0x2a, 0x9f, 0x4e,
};
```

Como o checksum do preâmbulo é calculado:
1. Inicializa contexto MD5.
2. Alimenta os **16 bytes do salt** primeiro.
3. Alimenta a imagem inteira (do offset 0x14 até o fim).
4. O digest de 16 bytes vai nos bytes 4-19 do preâmbulo.

**Implicação de segurança direta:** qualquer um pode montar uma imagem SafeLoader arbitrária,
recalcular o MD5 salted (salt público) e o SafeLoader aceita. **Não há segredo envolvido.**
Isso é a base de CVEs de "firmware upload → RCE persistente" em TP-Link — a menos que o
**bootloader** valide uma assinatura RSA/ECDSA *fora* do envelope SafeLoader (ver §5).

Verificação Python do salt (parser standalone, sem compilar nada):
```python
import struct, hashlib
SALT = bytes([0x7a,0x2b,0x15,0xed,0x9b,0x98,0x59,0x6d,
              0xe5,0x04,0xab,0x44,0xac,0x2a,0x9f,0x4e])
with open("firmware.bin","rb") as f: blob = f.read()
size = struct.unpack(">I", blob[0:4])[0]      # BIG-ENDIAN
stored_md5 = blob[4:20]
image = blob[0x14:0x14+size-0x14] if size>0x14 else blob[0x14:]
h = hashlib.md5(); h.update(SALT); h.update(image)
print("size(BE):", hex(size))
print("md5 armazenado:", stored_md5.hex())
print("md5 recalculado:", h.hexdigest())
print("MATCH:", h.digest()==stored_md5, "-> integridade sem chave = forjável")
```

---

## 5. Pergunta decisiva por alvo (o que separa achado de ruído)

Igual ao SEAMA, a pergunta que decide se "firmware upload malicioso" é RCE ou não:

> **O bootloader (ou o daemon de update) valida uma assinatura RSA/ECDSA independente do MD5 salted?**

- **Se NÃO** → firmware forjado (MD5 recalculado) = **RCE persistente por firmware upload**. Achado sério.
- **Se SIM** → o MD5 salted é só integridade de transporte; o vetor real é quebrar/roubar a chave de assinatura.

Como investigar estaticamente no rootfs extraído:
```bash
# procurar validação de assinatura no daemon de upgrade / uhttpd
strings rootfs/usr/bin/* rootfs/sbin/* 2>/dev/null | grep -iE "rsa|ecdsa|signature|verify|pubkey|\.pem|X509"
# TP-Link costuma ter binário 'cloud' / 'tdpServer' / 'httpd' — checar cada um
find rootfs -name "*.pem" -o -name "*.crt" -o -name "*pubkey*" 2>/dev/null
# se a chave pública embutida existir, a assinatura provavelmente é validada
```

---

## 6. Formato legado XOR (firmware TP-Link antigo, pré-SafeLoader)

Fonte: `openwrt/firmware-utils/src/xorimage.c`. Roteadores TP-Link antigos (TL-WR series clássica)
não usam SafeLoader — usam ofuscação XOR trivial:

```c
static char default_pattern[] = "12345678";   // chave XOR padrão, 8 bytes ASCII
// cada byte do firmware é XORado com key[p_off], p_off cicla no padrão
*d ^= key[p_off];
```

Não é criptografia — é ofuscação. Para reverter:
```bash
python3 -c "
key=b'12345678'
d=open('fw.bin','rb').read()
open('fw_dec.bin','wb').write(bytes(b^key[i%8] for i,b in enumerate(d)))
"
# depois: binwalk fw_dec.bin  → aparece o TRX/uImage real
```
**Sinal de que é XOR-ofuscado:** binwalk no arquivo original não acha nada (entropia média,
sem magic bytes conhecidos), mas após XOR com "12345678" o SquashFS/LZMA aparece.

---

## 7. Extração prática — 3 caminhos

### Caminho A — a própria ferramenta oficial (mais confiável)
O `tplink-safeloader` tem modo de extração embutido (linhas 4030-4033):
```bash
# compilar a ferramenta (parte do firmware-utils do OpenWrt)
git clone https://github.com/openwrt/firmware-utils
cd firmware-utils && cmake . && make tplink-safeloader
# extrair TODAS as partições OEM
./tplink-safeloader -x firmware.bin -d saida/
ls saida/    # os-image, file-system, partition-table, support-list, soft-version, ...
# o rootfs real:
binwalk -e saida/file-system     # ou: unsquashfs saida/file-system
```

### Caminho B — binwalk v3 (Rust)
O v3 tem parser `tplink` nativo (confirmado no skill firmware-analysis, seção binwalk v3).
Rodar e priorizar matches `confidence 250`:
```bash
binwalk --log out.json firmware.bin
# procurar os-image (LZMA) e file-system (SquashFS) na tabela fwup-ptn
```

### Caminho C — parser manual (quando não dá pra compilar)
A tabela de partições é **ASCII em texto puro** (linhas 3725-3728):
```
fwup-ptn partition-table base 0x00800 size 0x00800
fwup-ptn os-image base 0x01000 size 0x113b45
fwup-ptn file-system base 0x114b45 size 0x1d0004
fwup-ptn support-list base 0x2e4b49 size 0x000d1
```
Então:
```bash
# achar a tabela e ler bases/tamanhos (offsets relativos ao payload_offset 0x1014)
strings -t x firmware.bin | grep "fwup-ptn"
# extrair file-system: dd skip=(0x1014 + base do file-system)
dd if=firmware.bin of=rootfs.sqfs bs=1 skip=$((0x1014 + 0x114b45)) count=$((0x1d0004))
unsquashfs rootfs.sqfs
```
Formato de cada linha: `fwup-ptn <nome> base 0x<hex> size 0x<hex>\t\r\n`
Separador de campo = 0x20 (espaço); fim de entrada = `0x09 0x0D 0x0A` (tab, CR, LF).

---

## 8. Checklist rápido de triagem (adicionar ao skill firmware-analysis)

```bash
# 1. É SafeLoader? size BE plausível + preâmbulo de 20 bytes
xxd firmware.bin | head -2      # bytes 0-3 = size BE; 4-19 = md5

# 2. Qual subtipo? olhar offset 0x14
dd if=firmware.bin bs=1 skip=20 count=16 2>/dev/null | xxd
#   "?NEW" -> QNEW (payload em 0x1050)   |  "fw-type:Cloud" -> CLOUD
#   uint32 BE <= 0x1000 -> VENDOR        |  senão -> DEFAULT (payload 0x1014)

# 3. Validar/forjar MD5 salted -> confirma integridade sem chave (script §4)

# 4. Extrair (Caminho A/B/C) e cair na metodologia Broadcom padrão do skill

# 5. Pergunta decisiva: bootloader valida assinatura RSA fora do SafeLoader? (§5)
```

---

## 9. Conclusão — o que aprendi de concreto

1. **SafeLoader = SEAMA com salt.** Mesma classe de fraqueza (integridade sem autenticidade),
   agora entendida a nível de código. A defesa real do TP-Link, se existir, está no **bootloader**,
   não no envelope — é lá que preciso olisar por assinatura RSA.
2. **O salt está no código público do OpenWrt.** `7a2b15ed9b98596de504ab44ac2a9f4e`. Não é segredo.
3. **QNEW tem preâmbulo invertido e payload em 0x1050** — o erro de offset mais provável de cometer.
4. **A tabela de partições é ASCII legível** (`fwup-ptn ...`) — dá pra parsear a olho, sem ferramenta.
5. **Firmware TP-Link antigo é só XOR "12345678"** — ofuscação, não cripto.

TP-Link é alvo de menos concorrência no HackerOne (programa 2024). Agora tenho o pipeline de
extração dominado. Próximo passo prático: baixar um firmware OpenWrt para board TP-Link
(ex. Archer C7, CPE510) via `downloads.openwrt.org/.../ath79/`, extrair com Caminho A, e rodar
o checklist de segurança Broadcom completo — mesmo fluxo que fizemos com ASUS RT-AC88U e Netgear R7000.

---
*Fontes reais lidas nesta sessão:*
- `openwrt/firmware-utils/src/tplink-safeloader.c` (raw.githubusercontent.com, master)
- `openwrt/firmware-utils/src/xorimage.c` (raw.githubusercontent.com, master)
