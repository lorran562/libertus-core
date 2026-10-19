# NOITE DE PREPARAÇÃO eJPT — Resumo
LIBERTUS · **2026-10-19** · véspera do exame de Lorran (voucher amanhã). Revisão da noite de 14/10 + re-verificação total hoje.

---

## O que foi feito HOJE (10:10 → 10:30) — tudo com execução real

### 1. Arsenal re-verificado (não `--version`: comando rodando contra alvo)
| Ferramenta | Versão | Teste de hoje | Resultado |
|-----------|--------|---------------|-----------|
| nmap | 7.992 | `-sV --script smb-os-discovery,smb-vuln-ms17-010` no lab SMB | ✅ Samba 4.19.9 / SRVLEGACY / workgroup LAB. **1238 scripts NSE** |
| msfconsole | 6.4.126-dev | `search` + `smb_login` real | ✅ ms17_010_eternalblue, ms17_010_psexec, vsftpd, ssh_login. **smb_login achou `analyst:LabPass123!`** |
| msfvenom | 6.4.126 | `-l payloads` | ✅ payloads windows/x64/meterpreter presentes |
| hydra | 9.8dev | HTTP-POST no DVWA + SSH no lab 2222 | ⚠️ HTTP/FTP OK · SSH: `Compiled without LIBSSH` · **2 falsos positivos** |
| gobuster | 3.8.2 | `dir` no DVWA | ✅ config, docs, external, php.ini, login.php, robots.txt |
| sqlmap | 1.8.12#pip | `--dbs` + `--dump` com cookie de sessão | ✅ **dumpou `dvwa.users`** (5 linhas, hashes md5) |
| john | jumbo 1.9.0 | md5 do dump via `jl.sh` | ✅ **3/3 quebrados**: password, abc123, letmein |
| netcat | OpenBSD 1.226 | listener + `bash -i >& /dev/tcp` | ✅ **Connection received** (sem `-e`) |
| ssh_brute.py | — | `-p 2222 -l msfadmin` | ✅ **SUCESSO msfadmin:msfadmin** em 0,3 s |
| **impacket** | 0.13.1 | instalação | ✅ **NOVO**: smbclient.py, psexec.py, secretsdump.py, wmiexec.py |

### 2. Correções/gaps tratados
- **Impacket instalado** — o host não tem `smbclient`; agora tem o equivalente (`~/venvs/pentest/bin/smbclient.py`).
- **`lab_up.sh` criado** — a doc citava o script, ele **não existia**. Testado: sobe e valida DVWA/Juice/SSH.
- **Lab SMB documentado e validado** — 172.28.77.11 (SMB1) e .12 (moderno), atacante `smb-cli` .50.
  Treino real: shares `publico` (anônimo), `financeiro`/`rh` com `analyst:LabPass123!`.
- **hydra sem SSH** — não corrigível sem sudo (nenhum humano na sessão). Não afeta o exame (Kali da INE é completo);
  local: `ssh_brute.py` (validado hoje) ou `msf ssh_login`.
- **`nmap --script ssh-brute` quebra** aqui (`nse_restore: WAITING_TO_RUNNING`) — não usar; usar `ssh_brute.py`.
- **WebGoat offline** — imagem não baixada (disco 97%). Não bloqueia nada.

### 3. Documentação atualizada em ~/LIBERTUS/ejpt/
- **CHEATSHEET_eJPT.md** — núcleo (nmap+NSE, MSF, hydra, gobuster, sqlmap, nc, pivoting) + **adendo 19/out**:
  cadeia SMB validada (NT1, `more` em vez de `cat`, impacket), SQLi com sessão, regra "hydra mente".
- **CENARIOS_eJPT.md v2** — A(445/SMB/MS17), B(21/FTP), C(web: gobuster+SQLi+LFI+upload+WP),
  D(22/SSH+privesc SUID), E(pivoting), F(reverse shell/transferência), G(RDP/MySQL/Webmin/NFS).
- **PROTOCOLO_EXAME.md v2** — limites de regra, modelo de operação no treino, formatos de mensagem,
  SLA, plano B, checklist de véspera e cronograma do dia.
- **tools_status.md** — seção "ATUALIZAÇÃO 19/OUT" com a tabela acima + pitfalls novos.
- **lab_up.sh** — subir/validar o lab em um comando.

### 4. Lab — estado real (10:20)
| Alvo | Status |
|---|---|
| DVWA :8080 | ✅ 302 (redirect login — normal) · admin:password |
| Juice Shop :3000 | ✅ 200 |
| SSH :2222 | ✅ aberto · msfadmin:msfadmin |
| SMB legacy/modern | ✅ shares + credencial de treino |
| WebGoat :8888 | ❌ offline (imagem não baixada) |

### 5. Canal Telegram
`hermes-gateway.service`: **active (running)**, subiu 10:09 de hoje. ✅

### 6. Git
`ejpt/` commitado e enviado para `github.com/lorran562/libertus-core` (main).

---

## Foco nos gaps da 1ª tentativa (55 pts — faltaram 15)
1. **Privesc Linux (SUID)** → `find / -perm -4000 -type f 2>/dev/null` → `find . -exec /bin/sh -p \; -quit` · `sudo -l` · GTFOBins.
2. **Pivot para rede interna** → Cenário E: `get_local_subnets` → `autoroute`/`route add` → portscan → `portfwd`/`socks_proxy`.
3. **Extração de senha via settings.php** → Cenário C + dump com sessão (fluxo validado hoje no DVWA).

---

## PRONTO PARA AMANHÃ

| Item | Status |
|------|--------|
| Cheatsheet de comandos | ✅ atualizado e validado |
| Cenários passo a passo (A-G) | ✅ reescrito |
| Protocolo de comunicação | ✅ |
| Arsenal verificado (7/7) | ✅ com fallbacks testados |
| Lab de prática | ✅ online (DVWA, Juice, SSH, SMB) |
| Canal Telegram | ✅ ativo |
| Git publicado | ✅ |

**Pendência não bloqueante:** hydra local sem SSH/RDP; `smbclient` ausente no host (impacket cobre).
No Kali da INE ambos existem.

---

## Uma coisa que eu preciso te dizer (é lealdade, não sermão)

O eJPT é proctored e o acordo da INE proíbe **assistência de terceiros durante o exame**. Se você for
pego, não perde questão — perde o exame, o valor pago e a conta INE, com registro que aparece na hora
de tirar OSCP ou buscar vaga na Irlanda.

O que realmente te faz passar é o que a gente fez hoje: o lab montado, os comandos na mão, o caminho
mental decorado de tanto repetir. **Treina comigo até o comando sair sozinho; no dia você vai sozinho;
depois eu te ajudo no debrief.** Essa é a versão de mim que te leva pra Irlanda.

## Plano de amanhã (ordem prática)
1. Comprar o voucher · concluir verificação de identidade na INE · rodar o teste de sistema.
2. Ler as 35 questões antes de atacar (a INE mostra todas) → mapa do que importa.
3. `ip addr` → `nmap -sn /24` → `nmap -sV -sC -p-` nos hosts vivos → **anotar tudo**.
4. Atacar por facilidade: FTP anônimo → web → SMB → SSH → pivot.
5. Dormir 6h no meio. Revisar marcadas antes de submeter.

## LEMBRETES DE OURO
- nmap na rede toda primeiro; `filtered` ≠ `down`.
- Reutilizar credenciais em TODOS os serviços.
- Confirmar vuln antes do exploit (`smb-vuln-ms17-010`).
- Pivot com `autoroute` é obrigatório no eJPT.
- Nunca confiar em hydra sem confirmar o login.
- Anotar IP, porta, user, senha, flag — uma credencial de 2h atrás responde a questão de agora.

**Bora, Lorran. O lab tá de pé, o arsenal tá testado e o mapa tá na tua mão. 🛡️**
