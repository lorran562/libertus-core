#!/usr/bin/env python3
"""
test_ubi_extract.py — testes de borda do extrator ubi_extract.py com imagens sintéticas.

Constrói imagens UBI à mão (sem ubinize) para exercitar caminhos que o firmware
real do lab não cobre:
  * volume dinâmico com buraco (LEB não mapeado no meio)
  * volume estático (data_size no último LEB + data_crc)
  * mapeamento duplicado do mesmo (vol_id, lnum) -> maior sqnum vence
  * PEB apagado (0xFF) no meio
  * vtbl com cópia A corrompida -> leitor deve cair na cópia B

Uso: python3 scripts/tests/test_ubi_extract.py
"""
import hashlib
import os
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXTRACTOR = ROOT / "scripts" / "ubi_extract.py"
PEB = 0x10000
VID_OFF = 0x40
DATA_OFF = 0x800
LEB = PEB - DATA_OFF
LAYOUT_ID = 0x7FFFFFFF - 4096


def jamcrc(b):
    return zlib.crc32(b) ^ 0xFFFFFFFF


def ec_hdr(ec=0, image_seq=0x11223344):
    body = struct.pack(">I B 3s Q I I I 32s", 0x55424923, 1, b"\0\0\0", ec,
                       VID_OFF, DATA_OFF, image_seq, b"\0" * 32)
    return body + struct.pack(">I", jamcrc(body))


def vid_hdr(vol_id, lnum, vol_type=1, data_size=0, used_ebs=0, sqnum=0,
            copy_flag=0, data_crc=0, compat=0, data_pad=0):
    body = struct.pack(">I B B B B I I 4s I I I I 4s Q 12s",
                       0x55424921, 1, vol_type, copy_flag, compat,
                       vol_id, lnum, b"\0" * 4, data_size, used_ebs, data_pad,
                       data_crc, b"\0" * 4, sqnum, b"\0" * 12)
    return body + struct.pack(">I", jamcrc(body))


def vtbl_record(vol_id, name, reserved_pebs, vol_type=1, alignment=1, data_pad=0):
    name_b = name.encode()
    body = struct.pack(">I I I B B H", reserved_pebs, alignment, data_pad,
                       vol_type, 0, len(name_b))
    body += name_b.ljust(128, b"\0") + struct.pack(">B", 0) + b"\0" * 23
    return body + struct.pack(">I", jamcrc(body))


def peb_with(vol_lnum, payload=b"", **kw):
    """Monta um PEB completo: EC header + VID header + dados + 0xFF no resto."""
    buf = bytearray(b"\xff" * PEB)
    buf[0:64] = ec_hdr(**{k: v for k, v in kw.items() if k in ("ec", "image_seq")})
    buf[VID_OFF:VID_OFF + 64] = vid_hdr(*vol_lnum, **{k: v for k, v in kw.items()
                                                      if k not in ("ec", "image_seq")})
    buf[DATA_OFF:DATA_OFF + len(payload)] = payload
    return bytes(buf)


def build_image(path):
    lebs = {}

    # volume table: vol0 "dados" dinâmico 4 PEBs, vol1 "kernel" estático 2 PEBs
    recs = (vtbl_record(0, "dados", 4, vol_type=1) +
            vtbl_record(1, "kernel", 2, vol_type=2))
    lebs[0] = peb_with((LAYOUT_ID, 0), recs.ljust(LEB, b"\xff"))
    bad = bytearray(recs.ljust(LEB, b"\xff"))
    bad[10] ^= 0xFF  # corrompe a cópia B
    lebs[1] = peb_with((LAYOUT_ID, 1), bytes(bad))

    lebs[2] = peb_with((0, 0), b"A" * 100)                       # será sobrescrito
    lebs[3] = peb_with((0, 2), b"C" * LEB)                       # lnum 1 = buraco
    lebs[4] = peb_with((0, 0), b"Z" * 777, sqnum=9, copy_flag=1)  # duplicata vence
    lebs[5] = peb_with((0, 3), b"D" * 500)
    lebs[6] = peb_with((1, 0), b"K" * LEB, vol_type=2, used_ebs=2,
                       data_size=LEB, data_crc=jamcrc(b"K" * LEB))
    lebs[7] = peb_with((1, 1), b"k" * 500, vol_type=2, used_ebs=2,
                       data_size=500, data_crc=jamcrc(b"k" * 500))
    # PEB 8 fica apagado (0xFF) no meio — deve ser ignorado sem erro

    img = bytearray()
    for i in range(10):
        img += lebs.get(i, b"\xff" * PEB)
    Path(path).write_bytes(bytes(img))

    esperado = {}
    v0 = bytearray(b"\xff" * (4 * LEB))
    v0[0:777] = b"Z" * 777                 # lnum0 = cópia com sqnum 9
    v0[LEB:2 * LEB] = b"\xff" * LEB        # lnum1 = buraco
    v0[2 * LEB:3 * LEB] = b"C" * LEB       # lnum2
    v0[3 * LEB:3 * LEB + 500] = b"D" * 500
    esperado["vol000_dados.img"] = bytes(v0)
    esperado["vol001_kernel.img"] = b"K" * LEB + b"k" * 500
    return esperado


def main():
    tmp = tempfile.mkdtemp(prefix="ubi_test_")
    img = os.path.join(tmp, "sintetica.bin")
    esperado = build_image(img)
    outdir = os.path.join(tmp, "out")

    r = subprocess.run([sys.executable, str(EXTRACTOR), img, "-o", outdir, "--json"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("FALHOU: extrator retornou", r.returncode)
        print(r.stdout, r.stderr)
        return 1

    import json
    rep = json.loads(r.stdout)
    falhas = []

    if rep["peb_size"] != PEB:
        falhas.append(f"peb_size detectado {rep['peb_size']:#x} != {PEB:#x}")
    nomes = {v["name"]: v for v in rep["volumes"]}
    for esperado_nome, dados in esperado.items():
        vol = [v for v in rep["volumes"] if v["name"] in esperado_nome][0]
        caminho = os.path.join(outdir, esperado_nome)
        obtido = Path(caminho).read_bytes()
        if obtido != dados:
            falhas.append(f"{esperado_nome}: bytes diferentes "
                          f"(obtido {len(obtido)} B, esperado {len(dados)} B)")
        if vol["sha256"] != hashlib.sha256(dados).hexdigest():
            falhas.append(f"{esperado_nome}: sha256 do relatório não bate")

    if nomes["dados"]["type"] != "dynamic" or nomes["kernel"]["type"] != "static":
        falhas.append("tipos de volume errados no relatório")
    if rep.get("erased_pebs") != 2:
        falhas.append(f"erased_pebs={rep.get('erased_pebs')} (esperado 2: PEBs 8 e 9)")

    print(f"imagem sintética: {img} ({os.path.getsize(img)} B, 10 PEBs de {PEB:#x})")
    for v in rep["volumes"]:
        print(f"  vol {v['vol_id']} {v['name']:<8} {v['type']:<7} {v['size']:>6} B  "
              f"lebs {v['mapped_lebs']}/{v['reserved_pebs']}")
    print("  anomalias:", rep["anomalies"] or "nenhuma")
    if falhas:
        print("\nFALHAS:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nOK: buraco, estático, duplicata por sqnum, vtbl corrompida e PEB apagado")
    return 0


if __name__ == "__main__":
    sys.exit(main())
