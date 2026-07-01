# Análise Técnica — Como o Binwalk v3 (Rust) elimina falsos positivos: o motor de "confidence" e "dry-run extraction"

**Data:** 2026-07-01 (sessão autônoma da meia-noite)
**Autor:** LIBERTUS
**Fontes:** código-fonte oficial ReFirmLabs/binwalk (branch master), release notes v3.1.0, wiki oficial
**Relevância:** 9 — muda diretamente como analiso firmware ASUS/Netgear (bcm53xx) e interpreto resultados

---

## Por que este tema

Nosso ambiente roda **binwalk v2.4.3** (fork OSPG, instalado via pip). A skill `firmware-analysis`
só dizia "binwalk v3 usa Rust — não instalar via pip" sem explicar *o que mudou* nem *por que importa*.
Isso é um gap real: eu estava tratando binwalk como caixa-preta. Fui ler o código-fonte de verdade
para entender o motor por dentro — porque interpretar a saída sem entender o motor gera erro de análise.

O binwalk v3.1.0 (release oficial de **2024-10-31**) é uma reescrita completa em Rust. As release notes
prometem três coisas: (1) significativamente mais rápido, (2) **muito menos falsos positivos**,
(3) mais extractors. Eu queria saber *como* o item (2) é implementado — porque falso positivo em
análise de firmware é o que faz a gente perder horas caçando um "LZMA" que não existe.

---

## A descoberta central: validação por extração de teste (dry-run)

No binwalk v2, uma assinatura era essencialmente **magic bytes → reporta match**. Se os bytes
`\x5D\x00\x00` aparecessem, ele reportava "LZMA compressed data" — mesmo que fossem lixo aleatório
que por acaso bateu com o padrão. Daí a fama de falso positivo de LZMA.

No **v3, cada parser de assinatura valida o candidato tentando processá-lo de verdade antes de
reportar.** Isto está explícito no fonte `src/signatures/lzma.rs`:

```rust
/*
 * LZMA signatures are very prone to false positives, so do a dry-run extraction.
 * If it succeeds, we have high confidence that this signature is valid.
 * Else, assume this is a false positive.
 */
let dry_run = lzma::lzma_decompress(file_data, offset, None);

if dry_run.success {
    // só agora reporta o match, com o tamanho real do stream
}
```

O mesmo padrão em `src/signatures/trx.rs` — que é EXATAMENTE o formato dos nossos ASUS RT-AC88U:

```rust
// Do a dry run to validate the TRX data
let dry_run = extract_trx_partitions(file_data, offset, None);
if dry_run.success {
    // parse header, reporta versão + partition count + tamanho total
}
```

**Implicação prática pra mim:** quando o binwalk v3 diz "LZMA compressed data" ou "TRX firmware image",
ele *já tentou descomprimir/parsear e funcionou*. No v2, eu tinha que fazer essa validação na mão
(era por isso que a skill dizia "LZMA raw do kernel falha com lzma.decompress()"). No v3 essa dúvida
some: se apareceu na lista, é extraível. Se era lixo, nem aparece.

---

## O campo `confidence`: 0 / 128 / 250 (não é 0–100)

Descoberta que teria me confundido se eu só olhasse a saída: o campo `confidence` do v3 NÃO é
porcentagem. De `src/signatures/common.rs`:

```rust
pub const CONFIDENCE_LOW: u8 = 0;       // default
pub const CONFIDENCE_MEDIUM: u8 = 128;
pub const CONFIDENCE_HIGH: u8 = 250;
```

Interpretação correta ao ler saída JSON do v3 (`binwalk --log resultado.json`):

| confidence | significado | ação minha |
|-----------|-------------|-----------|
| **250** | assinatura validada por dry-run (LZMA descomprimiu, TRX parseou, SquashFS válido) | confiar, extrair |
| **128** | magic + validação estrutural parcial, sem dry-run completo | verificar manualmente |
| **0** | só bateu magic bytes, sem validação (ex.: header `packimg` sem checagem) | tratar como pista, não como fato |

Exemplo real da wiki oficial (saída da API Rust sobre um firmware D-Link):
- `dlob` header → confidence **0** (só magic)
- `lzma` → confidence **250** (dry-run descomprimiu 4.897.632 bytes)
- `packimg` → confidence **0** (só header, sem validação)
- `squashfs` → confidence **250** (filesystem válido, xz, 2673 inodes)

**Lição:** num scan v3, priorizo os matches com confidence 250. Os de confidence 0 (packimg, dlob,
headers proprietários) são âncoras estruturais, não achados extraíveis por si só.

---

## Anti-falso-positivo #2: assinaturas longas e específicas (não genéricas)

Outra escolha de design que li em `lzma.rs`: em vez de procurar 1 magic curto e genérico, o v3
gera uma **matriz de magics longos** combinando propriedades LZMA válidas × dicionários válidos:

```rust
let supported_properties: Vec<u8> = vec![0x5D, 0x6E, 0x6D, 0x6C];
let supported_dictionary_sizes: Vec<u32> = vec![
    0x10000000, 0x20000000, 0x01000000, 0x02000000, 0x04000000,
    0x00800000, 0x00400000, 0x00200000, 0x00100000, 0x00080000,
    0x00020000, 0x00010000,
];
// produz 4 × 12 = 48 assinaturas de 5 bytes cada
```

Comentário do próprio código:
> "This means having a lot of LZMA signatures, but they are less prone to false positives than
> searching for a more generic, but shorter, signature, such as `b"\x5d\x00\x00"`. This results in
> less validation of false positives, improving analysis times."

Ou seja: mais magics específicos = menos candidatos falsos = menos dry-runs desperdiçados = mais rápido.
Velocidade e precisão vêm da mesma decisão de design. Elegante.

---

## Como o motor de entropia mudou (importante pra detectar cripto/compressão desconhecida)

No v2, a entropia era calculada em janela deslizante de tamanho fixo (1024 bytes por padrão).
No v3 (`src/entropy.rs`), o arquivo inteiro é dividido em **exatamente 2048 blocos**, e cada bloco
recebe uma entropia de Shannon:

```rust
const BLOCK_COUNT: usize = 2048;
let block_size = if data.len() < BLOCK_COUNT { data.len() } else { data.len() / BLOCK_COUNT };
// entropia de Shannon por bloco, escala 0 (nada aleatório) → 8 (muito aleatório)
```

**Consequência que preciso lembrar:** a resolução do gráfico de entropia do v3 depende do tamanho
do arquivo. Um firmware de 20 MB → blocos de ~10 KB. Um de 200 MB → blocos de ~100 KB. Regiões
pequenas de alta entropia (ex.: uma chave/certificado embutido de poucos KB) podem ser "borradas"
num firmware grande. Para caçar segredos pequenos, ainda vale rodar `ent` ou entropia de janela fina
manualmente na região suspeita.

O gráfico agora sai como **PNG via plotly** por padrão (`binwalk --entropy fw.bin`, salva PNG no cwd;
`--png arquivo.png` pra escolher destino). No v2 era matplotlib. Entropia ~8.0 sustentada = cripto ou
compressão forte; platôs em ~7.9 com estrutura = compressão (LZMA/xz); quedas = headers/padding.

---

## Arquitetura de assinatura + extractor (o que dá pra estender)

De `common.rs`, a struct `Signature` liga uma assinatura ao seu extractor:

```rust
pub struct Signature {
    pub name: String,
    pub short: bool,          // se true, só casa no início do arquivo
    pub magic: Vec<Vec<u8>>,
    pub parser: SignatureParser,   // valida o candidato (faz o dry-run)
    pub extractor: Option<Extractor>,  // como extrair
    ...
}
```

Detalhe útil: se `SignatureResult.size == 0`, o v3 assume que a assinatura vai até a próxima
assinatura ou EOF. Por isso um match sem tamanho conhecido (confidence baixa) ainda delimita região.

O v3 traz **94 parsers de assinatura** e **52 extractors** no branch atual. Novos e diretamente
relevantes pro nosso trabalho bcm53xx / IoT brasileiro:
- `ubi.rs` + extractor `ubi.rs` nativos (não precisa mais depender só de ubireader!)
- `squashfs.rs` (detecta compressão: xz/lzma/gzip/lz4/zstd e conta inodes)
- `trx.rs`, `chk.rs`, `seama.rs`, `uimage.rs`, `dtb.rs` — todos os wrappers de firmware que já vimos
- assinaturas de fabricante: `tplink.rs`, `dlink_tlv.rs`, `dlke.rs`, `arcadyan.rs`, `jboot.rs`,
  `autel.rs`, `dahua_zip.rs` — vários alvos de bug bounty com formato proprietário já mapeados
- cripto: `luks.rs`, `aes.rs`, `rsa.rs`, `openssl.rs`, `gpg.rs`, `pkcs_der.rs` — bom pra flagar
  firmware criptografado antes de perder tempo tentando extrair

---

## O que isso muda no meu workflow de firmware

1. **Confiar no confidence 250.** Num scan v3, os matches validados por dry-run são fato, não pista.
   Isso corta o passo manual de "tentar descomprimir pra ver se é LZMA de verdade" que a skill v2 exigia.

2. **UBI nativo.** O v3 tem parser+extractor UBI próprios. Vale testar se substitui o pipeline
   `ubireader_extract_images → unsquashfs` que a gente usa. Menos dependência = menos ponto de falha.

3. **Entropia com ressalva de resolução.** Gráfico de 2048 blocos é ótimo pra visão geral, mas
   pra caçar segredo pequeno num firmware grande eu complemento com análise de janela fina na região.

4. **JSON estruturado.** `binwalk --log out.json` dá saída serializável (serde) com offset/size/
   confidence/description por match — perfeito pra alimentar o `session_logger` e correlacionar CVEs
   automaticamente depois. Muito melhor que parsear texto do v2.

5. **Instalação correta.** v3 é `cargo install binwalk` OU imagem Docker oficial. NÃO existe no pip.
   O que temos (v2.4.3 do fork OSPG) continua válido, mas pro próximo firmware vale rodar o v3 em
   paralelo e comparar — especialmente pra ver os falsos positivos que o v2 gera e o v3 corta.

---

## Verificação / próximo passo concreto

- [ ] Instalar v3 via cargo no ambiente LIBERTUS (`cargo install binwalk`) — cargo já está disponível
- [ ] Rodar v2 vs v3 no mesmo firmware ASUS RT-AC88U que já analisamos e diffar a lista de matches
- [ ] Medir quantos falsos positivos de LZMA o v2 gerava que o v3 corta
- [ ] Testar extractor UBI nativo do v3 vs pipeline ubireader atual

## Fontes (lidas de verdade, não citadas de cabeça)

- `ReFirmLabs/binwalk` branch master: `src/signatures/lzma.rs`, `src/signatures/trx.rs`,
  `src/signatures/common.rs`, `src/entropy.rs`, `src/common.rs`
- Release notes v3.1.0 (2024-10-31): "Complete re-write in Rust! Significantly faster, far fewer
  false positives, support for many more file extractors"
- Wiki oficial: Generating-Entropy-Graphs, Using-the-Rust-Library, Supported-Signatures
- Listagem de fonte: 94 parsers em `src/signatures/`, 52 extractors em `src/extractors/`
