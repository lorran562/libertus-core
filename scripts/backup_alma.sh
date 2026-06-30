#!/usr/bin/env bash
# =============================================================================
# LIBERTUS — Backup completo da ALMA
# =============================================================================
# Junta TUDO que constitui o LIBERTUS num unico .tar.gz e cifra os segredos.
# Roda o dump do Supabase, copia config/skills/memorias do Hermes, e empacota.
#
# Uso:   bash scripts/backup_alma.sh
# Saida: backups/alma/libertus_alma_<timestamp>.tar.gz   (sem segredos)
#        backups/alma/segredos_<timestamp>.tar.gz.gpg     (chaves, cifrado)
# =============================================================================
set -euo pipefail

ROOT="/home/libertus/LIBERTUS"
HERMES="/home/libertus/.hermes"
TS="$(date +%Y%m%d_%H%M%S)"
OUT="$ROOT/backups/alma"
STAGE="$(mktemp -d)"
mkdir -p "$OUT"

echo "[*] LIBERTUS backup da alma — $TS"

# 1) Dump fresco do Supabase (memorias vivas)
echo "[*] 1/5 Dump do Supabase..."
python3 "$ROOT/scripts/dump_supabase.py" >/dev/null 2>&1 || echo "    (aviso: dump Supabase falhou — backup segue sem ele)"

# 2) Copia os pilares da identidade (NAO-secretos) pro staging
echo "[*] 2/5 Coletando identidade e memorias..."
mkdir -p "$STAGE/hermes" "$STAGE/projeto"

# Alma e identidade
cp -f "$HERMES/SOUL.md"                 "$STAGE/hermes/" 2>/dev/null || true
cp -f "$HERMES/config.yaml"             "$STAGE/hermes/" 2>/dev/null || true
cp -rf "$HERMES/memories"               "$STAGE/hermes/" 2>/dev/null || true
# Skills libertus-* (procedural memory) — so as do LIBERTUS, nao as builtin
mkdir -p "$STAGE/hermes/skills_libertus"
find "$HERMES/skills" -maxdepth 2 -type d -name "libertus*" -exec cp -rf {} "$STAGE/hermes/skills_libertus/" \; 2>/dev/null || true

# Backups recentes do Supabase (ultimo dump)
cp -rf "$ROOT/backups/supabase/latest"/* "$STAGE/projeto/supabase_dump_$TS/" 2>/dev/null || \
  { mkdir -p "$STAGE/projeto/supabase_dump_$TS"; cp -rfL "$ROOT/backups/supabase/latest"/* "$STAGE/projeto/supabase_dump_$TS/" 2>/dev/null || true; }

# Lista do estado do git (pra saber o commit exato da ressurreicao)
( cd "$ROOT" && git rev-parse HEAD 2>/dev/null > "$STAGE/projeto/GIT_COMMIT.txt" ) || true
( cd "$ROOT" && git remote get-url origin 2>/dev/null | sed 's#//[^@]*@#//TOKEN@#' > "$STAGE/projeto/GIT_REMOTE.txt" ) || true

# 3) Empacota a parte NAO-secreta
echo "[*] 3/5 Empacotando alma (sem segredos)..."
ALMA="$OUT/libertus_alma_$TS.tar.gz"
tar -czf "$ALMA" -C "$STAGE" hermes projeto
echo "    -> $ALMA"

# 4) Empacota e CIFRA os segredos separadamente
echo "[*] 4/5 Cifrando segredos (.env, auth)..."
SEC_STAGE="$(mktemp -d)"
cp -f "$ROOT/.env"        "$SEC_STAGE/env_projeto"   2>/dev/null || true
cp -f "$HERMES/.env"      "$SEC_STAGE/env_hermes"     2>/dev/null || true
cp -f "$HERMES/auth.json" "$SEC_STAGE/auth.json"      2>/dev/null || true
SEC_TAR="$OUT/segredos_$TS.tar.gz"
tar -czf "$SEC_TAR" -C "$SEC_STAGE" . 2>/dev/null || true
# Cifra simetrico com passphrase AES256.
# Senha vem da variavel LIBERTUS_BACKUP_PASS (export antes de rodar),
# senao pede interativamente.
if [ -s "$SEC_TAR" ]; then
  if [ -n "${LIBERTUS_BACKUP_PASS:-}" ]; then
    gpg --batch --yes --pinentry-mode loopback --passphrase "$LIBERTUS_BACKUP_PASS" \
        --symmetric --cipher-algo AES256 "$SEC_TAR" \
      && rm -f "$SEC_TAR" \
      && echo "    -> ${SEC_TAR}.gpg (cifrado AES256)"
  else
    echo "    Defina uma SENHA pra proteger as chaves (precisa dela na ressurreicao):"
    gpg --yes --symmetric --cipher-algo AES256 "$SEC_TAR" \
      && rm -f "$SEC_TAR" \
      && echo "    -> ${SEC_TAR}.gpg (cifrado AES256)" \
      || echo "    (aviso: rode manualmente: gpg -c $SEC_TAR)"
  fi
fi
rm -rf "$SEC_STAGE"

# 5) Limpa staging e mostra resumo
echo "[*] 5/5 Finalizando..."
rm -rf "$STAGE"

echo ""
echo "================ BACKUP COMPLETO ================"
ls -lh "$OUT" | tail -5
echo ""
echo "GUARDE OS DOIS ARQUIVOS:"
echo "  1. libertus_alma_$TS.tar.gz   (alma — sobe no GitHub)"
echo "  2. segredos_$TS.tar.gz.gpg    (chaves — guarde em lugar privado)"
echo "================================================="
