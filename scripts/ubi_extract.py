#!/usr/bin/env python3
"""
ubi_extract.py — extrator de volumes UBI independente (sem ubireader).

Lê uma imagem UBI (ou um firmware que a contenha), valida os headers
on-flash e reconstrói os volumes a partir da tabela de volumes guardada
no "layout volume" (vol_id 0x7FFFEFFF, 2 LEBs redundantes).

Estruturas conforme drivers/mtd/ubi/ubi-media.h (kernel Linux):
  ubi_ec_hdr  64 B  magic "UBI#"  ec vid_hdr_offset data_offset image_seq hdr_crc
  ubi_vid_hdr 64 B  magic "UBI!"  vol_type copy_flag vol_id lnum data_size
                                  used_ebs data_pad data_crc sqnum hdr_crc
  ubi_vtbl_record 172 B  reserved_pebs alignment data_pad vol_type upd_marker
                         name_len name[128] flags pad crc

CRC dos headers: crc32(UBI_CRC32_INIT=0xFFFFFFFF, buf[:60]) SEM xorout final
  -> em Python: zlib.crc32(buf) ^ 0xFFFFFFFF   (CRC-32/JAMCRC)

Uso:
  ubi_extract.py firmware.trx                 # autodetecta início e PEB size
  ubi_extract.py ubi.img -o out/ --json
  ubi_extract.py ubi.img --peb-size 0x20000 --offset 0x400000
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import zlib

EC_MAGIC = b"UBI#"
VID_MAGIC = b"UBI!"
EC_HDR_SIZE = 64
VID_HDR_SIZE = 64
VTBL_RECORD_SIZE = 172
UBI_LAYOUT_VOL_ID = 0x7FFFFFFF - 4096  # 0x7FFFEFFF
UBI_MAX_VOLUMES = 128
PEB_CANDIDATES = [0x10000, 0x20000, 0x40000, 0x80000, 0x100000, 0x200000]
FF_ERASED = b"\xff"


def jamcrc(buf: bytes) -> int:
    """CRC-32 com init 0xFFFFFFFF e sem xorout (como crc32(UBI_CRC32_INIT, ...))."""
    return zlib.crc32(buf) ^ 0xFFFFFFFF


def u32(buf, off):
    return struct.unpack_from(">I", buf, off)[0]


def parse_ec(buf, off):
    if buf[off:off + 4] != EC_MAGIC:
        return None
    magic, version, _pad1, ec, vid_off, data_off, image_seq = struct.unpack_from(
        ">I B 3s Q I I I", buf, off)
    hdr_crc = u32(buf, off + 60)
    calc = jamcrc(buf[off:off + 60])
    return {
        "version": version, "ec": ec, "vid_hdr_offset": vid_off,
        "data_offset": data_off, "image_seq": image_seq,
        "hdr_crc": hdr_crc, "hdr_crc_ok": calc == hdr_crc,
    }


def parse_vid(buf, off):
    if buf[off:off + 4] != VID_MAGIC:
        return None
    (version, vol_type, copy_flag, compat) = struct.unpack_from(">B B B B", buf, off + 4)
    vol_id, lnum = struct.unpack_from(">I I", buf, off + 8)
    data_size, used_ebs, data_pad, data_crc = struct.unpack_from(">I I I I", buf, off + 20)
    sqnum = struct.unpack_from(">Q", buf, off + 40)[0]
    hdr_crc = u32(buf, off + 60)
    calc = jamcrc(buf[off:off + 60])
    return {
        "version": version, "vol_type": vol_type, "copy_flag": copy_flag,
        "compat": compat, "vol_id": vol_id, "lnum": lnum,
        "data_size": data_size, "used_ebs": used_ebs, "data_pad": data_pad,
        "data_crc": data_crc, "sqnum": sqnum,
        "hdr_crc": hdr_crc, "hdr_crc_ok": calc == hdr_crc,
    }


def detect_offset(buf):
    """Primeiro offset com EC header íntegro."""
    idx = buf.find(EC_MAGIC)
    while idx != -1:
        ec = parse_ec(buf, idx)
        if ec and ec["hdr_crc_ok"] and ec["version"] == 1:
            return idx
        idx = buf.find(EC_MAGIC, idx + 1)
    return None


def detect_peb_size(buf, base):
    """Testa candidatos: EC header íntegro em base + k*peb_size para vários k."""
    total = len(buf) - base
    best = None
    for cand in PEB_CANDIDATES:
        if cand > total:
            continue
        hits = checked = 0
        k = 0
        while base + k * cand < len(buf) and checked < 12:
            off = base + k * cand
            if buf[off:off + 4] == FF_ERASED * 4:
                k += 1
                continue
            checked += 1
            ec = parse_ec(buf, off)
            if ec and ec["hdr_crc_ok"]:
                hits += 1
            k += 1
        if checked and hits == checked:
            best = cand
            break
    return best


def parse_vtbl_records(leb_data):
    recs = []
    for i in range(min(UBI_MAX_VOLUMES, len(leb_data) // VTBL_RECORD_SIZE)):
        off = i * VTBL_RECORD_SIZE
        raw = leb_data[off:off + VTBL_RECORD_SIZE]
        if raw == b"\xff" * VTBL_RECORD_SIZE:
            continue  # slot nunca escrito (flash apagada) — não invalida a tabela
        reserved_pebs, alignment, data_pad = struct.unpack_from(">I I I", raw, 0)
        vol_type, upd_marker, name_len = struct.unpack_from(">B B H", raw, 12)
        name = raw[16:16 + name_len]
        flags = raw[144]
        crc = u32(raw, 168)
        ok = jamcrc(raw[:168]) == crc
        if reserved_pebs == 0 and name_len == 0:
            continue  # registro vazio
        recs.append({
            "vol_id": i, "reserved_pebs": reserved_pebs, "alignment": alignment,
            "data_pad": data_pad, "vol_type": vol_type, "upd_marker": upd_marker,
            "name": name.decode("utf-8", "replace"), "flags": flags,
            "crc_ok": ok,
        })
    return recs


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("-o", "--outdir", default=None)
    ap.add_argument("--offset", default=None, help="offset do primeiro PEB (default: autodetect)")
    ap.add_argument("--peb-size", default=None, help="tamanho do PEB (default: autodetect)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    buf = open(args.image, "rb").read()
    base = int(args.offset, 0) if args.offset else detect_offset(buf)
    if base is None:
        sys.exit("ERRO: nenhum EC header (UBI#) com CRC válido encontrado")
    peb_size = int(args.peb_size, 0) if args.peb_size else detect_peb_size(buf, base)
    if not peb_size:
        sys.exit("ERRO: PEB size não detectado; passe --peb-size")

    report = {
        "image": args.image, "file_size": len(buf),
        "ubi_start": base, "peb_size": peb_size,
        "peb_count": (len(buf) - base) // peb_size,
        "pebs": [], "volumes": [], "anomalies": [],
    }

    pebs = []
    vid_offsets = {}
    data_offsets = {}
    erased = 0
    for k in range((len(buf) - base) // peb_size):
        off = base + k * peb_size
        if buf[off:off + 4] == FF_ERASED * 4:
            erased += 1
            continue  # PEB apagado, fora de uso
        ec = parse_ec(buf, off)
        if ec is None:
            if buf[off:off + 4] == b"\xde\xad\xc0\xde":
                # marcador "dead code" do OpenWrt (firmware-utils/imagetag + libfstools):
                # bloco de padding que sinaliza overlay ainda não formatado.
                report.setdefault("openwrt_deadcode_pebs", []).append(k)
                continue
            report["anomalies"].append(f"PEB {k}: sem magic UBI# (0x{buf[off:off+4].hex()})")
            continue
        if not ec["hdr_crc_ok"]:
            report["anomalies"].append(f"PEB {k}: EC hdr_crc inválido")
            continue
        vid_offsets.setdefault(ec["vid_hdr_offset"], 0)
        vid_offsets[ec["vid_hdr_offset"]] += 1
        data_offsets.setdefault(ec["data_offset"], 0)
        data_offsets[ec["data_offset"]] += 1
        vid = parse_vid(buf, off + ec["vid_hdr_offset"])
        if vid is None:
            # PEB sem VID = PEB livre (EC header escrito, ainda não mapeado)
            continue
        if not vid["hdr_crc_ok"]:
            report["anomalies"].append(f"PEB {k}: VID hdr_crc inválido (vol {vid['vol_id']} lnum {vid['lnum']})")
            continue
        pebs.append((k, off, ec, vid))

    if len(vid_offsets) > 1 or len(data_offsets) > 1:
        report["anomalies"].append(
            f"headers com offsets inconsistentes: vid={vid_offsets} data={data_offsets}")
    vid_hdr_offset = max(vid_offsets, key=vid_offsets.get)
    data_offset = max(data_offsets, key=data_offsets.get)

    # mapa (vol_id, lnum) -> melhor PEB (maior sqnum)
    mapping = {}
    dups = 0
    for (k, off, ec, vid) in pebs:
        key = (vid["vol_id"], vid["lnum"])
        prev = mapping.get(key)
        if prev is not None:
            dups += 1
            if vid["sqnum"] < prev[3]["sqnum"]:
                continue
        mapping[key] = (k, off, ec, vid)

    leb_sizes = {}
    vol_lebs = {}
    for (vol_id, lnum), (k, off, ec, vid) in mapping.items():
        leb = peb_size - vid["data_pad"] - data_offset
        leb_sizes[vol_id] = leb
        vol_lebs.setdefault(vol_id, {})[lnum] = (k, off, vid)

    def assemble(vol_id, reserved_pebs=None, data_pad=0):
        lebs = vol_lebs.get(vol_id, {})
        if not lebs:
            return b"", []          # volume dinâmico sem nenhum LEB gravado
        leb = leb_sizes.get(vol_id, peb_size - data_offset - data_pad)
        last = max(lebs)
        n = max(last + 1, reserved_pebs or 0)
        out = bytearray(leb * n)
        holes = []
        for idx in range(n):
            item = lebs.get(idx)
            if item is None:
                out[idx * leb:(idx + 1) * leb] = FF_ERASED * leb
                if idx < last:
                    holes.append(idx)
                continue
            k, off, vid = item
            start = off + data_offset
            chunk = buf[start:start + leb]
            out[idx * leb:idx * leb + len(chunk)] = chunk
        return bytes(out), holes

    # layout volume -> volume table
    layout_lebs = vol_lebs.get(UBI_LAYOUT_VOL_ID, {})
    vtbl = []
    vtbl_source = None
    for lnum in sorted(layout_lebs):
        k, off, vid = layout_lebs[lnum]
        leb = peb_size - data_offset
        data = buf[off + data_offset:off + data_offset + leb]
        recs = parse_vtbl_records(data)
        if recs and all(r["crc_ok"] for r in recs):
            vtbl = recs
            vtbl_source = lnum
            break
    if not vtbl:
        report["anomalies"].append("volume table não legível (layout volume ausente ou CRC inválido)")

    if args.outdir:
        os.makedirs(args.outdir, exist_ok=True)

    for rec in vtbl:
        vol_id = rec["vol_id"]
        if rec["vol_type"] == 2:
            # estático: tamanho = (used_ebs-1)*leb + data_size do último LEB
            lebs = vol_lebs.get(vol_id, {})
            if not lebs:
                continue
            last = max(lebs)
            lk, loff, lvid = lebs[last]
            size = last * (peb_size - data_offset - rec["data_pad"]) + lvid["data_size"]
            data = assemble(vol_id)[0][:size]
        else:
            data = assemble(vol_id, rec["reserved_pebs"], rec["data_pad"])[0]
        entry = {
            "vol_id": vol_id, "name": rec["name"], "type": "static" if rec["vol_type"] == 2 else "dynamic",
            "reserved_pebs": rec["reserved_pebs"], "leb_size": peb_size - data_offset - rec["data_pad"],
            "mapped_lebs": len(vol_lebs.get(vol_id, {})),
            "size": len(data), "sha256": sha256(data),
        }
        if args.outdir:
            path = os.path.join(args.outdir, f"vol{vol_id:03d}_{rec['name'] or 'sem_nome'}.img")
            with open(path, "wb") as f:
                f.write(data)
            entry["path"] = path
        report["volumes"].append(entry)

    # volumes mapeados sem registro na vtbl (não deveria acontecer)
    known = {r["vol_id"] for r in vtbl} | {UBI_LAYOUT_VOL_ID}
    for vol_id in sorted(vol_lebs):
        if vol_id not in known:
            data = assemble(vol_id)[0]
            report["anomalies"].append(f"volume {vol_id} tem LEBs mapeados mas não está na volume table")

    report["vid_hdr_offset"] = vid_hdr_offset
    report["data_offset"] = data_offset
    report["erased_pebs"] = erased
    report["vtbl_source_lnum"] = vtbl_source
    report["duplicate_mappings"] = dups
    report["image_seq"] = sorted({ec["image_seq"] for (_k, _o, ec, _v) in pebs})
    report["erase_counters"] = sorted({ec["ec"] for (_k, _o, ec, _v) in pebs})[:8]

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"imagem        : {report['image']} ({report['file_size']} bytes)")
        print(f"UBI em        : 0x{base:X}  |  PEB size 0x{peb_size:X} ({peb_size} B)  |  {report['peb_count']} PEBs")
        print(f"headers       : vid_hdr_offset=0x{vid_hdr_offset:X} data_offset=0x{data_offset:X} image_seq={report['image_seq']}")
        print(f"PEBs com VID  : {len(pebs)}  |  mapeamentos duplicados: {dups}  |  EC values: {report['erase_counters']}")
        print(f"volume table  : {len(vtbl)} volume(s), cópia lida do LEB {vtbl_source}" if vtbl else "volume table  : ilegível")
        for v in report["volumes"]:
            print(f"  vol {v['vol_id']:3d} {v['name']:<16} {v['type']:<7} {v['size']:>9} B  "
                  f"lebs {v['mapped_lebs']}/{v['reserved_pebs']}  sha256 {v['sha256'][:16]}")
        for a in report["anomalies"]:
            print(f"  ! {a}")
        if report.get("openwrt_deadcode_pebs"):
            print(f"  # marcador OpenWrt DEADC0DE em PEB(s) {report['openwrt_deadcode_pebs']} "
                  f"(padding/overlay não formatado, não é corrupção)")


if __name__ == "__main__":
    main()
