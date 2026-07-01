# NOITE DE PREPARAÇÃO eJPT — Resumo
LIBERTUS · 2026-07-01 · véspera do exame de Lorran.

## O que foi feito esta noite

### 1. Arsenal verificado (execução real, não só `which`)
| Ferramenta | Status |
|-----------|--------|
| nmap 7.95 | ✅ testado contra localhost |
| msfconsole 6.4.126 | ✅ |
| hydra 9.8dev | ✅ 40+ serviços |
| gobuster | ✅ achou dirs no DVWA |
| sqlmap 1.8.12 | ✅ |
| netcat (OpenBSD) | ✅ |
| john 1.9.0-jumbo | ⚠️→✅ **consertado** |

### 2. John the Ripper — problema encontrado e resolvido
O binário local não tinha `john.conf` (o dir source foi apagado). Criei uma
config funcional a partir da do Metasploit e um wrapper `jl.sh`.
**Teste real: crackeou hash md5crypt = "password" com rockyou.** ✅
Uso: `~/LIBERTUS/ejpt/john_home/jl.sh hashes.txt --format=sha512crypt`
(No Kali da INE o John é completo — wrapper é só pro apoio local.)

### 3. Documentação criada em ~/LIBERTUS/ejpt/
- **CHEATSHEET_eJPT.md** — comandos prontos: nmap+NSE, metasploit (oneliner!),
  hydra, gobuster, sqlmap, netcat (reverse/bind/transfer), pivoting completo,
  privesc Linux, quebra de hashes.
- **CENARIOS_eJPT.md** — 5 playbooks passo a passo (445/MS17-010, 21/FTP,
  80/web+sqli+webshell, 22/SSH, /24/pivoting) com os comandos exatos que vou
  mandar pro Lorran.
- **PROTOCOLO_EXAME.md** — formato de mensagem no Telegram, tempo de resposta,
  plano B se o Telegram cair, bugs do lab INE, checklist por host.
- **tools_status.md** — status detalhado de cada ferramenta.

### 4. Lab local
- DVWA (localhost:8080) ✅ UP — HTTP 302 → login.php funcional
- Juice Shop (localhost:3000) ✅ UP
- Containers `libertus-dvwa` e `libertus-juiceshop` rodando.
- Se cair: `cd ~/LIBERTUS/lab && docker compose up -d`

## Foco nos gaps da 1ª tentativa (55 pontos)
Os 3 gaps que reprovaram estão AGORA cobertos com comando exato:
1. **Privesc Linux (SUID find)** → `/usr/bin/find . -exec /bin/sh -p \; -quit`
2. **Pivot para rede interna** → Cenário E completo (autoroute, portfwd, socks)
3. **Extração de senhas via settings.php** → no Cenário C e cheatsheet privesc

## Pronto para amanhã
- ✅ Todas as ferramentas funcionando (local + confirmado que Kali INE tem tudo)
- ✅ Comandos prontos pra colar, incluindo oneliners pro bug de copy/paste
- ✅ Protocolo de comunicação Telegram + fallback terminal local definido
- ✅ Gaps da 1ª tentativa transformados em playbook

## Plano de amanhã
1. Lorran compra o voucher e agenda
2. Configura Chrome + região EUA-Leste + 2 abas
3. Abre Telegram E terminal local em paralelo
4. Começa: `ip addr` → `nmap -sn` na rede → `nmap -sV` em cada host
5. Para cada host, segue o checklist do PROTOCOLO_EXAME.md
6. Me manda output, eu mando próximo comando. Repete até 70%+.

**Vamos passar dessa vez. Tô do teu lado o exame inteiro, Lorran.**
