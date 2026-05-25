# STATUS DAS FERRAMENTAS - eJPT PREP
Gerado por LIBERTUS em 25/05/2026

---

## FERRAMENTAS INSTALADAS

| Ferramenta | Status | Versao | Caminho |
|------------|--------|--------|---------|
| nmap       | OK     | 7.95   | /snap/bin/nmap |
| gobuster   | OK     | instalado | /home/libertus/go/bin/gobuster |
| sqlmap     | OK     | 1.8.12 | /snap/bin/sqlmap |
| nc/netcat  | OK     | OpenBSD netcat | /usr/bin/nc, /usr/bin/netcat |
| msfconsole | AUSENTE | N/A | nao instalado |
| hydra      | AUSENTE | N/A | nao instalado |
| john       | AUSENTE | N/A | nao instalado |

---

## DETALHES

### nmap 7.95
- Caminho: /snap/bin/nmap
- Status: PRONTO

### gobuster
- Caminho: /home/libertus/go/bin/gobuster
- Status: PRONTO
- Nota: wordlist /usr/share/wordlists/ NAO existe neste sistema
  Wordlists alternativas: ~/sqlmap/data/txt/ (para SQLmap)

### sqlmap 1.8.12
- Caminho: /snap/bin/sqlmap
- Status: PRONTO (versao levemente desatualizada, funcional)

### nc / netcat
- Caminho: /usr/bin/nc e /usr/bin/netcat
- Status: PRONTO (OpenBSD netcat)

---

## FERRAMENTAS AUSENTES - INSTALAR ANTES DO EXAME

### msfconsole (Metasploit Framework)
- CRITICO para eJPT - MS17-010, meterpreter, pivoting
- Instalar:
  curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall
  chmod 755 msfinstall && sudo ./msfinstall

### hydra
- Necessario para brute force SSH/FTP/HTTP
- Instalar: sudo apt install hydra -y

### john (John the Ripper)
- Necessario para crack de hashes
- Instalar: sudo apt install john -y

### wordlists (SecLists / rockyou)
- /usr/share/wordlists/ NAO existe
- Instalar: sudo apt install wordlists seclists -y
  Ou: sudo gzip -d /usr/share/wordlists/rockyou.txt.gz (apos instalacao)

---

## LAB LOCAL

| Servico | URL | Status |
|---------|-----|--------|
| Juice Shop | http://localhost:8080 | ONLINE (OWASP Juice Shop) |
| localhost:3000 | http://localhost:3000 | OFFLINE / sem resposta |

---

## ACOES URGENTES ANTES DO EXAME

1. sudo apt install metasploit-framework hydra john wordlists -y
2. Verificar se msfdb init foi executado
3. Baixar SecLists: sudo apt install seclists
4. Testar: msfconsole -q -x "version; exit"
