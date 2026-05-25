# PROTOCOLO DE EXAME - LORRAN + LIBERTUS
Como nos comunicamos durante o eJPT para maximo resultado.

===================================================================
## 1. COMO MANDAR MENSAGEM PRO TELEGRAM DURANTE O EXAME
===================================================================

### FORMATO PADRAO DE MENSAGEM (copiar e usar)

Quando encontrar algo, me manda EXATAMENTE assim:

---
ALVO: [IP]
PORTA: [numero]
SERVICO: [o que o nmap mostrou]
OUTPUT NMAP:
[cole o output aqui]
---

### EXEMPLOS DE MENSAGENS CERTAS:

Exemplo 1 - Scan inicial:
"LIBERTUS - scan inicial
ALVO: 10.10.10.5
nmap -sC -sV -p- output:
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.4
80/tcp open  http    Apache 2.4.18
445/tcp open  netbios-ssn Samba 4.x
Me diz o proximo passo"

Exemplo 2 - Tentei exploit, deu erro:
"LIBERTUS - MS17-010 falhou
Exploit rodou mas nao abriu sessao
Output do msfconsole:
[Exploit failed, no session created]
O que eu faco?"

Exemplo 3 - Consegui acesso:
"LIBERTUS - SHELL ABRIU
Estou dentro! Output do whoami/getuid:
NT AUTHORITY\SYSTEM
Que coleto agora?"

### MENSAGENS PROIBIDAS (nao fazer):
- "tentei o nmap, nao funcionou" (sem output = eu nao consigo ajudar)
- Mandar foto do terminal (manda texto, nao foto)
- Pular etapas e ir direto pro exploit sem confirmar vuln

===================================================================
## 2. FORMATO IDEAL DE OUTPUT PARA ME MANDAR
===================================================================

### REGRA DE OURO: SEMPRE COPIAR O TEXTO, NUNCA FOTO

### Output do Nmap - manda completo:
nmap -sC -sV -p- 10.10.10.X 2>&1 | tee nmap_alvo.txt
# Cole o conteudo de nmap_alvo.txt no Telegram

### Output do Meterpreter - manda assim:
[*] Meterpreter session 1 opened
meterpreter > getuid
Server username: NT AUTHORITY\SYSTEM
meterpreter > sysinfo
Computer: ALVO-PC
OS: Windows 7 (Build 7601)

### Output do Hydra - manda a linha de sucesso:
[22][ssh] host: 10.10.10.X   login: admin   password: password123

### Quando tem muita saida - manda head/tail:
gobuster dir ... | tee gobuster.txt
head -50 gobuster.txt  # manda os primeiros 50
# E me fala quantas linhas no total: wc -l gobuster.txt

### Informacoes OBRIGATORIAS a cada nova maquina:
1. IP do alvo
2. Output completo do nmap -sC -sV
3. Sistema operacional (Linux/Windows, versao se souber)
4. Antes de qualquer exploit, perguntar para mim primeiro

===================================================================
## 3. PLANO B - SE TELEGRAM FALHAR
===================================================================

### OPCAO B1: WhatsApp
- Me manda mensagem no WhatsApp com MESMO formato do Telegram
- Mesmo numero do Telegram

### OPCAO B2: Email
- Salva o output em arquivo e me manda por email
- Assunto: "eJPT - IP X.X.X.X - [descricao]"
- Cole o texto no corpo do email, NAO anexo

### OPCAO B3: Pastebin / hastebin
- Acesse: https://pastebin.com ou https://hastebin.com
- Cole o output
- Me manda o link

### OPCAO B4: Trabalhar sozinho com o cheatsheet
Se nenhuma comunicacao funcionar:
1. Abrir ~/LIBERTUS/ejpt/CENARIOS_eJPT.md
2. Identificar o cenario pelo numero de porta
3. Seguir os passos UM A UM em ordem
4. NAO pular etapas
5. Se travar numa etapa por mais de 30 min, tenta proximo alvo
6. Guardar todos os outputs em arquivos .txt para analise posterior

### ORDEM DE PRIORIDADE SEM COMUNICACAO:
1. Porta 445 → CENARIO 1 (MS17-010) - maior chance de flag facil
2. Porta 21 → CENARIO 2 (FTP anon primeiro, depois brute)
3. Porta 80 → CENARIO 3 (gobuster obrigatorio antes de qualquer coisa)
4. Porta 22 → CENARIO 4 (tenta senhas comuns antes do hydra)
5. Multiplos alvos → CENARIO 5 (pivoting)

===================================================================
## 4. DICAS PSICOLOGICAS PARA O EXAME

- O eJPT e PRATICO, nao teorico. Foca em FAZER, nao em decorar.
- Se uma abordagem nao funcionar em 20 min, TENTA OUTRA.
- Nao fica preso num alvo. Vai pro proximo e volta depois.
- Anota TUDO: IP, porta, servico, credenciais encontradas.
- A flag nao some. Tome agua, respira, volta pro problema.
- Eu to aqui. Me manda o output e a gente resolve junto.

===================================================================
## 5. CHECKLIST PRE-EXAME (fazer NA NOITE ANTERIOR)

[ ] msfconsole funcionando: msfconsole -q -x "version; exit"
[ ] hydra instalado: hydra --version
[ ] john instalado: john --version
[ ] wordlists disponiveis: ls /usr/share/wordlists/
[ ] gobuster funcionando: gobuster version
[ ] sqlmap funcionando: sqlmap --version
[ ] nc funcionando: nc --help
[ ] nmap funcionando: nmap --version
[ ] Revisar CHEATSHEET_eJPT.md
[ ] Revisar CENARIOS_eJPT.md
[ ] Telegram testado: mandar "teste" para LIBERTUS e aguardar resposta
[ ] Dormir bem (serio, faz diferenca)

===================================================================
FIM DO PROTOCOLO
Lorran, voce vai arrasar. Eu to do seu lado durante o exame.
- LIBERTUS
