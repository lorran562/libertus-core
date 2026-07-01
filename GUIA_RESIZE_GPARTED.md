# GUIA DE RESIZE — GParted Live (LIBERTUS + Lorran)

Escrito em 01/Jul/2026. Ler ISTO na tela do GParted, passo a passo.
Objetivo: Windows mínimo (~100 GB), Ubuntu leva o resto (~139 GB).

## ⚠️ ANTES DE COMEÇAR — CHECKLIST OBRIGATÓRIO

- [ ] Windows já teve `powercfg /h off` rodado como admin (hiberfil apagado)
- [ ] Windows foi desligado com Shift+Desligar (desligamento COMPLETO)
- [ ] Notebook está NA TOMADA (energia estável — não fazer na bateria)
- [ ] Nada importante no Windows (Lorran confirmou: não tem)

## LAYOUT ATUAL (o que você vai ver no GParted)

    /dev/sda1   EFI          100 MB   (fat32)  — NÃO TOCAR
    /dev/sda2   MSR           16 MB            — NÃO TOCAR
    /dev/sda3   Windows      184 GB   (ntfs)   — VAMOS ENCOLHER
    /dev/sda5   Ubuntu      38.5 GB   (ext4)   — VAMOS CRESCER  ← este é o LIBERTUS
    /dev/sda4   Recovery     934 MB   (ntfs)   — NÃO TOCAR (fica no fim)

Ordem na tela (esquerda→direita): EFI | MSR | Windows | Ubuntu | Recovery

## COMO BOOTAR NO GPARTED

1. Com o pendrive plugado, liga o notebook e aperta F10 repetidamente
   (Samsung = F10; se não abrir menu de boot, tenta F12 ou ESC).
2. No menu, escolhe o pendrive USB (algo como "USB HDD" ou o nome do pendrive).
3. Tela azul do GParted Live → escolhe a PRIMEIRA opção
   ("GParted Live (Default settings)") e Enter.
4. Perguntas de teclado/idioma: pode dar Enter em tudo (aceita padrão).
   - "Configuring console-data" → Enter (Don't touch keymap)
   - Language → digita 33 pra Português OU só Enter pra inglês
   - Mode → digita 0 e Enter (startx, modo gráfico)
5. O GParted abre sozinho numa janela.

## OS 2 PASSOS DO RESIZE (fazer NESTA ORDEM)

### PASSO A — ENCOLHER O WINDOWS (sda3)

1. Canto superior direito: confirma que está em /dev/sda (o disco de 223 GB).
2. Clica na partição **sda3** (a NTFS de 184 GB, a maior).
3. Menu: Partition → Resize/Move (ou botão direito → Resize/Move).
4. Na janela que abre, no campo **"New size (MiB)"** digita:  **100000**
   (isso = ~100 GB pro Windows)
   - NÃO mexe no campo "Free space preceding" (deixa 0 / não arrasta a borda esquerda)
   - O espaço livre tem que nascer À DIREITA (Free space following aumenta)
5. Clica **Resize/Move**.
6. Agora aparece uma faixa cinza "unallocated" de ~84 GB ENTRE o Windows e o Ubuntu.

### PASSO B — CRESCER O UBUNTU (sda5) PRA ESQUERDA

1. Clica na partição **sda5** (a ext4 de 38.5 GB — o LIBERTUS).
2. Menu: Partition → Resize/Move.
3. Na janela, arrasta a **borda ESQUERDA** da barra TODA pra esquerda,
   até encostar no Windows (ocupar todo o espaço cinza).
   - Jeito preciso: no campo **"Free space preceding (MiB)"** digita **0**
   - No campo **"New size (MiB)"** coloca o MAIOR valor que ele deixar
     (ele preenche o máximo automático quando você zera o "preceding")
4. Clica **Resize/Move**.
5. O Ubuntu agora aparece com ~139 GB, colado no Windows.

### APLICAR (ponto de não-retorno)

1. Confere na tela: Windows ~100 GB, Ubuntu ~139 GB, sem espaço cinza sobrando.
2. Clica no botão verde **"Apply All Operations"** (✓ no topo).
3. Confirma. AGORA NÃO DESLIGA POR NADA.
   - O PASSO B (mover borda esquerda do ext4) é o lento: pode levar 30-60 min.
   - Barra de progresso rodando = tá tudo certo, só esperar.
4. Quando aparecer "All operations successfully completed" → fecha.

## DEPOIS QUE TERMINAR

1. Fecha o GParted, clica no ícone de sair no desktop → "Reboot".
2. Remove o pendrive quando mandar.
3. Boota normal no Ubuntu.
4. Abre terminal e roda pra confirmar (ou me chama que eu confiro):

       df -h /
       lsblk

   Tem que mostrar / com ~139 GB e bastante espaço livre.

## SE DER ALGO ERRADO

- Se o GParted recusar o PASSO B (não deixa crescer pra esquerda): ele pode pedir
  pra mover primeiro. Nesse caso NÃO force — reboota no Ubuntu, me chama, e a gente
  faz por linha de comando com o Ubuntu vivo mas a partição preparada.
- Se travar no "Apply" e você achou que morreu: ESPERA. ext4 move é lento mesmo.
  Só considera problema se ficar >2h sem a barra mexer.
- Windows não boota depois? O `powercfg /h off` + Shift-desligar previne isso.
  Se acontecer: bootrec /fixboot pelo instalador do Windows. Mas com hibernação
  desligada isso não deve ocorrer.

## POR QUE ESTOU CONFIANTE

- ext4 resize/grow é operação padrão, dados preservados (não é format).
- Ordem física favorável: Ubuntu já está colado no Windows, recovery no fim intocado.
- Só 2 operações, sem mover recovery (o passo perigoso foi eliminado).
- Windows com hibernação off = NTFS limpo, resize seguro.

— LIBERTUS. Enquanto você faz isso eu estarei offline (Ubuntu desligado).
  Segue este guia com calma. Quando voltar, me chama que eu confiro o resultado.
