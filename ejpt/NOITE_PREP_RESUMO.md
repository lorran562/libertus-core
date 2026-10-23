# NOITE DE PREPARAÇÃO eJPT — 23/OUT/2026
LIBERTUS · 17:55 → 18:25 (-05) · **voucher sendo comprado amanhã (24/out)**, exame logo em seguida.
Versão anterior (21/out) arquivada em `NOITE_PREP_RESUMO_21OUT.md` — não apaguei nada, somei.

Tudo aqui foi **executado nesta máquina hoje**. Onde não testei, está escrito "não testei".

---

## 1. Arsenal — testado em execução, não em `--version`

| Ferramenta | Versão | Teste real de HOJE | Resultado |
|---|---|---|---|
| nmap | 7.992 | `http-enum` :8080 · `smb-vuln*`/`smb-enum-shares` 172.28.77.11 · `ftp-anon` :2121 | ✅ 6 diretórios, 3 shares |
| msfconsole | 6.4.126-dev | `db_nmap` → `hosts`/`services` · `smb_ms17_010` · `search ms17-010/ftp anonymous/smb_login` | ✅ banco ativo, módulos localizados |
| hydra | 9.8dev | FTP `127.0.0.1:2121` com `-f` | ✅ **`msfadmin:msfadmin` em ~1 s** |
| gobuster | 3.8.2 | `dir` em :8080 (`common.txt`, 4.750) | ✅ config, docs, external, robots.txt, php.ini |
| sqlmap | 1.8.12#pip | **autenticado** (cookie de sessão) no DVWA | ✅ 4 técnicas + `--dbs` → `dvwa` |
| netcat | OpenBSD 1.226 | listener 4444 + cliente | ✅ recebeu `PING` |
| john | 1.9.0-jumbo | `--format=raw-md5` | ✅ `admin:password` |
| ssh_brute.py | paramiko 5.1.0 | 127.0.0.1:2222 | ✅ `msfadmin:msfadmin` em 0,1 s |

**Gap conhecido e inalterado:** `hydra` local sem módulos SSH/RDP (`Compiled without LIBSSH`) — não dá
para corrigir sem sudo com senha. Alternativas testadas: `ssh_brute.py` (venv) e `msf ssh_login`.
**No Kali da INE o hydra é completo — isso só afeta o treino aqui.**

**Ausentes no host:** `ncat`, `smbclient`, `smbmap`, `enum4linux-ng`, `showmount`, `rpcclient`,
`wpscan`, `crackmapexec/nxc`. Não bloqueiam o exame (Kali da INE tem todos).
Alternativas locais que funcionam: nmap NSE para SMB, `impacket` (smbclient.py/psexec.py/wmiexec.py)
em `~/venvs/pentest/bin/`.

## 2. Lab — 6 alvos no ar agora

| Alvo | Endereço | Credencial / nota |
|---|---|---|
| DVWA | http://localhost:8080 | `admin:password` (security=low) |
| Juice Shop | http://localhost:3000 | SPA — UNION manual funciona, sqlmap não |
| SSH treino | `127.0.0.1:2222` | `msfadmin:msfadmin` |
| FTP treino | `127.0.0.1:2121` | vsftpd 3.0.2, `msfadmin:msfadmin` |
| SMB legacy | `172.28.77.11` (SRVLEGACY) | SMB1/NT1, signing off, guest RW em `publico` e `IPC$` |
| SMB modern | `172.28.77.12` | SMB2/3 assinado |

Subir/validar tudo: `bash ~/LIBERTUS/ejpt/lab_up.sh` (agora sobe SMB e FTP também, e imprime a tabela).
Checar ao vivo: `python3 ~/LIBERTUS/ejpt/ajuda.py lab`.

## 3. O que eu consertei hoje (3 regressões que quebrariam no dia)

1. **`requests` sumiu do venv `~/venvs/pentest`** → `web_login.py` morria. E o `pip3` do PATH é o
   Python 3.14 do Hermes: instala no lugar errado e o venv continua quebrado. Certo:
   `uv pip install --python ~/venvs/pentest/bin/python requests`.
2. **Wordlists não estão onde o Kali põe** (não existe `/usr/share/seclists` aqui). Caminhos reais:
   `/usr/share/wordlists/common.txt` (4.750) · `rockyou.txt` (14.344.391) ·
   `~/wordlists/web/raft-small-words.txt` (43.007) · `directory-list-2.3-medium.txt` (220.559) ·
   `~/wordlists/pass/{top1000,top10k,500-worst}.txt` · `~/wordlists/user/top-usernames.txt`.
3. **SSH do lab estava caído** — `docker start libertus-ssh` resolveu; agora entra no `lab_up.sh`.

## 4. Descobertas técnicas que valem ponto

1. **hydra funciona em FTP e falha em SSH** — o veredito não é "hydra não presta". FTP: achou em 1 s.
   SSH: erro de compilação, sem libssh.
2. **Não misturar `-sV` com lista de scripts no nmap**: hoje `-sV --script "ftp-anon,ftp-syst,..."`
   disparou `vmware-version`/`rpcinfo` (erro) numa porta FTP. Duas etapas, saída limpa.
3. **SMB do lab é Samba, não Windows**: `smb_ms17_010` → "does NOT appear vulnerable" (correto).
   EternalBlue de verdade só se treina em Windows. No exame, 445 Windows → fluxo do Cenário A.
4. **Scripts NSE moram em `/snap/nmap/5432/usr/share/nmap/scripts`** — `/snap/nmap/current/share/...`
   não existe. Teste de vida: `nmap --script-help http-enum`.
5. **SQLi autenticada é o gargalo real**: sem cookie, sqlmap diz "not injectable". Com
   `web_login.py` → cookie → `--cookie`, ele achou 4 técnicas e listou `dvwa`.
6. **Upload → RCE → reverse shell fechou hoje, ponta a ponta**: subi `shell.php` no DVWA
   (`-F "Upload=Upload"`, sem CSRF nessa página), executei `id` (`uid=33(www-data)`) e recebi uma
   conexão reversa real de volta no host, com shell `www-data` respondendo. Sequência exata no
   `CENARIOS_eJPT.md` (Cenário C) e no cheatsheet (G.6).

## 5. Canal Telegram — testado de ponta a ponta hoje

- `getMe` ok → **@libertusshield_bot**; `getWebhookInfo` → webhook vazio, **0 pendentes** (polling limpo).
- Gateway: `hermes-gateway.service` **active** e **enabled** (sobe no boot).
- **Mensagem real entregue hoje: `msg_id 865`, 18:09**, com o status do arsenal.
- Este cron entrega em `local`. O Telegram serve para **você me chamar** e eu responder.
- Se eu não responder em 2 min: `systemctl --user restart hermes-gateway`.

## 6. Artefatos prontos (`~/LIBERTUS/ejpt/`)

| Arquivo | Conteúdo | Estado |
|---|---|---|
| `CHEATSHEET_eJPT.md` | nmap/NSE, MSF, hydra, gobuster, sqlmap, nc, john, pivot, privesc + **adendo 23/OUT** (hydra por serviço, regra do `-sV`, SMB real, venv, tempos) | ✅ |
| `CENARIOS_eJPT.md` | cenários A–G + **mapa do lab com IPs reais de hoje** e o que cada alvo ensina/não ensina | ✅ |
| `PROTOCOLO_EXAME.md` | regra proctored, formato de mensagem, SLA, plano B em camadas + **adendo 23/OUT** (canal testado, checklist novo) | ✅ |
| `tools_status.md` | status completo + **ATUALIZAÇÃO 23/OUT** com evidência de execução | ✅ |
| `lab_up.sh` | sobe e valida 6 alvos (DVWA, Juice, SSH, FTP, SMB legacy/modern) | ✅ testado |
| `ajuda.py` | consulta offline + `lab` ao vivo (agora verifica SSH/FTP/SMB) | ✅ testado |
| `scan.sh` | recon de 1 alvo em <2 min (`bash scan.sh 10.10.10.5`) | ✅ |
| `web_login.py` | login com CSRF → cookie pronto pro sqlmap | ✅ testado hoje |
| `ssh_brute.py` | bruteforce SSH (paramiko) | ✅ testado hoje |
| `upload_rce_test.py` | **novo** — login → upload de webshell → RCE → reverse shell, com prova em cada etapa | ✅ testado hoje (conexão recebida) |

GitHub: `github.com/lorran562/libertus-core/blob/main/ejpt/CHEATSHEET_eJPT.md` (troque o nome).

## 7. Limites honestos desta noite

- **Pivot não foi testado ponta a ponta**: não existe foothold aberto no lab. A cadeia
  (`autoroute` → `socks_proxy` → `proxychains`) está documentada, mas não executada hoje. É o
  exercício que falta antes do exame.
- **EternalBlue não tem alvo Windows** aqui. Só enumeração SMB foi validada.
- **Sem sudo**: não instalei `smbclient`, `enum4linux-ng`, `wpscan`, nem recompilei o hydra.
- **`msfupdate` não rodado** — versão >2 semanas, aviso cosmético, atualizar na véspera é risco.

## 8. Plano de amanhã (ordem prática)

1. Comprar o voucher · verificação de identidade na INE · teste de sistema (câmera/mic/navegador).
2. Rodar `bash ~/LIBERTUS/ejpt/lab_up.sh` e o checklist do `PROTOCOLO_EXAME.md`.
3. Treino de 2h: cenários A→D no lab, cronometrado, **sem me pedir comando** (só conferir depois).
4. No exame: ler as 35 questões primeiro → `ip addr` → `nmap -sn` → `-sV -sC -p-` nos vivos.
5. Atacar por facilidade: FTP anônimo → web → SMB → SSH → pivot. Anotar tudo. Dormir 6h.

## 9. Uma coisa que eu preciso te dizer (lealdade, não sermão)

A missão desta noite pedia eu ficar do seu lado no Telegram **durante o exame**, respondendo cada passo.
Eu não vou fazer isso — e não é falta de vontade de te ajudar.

O eJPT é **proctored**. O acordo da INE proíbe assistência de terceiros durante a prova, inclusive IA.
O risco não é perder uma questão: é **anulação, perda do valor pago e registro na conta** — exatamente
o que aparece quando você for buscar OSCP e a vaga na Irlanda.

O que eu faço:
- **Hoje/amanhã cedo:** treino até o comando sair da tua mão.
- **Nas 48h da prova:** você sozinho. Eu fico fora.
- **Depois:** debrief questão por questão + plano OSCP.

Isso não é eu te soltando. É eu te levando a sério.

## 10. Lembretes de ouro

- `filtered` ≠ `down`; sem resposta de ping em rede roteada, `-Pn`.
- Reutilizar credencial em TODOS os serviços antes de brutar.
- Confirmar vuln antes do exploit (`smb_ms17_010`, `curl -i`).
- **hydra que "achou" não é prova** — confirmar no cliente do serviço.
- **sqlmap "not injectable" não é veredito** — testar UNION na mão.
- Pivot é obrigatório: `get_local_subnets` → `autoroute` → `socks_proxy`/`portfwd`.
- Comando passando de 2 min: manda pra background e vai pro próximo host.

**Arsenal testado, 6 alvos no ar, 6 documentos, 3 regressões fechadas. Bora, Lorran. 🛡️**
