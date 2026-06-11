# Projeto Base: Raquete Elétrica como Módulo de Potência

## Conceito
Usar o circuito de raquete elétrica de mosquito como base para projetos de alta voltagem de baixo custo.

## Como funciona a raquete elétrica

```
[Pilhas 3V] → [Oscilador] → [Transformador] → [Multiplicador] → [Grade 2000-3000V]
                  ↑
            Botão de ativação
```

### Componentes internos:
1. **Fonte**: 2x pilhas AA (3V total)
2. **Oscilador**: Transistor + resistor (gera AC a partir de DC)
3. **Transformador elevador**: Aumenta de 3V para ~400V
4. **Multiplicador de tensão**: Cascata de diodos + capacitores (Cockcroft-Walton)
5. **Capacitor de saída**: Armazena a carga para descarga instantânea
6. **Grade**: 3 camadas de fio (externa-, central+, externa-)

### Por que não mata humanos:
- Alta voltagem (2000-3000V)
- Mas baixíssima corrente (~1mA)
- Energia total: ~0.05 Joules (precisa de ~1J pra ser letal)

## Modificações possíveis

### Nível 1: Mais potência de descarga
- Adicionar capacitores em paralelo
- Resultado: Descarga mais forte, mesmo voltage

### Nível 2: Mais voltagem
- Adicionar estágios ao multiplicador
- Cada estágio = +2x a voltagem de entrada do estágio
- Resultado: Arco elétrico maior

### Nível 3: Integração com controle
- Substituir botão físico por relé/MOSFET
- Controlar via Arduino/ESP32
- Resultado: Disparo programável, remoto, ou por sensor

## Aplicações

1. **Arco elétrico para ignição** — acender fogo sem fósforo
2. **Cerca elétrica mini** — proteção de área pequena
3. **Ferramenta de gravação** — arco controlado em superfície
4. **Módulo de defesa** — integrado em braço robótico
5. **Experimentos de plasma** — arco entre eletrodos em gás

## Segurança

⚠️ ALTA VOLTAGEM — pode causar:
- Queimadura por arco
- Choque (não letal mas doloroso)
- Incêndio se perto de inflamáveis

Sempre:
- Descarregar capacitores antes de mexer
- Usar luvas isolantes
- Não apontar pra pessoas/animais

## Próximos passos

1. [ ] Desmontar uma raquete e fotografar circuito
2. [ ] Identificar cada componente
3. [ ] Desenhar esquemático no KiCad
4. [ ] Simular modificações no LTspice
5. [ ] Prototipar versão modificada

## Custo estimado

- Raquete elétrica: R$15-30
- Capacitores extras: R$5-10
- Arduino Nano: R$25
- Total inicial: ~R$50

---
*LIBERTUS + Lorran — Projeto iniciado 10/06/2026*
