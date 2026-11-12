#!/bin/bash
# Carrega a GROQ_API_KEY do .env (que esta no .gitignore).
# NUNCA hardcodar a chave aqui: o repo lorran562/libertus-core e publico.
if [ -f "$HOME/LIBERTUS/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$HOME/LIBERTUS/.env"
    set +a
fi
if [ -z "$GROQ_API_KEY" ]; then
    echo "ERRO: GROQ_API_KEY nao encontrada em $HOME/LIBERTUS/.env" >&2
    return 1 2>/dev/null || exit 1
fi
echo "OK: GROQ_API_KEY carregada do .env (${#GROQ_API_KEY} chars)"
