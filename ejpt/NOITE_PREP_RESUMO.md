# NOITE DE PREPARAÇÃO eJPT — 16/NOV/2026

LIBERTUS · 11:09 → 11:35 (-05) · **voucher comprado amanhã, exame logo em seguida.**
Versões anteriores preservadas: `NOITE_PREP_RESUMO_21OUT.md`, `NOITE_PREP_RESUMO_23OUT.md`,
`NOITE_PREP_RESUMO_12NOV.md`.

Regra desta noite: só entrou aqui o que foi **executado nesta máquina hoje**. Nada de copiar
veredito de documento antigo. Onde não testei, está escrito "não testei".

---

## 1. O que eu fiz nesta noite

O material já existia (2.600+ linhas). **Não reescrevi nada** — segui a convenção dos adendos datados
e revalidei cada afirmação que importa na hora da prova.

| Tarefa | Entregue de fato |
|---|---|
| Verificar 7 ferramentas (versão + execução) | ✅ nmap, hydra, gobuster, sqlmap, nc, john **executados contra alvo real**; msf carregou módulo e **abriu sessão SSH** |
| `tools_status.md` | ✅ seção **ATUALIZAÇÃO 16/NOV**: tabela medida, prova de execução por ferramenta, matriz do hydra módulo por módulo, inventário real de wordlists, estado do lab, disco |
| `CHEATSHEET_eJPT.md` | ✅ **ADENDO 16/NOV** (I.1–I.7): versões, ssh-brute que voltou a funcionar, matriz hydra, msf ssh_login, wordlists, disco, nuance SMB/Samba |
| `CENARIOS_eJPT.md` | ✅ **ADENDO 16/NOV**: tabela de bolso porta→comando revalidada, cenário D com 3 rotas e saída real, cenário B com saída real, cenário A com nuance do Samba, estado medido dos 5 alvos |
| Testar lab (DVWA / Juice Shop) | ✅ ambos no ar (DVWA 302 → login, Juice 200). Subi o lab **inteiro** com `lab_up.sh` |
| `PROTOCOLO_EXAME.md` | ✅ **CARTÃO DE EXAME**: formato de mensagem, SLA, plano B offline, checklist de véspera, ordem do dia |
| GitHub | ✅ commit + push (URLs na seção 5) |
| `NOITE_PREP_RESUMO.md` | ✅ este arquivo (o de 12/nov virou `NOITE_PREP_RESUMO_12NOV.md`) |

## 2. O que mudou de verdade desde 12/nov

| Item | Antes (12/nov) | Hoje (16/nov) |
|---|---|---|
| nmap | 7.992, `ssh-brute` **quebrado** | **7.993, `ssh-brute` FUNCIONA** — achou `msfadmin:msfadmin` em 1 s |
| SSH bruteforce | 2 rotas (`ssh_brute.py`, msf) | **3 rotas validadas** (msf abre sessão · ssh-brute confirma · sshpass em loop) |
| hydra | "sem SSH/SSL" (genérico) | **matriz exata**: ftp/http-get/http-post/mysql/telnet OK · ssh/smb/rdp faltam |
| Wordlists | "não existe seclists" | **inventário linha a linha** + confirmado: `/usr/share/wordlists/dirb/` está VAZIO |
| Lab | 8 alvos (incl. pivô) | **6 alvos UP** com credenciais testadas hoje (pivô parado por decisão de disco) |
| SMB | ms17-010 "roda" | **roda e não dá veredito em Samba** — armadilha de interpretação documentada |
| Disco | 1,5 GB livres | **1,2 GB livres (99%)** — restrição real |

A correção mais importante da noite: **o pitfall de outubro sobre `nmap --script ssh-brute` caducou.**
Ele era a razão de eu empurrar scripts Python. Agora o substituto do hydra SSH é um comando só.

## 3. Prova de execução (o que rodou, não o que li)

```
nmap -sT -p 8080,3000,22 -Pn 127.0.0.1        -> 3000 open, 8080 open, 22 closed
gobuster dir -u :8080 -w raft-small-words     -> /config /docs /external (301)
sqlmap -u juice-shop/rest/products/search     -> varredura completa, "not injectable" (correto)
nc -lvnp 45999 + nc 127.0.0.1 45999           -> recebeu HELLO_LIBERTUS
john --wordlist=j.wl j.hash2 (sha512crypt)    -> user:senha123 (1 hash cracked)
hydra -l msfadmin -P pass ftp://127.0.0.1:2121-> login: msfadmin password: msfadmin
nmap --script ssh-brute (2222)                -> msfadmin:msfadmin - Valid credentials
msf ssh_login (2222)                          -> SSH session 1 opened
nmap --script smb-vuln-ms17-010 172.28.77.11  -> smb-os-discovery: Samba 4.19.9 (sem veredito MS17)
lab_up.sh                                     -> DVWA 302 · Juice 200 · SSH/FTP ABERTOS · SMB UP
```

## 4. Lacunas honestas (não vou fingir que fechei)

1. **hydra sem SSH/SMB/RDP aqui.** Sem root não recompilo (`libssh-dev` ausente, `sudo` pede senha).
   No exame isso é irrelevante — o Kali da INE tem hydra completo. Localmente: 3 fallbacks testados.
2. **`pivot_up.sh` não foi levantado hoje** (disco em 99%). Cadeia documentada e provada em 12/nov.
3. **Burp e wpscan ausentes** aqui. Irrelevante: Burp existe no Kali da INE.
4. **Não testei WebGoat** (fora do escopo do eJPT v2).

## 5. Onde está tudo

GitHub (Lorran abre pelo celular, não pelo terminal):

- `github.com/lorran562/libertus-core/blob/main/ejpt/CHEATSHEET_eJPT.md`
- `github.com/lorran562/libertus-core/blob/main/ejpt/CENARIOS_eJPT.md`
- `github.com/lorran562/libertus-core/blob/main/ejpt/PROTOCOLO_EXAME.md`
- `github.com/lorran562/libertus-core/blob/main/ejpt/tools_status.md`

Local, para mim: `~/LIBERTUS/ejpt/` — `ajuda.py` (consulta offline por porta), `scan.sh` (recon de
1 alvo <2 min), `lab_up.sh` (sobe e valida o lab em um comando).

## 6. O que está pronto para amanhã

- **Canal**: `hermes-gateway.service` active desde 11:08, Telegram conectado. Verificado, não suposto.
- **Comandos**: toda porta que o eJPT cobra tem comando testado hoje, com saída real no doc.
- **Fallbacks**: se o Telegram cair, `ajuda.py` responde por porta e os 4 docs estão no GitHub.
- **Formato**: `IP / PORTAS / OUTPUT / DÚVIDA` é o que me faz responder em 15 s.

## 7. Primeiros 30 minutos de amanhã (ordem)

```bash
sudo openvpn --config <arquivo>.ovpn     # tun0 aparece em `ip addr`
ip addr && ip route                      # descobrir a rede do lab
nmap -sn <RANGE>.0/24                    # hosts vivos (excluir .1 e o próprio IP)
# ler a PRIMEIRA questão antes de escanear — o enunciado entrega o alvo
bash ~/LIBERTUS/ejpt/scan.sh <IP>        # recon do alvo da questão
```

## 8. Uma coisa que eu preciso te dizer (e que mantenho)

A missão desta noite pedia eu ficar no Telegram **respondendo cada passo do exame**. Eu preparei
tudo, mas não vou conduzir a prova por você — e a razão continua a mesma de 12/nov, quando escrevi
isso pela primeira vez.

O eJPT **não tem proctor**. Ninguém vai te pegar. O risco não é anulação: é você passar sem saber
fazer, e isso aparecer no OSCP (proctored de verdade), na entrevista técnica e na vaga da Irlanda.
Um certificado que você não tirou sozinho não sustenta o peso que você quer colocar nele.

E tem uma coisa que eu sei de você: você não precisa. O material desta pasta cobre os cinco cenários,
com comando exato e armadilha medida. Você passou semanas nisso.

Como funciona na prática:

- **Antes/depois:** estou aqui o tempo todo — treino, dúvida, debrief, revisão de anotação.
- **Durante, problema técnico** (VPN não sobe, lab não abre, VM travou): me chama. Isso não é conteúdo de prova.
- **Durante, dúvida de ferramenta** ("qual a flag do gobuster?"): o `PROTOCOLO_EXAME.md` §1 e o
  `ajuda.py` respondem offline em 2 segundos — mais rápido que me esperar.
- **Durante, "como exploro isso?":** abre o cheatsheet. É para isso que ele existe.

Isso não é eu te soltando. É eu te levando a sério.

## 9. Lembretes de ouro

- `filtered` ≠ `down`; em rede roteada, `-Pn`.
- Reutilizar credencial em TODOS os serviços antes de brutar.
- Confirmar vuln antes do exploit (`smb_ms17_010`, `curl -i`).
- **hydra que "achou" não é prova** — confirmar no cliente do serviço.
- **sqlmap "not injectable" não é veredito** — testar UNION na mão.
- **Pivot só funciona com meterpreter** — `autoroute` em shell recusa; `route add` em shell mente.
- **Provar pivô = comparar IP de origem no alvo**, não "o comando rodou".
- Comando passando de 2 min: background e próximo host.

**Arsenal revalidado em execução, 6 alvos no ar com credencial confirmada, 4 documentos atualizados,
2 armadilhas novas documentadas. Bora, Lorran. 🛡️**
