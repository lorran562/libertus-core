#!/usr/bin/env bash
# scan.sh — recon rápido de UM alvo para o eJPT. Feito pra rodar em <2 min.
#
# Uso:  bash ~/LIBERTUS/ejpt/scan.sh 10.10.10.5
#       bash ~/LIBERTUS/ejpt/scan.sh 10.10.10.5 --full     (todas as 65535 portas)
#
# Salva tudo em ~/LIBERTUS/ejpt/recon/<ip>_<hora>.txt e mostra o resumo na tela.
# Autorizado apenas em labs/exame (eJPT, HTB, THW) com permissão.
set -u

IP="${1:?uso: scan.sh IP [--full]}"
MODO="${2:-}"
DIR="$HOME/LIBERTUS/ejpt/recon"
mkdir -p "$DIR"
F="$DIR/$(printf '%s' "$IP" | tr '/.:' '___')_$(date +%H%M).txt"

log() { printf '%s\n' "$*" | tee -a "$F"; }

log "=================================================="
log " ALVO: $IP   $(date '+%d/%m/%Y %H:%M')"
log "=================================================="

# ---------- 1. portas ----------
log ""
log "== [1] PORTAS ABERTAS =="
if [ "$MODO" = "--full" ]; then
  PORTOPT="-p- --min-rate 2000"
  log "modo FULL (65535 portas) — pode levar 2-5 min"
else
  PORTOPT="--top-ports 1000"
fi

PORTS=$(nmap -Pn -T4 $PORTOPT --open -oG - "$IP" 2>/dev/null \
        | grep -oE '[0-9]+/open' | cut -d/ -f1 | sort -un | paste -sd, -)

if [ -z "${PORTS:-}" ]; then
  log "Nenhuma porta aberta no scan inicial. Tentando -Pn em portas comuns..."
  PORTS="21,22,80,139,443,445,3306,3389,8080"
fi
log "portas: ${PORTS:-nenhuma}"
log ""

# ---------- 2. versão + scripts default ----------
log "== [2] VERSÃO + SCRIPTS DEFAULT (-sV -sC) =="
nmap -Pn -T4 -p "${PORTS:-21,22,80,445,8080}" -sV -sC --open "$IP" 2>/dev/null \
  | grep -v 'Script execution failed' | tee -a "$F"
log ""

# ---------- 3. web rápido ----------
WEB=""
for p in $(printf '%s' "${PORTS:-}" | tr ',' ' '); do
  case "$p" in
    80|443|8000|8080|8081|3000|5000|9000) WEB="$WEB $p" ;;
  esac
done
if [ -n "${WEB// /}" ]; then
  log "== [3] WEB (headers + título + robots) =="
  for p in $WEB; do
    ESQ="http"
    [ "$p" = "443" ] && ESQ="https"
    U="$ESQ://$IP:$p"
    log "--- $U"
    curl -s -k -m 8 -i "$U/" 2>/dev/null | head -12 | tee -a "$F"
    TIT=$(curl -s -k -m 8 "$U/" 2>/dev/null | grep -oiE '<title>[^<]*' | head -1 | sed 's/<title>//i')
    [ -n "${TIT:-}" ] && log "TITULO: $TIT"
    R=$(curl -s -k -m 8 -o /dev/null -w '%{http_code}' "$U/robots.txt" 2>/dev/null)
    if [ "$R" = "200" ]; then
      log "robots.txt:"; curl -s -k -m 8 "$U/robots.txt" | head -15 | tee -a "$F"
    fi
    log ""
  done
fi

# ---------- 4. próximos passos ----------
log "=================================================="
log " PRÓXIMOS PASSOS"
log "=================================================="
case ",${PORTS}," in
  *,21,*)  log " FTP 21  -> nmap -p21 --script ftp-anon,ftp-vsftpd-backdoor,ftp-proftpd-backdoor $IP" ;;
esac
case ",${PORTS}," in
  *,22,*)  log " SSH 22  -> (hydra sem ssh aqui) ssh_brute.py ou msf ssh_login" ;;
esac
case ",${PORTS}," in
  *,445,*) log " SMB 445 -> nmap -p445 --script smb-os-discovery,smb-vuln-ms17-010,smb-enum-shares $IP" ;;
esac
if [ -n "${WEB// /}" ]; then
  log " WEB     -> gobuster dir -u http://$IP:PORT -w ~/wordlists/web/raft-small-words.txt -x php,txt,html -t 40"
fi
log " arquivo completo: $F"
