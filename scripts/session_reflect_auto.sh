#!/bin/bash
# session_reflect_auto.sh — Reflexão automática idempotente
# =========================================================
# Roda session_reflect.py --auto SOMENTE se houve atividade nova
# (commit git ou sessão Hermes) desde a última reflexão.
# Evita o anti-padrão do daemon antigo: refletir sobre o nada.
#
# Uso: chamado por cronjob a cada 6h. Silencioso se não há o que refletir.

set -euo pipefail

LIBERTUS_DIR="$HOME/LIBERTUS"
STAMP="$LIBERTUS_DIR/logs/.last_reflect_stamp"
cd "$LIBERTUS_DIR"

# Carregar ambiente (ANTHROPIC_API_KEY necessário pro --auto)
set -a
source "$LIBERTUS_DIR/.env" 2>/dev/null || true
set +a

# Marca da última reflexão (epoch). Se nunca rodou, assume 0.
last=0
if [ -f "$STAMP" ]; then
    last=$(cat "$STAMP" 2>/dev/null || echo 0)
fi

# Houve commit git DESDE a última reflexão? (atividade real deixa rastro)
# Usa o timestamp do stamp como referência, não uma janela fixa — assim é idempotente.
if [ "$last" -gt 0 ]; then
    since_ref="@$last"
else
    since_ref="6 hours ago"
fi
commit_recente=$(git log --since="$since_ref" --oneline 2>/dev/null | wc -l)

# Houve sessão Hermes modificada desde a última reflexão?
sessao_nova=0
SESS_DB="$HOME/.hermes/state.db"
if [ -f "$SESS_DB" ]; then
    mtime=$(stat -c %Y "$SESS_DB" 2>/dev/null || echo 0)
    if [ "$mtime" -gt "$last" ]; then
        sessao_nova=1
    fi
fi

if [ "$commit_recente" -eq 0 ] && [ "$sessao_nova" -eq 0 ]; then
    # Nada novo — não reflete sobre o vazio. Sai em silêncio.
    echo "[session_reflect_auto] Sem atividade nova desde a última reflexão. Pulando."
    exit 0
fi

echo "[session_reflect_auto] Atividade detectada (commits=$commit_recente sessao_nova=$sessao_nova). Refletindo..."
python3 scripts/session_reflect.py --auto

# A reflexão acabou de gerar memória nova (Supabase) — indexar antes de sair,
# senão a lição de hoje só existiria para a próxima sessão que abrir briefing.
# O guardião é idempotente e sai em ~0.07s quando nada mudou.
echo "[session_reflect_auto] Atualizando memória vetorial..."
"$LIBERTUS_DIR/venv/bin/python" memoria/auto_indexar.py --quiet --supabase --baixar-supabase || true

# Atualiza o stamp
date +%s > "$STAMP"
echo "[session_reflect_auto] Reflexão concluída e stamp atualizado."
