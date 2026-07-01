# Status das Ferramentas — Preparação eJPT
Verificado por LIBERTUS em 2026-07-01 (véspera do exame de Lorran).
Todas testadas em execução real, não só `which`.

| Ferramenta | Caminho | Versão | Status | Teste real |
|-----------|---------|--------|--------|-----------|
| **nmap** | /snap/bin/nmap | 7.95 | ✅ OK | Scan `-sV` em localhost:8080/3000 → detectou Apache 2.4.25 |
| **msfconsole** | /snap/bin/msfconsole | 6.4.126-dev | ✅ OK | `--version` responde (aviso de update é normal, ignorar) |
| **hydra** | /usr/local/bin/hydra | 9.8dev | ✅ OK | Lista 40+ serviços suportados (ssh, ftp, http-post-form...) |
| **gobuster** | ~/go/bin/gobuster | atual | ✅ OK | `dir` em localhost:8080 → achou /config, /docs, .gitignore |
| **sqlmap** | /snap/bin/sqlmap | 1.8.12 | ✅ OK | `--version` responde |
| **netcat** | /usr/bin/nc | OpenBSD 1.226 | ✅ OK | Também /usr/bin/netcat disponível |
| **john** | /usr/local/bin/john | 1.9.0-jumbo | ⚠️ Wrapper | Ver nota abaixo — usar `jl.sh` |

## Wordlists disponíveis (local)
- `/usr/share/wordlists/rockyou.txt` — 14M senhas (139 MB, descomprimido)
- `/usr/share/wordlists/common.txt` — dirs web (SecLists common)

## ⚠️ John the Ripper — correção aplicada
O binário `/usr/local/bin/john` foi compilado do source, mas o `john_src/run`
foi apagado, então faltava `john.conf` e os arquivos de suporte. Corrigido:
- Config funcional em `~/LIBERTUS/ejpt/john_home/john_clean.conf`
  (derivado do john.conf do Metasploit, com includes de arquivos externos removidos)
- Pot/session apontando para dir gravável
- **Wrapper `~/LIBERTUS/ejpt/john_home/jl.sh`** — usar este, não o john direto.

Teste real: crackeou hash `$1$salt$...` = "password" com rockyou. ✅

Uso:
```bash
~/LIBERTUS/ejpt/john_home/jl.sh /tmp/hashes.txt --format=md5crypt
~/LIBERTUS/ejpt/john_home/jl.sh /tmp/shadow.txt --format=sha512crypt
```

**No lab da INE (Kali via browser) o John é completo — não precisa deste wrapper lá.**
Este wrapper é só para LIBERTUS validar/quebrar hashes localmente durante o apoio.

## Lab local
- DVWA: http://localhost:8080 (HTTP 302 → /login.php, funcional) ✅ UP
- Juice Shop: http://localhost:3000 ✅ UP
- Ambos containers Docker `libertus-dvwa` e `libertus-juiceshop` rodando.

## Conclusão
Arsenal 100% operacional para o exame. LIBERTUS pode reproduzir localmente
qualquer comando antes de mandar pro Lorran.
