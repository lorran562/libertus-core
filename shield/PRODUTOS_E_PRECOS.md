# SHIELD — O QUE VENDER (catálogo operacional)

> Feito pelo LIBERTUS, 13/10/2026. Regra deste arquivo: nada de teoria —
> cada produto tem gatilho, preço, o que o cliente RECEBE e a mensagem pronta.
> Se não tem preço e mensagem, não está pronto pra vender.

## A regra que faz vender em cidade pequena

Dono de clínica, contador e advogado em Ariquemes NÃO compra "segurança".
Ele compra três coisas só:

1. **Não perder dinheiro** (multa da LGPD, site fora do ar, cliente bravo)
2. **Não passar vergonha** (site invadido, Instagram clonado, dado de paciente vazando)
3. **Não ficar sem alguém pra chamar quando quebrar** (o "meu TI" mensal)

Falar de "vulnerabilidade XSS com reflexão" = não vende.
Falar "seu site mostra dado do seu cliente sem proteção e isso é multa da LGPD" = vende.

## PRODUTO 1 — Diagnóstico Express + Laudo LGPD  ·  R$ 497 (pagamento único)

**Gatilho:** qualquer empresa que guarda dado de cliente (clínica, dentista, contador, advogado, imobiliária, laboratório).

**O que o cliente recebe:**
- Laudo técnico de 3–5 páginas com o nome dele na capa
- Problemas encontrados com severidade (Crítico/Alto/Médio/Baixo)
- Exposição legal: qual artigo da LGPD está em risco + faixa de multa
- Plano de correção priorizado (o que fazer primeiro)
- Proposta de correção com preço na última página

**Custo real de produção:** quase zero — o LIBERTUS gera o laudo a partir do
domínio, em minutos. É esse o produto: o documento.

**Mensagem de abertura (WhatsApp):**
> Bom dia! Aqui é o Lorran, da SHIELD (cibersegurança aqui de Ariquemes).
> Fiz uma análise pública do site da [NOME] — só o que qualquer navegador vê,
> nada invasivo. Achei [ACHADO CONCRETO: ex. "o site não protege o formulário
> de contato, e ele recebe dado de paciente"]. Isso pesa na LGPD.
> Montei um laudo de 4 páginas com o que achei e o que fazer. Te mando sem
> custo pra você avaliar?

**Por que a abertura funciona:** dá o valor ANTES de pedir dinheiro, cita achado
específico da empresa dele (não é spam genérico), e não exige que ele entenda
nada de tecnologia.

**Fechamento:** o laudo inteiro é grátis. O que é pago é a **correção**
(R$ 497) e/ou o acompanhamento mensal.

---

## PRODUTO 2 — Escudo Mensal  ·  R$ 297/mês (recorrente)

**Este é o produto que paga as contas.** Os outros dão caixa pontual; este dá
previsibilidade. 10 clientes = R$ 2.970/mês entrando todo mês.

**O que o cliente recebe todo mês:**
- Relatório de 1 página: o que foi checado, o que está ok, o que mudou
- Alerta imediato se algo crítico aparecer (site fora, certificado vencendo, exposição nova)
- Backups verificados
- Canal direto no WhatsApp pra emergência

**Como produzir:** o LIBERTUS roda a verificação mensal e gera o relatório.
O trabalho humano é ler e mandar. Escala sem aumentar horas.

**Gatilho de venda:** fechar junto com o Diagnóstico Express — "o laudo achou
os problemas, eu corrijo e deixo monitorando por R$ 297/mês".

---

## PRODUTO 3 — Socorro Digital  ·  R$ 397 a R$ 997 (emergência)

**Gatilho:** site invadido, Instagram clonado/perdido, e-mail comprometido,
"meu sistema tá pedindo resgate", cliente recebendo boleto falso com a marca dele.

**Por que é o caixa mais rápido que existe:** quem está com o problema AGORA
não pesquisa preço, não pede proposta pra três, não espera. Paga hoje.

**O que o cliente recebe:**
- Relatório do que aconteceu (pra ele saber o tamanho do estrago)
- Recuperação do acesso / limpeza do que foi injetado
- O que vazou e o que ele é obrigado a comunicar (LGPD)
- Blindagem imediata pra não acontecer de novo

**Como ser chamado:** este produto não se vende por abordagem fria — se vende
por ESTAR VISÍVEL quando acontece. Bio do Instagram + post fixado:
"Foi invadido? Fale comigo agora." + indicação de quem já atende essas empresas
(contador, agência de marketing, o técnico de informática que não faz segurança).

---

## PRODUTO 4 — Análise técnica em dólar (internacional)  ·  US$ 50 a 300

**Canal:** Fiverr + Upwork + LinkedIn. Cliente estrangeiro decide mais rápido,
paga em dólar e não precisa te ver pessoalmente.

**O que vender (tudo com o que já temos instalado):**
- **Análise de arquivo/script suspeito** — "recebi esse JS/PHP/binário, é golpe?" → US$ 50–150
- **Desobfuscação de código** (JS malicioso, PHP ofuscado) → US$ 80–200
- **Análise de firmware/IoT** (empresa de hardware quer saber se o binário tem problema) → US$ 200–2000
- **Code review de segurança** de app pequeno → US$ 150–500
- **Reconstrução/análise de app Electron/JS empacotado** → US$ 150–400

**Por que agora:** com REA + Ghidra a análise de binário/firmware deixou de ser
"eu acho" e virou laudo com hash, endereço, pseudocódigo e evidência. Isso é
exatamente o que o cliente de fora paga caro e não acha fácil.

**Custo de entrada:** zero. É perfil + 3 serviços publicados + portfólio
(usar os laudos daqui como amostra, sem nome de cliente).

---

## PRODUTO 5 — O que vende sem você (o que escala)

Só depois que os 1–4 estiverem girando. Duas apostas realistas:

1. **Ferramenta paga pra quem já é da área** — exemplo: pipeline de análise de
   firmware, ou o gerador de laudo LGPD como serviço web. Vende pra outros
   técnicos/pentesters e pra quem faz bug bounty. Preço em dólar, entrega
   automática. Aqui o LIBERTUS é literalmente o produto.
2. **Curso curto pro técnico de TI local** — "como auditar um site e cobrar
   por isso". Vende pra quem já tem a relação com os clientes e não sabe fazer.

**Aviso honesto:** isso demora e depende de audiência. Não é por aqui que sai
o primeiro dinheiro. É por onde sai o dinheiro grande depois.

---

## Ordem de execução (não tentar tudo junto)

1. **Esta semana:** rodar a lista de leads dos 3 verticais que já estão no
   pipeline (clínicas/dentistas, contadores, advogados/imobiliárias) em
   Ariquemes. Gerar laudo pra todos. Mandar mensagem pra 20.
2. **Próxima semana:** fechar 1 Diagnóstico Express (R$ 497) + 1 Escudo Mensal
   (R$ 297/mês). O objetivo NÃO é faturar muito — é ter o PRIMEIRO cliente
   usando como prova social.
3. **Depois disso:** publicar os 3 serviços no Fiverr/Upwork com os laudos como
   portfólio. Canal em dólar aberto.
4. **Só então:** pensar em produto que escala.

## Regra de follow-up que já sabemos que funciona

- Quem responde rápido é a recepção, não quem decide. Trocar de canal e de
  pessoa (ligar e pedir o responsável), não repetir mensagem no mesmo contato.
- Nunca inventar urgência. Usar fato verificável e verdadeiro ("a falha que
  reportei continua aberta, acabei de confirmar").
- Nunca travar num lead só. Lista paralela sempre viva.

## O que NUNCA fazer (não é moralismo, é sobrevivência)

- Não usar certificado/credencial forjada como prova. É estelionato, é
  verificável, e fecha a porta da Irlanda/OSCP.
- Não invadir nada sem contrato assinado. O Diagnóstico Express é 100% passivo
  (só dado público) — é o que dá pra fazer sem autorização, e é o que basta pra
  provar valor e cobrar.
