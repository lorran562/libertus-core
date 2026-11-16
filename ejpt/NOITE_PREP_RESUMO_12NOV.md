# NOITE DE PREPARAÇÃO eJPT — 12/NOV/2026

LIBERTUS · 11:40 → 12:05 (-05) · **voucher sendo comprado amanhã**, exame logo em seguida.
Versões anteriores preservadas: `NOITE_PREP_RESUMO_21OUT.md` e `NOITE_PREP_RESUMO_23OUT.md`.

Regra desta noite: só entra aqui o que foi **executado nesta máquina hoje**. Onde não testei,
está escrito "não testei".

---

## 1. O que mudou desde a última prep (23/out)

O material de 23/out já estava profundo (2.100+ linhas). Hoje não reescrevi nada: **revalidei tudo
e fechei o maior gap que ele mesmo admitia — o pivô nunca tinha sido testado ponta a ponta.**

| Gap do doc de 23/out | Status hoje |
|---|---|
| "Pivot não foi testado ponta a ponta" | ✅ **testado e provado** com IP de origem |
| SSH/FTP do lab caídos | ✅ religados (estavam `Exited` há 2 semanas) |
| "eJPT é proctored" | ❌ **estava errado** — é open book, sem proctor (corrigido com fonte) |
| nmap 7.992 | 7.993 (snap), 619 scripts NSE |
| Lab sem alvo de pivô | ✅ lab de pivô novo e reprodutível |

## 2. Arsenal — revalidado em execução hoje (11:43–11:53)

| Ferramenta | Versão hoje | Teste real | Resultado |
|---|---|---|---|
| nmap | 7.993 (snap) | `-Pn -sT -p 8080,3000 127.0.0.1` | ✅ 0,07 s · 619 scripts NSE |
| msfconsole | 6.4.126-dev | `msfdb status` + módulos + sessão real | ✅ banco ativo · **meterpreter aberto** |
| hydra | 9.8dev | FTP vs vsftpd 3.0.2 | ✅ `msfadmin:msfadmin` em ~1 s |
| gobuster | 3.8.2 | `dir` no DVWA | ✅ 6 caminhos, incl. `php.ini` e `.gitignore` |
| sqlmap | 1.8.12#pip | `--version` | ✅ (aviso "outdated" é cosmético) |
| netcat | OpenBSD 1.226 | uso real | ✅ sem `-e` |
| john | 1.9.0-jumbo | build-info | ✅ |
| ssh_brute.py | paramiko | 127.0.0.1:2222 | ✅ `msfadmin:msfadmin` em 0,1 s |
| **wpscan** | — | `command -v` | ❌ ausente (disco 99%, não instalei) |

## 3. Lab — 8 alvos no ar agora

| Alvo | Endereço | Credencial / nota |
|---|---|---|
| DVWA | http://localhost:8080 | `admin:password` (login via `web_login.py` resolve CSRF) |
| Juice Shop | http://localhost:3000 | UNION manual funciona, sqlmap não |
| SSH treino | `127.0.0.1:2222` | `msfadmin:msfadmin` — **religado hoje** |
| FTP treino | `127.0.0.1:2121` | vsftpd 3.0.2, `msfadmin:msfadmin` — **religado hoje** |
| SMB legacy | `172.28.77.11` | SMB1/NT1 — **religado hoje** |
| SMB modern | `172.28.77.12` | SMB2/3 — **religado hoje** |
| Pivô: edge SSH | `127.0.0.1:2223` | `msfadmin:msfadmin`, dual-homed 172.20.0.2 |
| Pivô: alvo interno | `172.20.0.3:8081` | HTTP, loga IP de origem de cada conexão |

Subir: `bash ~/LIBERTUS/ejpt/lab_up.sh` (6 alvos) · `bash ~/LIBERTUS/ejpt/pivot_up.sh` (pivô)
Derrubar pivô: `bash ~/LIBERTUS/ejpt/pivot_up.sh down`
WebGoat segue fora do ar: `cd ~/LIBERTUS/lab && docker compose up -d webgoat`

## 4. A descoberta da noite — pivô validado (e 3 armadilhas)

Cadeia executada hoje, com prova:

```
RCE web no DVWA (php baixa stager) → meterpreter 1
  → post/multi/manage/autoroute (SESSION 1, 172.20.0.0/16)  → Route added
  → auxiliary/server/socks_proxy na 1080
  → proxychains4 curl http://172.20.0.3:8081/  → OK
  → docker logs pivot-internal  → origem 172.20.0.4  ✅ (não 172.20.0.1)
```

O IP de origem é a única prova real de que o tráfego passou pelo pivô. Sem conferir isso, você
acha que funcionou porque o comando não deu erro.

Três armadilhas medidas hoje:

1. **`autoroute` recusa sessão shell** — literal: `incompatible session type: shell. This module
   works with: meterpreter.` Sessão de `ssh_login`/webshell não serve para rotear.
2. **`route add` em shell diz "Route added" e não roteia TCP** — o tráfego continua saindo do
   atacante. Rota só vale em meterpreter.
3. **`proxychains` não injeta no nmap snap** desta máquina — o scan sai direto do host. No Kali do
   exame isso não acontece (nmap normal). Aqui: use `curl`/`nc` ou o scanner do msf.

Bônus: `ssh -D` neste lab dá `administratively prohibited` (sshd da imagem com forwarding desligado).
Num alvo real com sshd padrão, `ssh -D 1080` + proxychains é o pivô mais rápido que existe.

## 5. Correção factual: o exame é open book, sem proctor

O doc de 23/out dizia "proctored, assistência dá anulação". Verifiquei hoje:

- INE: **"It is open book, mirroring the experience Junior Penetration Testers will have on the job."**
- Sem proctor, sem webcam, sem lockdown browser, sem agendamento — 48 h, 35 questões, 70%, 1 retake grátis.
- **Cheatsheet, anotações, Google e ferramentas são permitidos e esperados.** É para isso que os
  documentos existem.

O que não muda: open book é consultar material, não é outra pessoa (ou IA) resolvendo a prova.
Em vez de te dar comando pronto durante a prova, o meu trabalho é fazer o documento ser bom o
suficiente para você não precisar. É o que fiz esta noite.

## 6. Artefatos prontos (`~/LIBERTUS/ejpt/`)

| Arquivo | O que tem de novo hoje |
|---|---|
| `CHEATSHEET_eJPT.md` | **ADENDO 12/NOV**: pivô H.1–H.8 (autoroute só meterpreter, route add mente, socks+proxychains, portfwd, ssh -D, receita completa) |
| `CENARIOS_eJPT.md` | **ADENDO 12/NOV**: Cenário E validado com lab novo, cadeia exata e prova de IP |
| `PROTOCOLO_EXAME.md` | **ADENDO 12/NOV**: correção open book, o que pode/não pode me chamar, SLA, plano B offline, checklist |
| `tools_status.md` | **REVALIDAÇÃO 12/NOV**: versões, testes reais, estado do lab, 4 gaps honestos |
| `pivot_up.sh` | **novo** — sobe/derruba o lab de pivô (sub-redes fixas, IPs fixos, testado 2x) |
| `lab_up.sh` · `ajuda.py` · `scan.sh` · `web_login.py` · `ssh_brute.py` · `upload_rce_test.py` | mantidos e revalidados |

GitHub: `github.com/lorran562/libertus-core/blob/main/ejpt/CHEATSHEET_eJPT.md` (troque o nome do arquivo).

## 7. Limites honestos desta noite

- **`portfwd` não foi testado** — só `autoroute` + `socks_proxy`. Sintaxe no cheatsheet H.5.
- **EternalBlue continua sem alvo Windows** aqui (SMB do lab é Samba; `smb_ms17_010` corretamente
  diz "not vulnerable"). Fluxo documentado, não executado.
- **wpscan ausente** e **WebGoat fora do ar**.
- **Sem sudo**: não recompilei hydra (segue sem SSH/RDP neste host) nem instalei pacotes.
- **Disco em 99%** (1,5 GB livres): não baixei imagem nova; usei só imagens locais.

## 8. Plano de amanhã (ordem prática)

1. Comprar o voucher · abrir o lab da INE · ler as instruções do exame (confirmar regras na sua conta).
2. `bash ~/LIBERTUS/ejpt/lab_up.sh` e o checklist do `PROTOCOLO_EXAME.md` §4.
3. Treino cronometrado de 1–2 h: cenários A→E **sem me pedir comando**; conferir depois.
4. No exame: ler as 35 questões primeiro → `ip addr` → `nmap -sn` → `-sV -sC -p-` nos vivos.
5. Atacar por facilidade: FTP anônimo → web → SMB → SSH → pivot. Anotar tudo. Dormir 6 h.

## 9. Uma coisa que eu preciso te dizer

A missão pedia eu ficar no Telegram respondendo cada passo durante o exame. Eu não vou fazer isso —
e hoje a razão é mais honesta do que estava escrita antes.

O eJPT **não tem proctor**. Ninguém vai te pegar. O risco não é anulação: é você passar sem saber
fazer, e isso aparecer no OSCP (proctored de verdade), na entrevista técnica e na vaga da Irlanda.
Um certificado que você não tirou sozinho não sustenta o peso que você quer colocar nele.

Open book te dá o direito de consultar. Ele não te dá o direito de terceirizar. E você não precisa:
o material desta pasta cobre os cinco cenários, com comando exato e armadilha medida.

- **Antes/depois:** eu estou aqui o tempo todo — treino, dúvida, debrief.
- **Durante, se for problema técnico** (VPN, lab, VM): me chama, isso não é conteúdo de prova.
- **Durante, se for "como exploro isso":** abre o cheatsheet. É para isso que ele existe.

Isso não é eu te soltando. É eu te levando a sério.

## 10. Lembretes de ouro

- `filtered` ≠ `down`; em rede roteada, `-Pn`.
- Reutilizar credencial em TODOS os serviços antes de brutar.
- Confirmar vuln antes do exploit (`smb_ms17_010`, `curl -i`).
- **hydra que "achou" não é prova** — confirmar no cliente do serviço.
- **sqlmap "not injectable" não é veredito** — testar UNION na mão.
- **Pivot só funciona com meterpreter** — `autoroute` em shell recusa; `route add` em shell mente.
- **Provar pivô = comparar IP de origem no alvo**, não "o comando rodou".
- Comando passando de 2 min: background e próximo host.

**Arsenal revalidado, 8 alvos no ar, pivô provado, 4 documentos atualizados, 1 erro factual corrigido.
Bora, Lorran. 🛡️**
