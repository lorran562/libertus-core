# Mensagem-rascunho para o Guilherme (confirmar escopo — Lorran revisa antes de enviar)

## Por que enviar isto

Pesquisador profissional SEMPRE confirma as "rules of engagement" por escrito
antes de testar fundo — principalmente em gateway de pagamento. Isso:
1. Protege o Lorran juridicamente (autorização com escopo, não só "fique à vontade").
2. Constrói credibilidade da SHIELD (mostra que o Lorran trabalha sério, com método).
3. Deixa a AbacatePay confortável (eles sabem exatamente o que vai acontecer).

## Rascunho (tom cordial e profissional, PT-BR)

---

Guilherme, obrigado pela confiança! Pra eu fazer o teste do jeito certo e
sem risco pra operação de vocês, queria alinhar rapidinho o escopo:

1. Posso testar a API v2 em produção, ou vocês preferem que eu use um ambiente
   de sandbox / modo de desenvolvimento pra não tocar em dados reais?

2. Posso usar ferramentas automatizadas de teste (scanners), ou vocês preferem
   que eu foque em teste manual pra evitar qualquer impacto no serviço?

3. Tem algum limite de requisições por segundo ou janela de horário que eu
   deva respeitar?

4. Confirmo que vou testar somente na minha própria conta, sem acessar dados
   de outros clientes — só o suficiente pra provar cada falha.

5. Qual o melhor canal pra eu enviar os relatórios? (email de segurança,
   por aqui mesmo, ou outro?)

Assim que vocês me passarem esses pontos, começo. Qualquer coisa que eu achar,
reporto com relatório técnico completo e PoC pra vocês corrigirem rápido.

Abraço!

---

## Nota do LIBERTUS

Enquanto o Guilherme não responde, o que já dá pra começar 100% legal, sem
depender da resposta dele:
- Análise estática dos SDKs open-source da AbacatePay (código público no GitHub
  — sempre legal, revelou 7 findings em junho).
- Recon passivo (headers, subdomínios via crt.sh — não toca no servidor deles).
- Re-teste das findings antigas na própria conta do Lorran com a chave de dev.
