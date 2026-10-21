#!/usr/bin/env python3
"""
sqfs_probe.py — localiza e VALIDA imagens SquashFS dentro de um firmware.

Motivo de existir: o binwalk v2 (fork OSPG, o que temos em ~/.local/bin) decide
"isto é SquashFS" com 4 bytes de magic + versão (offset 28/30) + ID de compressão
(offset 20). Ele NÃO confere block_size, block_log nem bytes_used. Resultado:
falso positivo em 10 bytes e falso negativo quando bytes_used passa do fim do
arquivo (a menos que se rode `binwalk -I`).

Este script aplica as mesmas checagens que o read_super() do unsquashfs faz
(squashfs-tools), reporta o veredito POR CAMPO e imprime o comando exato de
extração — incluindo o patch de magic para imagens de vendor (hsqt/shsq/...).

Uso:
    python3 sqfs_probe.py firmware.bin
    python3 sqfs_probe.py firmware.bin --json

Saída: veredito + comandos prontos (dd + unsquashfs). Exit code 0 se achou ao
menos uma imagem extraível, 1 se achou apenas suspeitas, 2 se não achou nada.
"""
import json
import math
import struct
import sys

MAGICS = {
    b"hsqs": ("LE", "padrão (v4, little endian)"),
    b"hsqt": ("LE", "DD-WRT (little endian)"),
    b"shsq": ("LE", "não-padrão D-Link (little endian)"),
    b"sqsh": ("BE", "big endian"),
    b"sqlz": ("BE", "LZMA big endian (squashfs 3.x)"),
    b"qshs": ("BE", "assinatura LZMA 3.3"),
    b"tqsh": ("BE", "DD-WRT big endian"),
}
COMPRESSORS = {1: "gzip", 2: "lzma", 3: "lzo", 4: "xz", 5: "lz4", 6: "zstd"}


def parse_super(data, off, endian):
    """Devolve dict com os campos do superblock (v4 = 96 bytes)."""
    if off + 96 > len(data):
        return {"error": "superbloco truncado (faltam bytes)"}
    fmt = endian + "4sIIIIHHHHHHQQQQQQQQ"
    vals = struct.unpack(fmt, data[off:off + 96])
    (magic, inodes, mkfs_time, block_size, fragments, compression, block_log,
     flags, no_ids, major, minor, root_inode, bytes_used, id_table,
     xattr_table, inode_table, dir_table, frag_table, lookup_table) = vals
    return dict(magic=magic, inodes=inodes, mkfs_time=mkfs_time,
                block_size=block_size, fragments=fragments,
                compression=compression, block_log=block_log, flags=flags,
                no_ids=no_ids, major=major, minor=minor, root_inode=root_inode,
                bytes_used=bytes_used, id_table=id_table,
                xattr_table=xattr_table, inode_table=inode_table,
                dir_table=dir_table, frag_table=frag_table,
                lookup_table=lookup_table)


def metadata_block_ok(data, table_start_abs, bytes_used_abs):
    """Confere o primeiro bloco de metadados de uma tabela (2 bytes de tamanho).

    SquashFS grava cada bloco de metadados como uint16 LE: bit 15 = bloco não
    comprimido, bits 0..14 = tamanho (máx. 8192). Se o ponteiro da tabela cair
    em padding/header de UBI, esse campo vira lixo — é o que pega imagem
    SquashFS "válida no superbloco" mas não extraível.
    """
    if table_start_abs + 2 > len(data) or table_start_abs + 2 > bytes_used_abs:
        return False, "ponteiro fora da área de dados"
    raw = struct.unpack("<H", data[table_start_abs:table_start_abs + 2])[0]
    blk = raw & 0x7FFF
    end = table_start_abs + 2 + blk
    if blk == 0 or blk > 8192:
        return False, f"tamanho de bloco implausível ({blk})"
    if end > bytes_used_abs:
        return False, f"bloco termina em 0x{end:X}, além de bytes_used 0x{bytes_used_abs:X}"
    return True, f"primeiro bloco = {blk} bytes"


def id_table_ok(data, image_off, id_table_rel, bytes_used_abs):
    """id_table_start aponta para o ÍNDICE da tabela (u64) — o bloco de metadados
    com os UIDs fica no endereço apontado por esse u64. É a mesma checagem que o
    binwalk v3 faz ("validate the UID table pointer and the first 64-bit pointer").
    """
    idx_abs = image_off + id_table_rel
    if idx_abs + 8 > len(data) or idx_abs + 8 > bytes_used_abs:
        return False, "índice da id_table fora da área de dados"
    ptr_rel = struct.unpack("<Q", data[idx_abs:idx_abs + 8])[0]
    if ptr_rel == 0 or ptr_rel >= bytes_used_abs:
        return False, f"primeiro ponteiro do índice = 0x{ptr_rel:X} (fora da imagem)"
    return metadata_block_ok(data, image_off + ptr_rel, bytes_used_abs)


def validate(sb, data, off, filesize, magic, endian):
    """Checagens equivalentes a read_super() do squashfs-tools + extras."""
    checks, fatal = [], False

    def check(ok, label, detail):
        nonlocal fatal
        checks.append({"ok": bool(ok), "check": label, "detail": detail})
        if not ok:
            fatal = True

    major, minor = sb["major"], sb["minor"]
    if major != 4:
        checks.append({"ok": False, "check": "versão",
                       "detail": f"s_major={major}.{minor} — unsquashfs moderno só monta v4.0 "
                                 f"(v3 exige unsquashfs3/sasquatch)"})
        return checks, True
    if minor != 0:
        checks.append({"ok": False, "check": "versão",
                       "detail": f"s_minor={minor} — só 0 é esperado em v4"})
        return checks, True

    comp = sb["compression"]
    check(comp in COMPRESSORS, "compressor",
          f"id={comp} ({COMPRESSORS.get(comp, 'DESCONHECIDO')})")

    bs, blog = sb["block_size"], sb["block_log"]
    check(4096 <= bs <= 1048576, "block_size", f"{bs} bytes (limite 4 KiB..1 MiB)")
    check(bs in (2 ** blog, 1 << blog), "block_log",
          f"block_log={blog} vs block_size={bs}" +
          ("" if bs == (1 << blog) else "  <- não batem"))
    if bs and bs & (bs - 1) == 0:
        checks.append({"ok": True, "check": "block_size potência de 2", "detail": "ok"})
    else:
        check(False, "block_size potência de 2", f"{bs} não é potência de 2")

    used = sb["bytes_used"]
    check(used >= 96, "bytes_used mínimo", f"{used} bytes")
    check(off + used <= filesize, "bytes_used cabe no arquivo",
          f"{off}+{used}={off + used} vs arquivo {filesize}" +
          ("" if off + used <= filesize else "  <- ponteiro além do EOF"))
    check(sb["id_table"] < max(used, 96), "id_table_start",
          f"0x{sb['id_table']:X} < bytes_used 0x{used:X}")
    check(sb["inode_table"] < sb["dir_table"] < max(used, 96), "ordem das tabelas",
          f"inode 0x{sb['inode_table']:X} < dir 0x{sb['dir_table']:X} < bytes_used 0x{used:X}")
    root_block = sb["root_inode"] >> 16
    check(root_block < max(used, 96), "root_inode",
          f"bloco 0x{root_block:X} dentro da imagem")

    # Estrutura de verdade: o primeiro bloco de metadados de cada tabela.
    if off + used <= filesize:
        ok_it, det_it = metadata_block_ok(data, off + sb["inode_table"], off + used)
        check(ok_it, "inode_table legível", det_it)
        ok_id, det_id = id_table_ok(data, off, sb["id_table"], off + used)
        check(ok_id, "id_table legível", det_id + " (falha aqui = imagem dentro de "
              "UBI/partição com headers intercalados; extraia o volume antes)")

    return checks, fatal


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    as_json = "--json" in sys.argv
    data = open(path, "rb").read()
    size = len(data)

    results = []
    for magic, (endian_hint, desc) in MAGICS.items():
        start = 0
        while True:
            off = data.find(magic, start)
            if off < 0:
                break
            start = off + 1
            endian = "<" if endian_hint == "LE" else ">"
            sb = parse_super(data, off, endian)
            entry = {"offset": off, "magic": magic.decode(), "variant": desc,
                     "endianness": "little" if endian_hint == "LE" else "big"}
            if "error" in sb:
                entry.update(verdict="NAO_VERIFICAVEL", reasons=[sb["error"]])
                results.append(entry)
                continue
            checks, fatal = validate(sb, data, off, size, magic, endian)
            entry["superblock"] = {k: (v if k != "magic" else v.decode("latin1"))
                                   for k, v in sb.items()}
            entry["checks"] = checks
            entry["compressor"] = COMPRESSORS.get(sb["compression"], "?")
            reasons = [f"{c['check']}: {c['detail']}" for c in checks if not c["ok"]]
            if fatal:
                entry["verdict"] = "INVALIDO"
                entry["reasons"] = reasons
            elif magic != b"hsqs":
                entry["verdict"] = "VALIDO_magic_vendor"
                entry["reasons"] = [f"magic '{magic.decode()}' não é aceito pelo "
                                    f"unsquashfs: copie os 4 bytes para 'hsqs' antes de montar"]
            else:
                entry["verdict"] = "VALIDO"
                entry["reasons"] = reasons
            dn = path.split("/")[-1]
            dd = (f"dd if={path} of=/tmp/{dn}.{off}.sqfs bs=1M "
                  f"iflag=skip_bytes,count_bytes skip={off} count={sb['bytes_used']}")
            entry["cmd_extract"] = dd
            if magic != b"hsqs":
                entry["cmd_patch"] = (f"printf 'hsqs' | dd of=/tmp/{dn}.{off}.sqfs "
                                      f"bs=1 seek=0 conv=notrunc")
                entry["cmd_unsquashfs"] = f"unsquashfs -d /tmp/rootfs_{off} /tmp/{dn}.{off}.sqfs"
            else:
                entry["cmd_unsquashfs"] = f"unsquashfs -d /tmp/rootfs_{off} /tmp/{dn}.{off}.sqfs"
            results.append(entry)

    order = {"VALIDO": 0, "VALIDO_magic_vendor": 1, "INVALIDO": 2, "NAO_VERIFICAVEL": 3}
    results.sort(key=lambda r: (order.get(r["verdict"], 9), r["offset"]))

    if as_json:
        print(json.dumps({"file": path, "size": size, "candidates": results}, indent=2))
    else:
        print(f"arquivo: {path} ({size} bytes) — {len(results)} candidato(s)\n")
        if not results:
            print("nenhuma assinatura SquashFS conhecida encontrada.")
            print("tente: binwalk -I <arquivo>  (mostra assinaturas marcadas como inválidas)")
            print("e    : ubireader_extract_images <arquivo>  se houver UBI antes do FS")
        for r in results:
            print(f"[{r['verdict']}] offset {r['offset']} (0x{r['offset']:X}) "
                  f"magic '{r['magic']}' — {r['variant']}, {r['endianness']}-endian")
            if "superblock" in r:
                sb = r["superblock"]
                print(f"    v{sb['major']}.{sb['minor']} | {r['compressor']} | "
                      f"block_size {sb['block_size']} | bytes_used {sb['bytes_used']} | "
                      f"inodes {sb['inodes']}")
                if sb["compression"] == 3:
                    print("    nota: binwalk v2 rotula id=3 como 'gzip (non-standard type definition)';"
                          " em v4 isso é LZO.")
            for reason in r["reasons"]:
                print(f"    ! {reason}")
            if r["verdict"].startswith("VALIDO"):
                print(f"    extrair: {r['cmd_extract']}")
                if "cmd_patch" in r:
                    print(f"    patch  : {r['cmd_patch']}")
                print(f"    montar : {r['cmd_unsquashfs']}")
            print()

    if any(r["verdict"].startswith("VALIDO") for r in results):
        return 0
    return 1 if results else 2


if __name__ == "__main__":
    sys.exit(main())
