# AUTORIZAÇÃO — Teste de Segurança AbacatePay

## Registro de autorização (evidência legal — preservar)

**Data:** 24/09/2026 22:20
**Concedida por:** Guilherme (equipe AbacatePay)
**Canal:** WhatsApp (conversa com Lorran Gustavo)
**Pesquisador autorizado:** Lorran Gustavo — Independent Security Researcher, Ariquemes-RO, Brasil

### Transcrição literal (print/texto salvo)

> **Guilherme (AbacatePay):** "Fique à vontade para explorar nosso produto,
> estamos sempre à disposição para investigar possíveis falhas e corrigi-las
> o mais rápido possível. Novamente, muito obrigado pelo contato e feedback!"
>
> **Lorran:** "De nada, posso procurar mais falhas profunda então?"
>
> **Guilherme (AbacatePay):** "Claro! Qualquer novidade, pode nos avisar."

### O que esta autorização cobre (interpretação conservadora)

- Explorar o produto da AbacatePay em busca de falhas de segurança
- Reportar achados ("qualquer novidade, pode nos avisar")

### O que NÃO está explícito (precisa ser confirmado por escrito antes)

- [ ] Escopo de alvos: API v2 produção? Dashboard? Sandbox/devMode? Infra?
      SDKs open-source (esses já são legais independente — código público)?
- [ ] Ferramentas automatizadas (nuclei/ffuf/sqlmap/nmap) contra produção
      são permitidas, ou só teste manual / na própria conta?
- [ ] Existe ambiente de sandbox/teste preferido para não tocar produção real?
- [ ] Limite de rate / janela de horário para não impactar o serviço?
- [ ] Regra sobre dados: só a própria conta, nunca dados de outros clientes?
- [ ] Canal e formato de report (security@abacatepay.com? WhatsApp? Discord?)

## Histórico de disclosure anterior (boa-fé demonstrada)

- **26/06/2026:** 7 findings reportados (SDKs + API v2). Corrigidos: preço
  negativo, quantidade negativa, URLs de callback perigosas.
- **02/09/2026:** HTTP Parameter Pollution reconfirmado em
  /v2/transparents/simulate-payment e /check (testado só em devMode/sandbox).
- **24/09/2026:** autorização explícita concedida (este documento).

## Princípio inegociável

Teste dentro do escopo confirmado. Sem autorização escrita de escopo ampliado,
o teste seguro = própria conta + própria chave de dev + sem transação real +
análise estática de código público. Ficha criminal cyber aos 18 mata OSCP/Irlanda.
