# NOITE DE PREPARAÇÃO eJPT — Resumo
LIBERTUS · **2026-10-21, 12:28 → 12:42 (-05)** · véspera do exame (voucher comprado hoje)
Re-verificação de 20/out refeita **com execução real** — cada linha abaixo rodou nesta máquina hoje.

---

## 1. Ferramentas — testadas em execução, não `--version`

| Ferramenta | Versão | Teste real de HOJE | Resultado |
|---|---|---|---|
| nmap | 7.992 | `db_nmap -p 3000,8080` + `-sV -sC` (scan.sh) | ✅ portas 631/2222/3000/8000/8080 |
| msfconsole | 6.4.126-dev | `msfdb status` = **Database started**, `db_nmap` populou `hosts`/`services`, `info` de 5 módulos | ✅ |
| hydra | 9.8dev | `http-get` no DVWA | ⚠️ **falso positivo** (ver §3) · SSH ❌ sem LIBSSH |
| gobuster | 3.8.2 | `dir` no DVWA, raft-small-words | ✅ login/setup/phpinfo/config/docs/external |
| sqlmap | 1.8.12#pip | DVWA SQLi **autenticada** | ✅ 4 técnicas + `--dbs` → `dvwa` |
| netcat | OpenBSD 1.226 | listener 4444 + conexão | ✅ recebeu `LIBERTUS_NC_OK` |
| john | 1.9.0-jumbo | `--format=raw-md5` em hashes DVWA | ✅ `admin:password` |
| ssh_brute.py | paramiko 5.1.0 | SSH lab 127.0.0.1:2222 | ✅ `msfadmin:msfadmin` em 0,1 s |

Extras confirmados: `proxychains4`, `searchsploit`, `nikto`, `nuclei`, `ffuf`, `subfinder`,
`sshpass`, `impacket` (venv) — todos presentes e respondendo.

## 2. Lab local — no ar agora

| Alvo | Status | Acesso |
|---|---|---|
| DVWA | ✅ 8080 — **banco OK**, SQLi respondendo `First name: admin` | `admin:password` |
| Juice Shop | ✅ 3000 — SQLi do `/rest/products/search` confirmada | — |
| SSH treino | ✅ 2222 | `msfadmin:msfadmin` |
| msfdb | ✅ iniciado | `db_nmap` → `hosts`/`services` |

Subir/validar: `bash ~/LIBERTUS/ejpt/lab_up.sh` · checar ao vivo: `python3 ~/LIBERTUS/ejpt/ajuda.py lab`

## 3. O que eu descobri hoje que vale ponto (medido, não teórico)

1. **hydra mente em `http-get`**: apontou `admin:admin` num formulário cuja senha é `password` —
   a página responde 200 pra qualquer coisa, então "sucesso" é falso. Só usar com `F=` explícito.
2. **hydra local não tem SSH** (`Compiled without LIBSSH`). Três rotas que funcionam e foram
   testadas: `ssh_brute.py` (venv), `msf ssh_login`, `nmap ssh-brute`. No Kali da INE é completo.
3. **metasploit snap**: resource script só roda em `$HOME` **sem ponto** no nome — `/tmp/x.rc` dá
   "Cannot find resource script" e `~/.x.rc` dá Permission denied. Para 1-2 comandos: `-x`.
4. **SQLi atrás de login**: sqlmap sem `--cookie` responde "not injectable" e o alvo é perdido.
   Sequência correta (logar → cookie → sqlmap) está no cheatsheet com o resultado real.
5. **SPA/JSON (Juice Shop)**: sqlmap desiste; UNION na mão funciona. Payload verificada dumpeia a
   tabela Users (`admin@juice-sh.op` / `0192023a7bbd73250516f069df18b500` = md5 de `admin123`).
6. **john com `--format` errado** roda e não acha nada, sem erro claro. Tabela de formatos no cheatsheet.
7. **paramiko só existe no venv** `~/venvs/pentest` — `python3` puro quebra o `ssh_brute.py`.
8. **`db_nmap` usa o nmap embutido do snap (7.95)**, não o 7.992 do sistema. Cosmético, mas explica
   diferença de saída.

## 4. Canal Telegram — testado agora, não suposto

- Bot `@libertusshield_bot`: `getMe` OK, **mensagem de teste entregue** no chat do Lorran
  (msg_id 864, 12:35).
- `hermes-gateway.service` = active (running), `enabled` no boot (sobe sozinho).
- ⚠️ **Este cron entrega em `local`** (`~/.hermes/cron/output/`), não no Telegram — o resumo não
  chega sozinho no celular. O canal serve pra você **me chamar** e eu responder.
- Teste de 10 s antes de começar: mandar `teste` no Telegram. Sem resposta em 2 min:
  `systemctl --user restart hermes-gateway`.

## 5. Artefatos prontos (`~/LIBERTUS/ejpt/`)

| Arquivo | O que tem | Estado |
|---|---|---|
| `CHEATSHEET_eJPT.md` | nmap+NSE, MSF, hydra, gobuster, sqlmap, nc, john, pivot, privesc + **adendo 21/OUT** (hydra falso positivo, regra do `.rc`, wordlists com contagem, SQLi autenticada, formatos do john) | ✅ atualizado hoje |
| `CENARIOS_eJPT.md` | A(445) B(21) C(web) D(22) E(pivot) F(shell) G(bônus) + tabela de bolso + **adendo 21/OUT validado no lab** | ✅ atualizado hoje |
| `PROTOCOLO_EXAME.md` | regras, formato de mensagem, SLA, plano B em camadas, checklist de véspera + **adendo 21/OUT** | ✅ atualizado hoje |
| `tools_status.md` | status completo + **ATUALIZAÇÃO 21/OUT** com evidência de execução | ✅ atualizado hoje |
| `scan.sh` | **novo** — recon de 1 alvo em <2 min (`bash scan.sh 10.10.10.5`), salva em `recon/` | ✅ testado hoje |
| `web_login.py` | **novo** — loga em form (com CSRF) e devolve cookie pronto pro sqlmap | ✅ testado hoje |
| `ajuda.py` | consulta offline por porta/cenário (`445`, `web`, `ssh`, `pivot`, `msf`, `hydra`, `lab`) | ✅ testado hoje |
| `lab_up.sh` | sobe e valida DVWA/Juice/SSH | ✅ |
| `ssh_brute.py` | bruteforce SSH (paramiko) — fallback do hydra | ✅ testado hoje |

URL direta após o push:
`github.com/lorran562/libertus-core/blob/main/ejpt/CHEATSHEET_eJPT.md` (troque o nome do arquivo).

## 6. Limites honestos desta noite

- **Não consegui recompilar o hydra com SSH**: `libssh-dev` exige `apt` com sudo e não há humano na
  sessão de cron. Impacto zero no exame (Kali da INE tem hydra completo) e há 3 alternativas testadas.
- **`docker restart` / `apt install` bloqueados em cron.** O DVWA parecia quebrado; consertei sem
  reiniciar nada — a causa era CSRF token (aspas simples) no meu próprio script de login.
- **sqlmap marcado "outdated"** (1.8.12). Funciona; atualizar na véspera não vale o risco.
- Este resumo **não é entregue no Telegram** (entrega local do cron) — está no disco e no GitHub.

## 7. Uma coisa que eu preciso te dizer (é lealdade, não sermão)

O eJPT é **proctored** e o acordo da INE proíbe assistência de terceiros durante o exame — inclusive IA.
Se for pego, não perde questão: perde o exame, o valor pago e a conta, com registro que aparece na hora
do OSCP e da vaga na Irlanda.

Então o combinado continua o do protocolo: **hoje eu te treino até o comando sair sozinho; no dia você
vai sozinho; depois eu faço o debrief e a gente vai pro OSCP.** É assim que eu te levo pra Irlanda —
não te carregando na prova, mas te deixando rápido.

O que eu verifiquei hoje, objetivamente: arsenal 100% operacional, lab de pé, 6 documentos, um script
de recon e um consultor offline no bolso. Isso não é "quase pronto". Isso é pronto.

## 8. Plano de amanhã (ordem prática)

1. Comprar o voucher · verificação de identidade na INE · teste de sistema (câmera/mic/navegador).
2. Antes de começar: rodar o treino de 2h do `PROTOCOLO_EXAME.md` seção 9.
3. No exame: ler as 35 questões primeiro → `ip addr` → `nmap -sn /24` → `nmap -sV -sC -p-` nos vivos.
4. Atacar por facilidade: FTP anônimo → web → SMB → SSH → pivot.
5. Anotar tudo (IP, porta, user, senha, flag). Dormir 6h no meio. Revisar marcadas antes de submeter.

## LEMBRETES DE OURO
- `filtered` ≠ `down`; sem resposta de ping, `-Pn`.
- Reutilizar credencial em TODOS os serviços antes de brutar.
- Confirmar vuln antes do exploit (`smb-vuln-ms17-010`).
- Pivot é obrigatório: `get_local_subnets` → `autoroute` → `socks_proxy`/`portfwd`.
- **Nunca confiar em hydra sem confirmar o login na mão** (ele mentiu hoje).
- **sqlmap dizendo "not injectable" não é veredito** — testar UNION manual.
- Se o comando passa de 2 min, roda em background e vai para outro host.

**Bora, Lorran. Arsenal testado, lab de pé, mapa na tua mão. 🛡️**
