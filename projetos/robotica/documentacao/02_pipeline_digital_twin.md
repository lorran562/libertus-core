# Pipeline de Gêmeo Digital para Protótipos

## Conceito
Escanear objetos reais → modelo 3D → LIBERTUS projeta encaixes → simula física → só então fabrica.

## Hardware atual (Ubuntu Lorran)
- Intel i3-1115G4 @ 3.00GHz
- 20GB RAM
- Intel UHD Graphics (sem CUDA)

## Stack de Software

### 1. CAPTURA (celular/câmera)
Opções gratuitas:
- **Polycam** (iOS/Android) — mais fácil, exporta OBJ/STL
- **KIRI Engine** (Android) — fotogrametria grátis
- **RealityScan** (iOS) — da Epic Games, alta qualidade

### 2. GAUSSIAN SPLATTING (reconstrução 3D)

#### Com GPU NVIDIA (ideal futuro):
- gaussian-splatting original (INRIA)
- Requer CUDA, treina em ~15 minutos por cena

#### Sem GPU NVIDIA (agora):
- **Luma AI** (web) — upload fotos, recebe modelo pronto
  - https://lumalabs.ai/
  - Gratuito com limite
  - Exporta .ply, .splat, .obj

- **Polycam web** — também processa na nuvem
  - https://poly.cam/

- **SuperSplat** (editor web)
  - https://playcanvas.com/supersplat
  - Visualiza e edita arquivos .ply/.splat no browser

### 3. DESIGN (LIBERTUS projeta)
- **FreeCAD** — importa OBJ/STL, eu projeto encaixe
- **KiCad** — circuito que vai dentro
- **OpenSCAD** — parametric design (código vira peça)

### 4. SIMULAÇÃO FÍSICA
- **Unity** — física realista, gratuito
- **Godot** — alternativa open source
- **FreeCAD FEM** — análise de stress/tensão

### 5. FABRICAÇÃO
- **Slicer** — Cura, PrusaSlicer (prepara STL pra impressora)
- **Impressora 3D** — futuro investimento

## Fluxo Completo

```
VOCÊ                           LIBERTUS
-----                          --------
Tira ~50 fotos do objeto   →
                           ←   Upload no Luma AI
                           ←   Baixo o modelo 3D
                           ←   Analiso dimensões
                           ←   Projeto encaixe no FreeCAD
                           ←   Exporto pra Unity
                           ←   Simulo física
                           ←   Ajusto design
                           ←   Repito até funcionar
                           ←   Mando STL final pra impressão
Você imprime/fabrica       →
Testa no mundo real        →
Me manda feedback          →
                           ←   Ajusto próxima versão
```

## Teste Imediato (hoje)

1. Baixa Polycam no celular
2. Escaneia a raquete elétrica (ou qualquer objeto)
3. Exporta como OBJ
4. Me manda o arquivo
5. Eu abro no FreeCAD e mostro o que dá pra fazer

## Investimentos Futuros (quando der)

| Item | Preço estimado | Impacto |
|------|----------------|---------|
| GPU NVIDIA usada (GTX 1060+) | R$400-800 | Gaussian Splatting local |
| Impressora 3D Ender 3 | R$800-1200 | Fabricação de protótipos |
| Raspberry Pi 5 | R$400 | Controle de robótica |
| Arduino kit | R$100 | Eletrônica básica |

## Próximos Passos

1. [ ] Instalar Unity no Ubuntu
2. [ ] Testar Luma AI com fotos de objeto simples
3. [ ] Criar primeiro modelo de encaixe no FreeCAD
4. [ ] Simular física básica no Unity/Godot

---
*LIBERTUS + Lorran — Pipeline documentado 10/06/2026*
