<?php
// PoC real: como a COMPARAÇÃO de assinatura falha em PHP (executado em php:8.3-cli).
// Cada bloco imprime o que o PHP de fato faz — não é teoria.

function linha($t) { echo str_repeat('=', 4) . " $t\n"; }

echo "PHP " . PHP_VERSION . "\n\n";

// ---------------------------------------------------------------- 1
linha("1) LOOSE COMPARISON (==) vs HASH_EQUALS — magic hash '0e'");
$a = md5("240610708");   // 0e462097431906509019562988736854
$b = md5("QNKCDZO");     // 0e830400451993494058024219903391
echo "  md5(240610708) = $a\n";
echo "  md5(QNKCDZO)   = $b\n";
var_dump($a == $b);      // loose: ambos viram float 0.0
var_dump($a === $b);     // strict: compara como string
var_dump(hash_equals($a, $b));

// ---------------------------------------------------------------- 2
linha("2) A FORMA PRATICA — o atacante manda '0' em vez de um hash");
$esperado = md5("240610708");       // 0e4620...
$recebido = "0";                    // atacante nao conhece o segredo
var_dump($recebido == $esperado);   // PHP 8: ainda TRUE (ambos numeric strings)
var_dump($recebido === $esperado);
var_dump(hash_equals($esperado, $recebido));

linha("2b) mesma coisa com o digest do HMAC (hex, 64 chars)");
$mac = hash_hmac('sha256', 'payload=1', 'segredo');
echo "  hmac = $mac\n";
var_dump("0" == $mac);              // FALSE aqui porque o mac nao comeca com 0e
$mac_magic = "0e" . str_repeat("1", 62);   // so para mostrar o operador
var_dump("0" == $mac_magic);        // TRUE -> qualquer digest 0e+digitos e burlavel
var_dump(hash_equals($mac_magic, "0"));

// ---------------------------------------------------------------- 3
linha("3) STRINGS NAO NUMERICAS (PHP 8 mudou o comportamento)");
var_dump("abc" == 0);               // PHP 7: true | PHP 8: false
var_dump("1abc" == 1);              // PHP 7: true | PHP 8: false
var_dump(0 == "0e12345");           // numeric string -> true nas duas

// ---------------------------------------------------------------- 4
linha("4) COMPARACAO SO DE PREFIXO (truncamento do digest)");
$digest = hash_hmac('sha256', 'payload=1', 'segredo');
$truncado = substr($digest, 0, 6);  // bug classico: comparar so o prefixo
$tentativas = 0;
for ($i = 0; ; $i++) {
    $tentativas++;
    if (substr(hash_hmac('sha256', 'payload=1', 'x' . $i), 0, 6) === $truncado) break;
}
echo "  digest completo : $digest\n";
echo "  comparado ate   : $truncado (" . strlen($truncado) . " hex = "
     . (strlen($truncado) * 4) . " bits de entropia apenas)\n";
echo "  forjar o prefixo custou $tentativas tentativas locais\n";

echo "\n  (nota: aqui 'quebrei' o prefixo conhecido; num alvo real o digest\n";
echo "   nao e conhecido — o custo esperado e 16^n / 2. Com n=6 -> ~8.4M)\n";

// ---------------------------------------------------------------- 5
linha("5) SEGREDO AUSENTE / VAZIO = FAIL-OPEN");
function verificar_failopen($payload, $sig_recebida, $segredo) {
    $esperado = hash_hmac('sha256', $payload, $segredo);
    if (!$segredo) {          // "se nao tem segredo configurado, deixa passar"
        return true;
    }
    return hash_equals($esperado, (string)$sig_recebida);
}
var_dump(verificar_failopen('{"event":"paid"}', 'lixo', ''));
var_dump(verificar_failopen('{"event":"paid"}', 'lixo', 'segredo-real'));

// ---------------------------------------------------------------- 6
linha("6) strcmp / comparacao com tipos nao-string");
var_dump(@strcmp([], ""));      // PHP 8: TypeError (suprimido) -> null
var_dump((bool)@strcmp([], "")); // NULL e falsy -> "iguais" em codigo antigo
echo "  -> em PHP 7 strcmp(array, string) retornava NULL/Warning;\n";
echo "     `if (!strcmp($a,$b))` tratava como IGUAL. Em PHP 8 e TypeError.\n";
