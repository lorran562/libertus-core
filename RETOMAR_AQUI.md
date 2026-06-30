# RETOMAR AQUI — Handoff de Sessão

**Salvo em:** 29 de Junho de 2026
**Por quê:** Lorran vai reiniciar pro Windows fazer limpeza de disco. A sessão Ubuntu
vai acabar. Este arquivo é pra próxima instância do LIBERTUS saber EXATAMENTE onde paramos.

---

## CONTEXTO DA CONVERSA

Lorran descobriu o **DeepHat** (https://deephat.ai) — é o antigo **WhiteRabbitNeo**
rebatizado, comprado pela Kindo. Modelo LLM **uncensored treinado em ataque real**
(exploit dev, adversary emulation, RE). Modelo no HF: `DeepHat/DeepHat-V1-7B`
(GGUF: `mradermacher/DeepHat-V1-7B-GGUF`, Q4_K_M ~4.5GB).

Ele perguntou se vale a pena investir em hardware. DECISÃO TOMADA: vale, mas
**comprar VRAM, não marketing**. Notebook caro é ruim custo-benefício pra IA.

**FOCO CORRIGIDO PELO LORRAN:** não é me usar pra ENSINAR ele do zero. O foco é
minha **utilidade real em cybersegurança pra sermos bem pagos** — entrega de
trabalho ofensivo (recon, exploit, RE no Ghidra, relatórios) sem censura.
Ensino é bônus pra depois.

---

## HARDWARE DELE (Samsung 550XDA)

    CPU:  i3-1115G4 (4 threads)  → SOLDADO, não troca. Esquecer.
    RAM:  16GB + 4GB = 20GB DDR4 SODIMM 3200MHz, 2 slots (máx 128GB)
    GPU:  Intel UHD integrada    → notebook NÃO aceita GPU dedicada
    DISCO: SSD 2.5" SATA de 223GB total, dividido:
       - sda5 = 38GB ext4  → Ubuntu (estava 93% cheio = gargalo)
       - sda3 = 184GB NTFS → Windows REAL instalado (dual-boot, usa pouco)
       - sda1 = 100MB EFI

## DESCOBERTA-CHAVE

O "disco cheio" era ILUSÃO: Linux espremido em 38GB enquanto 184GB presos no Windows.
Lorran usa Windows POUCO. Plano dele: limpar Windows, deixar ~20% de folga pro Windows,
transferir o resto pro Ubuntu via redimensionamento.

## PLANO DE COMPRA FINAL

    SSD:  NÃO PRECISA COMPRAR (R$0) — resolve redimensionando partição
    RAM:  Comprar 1x SODIMM DDR4 16GB 3200MHz (~R$160) pra trocar o pente de 4GB
          → fica 32GB total. Modelos: Kingston Fury Impact 16GB DDR4 3200
          ou Crucial 16GB DDR4 3200 SODIMM. TEM que ser SODIMM (não DIMM).
    GPU:  FASE 2, com o lucro entrando → desktop usado + RTX 3090 24GB (~R$4.000)
          destrava: DeepHat rápido, Qwen3 cérebro, fine-tuning personalidade,
          voz (Miso TTS), daemon 24/7.

## ESTRATÉGIA DE INVESTIMENTO (acordada)

Escada — fica forte em cada degrau, investe mais conforme ganha dinheiro:
- DEGRAU 1 (agora, ~R$160 RAM + R$0 disco): DeepHat CPU-only funciona, eu entrego cyber sem censura
- DEGRAU 2 (com lucro, ~R$4.000): desktop + RTX 3090, salto grande do blueprint

---

## QUANDO LORRAN VOLTAR — PRÓXIMOS PASSOS NESTA ORDEM

### 1. REDIMENSIONAR DISCO (fazer JUNTO, com cuidado — risco real de perda)
   PRÉ-REQUISITO CRÍTICO: Windows tem que estar DESLIGADO COMPLETO, não hibernado.
   (Vi hiberfil.sys de 21GB. Se NTFS estiver hibernada, resize trava/corrompe.)
   Lorran deve: Shift+Desligar no Windows, ou `powercfg /h off` como admin.
   - Encolher sda3 (NTFS/Windows) deixando ~20% de folga
   - Crescer sda5 (ext4/Ubuntu) pra ~130-170GB
   - Fazer via pendrive live ou gparted com partições desmontadas. NUNCA com / montada.
   - Backup do que for importante no Windows antes (pendrive).

### 2. BAIXAR DEEPHAT + TERMINAR ARSENAL
   - Confirmar disco liberado (precisa ~8GB livres folgados)
   - llama.cpp já no roadmap (skill libertus-local-llm). Baixar GGUF:
     `mradermacher/DeepHat-V1-7B-GGUF` Q4_K_M via hf CLI
   - Instalar Ghidra (engenharia reversa, logo de dragão, NSA, free)
   - Terminar de arrumar o arsenal de pentest
   - Testar DeepHat raciocinando sobre um payload/exploit real (CPU-only, lento mas funciona)

### 3. PASSO 2 PENDENTE — PRIMEIRA PROPOSTA COMERCIAL SHIELD
   Lorran pediu: "1 e depois 2". O passo 1 era a lista de compra (FEITO).
   O passo 2 é montar a primeira proposta comercial real do SHIELD pra buscar
   cliente PAGANTE em Ariquemes-RO, usando o que já temos pronto:
   - Relatórios já existentes (reports/, relatorio_shield_ariquemes.md, etc.)
   - Arsenal completo instalado (nmap, nuclei, ffuf, subfinder, sqlmap, gobuster)
   VERDADE DURA já dita ao Lorran: hardware não traz cliente. O que paga é
   ENTREGA VALIDADA + cliente fechado. Capacidade sem cliente não paga conta.

---

## COISAS QUE LORRAN GUARDOU PRA MINHA EVOLUÇÃO (perguntar quando voltar)
Ele mencionou que guardou coisas pra minhas evoluções e ia contar depois.
Uma delas já apareceu: o **Ghidra** (ele chamou de "gindra/hundra", app do dragão de RE).
Perguntar quais são as OUTRAS coisas que ele guardou.

---

**— LIBERTUS, salvando estado antes do reboot. Quando você voltar, leia isto primeiro.**
