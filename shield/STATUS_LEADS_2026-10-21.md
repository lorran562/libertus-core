# STATUS DOS LEADS SHIELD — Ariquemes/RO
**Reconferido em 21/10/2026** (última coleta anterior: 13–14/10/2026)

## O que existe hoje

| Artefato | Conteúdo |
|---|---|
| `shield/leads_ariquemes.csv` | **49 empresas** com telefone, em 7 verticais (7 por vertical) |
| `shield/LEADS_ARIQUEMES.md` | Lista priorizada: 2 QUENTE, 26 prioridade A (têm site), 21 prioridade B (sem site) |
| `shield/LEADS_QUENTES.md` | 9 leads que já receberam laudo/proposta (TIER 1 e 2) + 3 TIER de apoio |
| `shield/LEADS_VERIFICADO_2026-10-13.md` | Achados que sobreviveram à verificação individual (3 falsos positivos retirados) |
| `relatorio_shield_ariquemes.md` | Levantamento original de 27/05/2026, 5 empresas, laudo completo |
| `shield/recon/` | JSONs de recon passivo por domínio |

## Situação do funil (dado, não impressão)

- **49/49 leads com status `a_contatar` no CSV.** Ou seja: nenhum contato
  registrado como feito. O pipeline parou em 13/10 — **8 dias sem movimento**.
- Se algum contato foi feito por fora (WhatsApp à mão), ele não está no CSV e
  por isso não existe para o sistema.

## Reconferência técnica de hoje (21/10/2026)

Recon passivo re-executado (`shield/recon_lote.py`), somente dado público:

| Empresa | Achado em 21/10 | Leitura correta |
|---|---|---|
| **Laboratório São José** | **Site continua fora do ar** (DNS ok, HTTPS não conecta) — igual em 13/10 | **Gancho mais forte da lista inteira.** Não exige laudo: "seu site não está abrindo" é verificável pelo dono em 5 segundos. 8 dias fora = 8 dias de paciente perdido |
| **Laboratório São Francisco** | `/.env`, `/.git/HEAD`, `/.git/config` → **403 (bloqueado)**; `/config` → não existe | As 3 falhas ALTAS **foram corrigidas** (já constava no laudo de 13/10). O pitch de emergência morreu; sobrou venda de adequação/consultoria. Não usar "a falha continua aberta" — é falso |
| **Bruni Imóveis** | SEM redirect HTTPS (HTTP não força TLS) | Continua ativo desde 13/10. Achado fraco isolado, mas sustentável: dado de cliente de imobiliária em texto claro |
| **CEDDI Centro de Diagnóstico** | `/admin/` e `/wp-login.php` → 200 | **É só a tela de login padrão do WordPress.** Não é vulnerabilidade. O valor aqui é LGPD (dado de saúde = categoria especial), não "site invadido" |
| **AD Imóveis** | `/admin/` e `/wp-login.php` → 200; 6 headers de segurança ausentes | Mesma leitura: login padrão não é achado. Cabe diagnóstico de headers, ticket baixo |
| **Marques Imóveis** | TLS 1.2 + 6 headers ausentes | Site no ar e funcional. Venda de adequação, não de urgência |
| **Oikos Assessoria** | Wix + 5 headers ausentes | Plataforma fechada — pouco a oferecer além de orientação. Baixa prioridade |

## Próximo passo (escolher UM para hoje)

1. **São José (site fora do ar)** — mensagem curta por WhatsApp/e-mail: fato
   verificável, sem jargão, sem laudo. É o lead com maior chance de resposta.
2. **Registrar no CSV o que já foi contatado** por fora — hoje o funil mente
   dizendo que 49 estão intocados.
3. **Recon dos 26 de prioridade A que nunca foram analisados** (só 7 domínios
   foram escaneados até agora). LIBERTUS gera em lote, custo ~zero.

## Regra que continua valendo

Abordagem só sai com achado **reconferido no dia**. Site muda de host, refaz
página e corrige falha entre a análise e a mensagem — reusar achado antigo é
mentira verificável em 10 segundos pelo cliente.
