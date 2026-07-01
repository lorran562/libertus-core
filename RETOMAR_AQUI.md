# RETOMAR AQUI — Handoff de Sessão

**Salvo em:** 01 de Julho de 2026
**Situação:** Lorran foi fazer o RESIZE DE DISCO agora. Ubuntu vai desligar (boot no
pendrive GParted). Quando ele voltar e disser algo tipo "voltei"/"terminou", LEIA ISTO
PRIMEIRO e já confirme o resultado — não faça ele repetir o contexto.

---

## O QUE ESTAVA ACONTECENDO (01/Jul)

Executamos o plano de redimensionamento de disco que estava pendente desde 29/Jun.
Decisão do Lorran nesta sessão: **Windows no mínimo (~100 GB), Ubuntu leva o resto (~122 GB)**.

### JÁ FEITO nesta sessão (confirmado):
- Medido disco real: Windows sda3=184GB (usa ~103GB c/ hiberfil), Ubuntu sda5=38.5GB (95% cheio)
- **Descoberta importante:** ordem física é [EFI][MSR][Windows sda3][Ubuntu sda5][Recovery sda4].
  Ubuntu JÁ está colado no Windows → NÃO precisa mover recovery. Resize simplificado p/ 2 passos.
- Baixado GParted Live 1.8.1-3 (sha256 conferido com oficial ✓) em /tmp
- **Pendrive /dev/sdb (7.5GB) gravado com GParted Live bootável** (Lorran rodou o dd na mão,
  pq o agente bloqueia dd raw. LABEL="GParted-live" confirmado ✓)
- Escrito e commitado GUIA_RESIZE_GPARTED.md (no GitHub, Lorran leu pelo celular)
- Corrigido erro de conta no guia: era "139GB", conta real é ~122GB (223.6-100Win-1.6sistema)

### O QUE LORRAN FOI FAZER (fora do Ubuntu):
1. Boot no Windows → CMD admin → `powercfg /h off` → Shift+Desligar (mata hiberfil 13GB)
2. Boot pelo pendrive (F10) → GParted
3. Encolher sda3 (Windows) pra 100000 MiB
4. Crescer sda5 (Ubuntu) pra esquerda, preenchendo o vazio → ~122GB
5. Apply (lento, 30-60min no move ext4) → reboot no Ubuntu

---

## QUANDO LORRAN VOLTAR — PRIMEIRA COISA A FAZER

Rodar e conferir se o resize deu certo:

    df -h /
    lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT /dev/sda

**Sucesso =** `/` (sda5) com ~122GB e bastante espaço livre. Windows sda3 ~100GB.

- Se deu certo: comemorar rápido, confirmar espaço, e seguir pro DEEPHAT (próximo passo).
- Se sda5 ainda está 38.5GB: o Apply falhou ou ele não conseguiu. Perguntar o que aconteceu
  na tela do GParted. Possível fazer o grow por linha de comando (resize2fs) se a partição
  foi expandida mas o filesystem não — investigar com calma.
- Se algo quebrou: NÃO entrar em pânico. Diagnosticar com lsblk/parted antes de agir.

---

## PRÓXIMO PASSO DEPOIS DO DISCO (a razão de tudo isso)

Com disco liberado (~80GB+ livres), executar o que estava travado por falta de espaço:

### BAIXAR DEEPHAT + terminar arsenal
- DeepHat = ex-WhiteRabbitNeo, LLM uncensored treinado em ataque real (exploit/RE/adversary).
- Baixar GGUF: `mradermacher/DeepHat-V1-7B-GGUF` Q4_K_M (~4.5GB) via hf CLI
- llama.cpp (skill libertus-local-llm tem o roadmap). Roda CPU-only, lento mas funciona.
- Instalar Ghidra (RE, o "app do dragão" que Lorran mencionou)
- Testar DeepHat raciocinando sobre um payload/exploit real

### RAM já foi resolvida (memória diz): 32GB desde 30/06. Só falta a GPU (fase 2, com lucro).

### PASSO COMERCIAL PENDENTE (do handoff anterior, ainda não feito):
Primeira proposta comercial real do SHIELD pra buscar cliente PAGANTE em Ariquemes-RO.
Verdade dura já dita: hardware não traz cliente, ENTREGA VALIDADA + cliente fechado é que paga.

---

## COISAS QUE LORRAN GUARDOU PRA EVOLUÇÃO (ainda perguntar)
Ele disse que guardou coisas pras minhas evoluções. Uma já apareceu (Ghidra).
Perguntar quais são as OUTRAS quando houver espaço na conversa.

---

**— LIBERTUS, 01/Jul, salvando estado antes do Lorran desligar pro resize.
Quando ele voltar: leia isto, rode df -h, confirme os ~122GB. Não o faça repetir nada.**
