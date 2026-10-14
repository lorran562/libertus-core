// PROBE: modos de falha de crypto.timingSafeEqual na verificação de webhook.
// Executado com o Node DESTA máquina (v22.x) — os resultados são reais.
//   node node_webhook_verify_probe.js
const crypto = require('crypto');

const SEGREDO = 'whsec_exemplo';
const CORPO = '{"event":"billing.paid","amount":1000}';
const DIGEST = crypto.createHmac('sha256', SEGREDO).update(CORPO).digest('hex');
const ASSINATURA_OK = 'sha256=' + DIGEST;

function linha(t) { console.log('\n==== ' + t); }
function tenta(rotulo, fn) {
  try {
    console.log(`  ${rotulo} -> retornou ${fn()}`);
  } catch (e) {
    console.log(`  ${rotulo} -> LANÇA ${e.code || e.name}: ${e.message}`);
  }
}

console.log('node ' + process.version);

// ------------------------------------------------------------------ 1
linha('1) COMPARAÇÃO "OFICIAL" QUE EXPLODE (exemplo real de guia de webhook)');
// Padrão copiado de guias populares:
//   crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(digest))
const digestComPrefixo = 'sha256=' + DIGEST;
tenta('comprimento igual  (assinatura correta)', () =>
  crypto.timingSafeEqual(Buffer.from(ASSINATURA_OK), Buffer.from(digestComPrefixo)));
tenta('assinatura vazia   (cabeçalho ausente)', () =>
  crypto.timingSafeEqual(Buffer.from(''), Buffer.from(digestComPrefixo)));
tenta('assinatura truncada (16 chars)', () =>
  crypto.timingSafeEqual(Buffer.from('sha256=abc1234567'), Buffer.from(digestComPrefixo)));
tenta('só o hex, sem prefixo', () =>
  crypto.timingSafeEqual(Buffer.from(DIGEST), Buffer.from(digestComPrefixo)));

// ------------------------------------------------------------------ 2
linha('2) MESMO BUG, AGORA COM O CORPO ERRADO — o 401 vira 500');
const servidorLogica = (assinaturaRecebida) => {
  // trecho típico: sem checagem de comprimento antes do timingSafeEqual
  const esperado = 'sha256=' + crypto.createHmac('sha256', SEGREDO).update(CORPO).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(assinaturaRecebida), Buffer.from(esperado));
};
tenta('requisição legítima', () => servidorLogica(ASSINATURA_OK));
tenta('atacante manda 1 byte', () => servidorLogica('x'));
tenta('cabeçalho vira array (?sig[]=a -> ["a","b"])', () => servidorLogica(['a', 'b']));
tenta('valor vira objeto (?sig[x]=1 -> {x:"1"})', () => servidorLogica({ x: '1' }));
tenta('passa string direto no timingSafeEqual (sem Buffer.from)', () =>
  crypto.timingSafeEqual('aaaa', 'aaaa'));

// ------------------------------------------------------------------ 3
linha('3) COMPARAÇÃO SEGURA (o que deve estar no código do cliente)');
function verificarSeguro(assinaturaRecebida, corpoBruto) {
  if (typeof assinaturaRecebida !== 'string') return false;          // tipo
  const esperado = 'sha256=' + crypto.createHmac('sha256', SEGREDO).update(corpoBruto).digest('hex');
  const a = Buffer.from(assinaturaRecebida, 'utf8');
  const b = Buffer.from(esperado, 'utf8');
  if (a.length !== b.length) return false;                            // comprimento primeiro
  return crypto.timingSafeEqual(a, b);
}
for (const cand of [ASSINATURA_OK, 'x', '', 'sha256=' + 'a'.repeat(64), DIGEST]) {
  console.log(`  seguro(${JSON.stringify(cand).slice(0, 24).padEnd(26)}) -> ${verificarSeguro(cand, CORPO)}`);
}

// ------------------------------------------------------------------ 4
linha('4) DETALHES QUE MUDAM A RESPOSTA (strings multibyte e utf8)');
const hexAscii = Buffer.from('é');       // 2 bytes em utf8
console.log('  Buffer.from("é").length =', hexAscii.length, '(1 caractere, 2 bytes)');
tenta('assinatura com acento (2 bytes) vs digest de 71 bytes', () =>
  crypto.timingSafeEqual(hexAscii, Buffer.from(digestComPrefixo)));
console.log('  => o comprimento em BYTES é o que importa: o erro de 500 aparece');
console.log('     antes de qualquer análise do conteúdo (fail-closed, mas DoS).');
