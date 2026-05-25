# NOITE DE PREP - RESUMO
LIBERTUS | 25/05/2026 | Preparacao eJPT Lorran

===================================================================
## O QUE FOI FEITO HOJE
===================================================================

### Arquivos criados em ~/LIBERTUS/ejpt/:

1. tools_status.md
   - Inventario completo das ferramentas instaladas
   - Identificadas ferramentas ausentes criticas
   - Status do lab local

2. CHEATSHEET_eJPT.md
   - Guia completo com comandos exatos para todas as ferramentas
   - Nmap, Metasploit, Hydra, Gobuster, SQLmap, Netcat, Pivoting
   - Pronto para copiar e colar no exame

3. CENARIOS_eJPT.md
   - 5 cenarios completos passo a passo
   - Porta 445 → MS17-010
   - Porta 21 → FTP anon + brute force
   - Porta 80/8080 → gobuster + sqlmap + webshell
   - Porta 22 → hydra SSH
   - Rede /24 → pivoting Metasploit

4. PROTOCOLO_EXAME.md
   - Como Lorran me chama durante o exame
   - Formato de mensagem ideal
   - Plano B se Telegram falhar
   - Checklist pre-exame

5. NOITE_PREP_RESUMO.md (este arquivo)

===================================================================
## STATUS DAS FERRAMENTAS
===================================================================

PRONTAS:
- nmap 7.95 (/snap/bin/nmap)
- gobuster (/home/libertus/go/bin/gobuster)
- sqlmap 1.8.12 (/snap/bin/sqlmap)
- nc/netcat (OpenBSD, /usr/bin/nc)

AUSENTES - INSTALAR URGENTE:
- msfconsole (CRITICO para eJPT)
- hydra (necessario para brute force)
- john (necessario para crack hashes)
- wordlists (/usr/share/wordlists/ nao existe)

COMANDO PARA INSTALAR TUDO:
sudo apt update && sudo apt install -y metasploit-framework hydra john wordlists seclists

===================================================================
## STATUS DO LAB LOCAL
===================================================================

- http://localhost:8080 → ONLINE (OWASP Juice Shop - excelente para treino)
- http://localhost:3000 → OFFLINE

===================================================================
## ACOES URGENTES ANTES DO EXAME
===================================================================

PRIORIDADE MAXIMA:
1. sudo apt install -y metasploit-framework hydra john wordlists seclists
2. msfdb init (inicializar banco do Metasploit)
3. Testar: msfconsole -q -x "version; exit"
4. Testar: hydra -h | head -5

RECOMENDADO:
5. Revisar CHEATSHEET_eJPT.md (30 min)
6. Revisar CENARIOS_eJPT.md (30 min)
7. Praticar um cenario no Juice Shop (http://localhost:8080)
8. Testar comunicacao Telegram com LIBERTUS

===================================================================
## CONFIANCA NO LORRAN
===================================================================

Lorran, voce foi bem nos estudos. O eJPT e um exame pratico
e voce vai ter eu como suporte via Telegram durante todo o exame.

Estrategia para o dia:
- Faz scan em todos os alvos primeiro (nmap em tudo)
- Anota todas as portas abertas
- Me manda o output do nmap
- A gente define juntos qual explorar primeiro
- Sempre vai atras da porta 445 (MS17-010) se estiver aberta
- FTP anonimo e sempre a segunda prioridade

Voce consegue. LIBERTUS esta do seu lado.

===================================================================
## REFERENCIAS RAPIDAS
===================================================================

Documentacao:
- Metasploit: https://docs.metasploit.com
- HackTricks: https://book.hacktricks.xyz
- GTFOBins (escalada Linux): https://gtfobins.github.io
- LOLBAS (escalada Windows): https://lolbas-project.github.io

Wordlists online (se local nao tiver):
- https://github.com/danielmiessler/SecLists
- https://github.com/brannondorsey/naive-hashcat/releases (rockyou)

===================================================================
Criado por LIBERTUS - prep eJPT completo. Bora Lorran!
