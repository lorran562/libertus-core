# SENTINEL

Proactive Firmware Intelligence Engine — by LIBERTUS / SHIELD Security Research

## Quick Start

```bash
python3 sentinel.py <path_to_rootfs>
```

## Example

```bash
python3 sentinel.py ~/LIBERTUS/lab/firmware/asus-rt-ac88u/extracted/rootfs
```

## Modules

- A: ELF binary inventory (arch, size, stripped, setuid)
- B: NVRAM->exec chain detection (command injection patterns)
- C: Hardcoded credentials (hashes, keys, tokens)
- D: Missing protections (no-PIE, no-NX, no-canary, no-RELRO)
- E: Suspicious strings (backdoors, shells, droppers)

## Output

Risk score 0-100 + structured JSON report saved to reports/

See IDEIA.md for full vision, evolution roadmap, and SHIELD monetization plan.
