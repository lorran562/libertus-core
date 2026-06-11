#!/usr/bin/env python3
"""
Extração manual do firmware ASUS RT-AC88U (TRX format)
Sem root, sem ferramentas externas — puro Python.
"""
import os, struct, lzma, sys

fw_path = "asus_rt-ac88u-openwrt.trx"
out_dir = "extracted"
os.makedirs(out_dir, exist_ok=True)

with open(fw_path, "rb") as f:
    data = f.read()

print(f"[*] Firmware: {len(data)} bytes ({len(data)//1024//1024}MB)")
print(f"[*] Magic: {data[:4]}")

# TRX Header (28 bytes)
# magic(4) + size(4) + crc(4) + flags(2) + version(2) + offset[3](4 each)
magic, size, crc32, flags, version = struct.unpack_from('<4sIIHH', data, 0)
off0, off1, off2 = struct.unpack_from('<III', data, 16)

print(f"[*] TRX Header:")
print(f"    Magic:   {magic}")
print(f"    Size:    {size} bytes")
print(f"    Flags:   0x{flags:04X}")
print(f"    Version: {version}")
print(f"    Offset0 (loader/kernel): {off0} (0x{off0:X})")
print(f"    Offset1 (linux kernel):  {off1} (0x{off1:X})")  
print(f"    Offset2 (rootfs):        {off2} (0x{off2:X})")

# Extrai LZMA kernel (offset 28)
kernel_lzma = data[28:off1]
print(f"\n[*] Kernel LZMA: {len(kernel_lzma)} bytes")

# Tenta descomprimir LZMA
print("[*] Descomprimindo kernel LZMA...")
try:
    # LZMA raw (sem container)
    dec = lzma.decompress(kernel_lzma)
    kernel_out = os.path.join(out_dir, "kernel.bin")
    with open(kernel_out, "wb") as f:
        f.write(dec)
    print(f"[+] Kernel extraido: {len(dec)} bytes -> {kernel_out}")
except Exception as e:
    print(f"[-] LZMA direto falhou: {e}")
    # Salva raw para análise
    with open(os.path.join(out_dir, "kernel.lzma"), "wb") as f:
        f.write(kernel_lzma)
    print(f"[*] Kernel LZMA salvo raw: {out_dir}/kernel.lzma")

# Extrai UBI filesystem (offset 0x400000)
rootfs_ubi = data[off1:]
print(f"\n[*] RootFS UBI: {len(rootfs_ubi)} bytes")

ubi_out = os.path.join(out_dir, "rootfs.ubi")
with open(ubi_out, "wb") as f:
    f.write(rootfs_ubi)
print(f"[+] RootFS UBI salvo: {ubi_out}")

# Analisa strings no kernel para info de versão
print("\n[*] Analisando strings no firmware completo...")
strings_found = []
current = []
for byte in data:
    if 32 <= byte <= 126:
        current.append(chr(byte))
    else:
        if len(current) >= 8:
            s = ''.join(current)
            strings_found.append(s)
        current = []

# Filtra strings interessantes
interesting = []
keywords = ['version', 'Version', 'passwd', 'password', 'admin', 'root', 
            'secret', 'key', 'token', 'login', 'auth', 'credential',
            'telnet', 'ssh', 'http', 'cgi', 'nvram', 'gpio',
            'asus', 'ASUS', 'RT-AC', 'RT-AX', 'WPS', 'wlan',
            '/etc/', '/tmp/', '/var/', 'busybox', 'BusyBox',
            'wget', 'curl', 'nc ', 'netcat', 'chmod', 'shell',
            'CONFIG', 'DEBUG', 'ERROR', '/proc/', '/sys/']

for s in strings_found:
    for kw in keywords:
        if kw in s:
            interesting.append(s)
            break

# Remove duplicatas e ordena
interesting = list(dict.fromkeys(interesting))

print(f"[*] Total strings >= 8 chars: {len(strings_found)}")
print(f"[*] Strings interessantes: {len(interesting)}")
print("\n=== STRINGS RELEVANTES ===")
for s in interesting[:80]:
    print(f"  {s[:120]}")

# Salva análise completa
analysis_file = os.path.join(out_dir, "strings_analysis.txt")
with open(analysis_file, "w") as f:
    f.write(f"Firmware: {fw_path}\n")
    f.write(f"Tamanho: {len(data)} bytes\n")
    f.write(f"TRX Version: {version}\n\n")
    f.write("=== TODAS AS STRINGS INTERESSANTES ===\n")
    for s in interesting:
        f.write(s + "\n")
print(f"\n[+] Análise completa salva: {analysis_file}")
