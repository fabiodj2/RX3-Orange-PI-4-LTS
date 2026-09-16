# Port do bridge MIDI: DDJ-FLX6 → DDJ-400 (RX3 on Pi/Orange Pi)

Data: 2026-09-16. Base: `flx6-rx3.py` do `xsploit/rx3-pi`, branch
`opus/human-friendly-setup`. Resultado: `ddj400-rx3.py`.

**Fonte de verdade usada:** `res/controllers/Pioneer-DDJ-400.midi.xml` e
`-script.js` oficiais do `mixxxdj/mixxx` (clonados direto do GitHub em
2026-09-16), **não** o `ddj400-rx3.py` mencionado no Issue #2 do
`xsploit/rx3-pi` — aquele arquivo nunca foi publicado no repositório, só
existiu no fork local de quem abriu a issue. Todo endereço MIDI (status +
note) e toda decisão abaixo vêm de ler o XML de verdade, não de suposição.

**Teste feito:** `python3 ddj400-rx3.py --check-mapping --mapping
Pioneer-DDJ-400.midi.xml` carregou **117 bindings sem conflito de endereço**
(FLX6 original carrega ~126). Isso só valida o parsing/estrutura — nenhum
teste foi feito com o controlador físico ou com o `rbp` rodando.

## O que foi mapeado 1:1 (mesmo código nativo RX3 do FLX6)

Jog (turn/touch/search), tempo slider (MSB/LSB), play, cue, loop in/out,
reloop, pfl (headphone cue), trim (pregain), EQ (parameter1-3), volume,
crossfader, headphone mix, load, hot-cues (pads 1-8), beat-loop (pads em
modo loop), beat-jump (pads em modo jump), browse (rotacionar + apertar pra
entrar), cycle tempo range, shift.

Os códigos nativos (`0x4101`, `0x410c`, `0x4305` etc.) são do firmware do
RX3, não do controlador — por isso são os mesmos do `flx6-rx3.py` sem
alteração.

## O que foi mapeado via combinação SHIFT (endereço MIDI próprio, confirmado)

Diferente do que eu temia inicialmente, o DDJ-400 **não** depende de lógica
em JavaScript pra combos de SHIFT — o firmware do controlador já manda uma
nota MIDI distinta pra cada combinação. Confirmado lendo o XML:

| Ação | Nota sem SHIFT | Nota com SHIFT | Resultado |
|---|---|---|---|
| Quantize (Deck1) | CUE = `0x90/0x0C` | `0x90/0x68` (`toggleQuantize`) | mapeado → nativo `0x410b` (quantize) |
| Voltar no browse | Encoder press = `0x96/0x41` | `0x96/0x42` (`MoveFocusBackward`) | mapeado → nativo `0x420d` (back) |
| Sync toggle vs. set-master | `syncPressed` = `0x90/0x58` | `syncLongPressed` = `0x90/0x5C` (**long-press**, não shift) | mapeado → `sync_enabled` (0x4112) / `sync_leader` (0x4111) |

O sync é *long-press*, não shift — o firmware do DDJ-400 já distingue toque
curto de toque longo e manda notas diferentes, o que resolveu sozinho o
que no FLX6 eram dois botões físicos separados.

## Pendências — NÃO mapeado, e por quê (duas categorias diferentes)

**1. Sem botão físico no DDJ-400 (o FLX6 tem, o 400 não tem):**
`slip_enabled` (SLIP dedicado), `keylock` (KEYLOCK dedicado), `PrepareView`
/`PrepareToggle` (VIEW/PREPARE dedicados). Não existe *nenhuma* entrada
para essas funções em lugar nenhum do XML oficial do DDJ-400 — o hardware
não tem esses botões. Pra ter essas funções vai ser preciso **roubar** uma
combinação SHIFT de algum botão que hoje faz outra coisa (ex.: SHIFT +
algum pad, SHIFT + algum botão de loop) — isso é uma decisão de produto que
precisa do controlador físico na mão pra não quebrar um fluxo mais usado.
Não inventei nenhuma combinação aqui de propósito.

**2. Botão físico existe, mas o código nativo do RX3 não está confirmado:**
`quickJumpBack/Forward`, `cueLoopCallLeft/Right`, `toggleLoopAdjustIn/Out`,
`increase/decreaseBeatjumpSizes`, `beatFx*` (toda a seção Beat FX), banco
de pad "sampler" (`samplerPadPressed`). Todos têm endereço MIDI próprio e
confirmado no XML — o que falta é o comando nativo do RX3 correspondente.
`pad-intent.h` aceita bancos de pad de 0 a 7 (hoje só usamos 0,1,3), então
um banco "sampler" é plausível, mas o número certo não está documentado em
lugar nenhum deste repositório — teria que ser descoberto via engenharia
reversa do `rbp` (strings, tabela de pad modes em `native-pad-modes.c`) ou
testado por eliminação no hardware. Não chutei nenhum valor.

## Premissas assumidas sem confirmação em hardware real

- **Resolução do jog wheel**: assumido 7200 pulsos/volta, igual ao FLX6
  (`pulse()`). DDJ-400 usa encoder óptico Pioneer padrão, mas isso não foi
  verificado - se a sensação de scratch ficar errada (rápida/lenta demais),
  é o primeiro lugar pra olhar.
- **Passo do grid-jog (SHIFT+jog em modo edição de grid)**: assumido igual
  ao FLX6 (5ms por passo a cada 16 ticks). O DDJ-400 manda a mesma forma de
  CC relativo (`jogSearch`, nota `0xB0/0x29`), mas a proporção não foi
  testada.

## Próximos passos sugeridos

1. Testar `--check-mapping` já validado; próximo é `--replay` com uma
   captura MIDI real do DDJ-400 físico (gravar com `amidi -d` batendo nos
   botões) pra confirmar que os endereços realmente disparam o que se
   espera.
2. Com o controlador físico em mãos, decidir as combinações SHIFT pra
   slip/keylock/prepare-view da categoria 1 acima.
3. Descobrir os códigos nativos da categoria 2 (beat-fx, quick-jump,
   sampler) — provavelmente via strings/disassembly do `rbp` ou testando
   valores por eliminação em ambiente controlado.
4. Confirmar resolução do jog e proporção do grid-jog contra o
   comportamento físico real.
