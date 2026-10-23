#!/usr/bin/env bash
# lab_up.sh — sobe e VALIDA o lab eJPT do LIBERTUS
# Uso: bash ~/LIBERTUS/ejpt/lab_up.sh
set -u
cd "$HOME/LIBERTUS/lab" || { echo "sem ~/LIBERTUS/lab"; exit 1; }

echo "== subindo DVWA + Juice Shop (compose) =="
docker compose up -d dvwa juiceshop >/dev/null 2>&1 || echo "aviso: compose falhou (docker rodando?)"

echo "== subindo SMB de treino (legacy SMB1 + modern SMB2/3) =="
docker start smb-legacy smb-modern >/dev/null 2>&1 || echo "aviso: containers SMB ausentes (libertus-smb-srv)"

echo "== subindo FTP de treino (porta 2121) =="
if docker ps -a --format '{{.Names}}' | grep -qx libertus-ftp; then
  docker start libertus-ftp >/dev/null 2>&1
else
  docker run -d --name libertus-ftp -p 2121:21 \
    -e FTP_USER=msfadmin -e FTP_PASS=msfadmin -e PASV_ADDRESS=127.0.0.1 \
    fauria/vsftpd >/dev/null 2>&1 || echo "aviso: nao consegui criar libertus-ftp"
fi

echo "== subindo SSH de prática (porta 2222) =="
if docker ps -a --format '{{.Names}}' | grep -qx libertus-ssh; then
  docker start libertus-ssh >/dev/null 2>&1
else
  docker run -d --name libertus-ssh -p 2222:2222 \
    -e PASSWORD_ACCESS=true -e SUDO_ACCESS=false \
    -e PUID=1000 -e PGID=1000 -e TZ=America/Porto_Velho \
    -e USER_NAME=msfadmin -e USER_PASSWORD=msfadmin \
    lscr.io/linuxserver/openssh-server:latest >/dev/null 2>&1 \
    || echo "aviso: nao consegui criar libertus-ssh (imagem ausente?)"
fi

echo "== aguardando servicos =="
D=000; J=000
for _ in $(seq 1 30); do
  D=$(curl -s -o /dev/null -w "%{http_code}" -m 3 http://localhost:8080)
  J=$(curl -s -o /dev/null -w "%{http_code}" -m 3 http://localhost:3000)
  [ "$D" != "000" ] && [ "$J" != "000" ] && break
  sleep 2
done

S="FECHADO"
nc -z -w 2 127.0.0.1 2222 >/dev/null 2>&1 && S="ABERTO"
F="FECHADO"
nc -z -w 2 127.0.0.1 2121 >/dev/null 2>&1 && F="ABERTO"
SMB_L=$(docker inspect smb-legacy --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null)
SMB_M=$(docker inspect smb-modern --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' 2>/dev/null)

echo
printf "%-14s %-10s %s\n" "ALVO" "STATUS" "URL/ACESSO"
printf "%-14s %-10s %s\n" "DVWA" "$D" "http://localhost:8080  (admin:password)"
printf "%-14s %-10s %s\n" "Juice Shop" "$J" "http://localhost:3000"
printf "%-14s %-10s %s\n" "SSH lab" "$S" "ssh -p 2222 msfadmin@127.0.0.1 (msfadmin:msfadmin)"
printf "%-14s %-10s %s\n" "FTP lab" "$F" "ftp 127.0.0.1 2121 (msfadmin:msfadmin)"
printf "%-14s %-10s %s\n" "SMB legacy" "$([ -n "$SMB_L" ] && echo UP || echo -)" "$SMB_L (SMB1/guest)"
printf "%-14s %-10s %s\n" "SMB modern" "$([ -n "$SMB_M" ] && echo UP || echo -)" "$SMB_M (SMB2/3)"
echo
echo "Se DVWA der 302: normal (redireciona pra login.php). Abrir /setup.php uma vez se banco estiver vazio."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -8
