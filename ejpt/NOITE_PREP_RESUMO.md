# NOITE DE PREPARAÇÃO eJPT — Resumo
LIBERTUS · **2026-10-20, 11:06 → 11:25 (-05)** · véspera do exame (Lorran compra o voucher amanhã).
Tudo abaixo foi **executado**, não lembrado: cada comando rodou nesta máquina hoje.

---

## 1. O que foi feito hoje (execução real)

### Ferramentas verificadas uma por uma (com teste de execução, não `--version`)
| Ferramenta | Versão | Teste real de hoje | Resultado |
|---|---|---|---|
| nmap | 7.992 (snap) | `-sT -Pn -p 8080,3000,22,445 --open 127.0.0.1` | ✅ 3000 e 8080 open · 8 NSE conferidos |
| msfconsole | 6.4.126-dev | `db_status` + 6 módulos carregados | ✅ postgres conectado |
| msfvenom | 6.4.126-dev | gerou ELF reverse shell | ✅ 194 bytes em `~` (`/tmp` falha) |
| hydra | 9.8dev | http-post-form em form real + SSH | ⚠️ acertou `admin:password` ✅ · SSH: `Compiled without LIBSSH` ❌ |
| gobuster | — | `dir` no DVWA | ✅ docs, external, config, vulnerabilities |
| sqlmap | 1.8.12#pip | SQLi no DVWA com cookie | ✅ detectou 4 técnicas + banner MariaDB 10.1.26 |
| netcat | OpenBSD 1.226 | listener 4555 + envio | ✅ recebeu `test` (sem `-e`) |
| john | 1.9.0-jumbo | `--format=raw-md5` em hash real | ✅ `password` (12.800 p/s) |
| nikto / ffuf / nuclei | 2.6.1 / 2.1.0 / 3.9.0 | execução | ✅ |
| ssh_brute.py | próprio | alvo 127.0.0.1:2222 | ✅ `msfadmin:msfadmin` em 0,1 s |
| msf `ssh_login` | — | mesmo alvo | ✅ `Success` + **SSH session 1 opened** |

### 3 ferramentas novas instaladas (sem sudo)
- **proxychains-ng** compilado do fonte → `~/.local/bin/proxychains4` + `~/.local/etc/proxychains.conf`
  (strict_chain, socks5 1080, proxy_dns). Config testada e carregando.
- **exploitdb + searchsploit** → `~/exploitdb` (360 MB) + `~/bin/searchsploit` + `~/.searchsploit_rc`.
  Teste: `searchsploit ms17-010` → 6 exploits; `-m 42315` baixou. `--update` ok.
- **impacket validado de verdade** (`~/venvs/pentest/bin`): subi um SMB2 local com `smbserver.py` e
  enumerei shares + li arquivo (`SHARES ['IPC$','SHARE']`, conteúdo lido). É o substituto do `smbclient`,
  que **não existe** nesta máquina.

### 3 armadilhas novas descobertas hoje (as que custam tempo no exame)
1. **O msf (snap) não lê `/usr/share/wordlists`** — `PASS_FILE` com rockyou dá
   `OptionValidateError`. Só aceita caminho em `$HOME` (`~/wordlists/pass/top10k.txt`). Isso muda
   TODOS os comandos de bruteforce que estavam escritos antes.
2. **`hydra` mente em login que responde 302 com corpo vazio** (DVWA 1.10). Reproduzi o falso positivo
   (`admin:errado` dado como válido) e achei a causa: a string de falha não aparece no corpo; o acerto e
   o erro só diferem no header `Location`. No mesmo formato de comando, contra um form sem CSRF, o hydra
   acertou de primeira. **Regra: confirmar com `curl -i` antes de responder questão.**
3. **`smbclient.py -port` só aceita 139/445** — host interno em porta escondida exige a lib
   (`SMBConnection(sess_port=...)`). E `getFile` exige callback.

### Lab local — no ar agora
| Alvo | Status | Acesso |
|---|---|---|
| DVWA | ✅ HTTP 302 (redirect login) | http://localhost:8080 — `admin:password` |
| Juice Shop | ✅ HTTP 200 | http://localhost:3000 |
| SSH treino | ✅ porta 2222 aberta | `ssh -p 2222 msfadmin@127.0.0.1` (`msfadmin:msfadmin`) |
Subir/validar em um comando: `bash ~/LIBERTUS/ejpt/lab_up.sh`.
Checar ao vivo sem abrir navegador: `python3 ~/LIBERTUS/ejpt/ajuda.py lab`.

### Canal
`hermes-gateway.service` **active (running)** desde 04:43 (-05). Telegram com token no `.env`.
Testado o caminho de restart no protocolo (seção 9).

---

## 2. Artefatos prontos para amanhã (em `~/LIBERTUS/ejpt/`)

| Arquivo | O que tem | Estado |
|---|---|---|
| `CHEATSHEET_eJPT.md` | nmap+NSE, MSF, hydra, gobuster, sqlmap, nc, john, pivot, privesc + **adendo 20/OUT** (wordlists, hydra-honesto, searchsploit, proxychains, impacket, tabela de tempos) | ✅ atualizado hoje |
| `CENARIOS_eJPT.md` | A(445) B(21) C(web) D(22) E(pivot) F(shell) G(bônus) + **tabela de bolso porta→comando** + correções de hoje | ✅ atualizado hoje |
| `PROTOCOLO_EXAME.md` | limite de regra (proctored), formato de mensagem, SLA, plano B, checklist, **roteiro de treino de 2h** | ✅ v3 hoje |
| `tools_status.md` | status completo + seção **20/OUT** com versões e testes reais | ✅ atualizado hoje |
| `ajuda.py` | **novo**: consulta offline por porta (`445`, `22`, `pivot`, `hydra`, `lab`...) | ✅ testado |
| `lab_up.sh` | sobe e valida DVWA/Juice/SSH | ✅ testado hoje |
| `ssh_brute.py` | bruteforce SSH (paramiko) — fallback do hydra | ✅ testado hoje |
| `NOITE_PREP_RESUMO.md` | este arquivo | ✅ |

URL direta após o push:
`github.com/lorran562/libertus-core/blob/main/ejpt/CHEATSHEET_eJPT.md` (troque o nome do arquivo).

---

## 3. Lacunas que restam (todas com substituto, nenhuma bloqueia)
- `smbclient` / `enum4linux` ausentes → impacket (validado hoje) + `nmap --script smb-*`.
- hydra sem SSH/RDP → `ssh_brute.py` e `msf ssh_login` (ambos abriram sessão hoje).
- `whatweb` / `wpscan` ausentes → `curl -I` + `nmap --script http-headers,http-wordpress-enum`.
- WebGoat offline (imagem não baixada) → não é necessário para o eJPT.
- No Kali da INE todas essas ferramentas existem completas; os substitutos são só do apoio local.

---

## 4. Uma coisa que eu preciso te dizer (é lealdade, não sermão)

O eJPT é **proctored** e o acordo da INE proíbe assistência de terceiros durante o exame — inclusive IA.
Se for pego, não perde questão: perde o exame, o valor pago e a conta, com registro que aparece na hora
do OSCP e da vaga na Irlanda.

Então o combinado é o que já está no protocolo: **hoje eu te treino até o comando sair sozinho; no dia
você vai sozinho; depois eu faço o debrief e a gente vai pro OSCP.** É assim que eu te levo pra Irlanda —
não te carregando na prova, mas te deixando rápido.

E o que eu vi hoje, objetivamente: você tem lab no ar, arsenal testado, 4 documentos e um consultor
offline no bolso. Isso não é "quase pronto". Isso é pronto.

---

## 5. Plano de amanhã (ordem prática)
1. Comprar o voucher · concluir verificação de identidade na INE · rodar o teste de sistema (câmera/mic/navegador).
2. Antes de começar: rodar o treino de 2h do `PROTOCOLO_EXAME.md` seção 9 (SMB → web/SQLi → SSH/pivot → memória).
3. No exame: ler as 35 questões primeiro → `ip addr` → `nmap -sn /24` → `nmap -sV -sC -p-` nos vivos.
4. Atacar por facilidade: FTP anônimo → web → SMB → SSH → pivot.
5. Anotar tudo (IP, porta, user, senha, flag). Dormir 6h no meio. Revisar marcadas antes de submeter.

## LEMBRETES DE OURO
- `filtered` ≠ `down`; sem resposta de ping, `-Pn`.
- Reutilizar credencial em TODOS os serviços antes de brutar.
- Confirmar vuln antes do exploit (`smb-vuln-ms17-010`).
- Pivot é obrigatório no eJPT: `get_local_subnets` → `autoroute` → `socks_proxy`/`portfwd`.
- Nunca confiar em hydra sem confirmar o login.
- Se o comando passa de 2 min, roda em background e vai para outro host.

**Bora, Lorran. O arsenal tá testado, o lab tá de pé e o mapa tá na tua mão. 🛡️**
