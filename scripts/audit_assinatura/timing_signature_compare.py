#!/usr/bin/env python3
"""
TIMING LEAK EM COMPARAÇÃO DE ASSINATURA — medição real + controle positivo.

Pergunta que este script responde (a que todo relatório de bug bounty precisa):
  "A comparação byte-a-byte desta implementação é explorável REMOTAMENTE?"

Não responde com opinião: mede o vazamento por byte (delta), mede o jitter
(sigma) real, calibra o método com um CONTROLE POSITIVO (servidor que vaza de
propósito) e só então calcula quantas requisições seriam necessárias.

Por que o controle positivo é obrigatório: um resultado "não achei sinal" só
tem valor se o mesmo método ACHA o sinal quando ele existe. Sem isso, o "não
achei" pode ser apenas um instrumento quebrado.

Partes:
  1  vazamento in-process: loop interpretado x memcmp C x compare_digest
  2  sigma real do loopback (keep-alive + TCP_NODELAY)
  3  regressão RTT x bytes de prefixo corretos  (sem sinal esperado)
  3b CONTROLE: mesmo servidor com vazamento amplificado (sinal esperado)
  4  tentativa real de recuperar o 1o byte por timing, nos dois modos
  5  Monte Carlo validando o modelo N = (z*sigma/delta)^2
  6  veredito + delta minimo para o ataque caber num orçamento de requisicoes

Uso: python3 timing_signature_compare.py     (saída = números desta máquina)
"""

import hmac
import http.client
import random
import socket
import statistics
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SIG = bytes(range(32))                 # "assinatura esperada" de 32 bytes
NS = time.perf_counter_ns
AMP = 50_000                            # 50 us por byte correto (controle positivo)


# ----------------------------------------------------------------------
# Implementações comparadas
# ----------------------------------------------------------------------
def cmp_naive_loop(a: bytes, b: bytes) -> bool:
    """Bug clássico: para no primeiro byte diferente (interpretado)."""
    if len(a) != len(b):
        return False
    for i in range(len(a)):
        if a[i] != b[i]:
            return False
    return True


def cmp_naive_amplificado(a: bytes, b: bytes) -> bool:
    """Controle positivo: mesmo loop, com dormida por byte correto.
    Simula vazamentos GRANDES (ex.: reduções de Montgomery no RSA da
    Brumley-Boneh), que é onde o ataque remoto de fato funcionou."""
    if len(a) != len(b):
        return False
    for i in range(len(a)):
        if a[i] != b[i]:
            return False
        time.sleep(AMP / 1e9)
    return True


def cmp_memcmp(a: bytes, b: bytes) -> bool:
    """`a == b` em Python cai em memcmp do C (o early-exit fica dentro do C)."""
    return a == b


def cmp_constant(a: bytes, b: bytes) -> bool:
    return hmac.compare_digest(a, b)


MODOS = {"naive": cmp_naive_loop,
         "amplificado": cmp_naive_amplificado,
         "memcmp": cmp_memcmp,
         "constante": cmp_constant}


# ----------------------------------------------------------------------
# PARTE 1 — vazamento por byte, in-process
# ----------------------------------------------------------------------
def medir_delta_inprocess(fn, n_amostras=20000):
    def mediana(k):
        cand = SIG[:k] + b"\xff" * (32 - k)
        t = []
        for _ in range(n_amostras):
            t0 = NS(); fn(SIG, cand); t1 = NS()
            t.append(t1 - t0)
        return statistics.median(t)

    pontos = {k: mediana(k) for k in (0, 8, 16, 31)}
    slope = (pontos[31] - pontos[0]) / 31
    return pontos[0], pontos, slope


# ----------------------------------------------------------------------
# Servidor HTTP real (loopback)
# ----------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    # PITFALL MEDIDO: sem TCP_NODELAY, escrita pequena + delayed-ACK faz o RTT
    # do loopback saltar para ~41 ms e o sigma para ~1,9 ms — ruído inventado
    # pelo próprio teste, não pela rede. Medido nesta máquina.
    disable_nagle_algorithm = True
    modo = "naive"

    def log_message(self, format, *args):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        corpo = self.rfile.read(n) if n else b""
        ok = MODOS[Handler.modo](corpo, SIG)
        self.send_response(200 if ok else 401)
        self.send_header("Content-Length", "1")
        self.end_headers()
        self.wfile.write(b"1" if ok else b"0")


def subir_servidor(modo):
    Handler.modo = modo
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def medir_rtt(host, port, corpo, n):
    c = http.client.HTTPConnection(host, port, timeout=10)
    c.connect()
    c.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    amostras = []
    for _ in range(n):
        t0 = NS()
        c.request("POST", "/webhook", body=corpo,
                  headers={"Content-Length": str(len(corpo))})
        c.getresponse().read()
        amostras.append(NS() - t0)
    c.close()
    return amostras


# ----------------------------------------------------------------------
# Estatística: a regressão é o juiz (dois pontos não provam nada)
# ----------------------------------------------------------------------
def regressao(xs, ys):
    """Mínimos quadrados + Pearson r + t. r ~ 0 => nenhum sinal de tempo."""
    n = len(xs)
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    slope = sxy / sxx
    r = sxy / (sxx * syy) ** 0.5 if sxx and syy else 0.0
    t = r * ((n - 2) / max(1 - r * r, 1e-12)) ** 0.5
    return slope, r, t


def testes_prefixo(host, port, n_por_k=300, k_max=31):
    """Para k = 0..31 bytes de prefixo corretos, mede RTT médio. Retorna a
    regressão completa — se a comparação vaza, o RTT cresce com k."""
    ks, medias = [], []
    for k in range(k_max + 1):
        cand = SIG[:k] + b"\xff" * (32 - k)
        amostras = medir_rtt(host, port, cand, n_por_k)
        ks.append(k); medias.append(statistics.mean(amostras))
    return ks, medias, regressao(ks, medias)


def recuperar_byte0(host, port, n_por_cand):
    """Tenta recuperar o byte 0: 256 candidatos, maior RTT médio ganha."""
    ranking = []
    for c in range(256):
        cand = bytes([c]) + b"\xff" * 31
        ranking.append((statistics.mean(medir_rtt(host, port, cand, n_por_cand)), c))
    ranking.sort(reverse=True)
    pos = [i for i, (_, c) in enumerate(ranking) if c == SIG[0]][0] + 1
    return pos, [f"0x{c:02x}" for _, c in ranking[:5]]


def mc_discriminacao(delta_ns, sigma_ns, n_amostras, tentativas=200, candidatos=256):
    acertos = 0
    for _ in range(tentativas):
        se = sigma_ns / n_amostras ** 0.5
        melhor, valor = -1, -1.0
        for c in range(candidatos):
            v = random.gauss(delta_ns if c == 0 else 0.0, se)
            if v > valor:
                valor, melhor = v, c
        if melhor == 0:
            acertos += 1
    return acertos / tentativas


def n_necessario(delta_ns, sigma_ns, z=7.4):
    """Separar o candidato certo do MÁXIMO de 255 ruídos (~2.9 sigma) com folga
    de ~4.5 sigma: z ~ 7.4. N = (z*sigma/delta)^2 amostras por candidato."""
    if delta_ns <= 0:
        return float("inf")
    return (z * sigma_ns / delta_ns) ** 2


def delta_minimo(sigma_ns, total_req, z=7.4):
    """Delta necessário para o ataque caber em `total_req` requisições."""
    n_cand = total_req / (256 * 32)
    return z * sigma_ns / (n_cand ** 0.5)


# ----------------------------------------------------------------------
def main():
    random.seed(1337)
    print("=" * 74)
    print("TIMING LEAK NA COMPARAÇÃO DE ASSINATURA — medição local (mesma máquina)")
    print("=" * 74)

    # ---------------- 1
    print("\n[1] VAZAMENTO IN-PROCESS (assinatura de 32 bytes, mediana de 20k reps)")
    slopes = {}
    for rotulo, fn in (("loop interpretado (early-exit)", cmp_naive_loop),
                       ("memcmp C (a == b)", cmp_memcmp),
                       ("compare_digest (constante)", cmp_constant)):
        base, pontos, slope = medir_delta_inprocess(fn)
        slopes[rotulo] = slope
        print(f"    {rotulo:32} 0 byte ok={base:>6} ns  31 bytes ok={pontos[31]:>7} ns"
              f"  delta={pontos[31]-base:>6} ns  {slope:>6.2f} ns/byte")

    # ---------------- 2
    print("\n[2] JITTER REAL NO LOOPBACK (keep-alive + TCP_NODELAY, 5 lotes x 600 req)")
    srv = subir_servidor("naive")
    porta = srv.server_address[1]
    lotes = [medir_rtt("127.0.0.1", porta, b"\xff" * 32, 600) for _ in range(5)]
    rtt = [x for lote in lotes for x in lote]
    sigma_bruto = statistics.stdev(rtt)
    sigmas_lote = [statistics.stdev(lote) for lote in lotes]
    # Postura de avaliação: assumir que o atacante pega as MELHORES condições.
    # sigma do lote mais quieto é o cenário conservador-para-o-atacante.
    sigma = min(sigmas_lote)
    print(f"    mediana={statistics.median(rtt):>8.0f} ns  media={statistics.mean(rtt):>9.0f} ns"
          f"  p99={sorted(rtt)[int(len(rtt)*0.99)]:>9} ns")
    print(f"    sigma global (5 lotes): {sigma_bruto:>11,.0f} ns")
    print(f"    sigma por lote        : {[f'{s:,.0f}' for s in sigmas_lote]}")
    print(f"    -> adotado sigma={sigma:,.0f} ns (lote mais quieto = melhor caso do atacante)")
    print(f"    -> variacao de sigma entre execucoes eh ORDEM DE GRANDEZA: nenhuma")
    print(f"       conclusao de timing vale sem ser re-medida nas condicoes do alvo.")

    # ---------------- 3 / 3b
    print("\n[3] REGRESSÃO: RTT x bytes de prefixo corretos (o juiz é o r de Pearson)")
    print(f"    {'modo':>12} {'slope (ns/byte)':>17} {'r':>8} {'t':>8}   leitura")
    resultados = {}
    for modo, rotulo in (("naive", "naive (real)"), ("amplificado", "amplificado (controle)")):
        if modo == "amplificado":
            srv.shutdown()
            srv = subir_servidor("amplificado")
            porta = srv.server_address[1]
        ks, medias, (slope, r, t) = testes_prefixo("127.0.0.1", porta, 300)
        resultados[modo] = (slope, r, t, medias[0], medias[-1])
        leitura = "SINAL DETECTADO" if abs(t) > 3 else "sem sinal (ruido)"
        print(f"    {rotulo:>12} {slope:>17.2f} {r:>8.3f} {t:>8.2f}   {leitura}")
    print(f"    (controle: cada byte correto dorme {AMP/1000:.0f} us de propósito —")
    print(f"     |t|>3 prova que o método acha vazamento quando ele existe)")

    # ---------------- 4
    print("\n[4] RECUPERAÇÃO REAL DO 1o BYTE (256 candidatos, ranking por RTT médio)")
    for n_cand, modo in ((512, "naive"), (128, "amplificado")):
        srv.shutdown()
        srv = subir_servidor(modo)
        porta = srv.server_address[1]
        pos, top = recuperar_byte0("127.0.0.1", porta, n_cand)
        veredito = "RECUPERADO" if pos == 1 else ("entre os 10 primeiros" if pos <= 10 else "FALHOU")
        print(f"    modo={modo:<12} {n_cand:>4} req/cand  byte correto=0x{SIG[0]:02x}"
              f"  posição={pos:>3}/256  top5={top}  -> {veredito}")
    print("    (256 = acaso puro; 1 = sinal perfeito)")

    # ---------------- 5
    delta_ref = abs(slopes["loop interpretado (early-exit)"])
    print(f"\n[5] MONTE CARLO VALIDANDO O MODELO (delta={delta_ref:.0f} ns = vazamento do loop interpretado)")
    print(f"    {'N/cand':>9} {'sucesso':>9}")
    for n in (1_000, 10_000, 100_000, 1_000_000):
        print(f"    {n:>9,} {mc_discriminacao(delta_ref, sigma, n)*100:>8.1f}%")
    n_teorico = n_necessario(delta_ref, sigma)
    print(f"    previsto pelo modelo (z=7.4): N = {n_teorico:,.0f} por candidato")

    # ---------------- 6
    print("\n[6] VEREDITO")
    for rotulo in ("loop interpretado (early-exit)", "memcmp C (a == b)"):
        delta = abs(slopes[rotulo])
        n_teo = n_necessario(delta, sigma)
        total = n_teo * 256 * 32
        horas = total * statistics.median(rtt) / 1e9 / 3600
        print(f"    {rotulo}")
        print(f"      delta={delta:>8.2f} ns/byte   sigma={sigma:,.0f} ns"
              f"   (razão sigma/delta = {sigma/max(delta,1e-9):>10,.0f}x)")
        print(f"      N/candidato={n_teo:>16,.0f}   total 32 bytes={total:>21,.0f} req")

    print(f"\n    REGRA DE DECISÃO (o que entra no relatório):")
    for alvo, nome in ((1e6, "10^6"), (1e7, "10^7"), (1e9, "10^9")):
        d = delta_minimo(sigma, alvo)
        print(f"      para atacar em {nome:>5} req no total, o alvo precisa vazar"
              f" >= {d/1000:>8.2f} us/byte")
    print(f"      vazamento medido do loop interpretado: {delta_ref/1000:.3f} us/byte "
          f"-> {delta_minimo(sigma,1e7)/delta_ref:,.0f}x abaixo do necessário")
    print(f"      controle positivo ({AMP/1000:.0f} us/byte) fica ACIMA do corte; RSA/OpenSSL")
    print(f"      da Brumley-Boneh vazava microssegundos por consulta — por isso funcionou.")

    # O vazamento cresce LINEAR com o tamanho do valor comparado. Um digest de
    # 32 bytes é imune; um blob de >500 bytes comparado em loop interpretado entra
    # na faixa plausível. Este é o critério acionável que sai da medição.
    print(f"\n[6b] ESCALA COM O TAMANHO DO VALOR COMPARADO (critério acionável)")
    corte_1e7 = delta_minimo(sigma, 1e7)
    corte_1e6 = delta_minimo(sigma, 1e6)
    print(f"      corte p/ 10^7 req = {corte_1e7/1000:.1f} us de vazamento;"
          f"  corte p/ 10^6 req = {corte_1e6/1000:.1f} us")
    # tamanho minimo para o vazamento do loop interpretado atingir cada corte
    for rotulo, corte in (("10^6 req", corte_1e6), ("10^7 req", corte_1e7)):
        print(f"      -> p/ caber em {rotulo}: valor comparado precisa ter "
              f">= {corte/delta_ref:,.0f} bytes (loop interpretado)")
    for L in (32, 128, 512, 4096, 65536):
        vaz = delta_ref * L
        n_cand = n_necessario(vaz, sigma)
        total = n_cand * 256 * 32
        veredito = "IMPRATICÁVEL" if total > 1e7 else "POSSÍVEL"
        print(f"      valor de {L:>6} bytes  vazamento total={vaz/1000:>10.2f} us"
              f"  total req={total:>21,.0f}  -> {veredito}")
    print(f"      => o vazamento cresce LINEAR com o comprimento: digest de 32-64 B é")
    print(f"         imune na prática; comparar blob/token de KB em loop interpretado é")
    print(f"         o único caso em que 'usar ==' vira achado explorável de verdade.")
    print(f"\n    Conclusão: 'usar == em vez de compare_digest' raramente é um achado Alto.")
    print(f"    Reporte com estes números (Baixo/Informativo) OU vá atrás dos modos que")
    print(f"    realmente quebram: sem verificação, prefixo truncado, fail-open de segredo,")
    print(f"    exceção não tratada (DoS) e divergência de encoding.")


if __name__ == "__main__":
    main()
