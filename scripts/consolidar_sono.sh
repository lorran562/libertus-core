#!/bin/bash
# Sono do LIBERTUS — consolidação cognitiva noturna (Passo 4b do grapify).
# Aprende de dia (indexar_fala), consolida de madrugada (isto).
# Rodado por cron às 3h. Best-effort: nunca deve falhar barulhento.
cd /home/libertus/LIBERTUS || exit 0
source venv/bin/activate 2>/dev/null
python3 core/consolidar_cron.py 2>&1
exit 0
