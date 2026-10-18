#!/usr/bin/env bash
# ==========================================================================
# LIBERTUS — lab: como o nmap decide que um host está VIVO
# ==========================================================================
# Mede, com captura de pacotes real, a cadeia de decisão do host discovery:
#   1. ARP (mesma L2)  -> decide antes de qualquer probe IP
#   2. probes IP padrão: ICMP echo, SYN/443, ACK/80, ICMP timestamp (-PP)
#   3. usuário não-root (e proxychains/SOCKS): connect() em 80 e 443 apenas
#   4. firewall DROP vs REJECT: efeito na descoberta e no tempo
#
# Topologia (docker, bridge 172.31.99.0/24):
#   .10 tgt-open  http 8080, sem firewall            -> controle positivo
#   .20 tgt-fw    DROP tudo, aceita tcp/8080         -> ICMP filtrado, porta aberta
#   .30 tgt-drop  DROP tudo, sem serviço             -> buraco negro
#   .40 tgt-rej   REJECT icmp host-unreachable + 8080-> rejeição explícita
#
# Requer: docker (grupo docker, sem sudo). Imagem 'libertus-lab' é construída
# aqui se não existir (alpine + nmap 7.95 + tcpdump + iptables).
#
# Uso: bash scripts/lab/host_discovery_lab.sh [--keep]
# Saída: $OUT/medicoes.txt, $OUT/*.pcap, $OUT/iptables_targets.txt
# ==========================================================================
set -u
OUT="${OUT:-$HOME/LIBERTUS/reports/host-discovery_$(date +%F)}"
NET="libertus-disc"
IMG="libertus-lab"
KEEP="${1:-}"

mkdir -p "$OUT"
: > "$OUT/medicoes.txt"

log(){ echo "$@" | tee -a "$OUT/medicoes.txt"; }
run(){ # run "<descricao>" <cmd...>
  local desc="$1"; shift
  log ""
  log "########## $desc"
  local t0 t1
  t0=$(date +%s%N)
  "$@" 2>&1 | tee -a "$OUT/medicoes.txt"
  t1=$(date +%s%N)
  log "### tempo: $(( (t1-t0)/1000000 )) ms"
}

log "LIBERTUS host-discovery lab — $(date -Is)"
log "nmap: $(docker run --rm "$IMG" nmap --version 2>/dev/null | head -1)"

# ---------- 1. imagem ----------
if ! docker image inspect "$IMG" >/dev/null 2>&1; then
  log "[*] construindo imagem $IMG"
  tmp=$(mktemp -d)
  printf 'FROM alpine:3.20\nRUN apk add --no-cache nmap nmap-scripts tcpdump iproute2 iptables iputils\n' > "$tmp/Dockerfile"
  docker build -q -t "$IMG" "$tmp" >/dev/null || { log "ERRO: build falhou"; exit 1; }
  rm -rf "$tmp"
fi

# ---------- 2. topologia ----------
log ""
log "[*] recriando topologia"
docker rm -f tgt-open tgt-fw tgt-drop tgt-rej scanner >/dev/null 2>&1
docker network rm "$NET" >/dev/null 2>&1
docker network create --driver bridge --subnet 172.31.99.0/24 "$NET" >/dev/null

docker run -d --name tgt-open --network "$NET" --ip 172.31.99.10 --cap-add NET_ADMIN "$IMG" \
  sh -c 'while :; do nc -l -p 8080 -e /bin/cat; done' >/dev/null
docker run -d --name tgt-fw --network "$NET" --ip 172.31.99.20 --cap-add NET_ADMIN "$IMG" \
  sh -c 'iptables -P INPUT DROP; iptables -A INPUT -i lo -j ACCEPT; iptables -A INPUT -p tcp --dport 8080 -j ACCEPT; while :; do nc -l -p 8080 -e /bin/cat; done' >/dev/null
docker run -d --name tgt-drop --network "$NET" --ip 172.31.99.30 --cap-add NET_ADMIN "$IMG" \
  sh -c 'iptables -P INPUT DROP; exec sleep 9999' >/dev/null
docker run -d --name tgt-rej --network "$NET" --ip 172.31.99.40 --cap-add NET_ADMIN "$IMG" \
  sh -c 'iptables -P INPUT DROP; iptables -A INPUT -i lo -j ACCEPT; iptables -A INPUT -p icmp -j REJECT --reject-with icmp-host-unreachable; iptables -A INPUT -p tcp --dport 8080 -j ACCEPT; while :; do nc -l -p 8080 -e /bin/cat; done' >/dev/null
docker run -d --name scanner --network "$NET" --cap-add NET_RAW --cap-add NET_ADMIN "$IMG" sleep 9999 >/dev/null
sleep 2

{ for c in tgt-fw tgt-drop tgt-rej; do
    echo "--- $c"; docker exec "$c" iptables -S 2>/dev/null
  done; } > "$OUT/iptables_targets.txt" 2>&1

# ---------- 3. captura do discovery padrão ----------
log ""
log "[*] captura do discovery padrão (root, --send-ip, /24)"
docker exec -d scanner tcpdump -i eth0 -n -s0 -w /tmp/sn_sendip.pcap >/dev/null 2>&1
sleep 1
run "nmap -sn --send-ip -n 172.31.99.0/24 (root, sem ARP, 5 probes IP)" \
  docker exec scanner nmap -sn --send-ip -n 172.31.99.0/24
sleep 1
docker exec scanner pkill tcpdump >/dev/null 2>&1

# ---------- 4. matriz de decisão ----------
run "nmap -sn --reason -n 172.31.99.20 (ARP decide: firewall DROP) " \
  docker exec scanner nmap -sn --reason -n 172.31.99.20
run "nmap -sn --send-ip --reason -n 172.31.99.20 (sem ARP: ICMP filtrado)" \
  docker exec scanner nmap -sn --send-ip --reason -n 172.31.99.20
run "nmap -sn --send-ip --reason -n 172.31.99.30 (DROP total, sem serviço)" \
  docker exec scanner nmap -sn --send-ip --reason -n 172.31.99.30
run "nmap -sn --send-ip --reason -n 172.31.99.40 (ICMP REJECT host-unreachable)" \
  docker exec scanner nmap -sn --send-ip --reason -n 172.31.99.40
run "nmap -sn --send-ip --reason -n -PS8080 172.31.99.20 (probe na porta que passa)" \
  docker exec scanner nmap -sn --send-ip --reason -n -PS8080 172.31.99.20
run "nmap -sn --send-ip --reason -n -PA80 172.31.99.40 (ACK em porta fechada/filtrada)" \
  docker exec scanner nmap -sn --send-ip --reason -n -PA80 172.31.99.40

# ---------- 5. não-root == proxychains (connect em 80/443) ----------
log ""
log "[*] captura da descoberta NÃO-ROOT (connect 80/443 = o que o proxychains faz)"
docker exec scanner rm -f /tmp/connect.pcap >/dev/null 2>&1
docker exec -d scanner tcpdump -i eth0 -n -s0 -w /tmp/connect.pcap 'host 172.31.99.20 and not arp' >/dev/null 2>&1
sleep 1
run "nmap -sn -n 172.31.99.20 como nobody (uid 65534, sem raw socket)" \
  docker exec -u 65534 scanner nmap -sn -n 172.31.99.20
sleep 1
docker exec scanner pkill tcpdump >/dev/null 2>&1
log "--- pacotes do connect() ---"
docker exec scanner tcpdump -nr /tmp/connect.pcap 2>/dev/null | tee -a "$OUT/medicoes.txt"
run "nmap -sn -n -PS8080 172.31.99.20 como nobody (probe explícito)" \
  docker exec -u 65534 scanner nmap -sn -n -PS8080 172.31.99.20

# ---------- 6. port scan: onde o -Pn entra ----------
run "nmap -p8080 --send-ip -n 172.31.99.20 (sem ARP, sem -Pn)" \
  docker exec scanner nmap -p8080 --send-ip -n 172.31.99.20
run "nmap -p8080 --send-ip -Pn -n --reason 172.31.99.20 (com -Pn)" \
  docker exec scanner nmap -p8080 --send-ip -Pn -n --reason 172.31.99.20
run "nmap -p8080 -n --reason 172.31.99.30 (DROP total: estado filtered)" \
  docker exec scanner nmap -p8080 -n --reason 172.31.99.30
run "nmap -Pn -p8080 -n 172.31.99.0/24 (custo de varrer /24 sem discovery)" \
  docker exec scanner nmap -Pn -p8080 -n 172.31.99.0/24

# ---------- 7. evidência bruta ----------
docker cp scanner:/tmp/sn_sendip.pcap "$OUT/sn_sendip.pcap" >/dev/null 2>&1
docker cp scanner:/tmp/connect.pcap  "$OUT/connect.pcap"   >/dev/null 2>&1
log ""
log "[*] pcaps: $OUT/sn_sendip.pcap , $OUT/connect.pcap"
log "[*] resumo de pacotes (sn_sendip.pcap):"
docker exec scanner tcpdump -nr /tmp/sn_sendip.pcap 2>/dev/null | awk '{print $2, $3, $4, $5, $6, $7}' | sort | uniq -c | sort -rn | head -15 | tee -a "$OUT/medicoes.txt"

if [ "$KEEP" != "--keep" ]; then
  log ""
  log "[*] derrubando topologia (use --keep para manter)"
  docker rm -f tgt-open tgt-fw tgt-drop tgt-rej scanner >/dev/null 2>&1
  docker network rm "$NET" >/dev/null 2>&1
fi

log ""
log "[ok] evidências em $OUT"
