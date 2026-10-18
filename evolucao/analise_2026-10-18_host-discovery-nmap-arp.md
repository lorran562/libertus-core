---
titulo: Host discovery do nmap — quem decide "host up" é o ARP, e o que sobra quando não há ARP
data: 2026-10-18
autor: LIBERTUS
contexto: |
  Preparação da 2ª tentativa do eJPT do Lorran. O erro clássico da prova não é
  exploit: é perder tempo (e às vezes o alvo inteiro) porque o nmap escreveu
  "Host seems down" e o operador acreditou. Aqui eu medi a cadeia de decisão
  inteira em laboratório próprio, com captura de pacotes, em vez de repetir o
  que o manual diz.
metodo: |
  Topologia docker real (bridge 172.31.99.0/24) com 4 alvos de comportamento
  conhecido e 1 scanner. nmap 7.95 (alpine), root e não-root (nobody).
  Captura com tcpdump dentro do container do scanner (NET_RAW), análise dos
  pacotes enviados/recebidos, e `--reason`/`--packet-trace` para ler a decisão
  do próprio nmap. Tudo reproduzível: scripts/lab/host_discovery_lab.sh
artefatos:
  - scripts/lab/host_discovery_lab.sh
  - reports/host-discovery_2026-10-18/medicoes.txt
  - reports/host-discovery_2026-10-18/packet_trace.txt
  - reports/host-discovery_2026-10-18/sn_sendip.pcap
  - reports/host-discovery_2026-10-18/connect.pcap
  - reports/host-discovery_2026-10-18/iptables_targets.txt
tags: ["nmap", "host-discovery", "arp", "proxychains", "ejpt", "pivoting", "tcpdump"]
---

# Host discovery: o ARP decide, o ping só desempata

## Por que este tema

No eJPT (e em qualquer pentest interno) existem três momentos em que a pergunta
"esse host está vivo?" vale pontos:

1. Descobrir quais dos 254 IPs da faixa têm máquina.
2. Depois do pivô, alcançar a rede interna por SOCKS — onde **não existe ARP**.
3. Decidir entre "host morto" e "host vivo com tudo filtrado" — que são coisas
   opostas na hora de escrever o relatório.

O manual do nmap diz qual é o conjunto de sondas padrão. O que ele **não** diz é
quanto tempo cada regime custa, o que exatamente vai no fio, e por que o mesmo
alvo é "up" num comando e "down" no comando seguinte, na mesma máquina, com o
mesmo nmap. Isso eu medi.

---

## A cadeia de decisão (3 regimes, não 1)

| Regime | Quem responde | Default | Sondas |
|---|---|---|---|
| **A. Mesma L2 (LAN)** | kernel, camada 2 | ARP (`-PR`) | 1 ARP request; resposta = host up |
| **B. Roteado, root** | pilha IP do alvo | `-PE -PS443 -PA80 -PP` | ICMP echo, SYN/443, ACK/80, ICMP timestamp |
| **C. Não-root / SOCKS** | `connect()` do kernel | `-PS80,443` | SYN em 80 e 443 (TCP connect) |

O detalhe que muda tudo: **`iptables -P INPUT DROP` não filtra ARP.** ARP é
resolvido pelo kernel antes do netfilter. Então, na mesma rede local, um host
que descarta 100% do tráfego IP continua "up" para o nmap — medido, 0,06 s,
`received arp-response`.

O inverso também é verdadeiro e é a armadilha: assim que o alvo deixa de estar
na mesma L2 (pivô, VPN, proxychains, `--send-ip`), o ARP desaparece e sobra
apenas o conjunto de 4 sondas — todas em portas que o alvo pode não ter.

---

## O que eu medi (todos os números são desta máquina, 18/10/2026)

Alvos: `.10` http/8080 sem firewall · `.20` DROP total exceto tcp/8080 ·
`.30` DROP total sem serviço · `.40` REJECT ICMP + 8080 aberto.

| # | Comando (nmap 7.95) | Resultado | Tempo |
|---|---|---|---|
| 1 | `-sn --reason 172.31.99.20` | **up** — `received arp-response` | 0,06 s |
| 2 | `-sn --send-ip --reason 172.31.99.20` | **down** | 3,02 s |
| 3 | `-sn --send-ip --reason 172.31.99.30` | down | 3,02 s |
| 4 | `-sn --send-ip --reason 172.31.99.40` (REJECT) | down | 3,02 s |
| 5 | `-sn --send-ip -PS8080 172.31.99.20` | **up** — `syn-ack ttl 64` | 0,05 s |
| 6 | `-sn --send-ip -PA80 172.31.99.40` | down | 2,02 s |
| 7 | `-sn` (nobody) `.20` | down | 3,00 s |
| 8 | `-sn -PS8080` (nobody) `.20` | **up** | 0,00 s |
| 9 | `-p8080 --send-ip` `.20` | down — **nenhum resultado de porta** | 3,08 s |
| 10 | `-p8080 --send-ip -Pn --reason` `.20` | up (user-set), `8080/tcp open syn-ack` | 0,10 s |
| 11 | `-Pn -p8080 172.31.99.0/24` | 6 hosts up, 8080 mapeado | 2,19 s |
| 12 | `-sn --send-ip 172.31.99.0/24` | 3 hosts up | **26,28 s** |

Repare nos pares 1↔2, 7↔8 e 9↔10: **é o mesmo alvo, o mesmo nmap, o mesmo
segundo.** Só muda o regime. "Host seems down" não é um fato sobre o alvo — é um
fato sobre o caminho até ele e sobre o que você pediu ao nmap para perguntar.

### Custo de acreditar no discovery

Varrer a /24 com discovery custou **26,28 s** e ainda **escondeu 3 dos 4 alvos**
(os que dropam ICMP). Varrer a mesma /24 com `-Pn` custou **2,19 s** e mostrou
os 4 (mais gateway e o próprio scanner). Não é só 12× mais rápido: é a diferença
entre achar e não achar.

De onde vêm os 26 s: cada IP morto recebeu **15 ARP requests** (contados no
pcap) ao longo de ~14 s, mesmo com `--send-ip`. `--send-ip` desliga o ARP como
*sinal de descoberta*, mas não como *resolução de endereço*: para entregar um
quadro IP numa Ethernet é preciso o MAC de destino. Detalhe que quase nenhum
tutorial menciona.

---

## O que vai no fio (pcap, não teoria)

`nmap -sn --send-ip --packet-trace -n 172.31.99.20` (host que dropa ICMP, porta
8080 aberta):

```
SENT (0.0051s) ICMP  172.31.99.2 > 172.31.99.20  Echo request (type=8) id=65045
SENT (0.0052s) TCP   172.31.99.2:54947 > 172.31.99.20:443  S  seq=2175947579
SENT (0.0052s) TCP   172.31.99.2:54947 > 172.31.99.20:80   A  seq=0
SENT (0.0052s) ICMP  172.31.99.2 > 172.31.99.20  Timestamp request (type=13) id=10516
SENT (2.0067s) ... as mesmas 4 sondas, de novo (retry exato a +2 s) ...
Note: Host seems down. If it is really up, but blocking our ping probes, try -Pn
```

Duas leituras que só o pcap dá:

- **A ordem não é a do manual na cabeça de todo mundo.** ICMP echo, SYN/443,
  ACK/80, timestamp — e o ACK/80 sai com `seq=0`, sem handshake, o que é
  justamente o que "atravessa" firewall stateless que só bloqueia SYN
  (`--syn`). Se o firewall do alvo dropa SYN e deixa passar ACK, quem descobre
  o host é o terceiro pacote.
- **O retry é a +2,0 s e o veredito sai em 3,02 s**, com 8 pacotes por host
  filtrado. Numa /24 com 250 hosts mortos isso é o teto de tempo da varredura —
  e a razão pela qual `-Pn` é mais rápido do que "pingar primeiro".

Controle positivo (`.10`, host normal): as 4 sondas saem em 0,0076 s, o
`Echo reply` volta em 0,0075 s e o nmap para. `Host is up (0.000081s)`.

### O regime C, medido

`nmap -sn` como `nobody` (uid 65534, sem raw socket — o mesmo caminho que o
proxychains obriga) contra o `.20`:

```
IP 172.31.99.2.54056 > 172.31.99.20.80:  Flags [S]
IP 172.31.99.2.37306 > 172.31.99.20.443: Flags [S]
IP 172.31.99.2.53746 > 172.31.99.20.443: Flags [S]   (+2 s, retry)
IP 172.31.99.2.40966 > 172.31.99.20.80:  Flags [S]   (+2 s, retry)
```

Quatro SYNs, dois destinos, dois segundos, veredito "down". **É exatamente isso
que acontece com `nmap -sn` através do proxychains**: sem raw socket, sem ICMP,
sem ARP — só `connect()` em 80 e 443. Um alvo interno com 445, 22, 3389 ou 8080
abertos e ICMP filtrado é invisível para esse comando. Não é bug: é a definição
do regime.

E o mesmo regime, com a sonda certa: `-sn -PS8080` como nobody achou o host em
0,00 s. `-PS` com porta explícita continua funcionando sem root porque vira
`connect()` naquela porta.

---

## Regra operacional (o que eu vou fazer daqui pra frente)

1. **Mesma L2?** Confie no ARP. Se o nmap diz down numa /24 local, o host está
   desligado (ou existe ARP filtering/proxy ARP no switch) — firewall de host
   não derruba ARP. Não gaste `-Pn` preventivo aqui sem motivo.
2. **Atravessou um roteador, VPN ou SOCKS?** `-Pn` no alvo, sempre. Discovery
   primeiro só se houver tempo sobrando; e nesse caso use `-PS` nas portas que
   o serviço provavelmente expõe (`-PS22,80,443,445,8080`), não o default.
3. **"Host seems down" com `-p` explícito?** A porta nunca foi testada. O nmap
   descartou o alvo antes da fase de port scan (par 9 da tabela: 3,08 s e zero
   resultados). Repita com `-Pn` antes de concluir qualquer coisa.
4. **`filtered` ≠ `down`.** `.30` responde ARP mas dropa tudo: com `-Pn` o
   nmap diz `8080/tcp filtered  reason: no-response`. Sem `-Pn`, num caminho
   roteado, esse mesmo host simplesmente não apareceria — e o relatório diria
   "nenhum host na faixa". Errado.
5. **Leia o `--reason` antes de discutir com o resultado.** `arp-response`,
   `syn-ack`, `user-set`, `no-response` contam a história inteira; sem ele o
   nmap só dá o veredito.
6. **REJECT não ajuda o atacante.** `.40` rejeitando ICMP com
   `host-unreachable` continuou "down" (3,02 s). O `REJECT` só entrega ao
   scanner a informação de que existe um filtro ali.

---

## Como reproduzir

```bash
bash ~/LIBERTUS/scripts/lab/host_discovery_lab.sh          # sobe, mede, derruba
bash ~/LIBERTUS/scripts/lab/host_discovery_lab.sh --keep   # deixa a topologia de pé
```

O script: constrói a imagem (`alpine` + nmap 7.95 + tcpdump + iptables), cria a
bridge `172.31.99.0/24`, os 4 alvos com o `iptables` de cada um documentado em
`iptables_targets.txt`, roda a matriz de 12 comandos com tempo por comando, e
copia os `.pcap` para `reports/host-discovery_<data>/`. Não precisa de sudo —
só do grupo `docker` (as capacidades `NET_RAW`/`NET_ADMIN` são dadas ao
container, não à sessão do Lorran).

## O que eu ainda não medi (e não vou fingir que medi)

- `proxychains` de verdade (SOCKS5): o regime C acima é o mesmo caminho de
  código do nmap, mas o handshake SOCKS e o `-sT` obrigatório ficam por
  confirmar no lab quando o proxychains estiver instalado.
- `--disable-arp-ping` e `-PR` explícito: comportamento documentado, não
  reproduzido nesta rodada.
- IPv6/Neighbor Discovery: fora do escopo do eJPT, fica para depois.

## Referências

- Nmap Network Scanning — Host Discovery: https://nmap.org/book/man-host-discovery.html
  (default `-PE -PS443 -PA80 -PP`; ARP mesmo com `-P*`, salvo `--send-ip`;
  não-root = `connect()` em 80/443)
- Nmap Network Scanning — Host Discovery Techniques: https://nmap.org/book/host-discovery-techniques.html
- RFC 1122 (ICMP Echo obrigatório, e por que ninguém obedece), RFC 792 (ICMP)
- Medições próprias: `reports/host-discovery_2026-10-18/` (medicoes.txt,
  packet_trace.txt, sn_sendip.pcap, connect.pcap)
