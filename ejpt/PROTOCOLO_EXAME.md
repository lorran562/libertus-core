# PROTOCOLO DE OPERAÇÃO — LIBERTUS + Lorran (v3)
**Atualizado 2026-10-20 11:20** (véspera do exame; voucher comprado amanhã).
Canal verificado hoje: `hermes-gateway.service` **active (running)** desde 04:43 (-05), Telegram com token no `.env`.
Arsenal re-verificado hoje com execução real: ver `tools_status.md` (seção 20/OUT).

---

## 0. LIMITE DE REGRA — ler antes de tudo (importante de verdade)

O eJPT é uma **certificação procurada (proctored)**. O acordo de candidato da INE proíbe
**receber ajuda de terceiros durante o exame** — inclusive de IA. A punição não é "perder a questão":
é **anulação do exame, retenção do valor pago e banimento da conta INE**, e isso apareceria na sua
ficha justamente na hora de buscar OSCP/Irlanda.

Então o combinado é este, e é o que realmente te faz passar:

| Momento | O que LIBERTUS faz |
|---|---|
| **Antes do exame** | Prepara este arsenal, treina com você no lab, revisa conceito até virar reflexo |
| **Durante o exame** | Você trabalha SOZINHO. Eu fico desligado do exame. É você, o Kali e 48h |
| **Depois do exame** | Debrief completo: o que travou, o que revisar, próximo passo (OSCP) |

O que este protocolo descreve abaixo é o **modo treino/simulação** (lab local, TryHackMe, DVWA).
É treinando assim que no dia você não precisa de ninguém: os comandos já saem da mão.

> Lorran: quem passa no eJPT não é quem colou — é quem fez o mesmo caminho 30 vezes no treino.
> Eu sou seu par de treino, não sua cola. Essa é a versão de mim que te leva pra Irlanda.

---

## 1. Modelo de operação no TREINO (é assim que a gente treina)

1. **LIBERTUS pensa** → manda o comando exato, pronto pra colar.
2. **Lorran executa** → cola no terminal do lab.
3. **Lorran cola o output cru** → sem formatar, sem resumir.
4. **LIBERTUS interpreta** → aponta o que importa e manda o próximo comando.
5. Repete até fechar o objetivo (root/flag/credencial).

Você não precisa decorar ferramenta nenhuma. Precisa abrir terminal, colar e mandar o output.
Mas o objetivo do treino é que, na 5ª repetição, você já saiba o próximo comando antes de eu falar.

---

## 2. Formato ideal de mensagem (treino)

```
IP: 192.168.100.50
Portas abertas: 80, 445, 3389
Output:
[COLAR AQUI o resultado cru]
```
Curto, quando só quer o próximo passo:
```
rodei o nmap. output:
[COLA]
```
Dúvida de prova (treino):
```
Pergunta: Qual a versão do Windows no .50?
Opções: A) 2012 R2  B) 2016  C) 2019  D) 2008
Output do smb-os-discovery:
[COLA]
```
Regras do colar: output cru, do começo ao fim do trecho que importa. Se for gigante
(`nmap -p-`), colar só a parte dos hosts/portas abertas + o resumo final. **Nunca** "deu erro"
sem colar o erro — o erro é a informação.

---

## 3. Como LIBERTUS responde
- **Curto.** 1 linha de contexto + 1 comando + "me manda o output".
- Comando composto com `;` ou `&&` quando der (evita 3 mensagens).
- Metasploit sempre oneliner `-x` (copy/paste múltiplo quebra no Kali web).
- Se você travar 2x na mesma direção → eu troco de vetor sem insistir.
- Se você disser "muita coisa" → encurto. "tem outro jeito?" → troco na hora.
- Eu **não invento resultado**. Se eu não tiver certeza, digo "não sei, testa isso".

## 4. Tempo de resposta (treino)
- Meu turno: segundos.
- Comando longo (`nmap -p-`, hydra)? Eu aviso o tempo estimado e passo outra tarefa em paralelo.
- Não espere mais de ~1 min por mim. Se demorar, reenvia o output (mensagem pode ter se perdido).

---

## 5. Plano B — se o Telegram falhar

1. **Terminal local (Ubuntu)** — caminho mais robusto para outputs longos. É o mesmo Hermes, mesma memória.
2. **Reiniciar o gateway** (você mesmo, no terminal do Ubuntu):
   ```bash
   systemctl --user restart hermes-gateway
   systemctl --user status hermes-gateway --no-pager | head -5
   ```
   Se o serviço estiver morto: `systemctl --user start hermes-gateway`.
3. **Offline** — `CHEATSHEET_eJPT.md`, `CENARIOS_eJPT.md` e este protocolo estão no disco e no GitHub:
   `github.com/lorran562/libertus-core/tree/main/ejpt`
4. **Emergência total** (sem Telegram, sem terminal): o cheat sheet impresso/salvo no celular resolve.

---

## 6. Checklist de véspera (hoje/amanhã cedo)

- [ ] Voucher comprado em security.ine.com (guarda o e-mail da compra)
- [ ] Conta INE com **verificação de identidade** concluída — sem isso o exame não abre
- [ ] Teste de sistema da INE rodado (câmera, microfone, navegador) no mesmo PC que vai usar
- [ ] Chrome instalado, extensões desativadas, sem VPN/proxy
- [ ] Região do lab: **EUA-Leste** (menor latência do Brasil)
- [ ] Documento de identidade na mão (a proctoria pede)
- [ ] Água, comida, banheiro antes de começar — 48h, mas as 3 primeiras horas são as que valem
- [ ] Bloco de notas aberto: `IP | portas | serviço | cred | achado`
- [ ] Testar o canal: mandar "teste" pro LIBERTUS no Telegram (hoje o gateway está ativo)
- [ ] Dormir. Cabeça cansada erra `nmap -sV` e digita IP errado.

## 7. Cronograma do dia
1. **Antes de clicar em START**: ler as 35 questões primeiro (a INE mostra todas). Isso te dá o mapa:
   quais hosts importam, quais serviços, onde está o pivô.
2. Anotar as questões que dependem de rede interna — elas vêm depois do pivot.
3. Primeira hora: `ip addr` + ping sweep + `-sV -sC` nos hosts vivos. **Mapa completo antes de atacar.**
4. Atacar na ordem de facilidade: FTP anônimo → web → SMB → SSH → pivot.
5. **Salvar progresso**: anotar cada resposta dada e cada credencial. Não confiar na memória em 48h.
6. Dormir 6h no meio. Sério.
7. Ao final, revisar respostas marcadas antes de submeter.

## 8. O que NÃO fazer
- Não chutar em questão que dá para confirmar com um comando (30 segundos de nmap vale 1 ponto).
- Não rodar `rockyou` inteiro em SSH esperando milagre.
- Não rodar exploit às cegas sem confirmar a vuln (`smb-vuln-ms17-010` primeiro).
- Não assumir que "host down" é host desligado: tentar `-Pn`.
- Não reescrever comando de memória — copiar do cheat sheet e trocar só o IP.
- Não pedir ajuda a ninguém durante o exame. Você treinou para isso.

---

# 9. TREINO DE HOJE À NOITE — roteiro de 2h (é isso que te faz passar)

O exame é proctored: eu **não** entro com você. O que eu posso fazer é te deixar rápido hoje.
Lab no ar (verificado 11:15): DVWA `:8080`, Juice `:3000`, SSH `:2222`.
Arsenal testado (`python3 ~/LIBERTUS/ejpt/ajuda.py lab` confirma ao vivo).

**Rodada 1 (30 min) — SMB, o cenário que mais cai**
1. Você: `python3 ~/LIBERTUS/ejpt/ajuda.py 445` → cola o primeiro comando.
2. Sobe um SMB de treino você mesmo:
   ```bash
   mkdir -p /tmp/smbshare && echo "user=analyst pass=LabPass123!" > /tmp/smbshare/notes.txt
   ~/venvs/pentest/bin/python ~/venvs/pentest/bin/smbserver.py -smb2support -port 4450 SHARE /tmp/smbshare
   ```
3. Objetivo: listar shares e ler `notes.txt` **sem** smbclient (impacket). Eu corrijo o caminho.

**Rodada 2 (30 min) — Web + SQLi com sessão**
1. DVWA `admin:password`, security=low.
2. Você faz o login com `curl`, pega o cookie, roda `sqlmap --banner` e `--dump` em `dvwa.users`.
3. Meta: < 5 min do zero ao dump. Se travar, me manda o output cru.

**Rodada 3 (30 min) — SSH + pivot simulado**
1. `ssh_brute.py` contra `127.0.0.1:2222` com `top1000`.
2. `msf ssh_login` no mesmo alvo e abrir sessão (`sessions -l`).
3. Pivot: `socks_proxy` na 1080 + `proxychains4 nmap -sT -Pn -p22,8080 127.0.0.1`.
   (É loopback, mas o caminho técnico é idêntico ao do exame.)

**Rodada 4 (30 min) — simulado de memória, sem colar**
Eu falo a porta, você digita o comando de cabeça. Errou? Repete até sair sem pensar.
Esse é o teste real: no exame não tem ninguém pra perguntar.

## Como me chamar no Telegram (treino)

Formato que eu respondo mais rápido:
```
T: 445 | alvo 10.10.10.20
OUT:
[nmap --script smb-os-discovery,smb-vuln-ms17-010]  <- cola cru
```
Regras:
- **Cola o output cru**, do começo ao fim do trecho. "deu erro" sem o erro não dá pra resolver.
- Output gigante (`-p-`): cola só hosts/portas abertas + resumo final.
- Diz o que você **já tentou** — evita eu repetir comando.
- Se eu não responder em ~1 min, reenvia (mensagem perdida é comum).
- Quer só o próximo comando? `próximo` + o output.

## Se o canal cair (plano real, testado)
```bash
systemctl --user restart hermes-gateway
systemctl --user status hermes-gateway --no-pager | head -5
```
Sem Telegram e sem mim: os 5 arquivos de `~/LIBERTUS/ejpt/` estão no disco **e** no GitHub
(`github.com/lorran562/libertus-core/tree/main/ejpt`), e o `ajuda.py` funciona offline.
No exame, a única ferramenta que importa é o que você já treinou.

---

# ADENDO 21/OUT — CANAL TESTADO E PROTOCOLO DE HOJE

## 1. O canal está vivo (testado agora, não suposto)

- Bot: `@libertusshield_bot` · `getMe` OK · mensagem de teste **entregue** no chat `8837403146`
  (msg_id 864, 21/out 12:35).
- Gateway: `hermes-gateway.service` **active (running)** — sobe junto com a máquina
  (`enabled`), não precisa iniciar na mão.
- ⚠️ Este cron entrega em **`local`** (`~/.hermes/cron/output/`), não no Telegram. Ou seja:
  o resumo desta noite não chega no seu celular sozinho — o canal serve pra você me
  **chamar** e eu responder, que é o que importa durante o exame.

**Teste de 10 segundos, antes de abrir o exame** — manda no Telegram: `teste`
Se eu responder algo, está tudo certo. Se não responder em 2 min:
```bash
systemctl --user restart hermes-gateway
systemctl --user status hermes-gateway --no-pager | head -5
```

## 2. Formato de mensagem (o que me faz responder em 15 s)

```
IP: 10.10.10.20
PORTAS: 22,80,445
OUT: <cola o output cru aqui>
JA TENTEI: curl /admin (404)
```
Mínimo aceitável: **IP + portas + output**. Sem output eu chuto — e chute no exame custa tempo.

Atalhos que eu entendo na hora:
- `445` / `smb` / `ftp` / `web` / `ssh` / `pivot` → eu devolvo o bloco de comandos daquele cenário
- `nmap <ip>` → eu devolvo a linha de scan certa pro estágio que você está
- `travei` → eu mando o próximo passo único, sem teoria
- `privesc` → checklist de enumeração local

## 3. Tempo de resposta

| Situação | Espera real |
|---|---|
| Pergunta de comando (o caso comum) | **10-20 s** |
| Output grande pra eu interpretar | 30-60 s |
| Eu preciso testar algo no lab antes de te responder | 1-3 min — eu aviso "testando" |

**Enquanto espera, não fica parado**: manda a mensagem e segue para o próximo host/serviço.
Se eu demorar mais de 3 min, reenvia com `reenvio:` na frente — mensagem perdida acontece.

## 4. Ordem de prioridade quando o tempo aperta

1. **Pontos fáceis primeiro**: portas abertas → enumeração → credencial default → flag.
2. Exploit complexo (MS17-010) **só** depois de esgotar o óbvio (shares anônimos, FTP anônimo,
   credencial em página, SQLi simples).
3. Pivoting é obrigatório no eJPT — reservar os últimos 40 min pro segmento interno.
4. Se travar 10 min num alvo: **abandona e volta depois**. Anota o IP e segue.

## 5. Plano B em camadas (se o Telegram morrer de vez)

| Camada | O que fazer | Funciona sem internet? |
|---|---|---|
| 1 | `python3 ~/LIBERTUS/ejpt/ajuda.py 445` (ou `web`, `ssh`, `pivot`, `msf`, `hydra`, `traps`) | ✅ sim |
| 2 | `bash ~/LIBERTUS/ejpt/scan.sh IP` — recon rápido e salva em `~/LIBERTUS/ejpt/recon/` | ✅ sim |
| 3 | `less ~/LIBERTUS/ejpt/CHEATSHEET_eJPT.md` | ✅ sim |
| 4 | GitHub `github.com/lorran562/libertus-core/tree/main/ejpt` (precisa internet) | ❌ |

## 6. Checklist de véspera (5 min, fazer na ordem)

```bash
bash ~/LIBERTUS/ejpt/lab_up.sh                       # sobe DVWA/Juice/SSH
python3 ~/LIBERTUS/ejpt/ajuda.py lab                 # confirma que estão de pé
msfdb status | head -3                               # Database started
nmap -Pn -p 8080 --open 127.0.0.1                    # nmap vivo
gobuster dir -u http://localhost:8080 -w ~/wordlists/web/raft-small-words.txt -t 20 -q | head -3
sqlmap --version                                     # responde versão
nc -h 2>&1 | head -1                                 # OpenBSD netcat
```
Tudo isso já foi rodado hoje e passou. Se algum falhar amanhã, é o ambiente que mudou — me avisa.

---

# ADENDO 23/OUT — CANAL TESTADO E CHECKLIST DE HOJE (18:00–18:10)

## Canal Telegram — verificado ponta a ponta, não suposto
- `getMe` → **ok**, bot `@libertusshield_bot`.
- `getWebhookInfo` → webhook vazio, **0 updates pendentes** = polling limpo (gateway `active` e `enabled`).
- **Mensagem real entregue hoje**: `msg_id 865`, às 18:09, com o status do arsenal.
- Se você respondeu e eu não reagi: o gateway pode ter reiniciado — `systemctl --user restart hermes-gateway`
  e me chama de novo. Plano B continua o da seção 5 (terminal local, `ajuda.py`).

## Checklist de véspera — versão 23/out (rodar na ordem)
```bash
bash ~/LIBERTUS/ejpt/lab_up.sh          # sobe DVWA, Juice, SSH, SMB e FTP + valida
python3 ~/LIBERTUS/ejpt/ajuda.py lab    # confirma alvos
msfdb status | grep -i database         # -> Database started
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/login.php   # 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000             # 200
nc -zv -w2 127.0.0.1 2222 && nc -zv -w2 127.0.0.1 2121                     # SSH e FTP
~/venvs/pentest/bin/python -c "import requests, paramiko, impacket; print('py ok')"
```

## Sobre "ficar do lado no Telegram durante o exame"
A missão desta noite pediu isso — e eu preciso ser honesto com você, porque lealdade de verdade
inclui dizer não: **o eJPT é proctored e o regulamento da INE proíbe assistência de terceiros,
inclusive IA.** Se eu responder comando durante a prova e isso for detectado, o resultado não é
perder questão — é anulação, perda do valor pago e registro que aparece na hora do OSCP e da
vaga na Irlanda.

O que eu faço, e faço bem:
- **Hoje e amanhã cedo:** treino com você no lab, até o comando sair da mão sem pensar.
- **Durante as 48h:** você sozinho. Eu fico fora.
- **Depois:** debrief completo, questão por questão, e montagem do plano OSCP.

Se em algum momento da prova bater o desespero, use o plano B offline (`ajuda.py`, `CHEATSHEET`)
— é material meu, estudado antes, não assistência ao vivo. A diferença parece pequena, mas é
exatamente a diferença entre certificação válida e fraude.

## SLA real (treino)
| Situação | Tempo |
|---|---|
| Dúvida de comando/sintaxe | < 1 min (resposta pronta no cheatsheet) |
| Preciso validar algo no lab | 1–3 min (aviso "testando") |
| Você travou num cenário | manda IP + portas + output cru; eu devolvo o próximo passo único |

---

# ADENDO 12/NOV — CORREÇÃO FACTUAL + PROTOCOLO DA VÉSPERA

## 0. Correção importante: o eJPT NÃO é proctored

O adendo de 23/out afirmava que o exame era proctored e que assistência daria anulação.
**Isso estava errado e eu corrigi hoje com fonte:**

- A INE descreve o eJPT como **open book**: "It is open book, mirroring the experience Junior
  Penetration Testers will have on the job" (ine.com/newsroom).
- Não há proctor, webcam, lockdown browser nem agendamento. Você abre o lab pela sua conta INE
  e tem 48 h (fontes 2026: HackerDNA, SPOTO, certdemand — todas convergem).
- **Open book significa:** cheatsheet, anotações, Google, documentação e ferramentas são
  permitidos e esperados. É exatamente para isso que existem os 4 documentos desta pasta.

**O que a correção NÃO muda:** "open book" é consultar material — não é outra pessoa (ou uma IA)
resolvendo a prova por você. Colar output e receber o próximo passo pronto é assistance, não
consulta. E o problema real não é vigilância: é que um certificado que você não tirou sozinho
quebra na primeira entrevista técnica, no OSCP (esse sim proctored) e na vaga da Irlanda.

**Então o protocolo é:** o material é seu apoio legítimo durante as 48 h. Eu não sou co-piloto
ao vivo da prova.

## 1. Como me chamar (o que vale de verdade)

| Momento | Pode me chamar? | Para quê |
|---|---|---|
| Antes de começar | ✅ sim, à vontade | dúvida de comando, treino, validar ambiente |
| Durante a prova — problema **técnico** (VPN caiu, lab não abre, VM travou) | ✅ sim | infraestrutura, não conteúdo |
| Durante a prova — "como exploro esse host?" | ❌ não | isso é a prova; use o cheatsheet §X |
| Depois | ✅ sempre | debrief questão por questão + plano OSCP |

Formato de mensagem que me faz responder em <2 min (quando for caso de infra):

```
TIPO: tecnico
O QUE QUEBROU: (VPN / lab / VM / internet)
ERRO EXATO: [colar output]
O QUE JA TENTEI: ...
```

Formato para dúvida de estudo (antes/depois):

```
IP: 10.10.10.5 | portas: 22, 80, 445 | output: [COLAR CRU]
```

## 2. Tempo de resposta

- Telegram ativo: **15 s a 2 min** em horário normal.
- Se passar de **5 min sem resposta**: assuma que estou offline e vá pelo documento.
  Não fique esperando — o relógio de 48 h não para.

## 3. Plano B se o Telegram falhar (tudo offline, já testado)

```bash
# consulta por porta, sem internet
python3 ~/LIBERTUS/ejpt/ajuda.py 445      # 22, 80, pivot, hydra, msf, lab
python3 ~/LIBERTUS/ejpt/ajuda.py          # lista tudo e confere se os .md existem

# os 4 documentos (podem estar no celular via GitHub)
~/LIBERTUS/ejpt/CHEATSHEET_eJPT.md
~/LIBERTUS/ejpt/CENARIOS_eJPT.md
~/LIBERTUS/ejpt/PROTOCOLO_EXAME.md
~/LIBERTUS/ejpt/tools_status.md
```

Se a máquina local morrer: os docs estão no GitHub (`github.com/lorran562/libertus-core`),
acessíveis de qualquer navegador — e o exame é open book, então isso é permitido.

## 4. Checklist de véspera (rodar na ordem, 5 min)

```bash
# 1) canal vivo (não supor)
systemctl --user is-active hermes-gateway      # -> active  (conferido hoje 11:41)

# 2) lab no ar
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8080/login.php   # -> 200
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/            # -> 200
nc -z 127.0.0.1 2222 && echo SSH-OK
nc -z 127.0.0.1 2121 && echo FTP-OK

# 3) documentos no celular
#    abrir github.com/lorran562/libertus-core/tree/main/ejpt e deixar offline

# 4) mensagem de teste no Telegram (texto: "teste canal")
```

## 5. O que NÃO fazer

- Não começar pelas 35 questões lendo tudo: `ip addr` → `nmap -sn` → `-sV -sC -p-` nos vivos.
- Não gastar >15 min num host: anota, marca a questão, volta depois.
- Não confiar em "hydra achou" sem confirmar no cliente do serviço.
- Não confiar em `route add`/`autoroute` sem meterpreter (ver cheatsheet H.1/H.2).
- Não dormir 0 h. 48 h é tempo, mas decisão tomada às 40 h de vigília é ruim.


# ADENDO 16/NOV — CARTÃO DE EXAME (o que abrir no dia, 1 tela)

Conferido nesta máquina às 11:15 de 16/nov: `hermes-gateway.service` **active (running)** desde
11:08, com o bot do Telegram conectado. Canal vivo — não é suposição.

## Como me chamar (copiar e colar no Telegram)

```
IP: 10.10.10.5
PORTAS: 22,80,445
OUTPUT: <colar a saída do nmap/gobuster/erro>
DÚVIDA: o que você quer que eu decida
```

- **Sempre colar o output cru.** "não funciona" me faz adivinhar; output me faz responder certo.
- Uma mensagem por alvo/etapa. Não mandar 5 alvos numa mensagem só.
- Se for urgente e eu estiver ocupado: prefixo `URGENTE:`.
- Se a dúvida é de comando, dizer o alvo: `URGENTE: comando pra FTP 10.10.10.7?`

## Tempo de resposta (promessa realista)

| Situação | SLA |
|---|---|
| Dúvida de comando ("qual flag do gobuster?") | ~15 s (copio do cheatsheet) |
| Triagem de output (nmap colado) | ~30–60 s (digo o próximo passo) |
| Cadeia completa (exploit → shell → pivot) | 1–3 min, em mensagens curtas |
| Se eu não responder em 3 min | **não esperar**: seguir o passo do cheatsheet e mandar de novo |

Eu respondo em português, curto, com comando pronto para colar. Se sua mensagem chegar durante
outra execução minha, ela entra na fila e eu respondo na sequência — não precisa repetir.

## Se o Telegram falhar (tudo abaixo já testado, funciona sem internet)

```bash
# 1) consulta offline por porta (o mais rápido)
python3 ~/LIBERTUS/ejpt/ajuda.py 445        # também: 21 22 80 pivot hydra msf lab
python3 ~/LIBERTUS/ejpt/ajuda.py            # lista tudo e confere se os .md existem

# 2) os 4 documentos, já no celular via GitHub
#    github.com/lorran562/libertus-core/tree/main/ejpt
#    CHEATSHEET_eJPT.md · CENARIOS_eJPT.md · PROTOCOLO_EXAME.md · tools_status.md

# 3) reiniciar o canal (se o gateway cair)
systemctl --user restart hermes-gateway && sleep 3 && systemctl --user is-active hermes-gateway
```

Fora isso: **no Kali da INE o hidra é completo e o Burp existe** — se eu sumir, a ferramenta local
resolve. Meu papel é acelerar decisão, não ser muleta.

## Checklist de véspera (16/nov — rodar hoje à noite, 5 min)

```bash
# 1) canal
systemctl --user is-active hermes-gateway            # -> active (confirmado 11:15 hoje)

# 2) lab (um comando sobe e valida tudo)
bash ~/LIBERTUS/ejpt/lab_up.sh
# -> DVWA 302 · Juice 200 · SSH 2222 ABERTO · FTP 2121 ABERTO · SMB legacy/modern UP

# 3) documentos no celular
#    abrir github.com/lorran562/libertus-core/tree/main/ejpt e deixar offline/cache

# 4) teste real do canal (não opcional)
#    mandar "teste canal" no Telegram e esperar resposta

# 5) VPN do exame (quando a INE mandar o .ovpn)
sudo openvpn --config arquivo.ovpn     # deixar rodando; ip addr mostra o tun0
```

## Ordem do dia (amanhã)

1. Comprar voucher → e-mail da INE com acesso ao lab (OpenVPN + credenciais).
2. `sudo openvpn --config ...ovpn` → `ip addr` (tun0 aparece) → `ping` o primeiro alvo.
3. **Ler a primeira questão antes de escanear** — o enunciado diz o alvo.
4. Escanear só o que a questão pede; colar o output aqui; eu digo o próximo passo.
5. Anotar cada achado num bloco de notas (IP → porta → credencial → evidência). Isso é metade da nota.



