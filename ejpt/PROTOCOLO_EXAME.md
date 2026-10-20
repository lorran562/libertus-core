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
