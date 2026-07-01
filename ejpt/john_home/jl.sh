#!/usr/bin/env bash
# LIBERTUS John wrapper — John local do Ubuntu precisa de config/pot/session em local gravável.
# Uso: jl HASHFILE [--format=FORMATO] [--wordlist=WL]  (default rockyou)
# Ex:  jl /tmp/hashes.txt --format=sha512crypt
JD="$HOME/LIBERTUS/ejpt/john_home"
WL="/usr/share/wordlists/rockyou.txt"
ARGS=()
for a in "$@"; do
  case "$a" in
    --wordlist=*) WL="${a#--wordlist=}";;
    *) ARGS+=("$a");;
  esac
done
/usr/local/bin/john --config="$JD/john_clean.conf" --pot="$JD/john.pot" \
  --session="$JD/sess" --wordlist="$WL" "${ARGS[@]}"
echo "--- resultado (--show) ---"
/usr/local/bin/john --config="$JD/john_clean.conf" --pot="$JD/john.pot" --show "${ARGS[@]}" 2>/dev/null
