#!/usr/bin/env python3
"""
trx_probe.py — leitor/verificador de cabecalho TRX (Broadcom) independente do binwalk.

Motivo: o binwalk v2 lista "TRX firmware image" olhando 4 bytes de magic, e o
binwalk v3 so aceita a assinatura se o CRC-32 bater. Nenhum dos dois explica
QUAL CRC. Este script mostra o campo, testa as convencoes candidatas e diz qual
bate — alem de checar a tabela de offsets, que o v2 ignora.

Formato (firmware-utils/src/trx.c):
  0x00 u32 magic  "HDR0" (0x30524448)
  0x04 u32 len    tamanho total, incluindo header (multiplo de 0x1000)
  0x08 u32 crc32  CRC de flag_version ate o fim
  0x0C u16 flags
  0x0E u16 version (1 ou 2)
  0x10 u32 offsets[4] (v1 usa 3 -> header de 28 bytes; v2 usa 4 -> 32 bytes)

CRC (crc32buf em trx.c): tabela refletida 0xEDB88320, init 0xFFFFFFFF,
SEM inversao final  -> e o CRC-32/JAMCRC, nao o CRC-32/ISO-HDLC do zlib.
Cobertura: bytes [12 .. len).
TRXv2: ao calcular, 8 bytes em (ultimo offset + 22) valem 0xFF (contadores
stable/try1-3 do bin header, mascarados pelo CFE) e sao restaurados depois.

Uso:
  trx_probe.py arquivo.trx            # analisa
  trx_probe.py --fix arq.trx          # regrava crc32/len corretos (backup .bak)
  trx_probe.py --json arq.trx         # saida para script
"""
import json
import struct
import sys
import zlib
from pathlib import Path

CRC_START = 12
MAGICS = {
    b"HDR0": "TRX (Broadcom/OpenWrt)",
    b"hsqs": None,  # nao e TRX, so para nao confundir
}


def jamcrc(data: bytes) -> int:
    """CRC-32 refletido, init 0xFFFFFFFF, sem xorout final (= crc32buf do trx.c)."""
    return zlib.crc32(data) ^ 0xFFFFFFFF


def parse(buf: bytes) -> dict:
    if len(buf) < 28:
        raise ValueError(f"arquivo curto demais para header TRX ({len(buf)} bytes)")
    magic, length, crc, flag_version = struct.unpack_from("<IIII", buf, 0)
    flags, version = flag_version & 0xFFFF, flag_version >> 16
    offs = list(struct.unpack_from("<4I", buf, 16))
    hdr_size = 32 if version == 2 else 28
    used = offs[:4] if version == 2 else offs[:3]
    return {
        "magic": magic,
        "len": length,
        "crc": crc,
        "flags": flags,
        "version": version,
        "header_size": hdr_size,
        "offsets_raw": offs,
        "offsets": [o for o in used if o != 0],
    }


def crc_candidates(buf: bytes, h: dict) -> dict:
    """Testa as convencoes plausiveis. Chave -> valor calculado."""
    out = {}
    ln = h["len"]
    end = min(ln, len(buf)) if ln else len(buf)
    if end <= CRC_START:
        return out

    body = buf[CRC_START:end]
    out["jamcrc[12:len]"] = jamcrc(body)
    out["zlib[12:len]"] = zlib.crc32(body)
    if len(buf) != end:
        out["jamcrc[12:eof]"] = jamcrc(buf[CRC_START:])
        out["zlib[12:eof]"] = zlib.crc32(buf[CRC_START:])
    # cobertura classica errada: a partir de 0x1C (fim do header v1)
    out["jamcrc[28:len]"] = jamcrc(buf[28:end])
    out["zlib[28:len]"] = zlib.crc32(buf[28:end])

    # TRXv2: mascarar bin header (offset do ultimo volume + 22, 8 bytes = 0xFF)
    if h["version"] == 2 and h["offsets"]:
        binhdr = h["offsets"][-1]
        if binhdr + 30 <= end:
            masked = bytearray(buf[CRC_START:end])
            base = CRC_START
            masked[binhdr + 22 - base: binhdr + 30 - base] = b"\xff" * 8
            out["jamcrc[12:len]+binhdr-mask"] = jamcrc(bytes(masked))
            out["zlib[12:len]+binhdr-mask"] = zlib.crc32(bytes(masked))
    return out


def analyze(path: Path, verbose: bool = True) -> dict:
    buf = path.read_bytes()
    res = {"file": str(path), "size": len(buf)}
    try:
        h = parse(buf)
    except ValueError as e:
        res["error"] = str(e)
        return res
    res.update(h)
    res["ok"] = False
    res["problems"] = []

    if h["magic"] != 0x30524448:
        res["problems"].append(f"magic {h['magic']:#010x} nao e HDR0 (0x30524448)")
    if h["version"] not in (1, 2):
        res["problems"].append(f"versao {h['version']} nao e 1 nem 2")
    if h["len"] > len(buf):
        res["problems"].append(f"len={h['len']} > tamanho do arquivo {len(buf)} (dump truncado?)")
    if h["len"] < h["header_size"]:
        res["problems"].append(f"len={h['len']} menor que o header ({h['header_size']})")
    if h["len"] and h["len"] % 0x1000:
        res["problems"].append(f"len={h['len']} nao e multiplo de 0x1000 (trx.c sempre alinha)")

    offs = h["offsets"]
    if offs:
        if offs[0] != h["header_size"]:
            res["problems"].append(
                f"offsets[0]={offs[0]:#x} != header_size {h['header_size']:#x}")
        if offs != sorted(offs):
            res["problems"].append(f"offsets fora de ordem: {[hex(o) for o in offs]}")
        bad = [o for o in offs if h["len"] and o >= h["len"]]
        if bad:
            res["problems"].append(f"offset dentro do header ou alem de len: {[hex(o) for o in bad]}")

    cands = crc_candidates(buf, h)
    res["crc_candidates"] = {k: f"0x{v:08X}" for k, v in cands.items()}
    match = [k for k, v in cands.items() if v == h["crc"]]
    res["crc_match"] = match
    if not match:
        res["problems"].append(f"CRC {h['crc']:#010x} nao bate com nenhuma convencao testada")
    res["ok"] = not res["problems"]
    res["crc_convention"] = match[0] if match else None

    if verbose:
        print(f"arquivo : {path}  ({len(buf)} bytes)")
        print(f"magic   : {h['magic']:#010x} ({buf[:4]!r})")
        print(f"versao  : {h['version']}   flags: {h['flags']:#06x}   header: {h['header_size']} bytes")
        print(f"len     : {h['len']} ({h['len']:#x})   arquivo: {len(buf)}")
        print(f"crc     : {h['crc']:#010x}")
        print(f"offsets : {[hex(o) for o in h['offsets_raw']]}")
        if cands:
            print("CRC candidatos:")
            for k, v in cands.items():
                print(f"   {'OK ' if v == h['crc'] else '   '} {k:<28} {v:#010x}")
        if res["problems"]:
            print("PROBLEMAS:")
            for p in res["problems"]:
                print(f"   ! {p}")
        else:
            print("VEREDITO: header consistente (magic + versao + len + offsets + CRC)")
    return res


def fix(path: Path) -> int:
    buf = bytearray(path.read_bytes())
    h = parse(bytes(buf))
    ln = h["len"] if h["len"] and h["len"] <= len(buf) else len(buf)
    if ln % 0x1000:
        ln += 0x1000 - (ln % 0x1000)
        ln = min(ln, len(buf))
    body = bytearray(buf[CRC_START:ln])
    if h["version"] == 2 and h["offsets"]:
        b = h["offsets"][-1]
        if b + 30 <= ln:
            body[b + 22 - CRC_START: b + 30 - CRC_START] = b"\xff" * 8
    crc = jamcrc(bytes(body))
    backup = path.with_suffix(path.suffix + ".bak")
    if not backup.exists():
        backup.write_bytes(bytes(buf))
    struct.pack_into("<I", buf, 4, ln)
    struct.pack_into("<I", buf, 8, crc)
    path.write_bytes(bytes(buf))
    print(f"regravado: len={ln} crc={crc:#010x} (backup em {backup.name})")
    return 0


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = {a for a in argv[1:] if a.startswith("--")}
    if not args:
        print(__doc__)
        return 2
    path = Path(args[0])
    if "--fix" in flags:
        return fix(path)
    res = analyze(path, verbose="--json" not in flags)
    if "--json" in flags:
        print(json.dumps(res, indent=2))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
