#!/bin/bash
# Analise estatica dos SDKs AbacatePay - FASE 1
# Rende zero requisicao ao servidor deles: 100% codigo publico.
cd "$(dirname "$0")/sdks" || exit 1
SRC='--include=*.ts --include=*.js --include=*.py --include=*.go --include=*.php --include=*.rb --include=*.java --include=*.kt --include=*.rs --include=*.ex --include=*.swift'
EXC='--exclude-dir=node_modules --exclude-dir=.git --exclude-dir=vendor --exclude-dir=dist --exclude-dir=build'

sep(){ echo; echo "════════════════════════════════════════════════════"; echo "### $1"; echo "════════════════════════════════════════════════════"; }

sep "1. SECRETS / KEYS HARDCODED"
grep -rniE "(api_key|apikey|secret|password|token|bearer|credential|private_key)[[:space:]]*[=:][[:space:]]*['\"][^'\"]{12,}" $SRC $EXC . | grep -viE "(test|example|spec|mock|placeholder|your_|xxxx|<|process\.env|os\.environ|getenv|ENV\[)" | head -30

sep "2. COMMAND INJECTION"
grep -rniE "(child_process|exec\(|execSync|os\.system|os\.popen|subprocess|shell_exec|passthru|Runtime\.getRuntime|eval\()" $SRC $EXC . | grep -viE "(test|spec|// |# )" | head -25

sep "3. SSL VERIFICATION DISABLED"
grep -rniE "(verify[[:space:]]*=[[:space:]]*[Ff]alse|InsecureSkipVerify[[:space:]]*:[[:space:]]*true|rejectUnauthorized[[:space:]]*:[[:space:]]*false|CURLOPT_SSL_VERIFYPEER[[:space:]]*,?[[:space:]]*(0|false)|verifyMode.*none)" $SRC $EXC . | head -20

sep "4. URL SEM ENCODING (onde o HPP mora) - interpolacao direta em path/query"
grep -rniE '(\$\{[a-zA-Z_.]+\}[^`"]*[?&/]|/[^ ]*\$\{|f["'\'']/[^"'\'']*\{|%s.*(/|\?)|\"\+[a-zA-Z_.]+\+\"/)' $SRC $EXC . | grep -iE "(url|path|endpoint|route|uri|request|http|fetch|/v[0-9]|billing|checkout|customer|charge|pix|transparent|coupon|withdraw|/check)" | grep -viE "encodeURIComponent|urlencode|url\.QueryEscape|URLEncoder|CGI\.escape|quote_plus|test|spec" | head -40

sep "5. TAXID / CPF / DADOS SENSIVEIS EM URL (o finding especifico de junho)"
grep -rniE "(taxId|cpf|cnpj|externalId|customerId|billingId|/check|/customer)" $SRC $EXC . | grep -iE "(url|path|\$\{|\"\+|%s|f['\"]|endpoint|route)" | grep -viE "(encodeURIComponent|urlencode|QueryEscape|test|spec|interface|type |struct|schema)" | head -30

sep "6. INFO DISCLOSURE (log de dados sensiveis)"
grep -rniE "(console\.(log|debug|error)|logger\.(debug|info)|print\(|fmt\.Print|System\.out|puts |p )" $SRC $EXC . | grep -iE "(key|token|secret|taxId|cpf|password|authorization|data|payload|body|json)" | grep -viE "(test|spec|// |error\(.err|README)" | head -25

sep "7. WEBHOOK / SIGNATURE VALIDATION"
grep -rniE "(webhook|signature|hmac|x-signature|verify.*sign|timestamp)" $SRC $EXC . | grep -viE "(test|spec)" | head -25

sep "8. RATE LIMIT / RETRY / TIMEOUT (ausencia = DoS surface)"
grep -rlniE "(rate|throttle|ratelimit)" $SRC $EXC . 2>/dev/null | head -10
echo "-- timeouts configurados:"
grep -rniE "(timeout|Timeout)" $SRC $EXC . | grep -viE "(test|spec)" | head -10
