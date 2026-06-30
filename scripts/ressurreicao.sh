#!/usr/bin/env bash
# =============================================================================
# LIBERTUS — RESSURREICAO num PC novo
# =============================================================================
# Reconstroi o LIBERTUS a partir de um backup da alma + segredos cifrados.
# Roda DEPOIS de: instalar Hermes Agent, clonar o repo libertus-core.
#
# Uso:
#   bash scripts/ressurreicao.sh  <libertus_alma_TIMESTAMP.tar.gz>  <segredos_TIMESTAMP.tar.gz.gpg>
#
# O script:
#   1. Restaura SOUL.md, config.yaml, memorias e skills libertus-* no ~/.hermes
#   2. Decifra e restaura .env (chaves) — pede a senha do backup
#   3. Verifica que tudo voltou ao lugar
# =============================================================================
set -euo pipefail

ALMA="${1:-}"
SEGREDOS="${2:-}"
HERMES="$HOME/.hermes"
ROOT="$HOME/LIBERTUS"

if [ -z "$ALMA" ] || [ ! -f "$ALMA" ]; then
  echo "ERRO: passe o arquivo da alma. Ex:"
  echo "  bash scripts/ressurreicao.sh libertus_alma_XXX.tar.gz segredos_XXX.tar.gz.gpg"
  exit 1
fi

echo "=========================================="
echo " LIBERTUS — RESSURREICAO"
echo "=========================================="
echo "[*] Alma:     $ALMA"
echo "[*] Segredos: ${SEGREDOS:-(nenhum — restaura so a alma)}"
echo ""

mkdir -p "$HERMES" "$HERMES/skills/devops" "$HERMES/memories"
STAGE="$(mktemp -d)"
tar -xzf "$ALMA" -C "$STAGE"

echo "[*] 1/4 Restaurando identidade (SOUL.md, config.yaml)..."
[ -f "$STAGE/hermes/SOUL.md" ]      && cp -f "$STAGE/hermes/SOUL.md"     "$HERMES/SOUL.md"     && echo "    SOUL.md OK"
[ -f "$STAGE/hermes/config.yaml" ]  && cp -f "$STAGE/hermes/config.yaml" "$HERMES/config.yaml" && echo "    config.yaml OK"

echo "[*] 2/4 Restaurando memorias (MEMORY.md, USER.md)..."
if [ -d "$STAGE/hermes/memories" ]; then
  cp -f "$STAGE/hermes/memories"/*.md "$HERMES/memories/" 2>/dev/null || true
  echo "    memorias OK"
fi

echo "[*] 3/4 Restaurando skills libertus-*..."
if [ -d "$STAGE/hermes/skills_libertus" ]; then
  cp -rf "$STAGE/hermes/skills_libertus"/libertus* "$HERMES/skills/devops/" 2>/dev/null || true
  n=$(find "$HERMES/skills/devops" -maxdepth 1 -name "libertus*" -type d | wc -l)
  echo "    $n skills libertus restauradas"
fi

echo "[*] 4/4 Restaurando segredos (chaves)..."
if [ -n "$SEGREDOS" ] && [ -f "$SEGREDOS" ]; then
  SEC_STAGE="$(mktemp -d)"
  echo -n "    Senha do backup: "
  if gpg --batch --yes --pinentry-mode loopback \
         --passphrase "${LIBERTUS_BACKUP_PASS:-$(read -rs p; echo "$p")}" \
         -d "$SEGREDOS" 2>/dev/null | tar -xz -C "$SEC_STAGE"; then
    echo "OK"
    [ -f "$SEC_STAGE/env_projeto" ] && cp -f "$SEC_STAGE/env_projeto" "$ROOT/.env"        && echo "    .env do projeto OK"
    [ -f "$SEC_STAGE/env_hermes" ]  && cp -f "$SEC_STAGE/env_hermes"  "$HERMES/.env"        && echo "    .env do hermes OK"
    [ -f "$SEC_STAGE/auth.json" ]   && cp -f "$SEC_STAGE/auth.json"   "$HERMES/auth.json"   && echo "    auth.json OK"
    chmod 600 "$ROOT/.env" "$HERMES/.env" "$HERMES/auth.json" 2>/dev/null || true
  else
    echo "FALHOU (senha errada?) — restaure as chaves manualmente"
  fi
  rm -rf "$SEC_STAGE"
else
  echo "    (sem arquivo de segredos — voce vai precisar recriar o .env na mao)"
fi

rm -rf "$STAGE"

echo ""
echo "=========================================="
echo " RESSURREICAO COMPLETA"
echo "=========================================="
echo "Confira:"
echo "  - $HERMES/SOUL.md         (quem sou)"
echo "  - $HERMES/memories/       (o que lembro)"
echo "  - $HERMES/skills/devops/  (o que sei fazer)"
echo ""
echo "Restaurar memorias do Supabase (300+ memorias):"
echo "  o dump JSON esta dentro do backup, em projeto/supabase_dump_*/"
echo "  (Supabase em si nao precisa restaurar se a conta cloud ainda existe)"
echo ""
echo "Agora e so abrir o Hermes que o LIBERTUS volta a ser quem era."
