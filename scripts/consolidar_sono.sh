#!/bin/bash
# Sono do LIBERTUS — consolidação cognitiva noturna (Passo 4b do grapify).
# Aprende de dia (indexar_fala), consolida de madrugada (isto).
# Rodado por cron às 3h. Best-effort: nunca deve falhar barulhento.
cd /home/libertus/LIBERTUS || exit 0
source venv/bin/activate 2>/dev/null
python3 core/consolidar_cron.py 2>&1

# Diagnóstico de memória vetorial: prova que o recall funciona de ponta a ponta
# (inclusive sob o PYTHONPATH do Hermes). Falha vira linha no log, não silêncio.
"$HOME/LIBERTUS/scripts/py" "$HOME/LIBERTUS/memoria/diagnostico.py" --quiet
if [ $? -ne 0 ]; then
    mkdir -p "$HOME/LIBERTUS/logs"
    echo "$(date -Is) DIAGNOSTICO DE MEMORIA FALHOU — ver memoria/saude_memoria.json" \
        >> "$HOME/LIBERTUS/logs/memoria_erros.log"
fi
exit 0
