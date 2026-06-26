# Email Template - Responsible Disclosure AbacatePay

**Para:** security@abacatepay.com  
**CC:** ajuda@abacatepay.com  
**Assunto:** [Responsible Disclosure] Vulnerabilidades identificadas em SDKs e CLI - AbacatePay

---

Olá equipe de segurança da AbacatePay,

Me chamo Lorran Gustavo, sou pesquisador de segurança da informação de Ariquemes-RO, Brasil, atuando sob o nome SHIELD Security (@shieldweb).

Realizei uma análise de segurança nos repositórios públicos da organização AbacatePay no GitHub e identifiquei algumas vulnerabilidades que gostaria de reportar de forma responsável, seguindo a política de segurança publicada em SECURITY.md.

## Resumo das Descobertas

Foram identificadas **7 vulnerabilidades** nos seguintes repositórios:
- abacatepay-cli
- abacatepay-nodejs-sdk  
- abacatepay-python-sdk

### Severidade:
- 2 vulnerabilidades de severidade MÉDIA
- 5 vulnerabilidades de severidade BAIXA/INFORMACIONAL

### Principais Issues:

1. **[MÉDIA]** Derivação previsível de senha do keyring no CLI - permite extração de tokens por atacante local
2. **[MÉDIA]** Ausência de URL encoding em query parameters nos SDKs Node.js e Python - risco de injection
3. **[BAIXA]** Mock token e IP interno hardcoded
4. **[BAIXA]** Webhook signing secret previsível em mock mode
5. **[BAIXA]** Logging excessivo de dados sensíveis no SDK Python
6. **[INFO]** Ausência de rejeição de timestamps antigos em webhooks
7. **[INFO]** Ausência de rate limiting client-side

## Relatório Completo

O relatório técnico completo com:
- Código vulnerável identificado
- Prova de conceito (PoC)
- Impacto detalhado
- Recomendações de correção

Está disponível em: https://github.com/lorran562/libertus-core/blob/main/abacatepay-audit/SECURITY_REPORT.md

## Metodologia

- Análise estática de código-fonte
- Nenhum teste ativo contra infraestrutura de produção
- Conformidade total com a política de segurança da AbacatePay

## Disponibilidade

Fico à disposição para:
- Esclarecimentos técnicos adicionais
- Auxiliar na validação das correções
- Discussão sobre parceria/bounty se aplicável

## Contato

**Lorran Gustavo**  
SHIELD Security  
Ariquemes, Rondônia - Brasil  
GitHub: github.com/lorran562

Agradeço a oportunidade e aguardo retorno.

Atenciosamente,
Lorran Gustavo
SHIELD Security

---

*Este email faz parte de um processo de responsible disclosure.*
*As vulnerabilidades não foram divulgadas publicamente além deste relatório.*
