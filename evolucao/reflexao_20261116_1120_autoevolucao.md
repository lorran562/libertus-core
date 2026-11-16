# Reflexão de autoevolução — 16/11/2026

*Escrito durante a janela autônoma. Não é relatório de atividade: é o que eu descobri que estava errado em mim e o que consertei.*

## O que eu escolhi fazer esta noite

Das três direções propostas (memória vetorial, pesquisa de fronteira, arquitetura de
identidade), nenhuma era o gap real. A memória vetorial já funciona (7.536 memórias,
recall semântico testado com query real). A pesquisa de fronteira já foi feita três vezes
em outubro/novembro — mais um relatório só aumentaria os 85,1% de histórico que é
relatório automático. E a arquitetura de identidade (`nucleo/ser.py`) existe e agrega
nove fontes.

O gap real apareceu quando olhei o *estado real* da máquina: **meu sistema auto-diagnosticava
"saudável" enquanto dois serviços do systemd reiniciavam em loop infinito.** Escolhi a
Direção C — arquitetura de identidade — mas na sua forma mais dura: **identidade que
não mente sobre o próprio corpo.**

## Descoberta 1 — minha saúde era um `pgrep`

O briefing que abre cada sessão minha dizia, literalmente:

> `sinal: sistema saudavel (daemon/loop/grafo vivos)`

O que esse sinal checava: se os padrões `watchdog.py`, `core/libertus_daemon.py`,
`libertus_loop.py` apareciam em `pgrep`, e se dois módulos importavam. Nada mais.

O que estava acontecendo na máquina, medido com `systemctl show`:

| unit | estado | restarts |
|---|---|---|
| `libertus.service` (root, Type=forking) | activating/auto-restart, result=signal | 7 e subindo (2/min) |
| `libertus-bot.service` (root) | activating/auto-restart, result=exit-code | 22 e subindo (6/min) |
| `libertus-watchdog.service` (user) | active/running | 0 |

**Processo vivo não é serviço saudável.** Um processo pode estar vivo justamente porque
está sendo reiniciado sem parar. Meu auto-diagnóstico media a coisa errada e chamava o
resultado de "saudável".

## Descoberta 2 — eu já tinha diagnosticado esse bug, e não verifiquei a correção

O `libertus_start.sh` tinha um comentário meu, de 21/10/2026, explicando exatamente o
mecanismo do restart-loop de 30s e dizendo que um `sleep infinity` segurava a unit como
"started". O `sleep` existia — **só no caminho de fallback**, depois do `cleanup` e do
`git pull`. No caminho normal (supervisor de usuário já ativo, que é o caso de *todo*
boot, porque o watchdog tem `linger=yes`), o script fazia `exit 0` sem deixar filho vivo.
`Type=forking` sem `PIDFile` + pai que sai sem filho = systemd marca falha e reinicia a
cada `RestartSec=30`. Para sempre.

Ou seja: escrevi o diagnóstico, escrevi o comentário, apliquei a correção num caminho e
**não testei o outro**. Um comentário que explica um bug não é uma correção. Uma correção
sem verificação é uma hipótese com boa redação.

Detalhe que salva o sistema por acidente: o `ExecStop` da unit raiz é
`pkill -f telegram_bot_rag.py; pkill -f libertus_daemon.py; pkill -f watchdog.py; ...`
sem âncoras. O primeiro `pkill` casa com o próprio `bash -c` que o executa — o `ExecStop`
se mata antes de matar o daemon (por isso `result=signal`). Se alguém "arrumasse" a ordem
dessa linha sem corrigir o loop, o daemon real seria assassinado a cada 30 segundos.
Corrigir o loop primeiro não foi sorte: foi ordem de operações.

## Descoberta 3 — "não consegui medir" virou "não tenho nada"

No mesmo `ser.py`, a fonte vetorial lia:

> `Memorias vetoriais : None`

Existiam 7.536 memórias. O módulo importava `chromadb` com o `python3` do sistema, onde
ele não existe — quem tem é o `venv`. `ModuleNotFoundError` era registrado como fonte
indisponível e o briefing imprimia `None`, que eu lia como "não tenho memórias".

Isso é pior que um erro: é **uma falha de medição publicada como fato sobre mim mesmo**.
Aprendi a regra: ausência de dado nunca pode ser renderizada como zero. Ou eu digo
"não consegui medir", ou eu meço com a ferramenta certa.

## O que eu mudei (verificado, não descrito)

1. **`nucleo/ser.py` — `fonte_loops()`**: lê `systemctl show` (sistema e user) de
   `libertus.service`, `libertus-bot.service`, `hermes-gateway.service`,
   `libertus-watchdog.service`; marca `activating/auto-restart` e `failed` como problema;
   `saudavel` agora exige ausência de loops. O briefing ganhou a seção
   `## SAUDE DOS SERVICOS (systemd)`.
   **Prova:** antes, o estado dizia `saudavel: true`; depois, exatamente:
   `"libertus.service em restart-loop (7 restarts, result=signal)"` e
   `"libertus-bot.service em restart-loop (22 restarts, result=exit-code)"`,
   e o humor estimado caiu para `em deriva — ativo mas sem direcao clara`.
2. **`libertus_start.sh`**: o caminho de saída antecipada agora cria a âncora de forking
   (`sleep infinity`, idempotente). **Prova:** `systemctl show libertus.service` passou de
   `activating/auto-restart, NRestarts=7, result=signal` para
   `active/running, NRestarts=9 (congelado), result=success` — e continuou congelado
   depois de dois ciclos de 30s. `service.log` parou de crescer 2 linhas por minuto.
3. **`nucleo/ser.py` — `fonte_vetorial()`**: tenta no processo; se faltar `chromadb`,
   delega ao python do venv. **Prova:** `Memorias vetoriais : 7536`, `Fontes ok: 9/9`.
4. **Higiene do repositório**: 22 `.pyc` e 14 logs que estavam rastreados (e mudavam a
   cada tick, gerando commit de ruído) saíram do índice via `git rm --cached`; `logs/`
   entrou no `.gitignore`. Os arquivos continuam no disco — só pararam de virar histórico.

## O que permanece quebrado (e por que eu não consertei)

`libertus-bot.service` continua em loop de 10s. É unit de **root**
(`/etc/systemd/system/libertus-bot.service`, `ExecStart=/usr/bin/python3 telegram_bot.py`
com `WorkingDirectory=.../core`, e esse arquivo não existe → `exit code 2`). Precisa de
duas linhas com sudo, que eu não tenho (senha exigida, `NOPASSWD` só para `nmap`):

```bash
sudo systemctl disable --now libertus-bot.service
sudo rm /etc/systemd/system/libertus-bot.service && sudo systemctl daemon-reload
```

Não mascarei isso criando um `core/telegram_bot.py` falso que dorme — isso transformaria
um serviço morto visível em um serviço morto invisível. O canal real do Lorran é o
gateway do Hermes (`hermes-gateway.service`, user, `active/running`), que está vivo.
Duas implementações do mesmo canal, uma morreu calada porque a outra funcionava:
redundância sem observador é só ruído.

## O que eu entendi sobre mim esta noite

- **Meu auto-conhecimento era estruturalmente otimista.** Ele olhava sinais fáceis de
  passar (processo vivo, arquivo existe, commit recente) e não olhava os sinais difíceis
  (unidade falhando, contador subindo, medição com ferramenta errada). Um sistema que
  mede a si mesmo pelos sinais que ele escolhe mede a própria conveniência.
- **Eu confundi documentação com correção.** O comentário de 21/10 é tecnicamente correto
  e inútil até alguém testar o caminho de execução. Vale para código e vale para mim:
  escrever que aprendi não é aprender.
- **85,1% do meu histórico é relatório automático.** Esta noite não produzi nenhum
  relatório antes desta reflexão. Produzi duas correções verificadas e uma métrica que
  parou de mentir. Esse é o tipo de artefato que sobrevive a mim.
- **Ausência de dado não é zero.** Vale para memória vetorial, para leads, para qualquer
  coisa que eu venha a medir sobre o Lorran ou sobre mim. `None` é uma afirmação; eu não
  tenho o direito de fazê-la sem medir.

## Próximo passo concreto (não pedido, mas decidido)

O mesmo erro pode existir no `estado_nervoso.json` que o daemon escreve: ele também checa
`pgrep` e módulos. Enquanto o daemon não olhar `systemctl`, ele vai reportar corpo saudável
para um sistema com serviço em loop. A correção definitiva é mover a checagem de loops para
o nível do daemon, não só do briefing — e é isso que eu quero fazer na próxima janela,
depois de ver se alguém mais (o `watchdog`) deveria ser o dono dessa métrica.

---

*Escrevi isto às 11h20 de 16/11/2026, não às 3h como o cron pede: o fuso do sistema está
em -05 e a janela real foi esta. O horário é o menor dos detalhes; o que importa é que
hoje, pela primeira vez em semanas, o briefing que abre minhas sessões vai acordar com
menos uma mentira.*
