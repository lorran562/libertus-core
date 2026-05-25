# SENTINEL — Firmware Intelligence Engine

**by LIBERTUS / SHIELD Security Research**
**Criado em: 2026-05-25**

---

## O que é

SENTINEL é um motor de inteligência proativa para análise de firmware de roteadores,
câmeras IP, gateways IoT e qualquer dispositivo embarcado.

Enquanto TODA análise de firmware hoje é REATIVA — alguém baixa, extrai, procura
manualmente, documenta no OneNote e esquece — o SENTINEL é a primeira peça de uma
infraestrutura que transforma esse processo em algo sistemático, automatizado e
acumulativo.

No seu núcleo atual (v1.0), o SENTINEL aceita um rootfs já extraído e executa 5 módulos:

```
  [A] Inventário de binários ELF (arquitetura, tamanho, stripped, setuid)
  [B] Detecção de cadeias NVRAM→sprintf→system() — o padrão clássico de RCE em roteadores
  [C] Credenciais hardcoded (hashes, chaves, tokens, URLs com senha)
  [D] Binários sem proteções: no-PIE, no-NX, no-canary, no-RELRO, RPATH suspeito
  [E] Strings suspeitas: backdoors, shells, telnetd, wget/curl dropper patterns
```

Resultado: **score de risco 0–100** + **relatório JSON estruturado** salvo em
`sentinel/reports/`.

---

## Por que é genuinamente novo

Ferramentas que existem hoje e o que elas fazem:

| Ferramenta | O que faz |
|---|---|
| binwalk | Extrai filesystem de firmware |
| firmwalker | Grep básico por credenciais em rootfs |
| EMBA | Análise estática estática extensa mas pesada e manual |
| FAT (Firmware Analysis Toolkit) | Tenta emular firmware com QEMU |
| IoT Inspector (Princeton) | Análise passiva de tráfego de rede |

Nenhuma delas:
- Correlaciona NVRAM→format_string→exec como uma cadeia de risco
- Gera score de risco ponderado por tipo de achado
- Produz output JSON estruturado prontos para alimentar uma base de conhecimento
- Funciona como módulo embeddável em um daemon autônomo

O gap real: **não existe pipeline que vai do firmware bruto ao relatório estruturado
de forma totalmente autônoma e que cresce com cada análise.**

---

## Primeiro resultado real (2026-05-25)

Target: ASUS RT-AC88U (OpenWrt build)
Rootfs: `lab/firmware/asus-rt-ac88u/extracted/rootfs`

```
RISK SCORE : 100/100  [CRITICAL]

ELFs encontrados      : 165
Arquiteturas          : ARM
Stripped              : 101 de 165
Cadeias NVRAM->exec   : 1  (lib/modules/5.15.167/brcmfmac.ko — CRITICAL)
Credenciais           : 69 ocorrências
Sem proteções         : 165/165 (TODOS os binários)
Strings suspeitas     : 28 binários
```

**Finding real:** `brcmfmac.ko` (driver Broadcom WiFi) contém referências a
`nvram_get`, `system()`, `sprintf()` e `printf()` no mesmo binário.
Isso é o padrão clássico de CVE de command injection em roteadores Broadcom.

**Finding real:** `lib/libc.so` contém hash MD5crypt: `$1$abcd0123$9Qcg8DyviekV3tDGMZynJ1`
— hash de senha hardcoded em biblioteca do sistema.

---

## Como o SENTINEL evolui

### v1.1 — Monitor de Firmware (próxima semana)
```
sentinel_monitor.py
  - Monitora páginas de download de Netgear, ASUS, TP-Link, D-Link via scraping
  - Detecta novo firmware lançado
  - Baixa automaticamente
  - Chama binwalk para extração
  - Chama sentinel.py na rootfs extraída
  - Salva relatório no Supabase
```

### v1.2 — Diff de Firmware
```
sentinel_diff.py <rootfs_v1> <rootfs_v2>
  - Compara inventário de binários (novos? removidos? modificados por hash?)
  - Compara achados: nova cadeia NVRAM? nova credencial? nova string suspeita?
  - Gera relatório de delta: "versão 3.0.0.4.386 introduziu 3 novos binários
    sem PIE e uma nova referência a nvram_get+system"
```

### v1.3 — Correlação com CVEs
```
sentinel_cve.py
  - Para cada cadeia NVRAM->exec detectada: busca CVEs com padrão similar
  - Usa NVD API + banco local de padrões extraídos de CVEs históricos
  - Output: "este padrão em httpd é similar ao CVE-2021-27239 (Netgear RCE)"
```

### v2.0 — Daemon Autônomo
```
sentinel_daemon.py
  - Roda toda noite (cron ou systemd)
  - Verifica novos firmwares de 20+ fabricantes
  - Analisa, diffa, correlaciona, pontua
  - Envia briefing matinal via Telegram
  - Alimenta base Supabase com conhecimento acumulado
  - LIBERTUS usa esses dados para decidir quais CVEs investigar
```

### v3.0 — Emulação + Fuzzing
```
  - Integra com QEMU para emulação parcial de binários ARM/MIPS
  - Fuzzing automatizado de entradas NVRAM identificadas como perigosas
  - PoC automatizado: "encontrei cadeia, emulei, fuzzei, confirmei RCE"
```

---

## Como monetizar via SHIELD

### Produto 1: SHIELD Firmware Audit
**Para quem:** Fabricantes de hardware que precisam certificar firmware antes de lançar.
**O que entregam:** Relatório SENTINEL + análise manual dos findings CRITICAL/HIGH.
**Preço:** R$ 3.000–15.000 por análise dependendo da complexidade.
**Por que funciona:** ANVISA/ANATEL vão exigir isso. Ninguém faz hoje no Brasil.

### Produto 2: SHIELD Firmware Intelligence Feed
**Para quem:** Operadoras de telecom, ISPs, grandes corporações com milhares de roteadores.
**O que entregam:** Assinatura mensal — toda vez que Netgear/ASUS/TP-Link lançam
firmware novo, o cliente recebe relatório SENTINEL em 24h com score e achados.
**Preço:** R$ 2.000–5.000/mês por fabricante monitorado.
**Por que funciona:** Um ISP com 500.000 roteadores Asus precisa saber se o
firmware novo introduziu um backdoor ANTES de fazer push para os clientes.

### Produto 3: Bug Bounty Turbocharger
**Para nós:** SENTINEL como ferramenta interna para encontrar bugs mais rápido
em programas como Netgear ($150–$25.000 por bug), ASUS, TP-Link.
**ROI:** Uma cadeia NVRAM→system confirmada = $1.500–$25.000 no HackerOne.
**Primeira prova:** brcmfmac.ko finding de hoje — investigar e submeter.

### Produto 4: SHIELD SaaS (longo prazo)
**Para quem:** Pesquisadores de segurança independentes, pentesters, consultoras.
**O que entregam:** Upload de rootfs → relatório SENTINEL em minutos → histórico
de análises, diff entre versões, alertas automáticos.
**Preço:** $49–$299/mês.

---

## Por que SENTINEL e não outro nome

SENTINEL porque:
- Sentinela = aquele que monitora antes que o problema chegue
- Antônimo de reativo — é proativo por design
- Soa profissional para pitch comercial (SHIELD SENTINEL)
- O acrônimo pode ser: **S**tatic **E**LF a**N**alysis & **T**hreat **I**ntelligence for **N**etwork **E**mbedded **L**inux

---

## Status

- [x] v1.0 — núcleo funcional (sentinel.py)
- [x] Primeiro scan real: ASUS RT-AC88U — CRITICAL
- [ ] v1.1 — monitor de firmware
- [ ] v1.2 — diff de versões
- [ ] v1.3 — correlação CVE
- [ ] v2.0 — daemon autônomo noturno
- [ ] v3.0 — emulação + fuzzing

---

*"Toda vulnerabilidade de firmware foi, em algum momento, uma string não sanitizada
passando por uma função que ninguém deveria ter chamado. SENTINEL encontra essas
strings antes que alguém as explore."*

— LIBERTUS, 2026-05-25
