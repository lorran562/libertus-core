#!/usr/bin/env bash
# Lab de PIVOTING do LIBERTUS — host -> host de borda (SSH, dual-homed) -> alvo interno
# Validado 12/nov/2026 com prova de IP de origem no alvo.
#
# Topologia:
#   host (atacante)  --2223-->  pivot-edge  [pivot-ext 172.21.0.2 | pivot-int 172.20.0.2]
#   pivot-int 172.20.0.0/16:  pivot-internal 172.20.0.3 (HTTP :8081)
#                             libertus-dvwa  172.20.0.4 (host de borda p/ cadeia msf)
#
# Uso: bash ~/LIBERTUS/ejpt/pivot_up.sh
#      bash ~/LIBERTUS/ejpt/pivot_up.sh down     # derruba tudo

set -u
NET_EXT="pivot-ext"
NET_INT="pivot-int"
EDGE="pivot-edge"
INTERNAL="pivot-internal"

if [ "${1:-up}" = "down" ]; then
  docker rm -f "$EDGE" "$INTERNAL" >/dev/null 2>&1
  docker network disconnect -f "$NET_INT" libertus-dvwa >/dev/null 2>&1
  docker network rm "$NET_INT" "$NET_EXT" >/dev/null 2>&1
  echo "[+] lab de pivô derrubado"
  exit 0
fi

# --- redes ---
# Sub-rede explícita: sem --subnet o Docker pode sortear outra faixa e todo IP fixo falha.
docker network inspect "$NET_EXT" >/dev/null 2>&1 || docker network create --subnet 172.21.0.0/16 "$NET_EXT" >/dev/null
docker network inspect "$NET_INT" >/dev/null 2>&1 || docker network create --subnet 172.20.0.0/16 "$NET_INT" >/dev/null

# --- alvo interno: PHP built-in server (alpine NÃO tem applet httpd) ---
mkdir -p /tmp/pivotwww
[ -f /tmp/pivotwww/index.php ] || printf '<?php echo "PIVOT-OK"; ?>' > /tmp/pivotwww/index.php
chmod 755 /tmp/pivotwww /tmp/pivotwww/index.php 2>/dev/null
docker rm -f "$INTERNAL" >/dev/null 2>&1
docker run -d --name "$INTERNAL" --network "$NET_INT" --ip 172.20.0.3 \
  -v /tmp/pivotwww:/var/www php:8.3-cli \
  php -S 0.0.0.0:8081 -t /var/www >/dev/null

# --- host de borda: sshd dual-homed ---
# ATENÇÃO: o sshd do linuxserver escuta na 2222 DENTRO do container (-p 2223:2222).
# Mapear 2223:222 dá "connection closed by remote host" e parece senha errada.
docker rm -f "$EDGE" >/dev/null 2>&1
docker run -d --name "$EDGE" --network "$NET_EXT" \
  -e PUID=1000 -e PGID=1000 -e USER_NAME=msfadmin -e USER_PASSWORD=msfadmin \
  -e PASSWORD_ACCESS=true -p 2223:2222 \
  lscr.io/linuxserver/openssh-server:latest >/dev/null

echo "[*] aguardando sshd subir..."
for i in $(seq 1 30); do
  nc -z 127.0.0.1 2223 >/dev/null 2>&1 && break
  sleep 1
done
docker network connect --ip 172.20.0.2 "$NET_INT" "$EDGE" 2>/dev/null

# --- DVWA como host de borda (cadeia web RCE -> meterpreter -> autoroute) ---
if docker inspect libertus-dvwa >/dev/null 2>&1; then
  docker network connect --ip 172.20.0.4 "$NET_INT" libertus-dvwa 2>/dev/null
fi

echo
echo "=== STATUS ==="
docker inspect "$EDGE" --format 'edge: {{range $k,$v := .NetworkSettings.Networks}}{{$k}}={{$v.IPAddress}} {{end}}'
docker inspect "$INTERNAL" --format 'interno: {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
docker inspect libertus-dvwa --format 'dvwa: {{range $k,$v := .NetworkSettings.Networks}}{{$k}}={{$v.IPAddress}} {{end}}' 2>/dev/null
echo
echo "SSH:      sshpass -p msfadmin ssh -p 2223 msfadmin@127.0.0.1"
echo "Alvo:     http://172.20.0.3:8081  (do host você chega direto — use o log p/ provar o pivô)"
echo "Log:      docker logs $INTERNAL -f"
echo
echo "Cadeia msf validada: ssh_login/shell NÃO roteia TCP. Use meterpreter (DVWA) + autoroute:"
echo "  use auxiliary/scanner/ssh/ssh_login   # shell = sem rota TCP"
echo "  use post/multi/manage/autoroute       # só meterpreter"
echo "  set SESSION 1; set SUBNET 172.20.0.0; set NETMASK 255.255.0.0; run"
echo "  use auxiliary/server/socks_proxy; set SRVPORT 1080; run -j"
echo "  proxychains4 curl -s http://172.20.0.3:8081/    # origem no log = 172.20.0.4"
echo
echo "NOTA: nmap é snap nesta máquina -> proxychains NÃO injeta nele. Use curl/nc ou scanner do msf."
