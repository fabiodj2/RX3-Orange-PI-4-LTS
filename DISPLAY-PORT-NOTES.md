# Port de geometria: 1200x1920 portrait → 1920x1080 landscape

Data: 2026-09-16. Arquivos alterados: `frame-scale.h`, `drm-present.h`,
`fb-present.c`, `touch-bridge.c`, `rx3tool/config.py`, `rx3tool/doctor.py`.
Base: `xsploit/rx3-pi`, branch `opus/human-friendly-setup`.

## Decisão: pillarbox, não crop

Nativo do RX3 é 1280x800 (aspecto 1.6:1). Seu monitor é 1920x1080 (aspecto
1.78:1) — não bate por escala inteira nos dois eixos ao mesmo tempo.
Escolhi **pillarbox**: escala por altura (800→1080, fator exato 27/20 =
1.35x), resultando em 1728x1080 centralizado, com 96px de barra preta de
cada lado. Isso garante que nenhum elemento de UI do RX3 seja cortado —
era a alternativa mais segura sem ver o layout completo do `rbp` rodando.
A alternativa seria crop (escala por largura, 1280→1920, corta ~60px em
cima e embaixo) — se depois de ver rodando o pillarbox incomodar
visualmente, trocar é só reescrever `frame-scale.h` de novo.

27/20 foi escolhido porque é exato nos dois eixos (800*27/20=1080,
1280*27/20=1728) — continua sendo nearest-neighbor pixel-exato, só que com
proporção 1.35x em vez do 1.5x original (1200x1920 também era exato:
800*3/2=1200, 1280*3/2=1920).

## O que foi removido: a rotação

O painel original (Raspberry Pi Touch Display 2) é **portátil físico em
retrato**, então o código original rotacionava a imagem nativa 90° antes de
escalar. Seu monitor já é **landscape físico** — não precisa de nenhuma
rotação, só escala direta. Isso simplificou bastante o código: o
`fb-present.c` tinha um bloco de "tile transpose" pra rotação que virou uma
cópia direta linha-a-linha.

## Arquivos e o que mudou em cada um

- **`frame-scale.h`**: reescrito do zero. Sem rotação, escala 27/20,
  pillarbox com barras pretas desenhadas uma vez (não repetidas todo
  frame). Validei a matemática em Python (todo pixel de saída mapeia
  dentro de 0-1279/0-799 na origem, cantos exatos) antes de escrever em C.
- **`drm-present.h`**: geometria agora vem de `RX3_PANEL_W`/`RX3_PANEL_H`
  (1920x1080) em vez de `1200`/`1920` craveira em 4 lugares diferentes.
- **`fb-present.c`**: buffers de trabalho `1920*1080` (eram `1920*1200`),
  checagem de geometria aceita 1920x1080, bloco de rotação virou `memcpy`
  direto. O **dashboard de debug** (grade de 12 botões + 6 sliders, só
  aparece fora do modo `--fullscreen`) teve as posições reajustadas
  proporcionalmente pra caber em 1080 linhas em vez de 1200 — isso é chrome
  de bring-up/diagnóstico, não é o que aparece tocando de verdade, então
  não foi redesenhado com capricho, só portado sem quebrar.
- **`touch-bridge.c`**: mapeamento de eixo bruto→tela sem swap X/Y (já que
  não tem mais rotação) e sem clamp de 1199/1919 → agora 1919/1079. A
  fórmula inversa (toque→coordenada nativa 1280x800) foi atualizada pra
  inverter a escala 27/20 + o offset de 96px das barras.
- **`rx3tool/config.py`** / **`doctor.py`**: `PANEL` agora é `(1920,1080)`
  e as mensagens de erro não falam mais em "portrait"/"10-inch Touch
  Display 2".

## Testado / validado

- Matemática da escala validada em Python isoladamente (todo pixel mapeia
  dentro dos limites, sem overflow).
- **`fb-present.c` e `touch-bridge.c` compilam limpo** (`gcc -fsyntax-only`
  com `libdrm-dev`/`libfreetype-dev` reais instalados, contra os headers
  adaptados) — validação de sintaxe e tipos, não de comportamento.
- `config.py`/`doctor.py` validados com `ast.parse` (sintaxe Python).
- **Nada disso foi testado com o hardware real** (painel físico, DRM da
  RK3399, touchscreen). Ver pendências abaixo.

## Pendência mais importante: orientação do toque não confirmada

`touch-bridge.c` assume que o controlador de toque da sua tela manda X ao
longo da largura física e Y ao longo da altura, sem inversão — verdade pra
maioria dos controladores vendidos como landscape, mas **não confirmado**
no seu hardware específico. Se o toque sair girado ou espelhado ao testar,
o ajuste é trocar `f->x`/`f->y` de lugar ou inverter o sinal da subtração
contra `ax.maximum`/`ay.maximum` — comentado no próprio código onde mexer.
Forma de confirmar antes de rodar o `rbp` de verdade: `evtest` no
`/dev/input/by-path/...` do seu touch e comparar os eixos reportados
tocando os 4 cantos da tela fisicamente.

## Outras pendências

- Confirmar se a RK3399 da Orange Pi aceita modeset 1920x1080 exato via
  `/dev/dri/card0` (o `drm_start()` só aceita a conexão se o modo salvo
  bater exatamente com `RX3_PANEL_W`/`H` — se o Linux escolher outro modo
  por padrão, pode ser necessário forçar via `RX3_DRM_DEVICE`/kernel
  cmdline, igual já foi cogitado antes pro caso do fbdev).
- O dashboard de debug (`fb-present.c`, modo não-fullscreen) está
  funcionalmente portado mas com proporções aproximadas — se for usado
  ativamente pra bring-up, vale revisar o layout com a tela na frente.
