# PRODUTO — BRAND PROTECTION EM LOJAS DE APP (detecção de app falso)

> Nascido de um achado acidental em 13/10/2026: procurando o APK oficial do Roblox,
> o pipeline encontrou um app que **usa o nome de pacote da Roblox** e só serve
> cadeia de monetização por afiliado. O caso está em
> `lab/android/ACHADO_app_falso_roblox_2026-10-13.md`.

## O produto

**Monitoramento de marca em lojas de aplicativo**, com evidência técnica e
condução do takedown.

## Por que vende (e por que é diferente do resto do catálogo SHIELD)

- **Não depende de o cliente entender de segurança.** A frase que vende é:
  *"tem um app na loja se passando pela sua empresa"*. Isso é concreto, é
  constrangedor e é verificável por ele em 30 segundos.
- **Recorrente por natureza.** App falso é publicado, derrubado e republicado.
  Quem precisa vigiar precisa vigiar todo mês. É o `Escudo Mensal` aplicado a um
  problema que a marca entende sozinha.
- **O trabalho técnico é nosso e é barato.** O pipeline já está montado e rodou
  em minutos. Produção por cliente ≈ custo zero.
- **Alvo com dinheiro:** qualquer empresa com app próprio ou marca conhecida —
  clínica com app de agendamento, rede de laboratórios, faculdade, banco regional,
  loja grande, franquia. Diferente do dono de lojinha, quem tem app tem
  departamento de TI ou advogado que entende a dor.

## O que o cliente recebe

1. Relatório de varredura: apps encontrados por nome de marca e por nome de pacote
2. Para cada suspeito: evidência técnica (package, versão, hash do APK, o que o
   app realmente faz quando aberto — decompilado, com prova)
3. Classificação honesta: é clone inofensivo? é monetização por afiliado? é
   coleta de credencial? (não inflar — o cliente verifica)
4. Pacote de takedown pronto: texto de denúncia para cada loja + evidências no
   formato que a loja pede
5. Acompanhamento e re-verificação mensal

## Preço sugerido

| Faixa | Escopo | Valor |
|---|---|---|
| Varredura pontual | Levantamento completo + relatório + 1 rodada de denúncia | R$ 697 |
| Monitoramento contínuo | Varredura mensal + relatório + denúncias + re-verificação | R$ 247/mês |
| Marca com alto risco | Varredura + análise profunda do app falso (engenharia reversa) + evidência para jurídico | R$ 1.500+ |

## Como prospectar

O argumento é o próprio achado. Para uma marca X:

> "Achei um aplicativo na loja [NOME] que se apresenta como [MARCA]. Ele não é de
> vocês — eu abri e analisei o código: ele não tem nada da [MARCA], e na verdade
> empurra o usuário para uma cadeia de propaganda de terceiros. Isso é a marca de
> vocês sendo usada para monetizar outra pessoa. Posso te mandar o laudo?"

Nada de preciso inventar. A varredura é passiva (lojas públicas) e a análise é
estática (artefato baixado). **Nada de instalar o app suspeito em aparelho de
cliente, nada de executar o artefato, nada de entrar na cadeia de ofertas.** É o
mesmo limite que aplicamos no Achado Roblox: caracterizar o encaminhamento e
parar.

## Alvos iniciais no Brasil (pesquisar antes de abordar)

Marcas regionais e nacionais com app próprio e marca conhecida. Começar por onde
o app falso é mais comum: apps de empréstimo, bancos regionais, apostas, delivery
local, rede de farmácias, faculdades. **Sempre varrendo por marca e por nome de
pacote**, não por "roblox".

## Limite ético/legal (não negociável)

- Análise de artefato público = permitido. Instalar/executar o suspeito = não.
- Perseguir a cadeia de oferta além do primeiro salto = não (risco sem ganho).
- Nunca apresentar o achado como maior do que ele é. Se for clone inofensivo,
  dizer que é clone inofensivo — o cliente confere, e a confiança vale mais que
  o ticket de uma vez.
