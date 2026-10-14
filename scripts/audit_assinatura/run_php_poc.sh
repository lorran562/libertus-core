#!/usr/bin/env bash
# Roda o PoC PHP real (php:8.3-cli via docker) — sem instalar nada no host.
# Uso: ./run_php_poc.sh
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
docker run --rm -v "$DIR:/w" -w /w php:8.3-cli php php_loose_compare_poc.php
