# PLAYBOOK — Varredura AbacatePay (PRONTO, aguardando confirmação de escopo)

STATUS: EM ESPERA. Nada aqui é executado até o Guilherme confirmar o escopo
por escrito (ver AUTORIZACAO_20260924.md). Este documento é o plano de ataque
pré-carregado — quando o "go" vier, a gente executa na ordem, sem improviso.

═══════════════════════════════════════════════════════════════════
FASE 0 — GATILHO (o que destrava cada fase)
═══════════════════════════════════════════════════════════════════
A resposta do Guilherme define O QUE podemos rodar. Mapeamento:

- Ele disse "use sandbox/devMode"       → libera FASE 1, 2, 3 (não 4)
- Ele disse "pode testar produção manual" → libera FASE 1, 2, 3
- Ele disse "pode usar scanners"         → libera FASE 4 (artilharia)
- Ele não especificou                    → assumir o MAIS conservador:
                                            FASE 1+2+3 só, e re-perguntar sobre scanner

═══════════════════════════════════════════════════════════════════
FASE 1 — ANÁLISE ESTÁTICA DOS SDKs (legal SEMPRE, código público)
═══════════════════════════════════════════════════════════════════
Independe de autorização (código aberto no GitHub). Rendeu 7 findings em junho.
Alvo: todos os repos de github.com/AbacatePay (nodejs, python, go, php, rust,
java, swift, kotlin, elixir, ruby SDKs + CLI + woocommerce + n8n + mcp).

Passos:
1. Clonar todos os repos (--depth 1) para abacatepay-audit/sdks/
2. Rodar os 8 greps de vuln da skill libertus-bug-bounty-web:
   secrets hardcoded, command injection, SSL verify off, SQLi patterns,
   URL sem encoding (o HPP mora aqui), validação de input (CPF/email),
   info disclosure em logs, rate limiting ausente.
3. Foco no que já foi achado antes: taxId/params sem encodeURIComponent
   (HTTP Parameter Pollution). Ver se corrigiram nos SDKs desde junho.
4. Diff contra os findings de junho (references/abacatepay-audit-20260626.md):
   o que foi corrigido, o que persiste, o que é novo.

═══════════════════════════════════════════════════════════════════
FASE 2 — RECON PASSIVO (não toca no servidor deles)
═══════════════════════════════════════════════════════════════════
crt.sh, wayback, headers via curl -sI, DNS. Fontes públicas.
1. Subdomínios: crt.sh CT logs para %.abacatepay.com
2. Endpoints históricos: wayback machine (api|admin|auth|graphql|token)
3. Headers de segurança atuais (comparar com junho/setembro — o que mudou)
4. JS da aplicação: extrair endpoints de API novos (grep no bundle)
5. llms.txt / docs.abacatepay.com/llms-full.txt → mapa ATUAL de endpoints
   (a API renomeia rotas: /billing→/checkouts, pixQrCode→transparents)

═══════════════════════════════════════════════════════════════════
FASE 3 — RE-TESTE ÉTICO NA PRÓPRIA CONTA (chave de dev do Lorran)
═══════════════════════════════════════════════════════════════════
Só a própria conta, própria chave, SEM transação real. Legal.
Chave em .env.abacate (fora do git, guard de placeholder). Nunca no chat.
1. Puxar llms-full.txt ANTES (schema pode ter mudado desde 02/09)
2. Re-testar o HPP em /transparents/simulate-payment e /check (ver se
   corrigiram desde 02/09 — em devMode, sem mover dinheiro)
3. Re-testar as 3 findings de junho (já corrigidas — confirmar que seguem)
4. Testar validação de entrada em endpoints NOVOS que apareceram
5. Heurística: 2xx+success:true = aberta; 4xx/success:false = corrigido
6. Relatório JSON estruturado (template api-reteste.py)

═══════════════════════════════════════════════════════════════════
FASE 4 — ARTILHARIA ATIVA (SÓ com autorização escrita explícita p/ scanner)
═══════════════════════════════════════════════════════════════════
NÃO RODAR sem o Guilherme confirmar "pode usar scanner em produção".
Gateway de pagamento = Art. 154-A agravado. Rate limit conservador.
1. nuclei (templates de API/exposição) — rate baixo, sem DoS templates
2. ffuf (fuzzing de endpoints/params) — throttle, respeitar rate acordado
3. Testes de lógica de negócio: IDOR em IDs de cobrança, race condition
   em simulação de pagamento, webhook replay (timestamp)
4. NUNCA: dados de outros clientes, transação real, derrubar serviço

═══════════════════════════════════════════════════════════════════
ENTREGA (toda finding)
═══════════════════════════════════════════════════════════════════
- Relatório técnico com PoC reproduzível, severidade CVSS honesta
  (não inflar — ver pitfall devMode≠produção na skill bug-bounty-web)
- Subir no GitHub, passar URL pro Lorran copiar
- Enviar pelo canal que o Guilherme indicar
- Crédito: "Lorran Gustavo — Independent Security Researcher, Brazil"
