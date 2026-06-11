# eJPT Segunda Tentativa — Plano de Recuperação

**Primeira tentativa:** 27/05/2026 — 55 pontos (reprovado, corte=70%)
**Voucher:** ainda válido, pode reagendar
**Status:** preparando segunda tentativa

## O QUE FALTOU (gaps identificados)

### 1. PRIVESC LINUX (crítico)
Na sessão real, entramos no .52 via Drupalgeddon2 e pegamos shell www-data.
Encontramos SUID find mas não escalamos pra root antes do lab travar.
**Ação:** praticar escalada via SUID no DVWA local.

### 2. PIVOT PARA REDE INTERNA (crítico)
DNS Server do .52 apontava pra 192.168.0.2 — rede interna.
Não conseguimos acessar via Metasploit autoroute.
**Ação:** praticar routes e portfwd no Metasploit.

### 3. SENHAS DO BANCO (médio)
MySQL do Drupal tinha credenciais que não conseguimos extrair.
settings.php continha a senha real.
**Ação:** memorizar sequência SSH → cat settings.php → MySQL.

### 4. PROBLEMAS DE AMBIENTE INE (mitigados)
- Teclado não digita "?"
- Copy/paste não funciona
**Mitigações já documentadas na skill.**

## ROTEIRO DE PRÁTICA (antes de reagendar)

### Semana 1: Privesc Linux
```bash
# Lab local
docker exec -it libertus-dvwa bash
# Ou direto no DVWA via browser: http://localhost:8080

# TryHackMe salas gratuitas:
# - Linux PrivEsc (grátis)
# - Kenobi (grátis)

# Técnicas a dominar:
# 1. SUID binaries: find / -perm -4000 2>/dev/null
# 2. Capabilities: getcap -r / 2>/dev/null
# 3. Cron jobs writeable
# 4. sudo -l (NOPASSWD)
```

### Semana 2: Pivoting com Metasploit
```bash
# Conceitos:
# 1. meterpreter > run autoroute -s 192.168.X.0/24
# 2. meterpreter > portfwd add -l 4444 -p 80 -r 192.168.X.X
# 3. proxychains nmap/curl através do pivot

# TryHackMe sala: Wreath (grátis, cobre pivoting completo)
```

### Semana 3: MySQL + Extração de Credenciais
```bash
# Sequência padrão quando tem shell no Linux:
cat /var/www/html/*/sites/default/settings.php 2>/dev/null  # Drupal
cat /var/www/html/*/wp-config.php 2>/dev/null               # WordPress
grep -r "password" /var/www/html/ 2>/dev/null | head -20

# Depois de ter credenciais:
mysql -h localhost -u USER -p'SENHA' -e "use DATABASE; select * from users;"
```

### Semana 4: Simulação Completa
- Rodar HackTheBox ou TryHackMe máquina "Easy"
- Cronometrar: meta = 4 horas do início ao root
- Documentar igual faria no exame real

## CHECKLIST ANTES DE REAGENDAR

- [ ] Escalar privilégio via SUID find sem googlar
- [ ] Configurar pivot Metasploit de memória
- [ ] Extrair senha de settings.php e acessar MySQL
- [ ] Completar 1 máquina HTB/THM em <4h
- [ ] Testar ambiente INE com voucher de demo (se disponível)

## DATA SUGERIDA PARA REAGENDAR

Após completar checklist acima. Estimo: 3-4 semanas de prática.
**Data alvo:** ~07/07/2026 (ajustar conforme progresso)

## LEMBRETE: PONTUAÇÃO

- Primeira tentativa: 55/100 (faltaram ~15 pontos / ~5 questões)
- As questões pendentes eram justamente: privesc, rede interna, senhas
- Com esses 3 gaps fechados, passa tranquilo

---
*Criado por LIBERTUS em 10/06/2026*
