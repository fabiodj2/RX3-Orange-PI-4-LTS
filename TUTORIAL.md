# Tutorial: RX3 na Orange Pi 4 LTS com DDJ-400 (port do xsploit/rx3-pi)

## Antes de tudo: o que eu não consigo fazer

Eu não tenho como logar no seu GitHub, criar fork nem dar `git push` por
você — não tenho token/credencial de conta sua, só consigo ler repositórios
públicos. A Parte 1 abaixo são comandos pra **você** rodar (no Mac ou na
Orange Pi, tanto faz, é só `git`). Depois disso é tudo seu, sob seu
controle.

## Mac ou Orange Pi pra compilar? → Orange Pi, sem Mac nenhum

Diferente do seu pipeline do PrimeBox (que usava Docker no Mac pra
cross-compilar o DirectFB), **esse repo (`rx3-pi`) foi desenhado pra
compilar direto no dispositivo alvo**. O próprio `README.md` dele instala
o cross-compilador ARM32 via `apt` *na Raspberry/Orange Pi* (que é ARM64) e
compila ali mesmo — sem Docker, sem Mac, sem cross-compile remoto. É o
caminho mais enxuto que existe pra esse projeto: um SSH na Orange Pi e
pronto.

---

## Parte 1 — Colocar os arquivos no seu fork

Isso roda em qualquer máquina com `git` e acesso à sua conta GitHub (o
mais simples é no seu Mac, onde você já deve estar logado).

```bash
# 1. Clonar seu fork (o que você já tem: fabiodj2/rx3-pi)
git clone https://github.com/fabiodj2/RX3-Orange-PI-4-LTS

# 2. IMPORTANTE: sua fork está no branch "main" (versão FLX6, sem o CLI
#    ./rx3). O trabalho todo que fizemos foi em cima da branch
#    "opus/human-friendly-setup" do repo original (tem o CLI, o rx3.conf
#    etc). Trazer essa branch pro seu fork primeiro:
git remote add upstream https://github.com/xsploit/rx3-pi.git
git fetch upstream opus/human-friendly-setup
git checkout -b orangepi4-ddj400 upstream/opus/human-friendly-setup

# 3. Baixe o pacote que eu gerei (orangepi4-ddj400-port.tar.gz, no card
#    de arquivos desta conversa) e extraia DENTRO do checkout, na raiz
#    (ele já tem a estrutura de pastas certa, incluindo rx3tool/):
tar xzf ~/Downloads/orangepi4-ddj400-port.tar.gz -C .

# 4. Conferir o que mudou
git status
#   novos:      ddj400-rx3.py, frame-scale.h (modificado), drm-present.h
#               (modificado), fb-present.c (modificado), touch-bridge.c
#               (modificado), DDJ400-PORT-NOTES.md, DISPLAY-PORT-NOTES.md
#   modificados: rx3tool/config.py, rx3tool/doctor.py, rx3tool/mapping.py,
#               rx3tool/launch.py

# 5. Commit e push pro seu fork
git add -A
git commit -m "Port: Orange Pi 4 LTS (1920x1080 landscape) + DDJ-400"
git push -u origin orangepi4-ddj400
```

Depois disso seu fork tem um branch `orangepi4-ddj400` com tudo. É esse
branch que você vai clonar na Orange Pi.

---

## Parte 2 — Preparar a Orange Pi

SSH na Orange Pi (`ssh root@192.168.15.10`, pelo IP fixo que você já usa).

```bash
# Dependências de build (cross-compilador ARM32 + libs nativas ARM64
# pro rx3-fb-present/rx3-touch-bridge, que rodam NA Orange Pi em ARM64)
apt update
apt install -y build-essential pkg-config libdrm-dev libfreetype-dev \
  gcc-arm-linux-gnueabi binutils-arm-linux-gnueabi \
  python3 python3-cryptography unzip libarchive-tools alsa-utils git

# Confirme o cross-compilador instalado
arm-linux-gnueabi-gcc --version
```

```bash
# Clonar o SEU fork, branch que você acabou de criar
cd ~
git clone --branch orangepi4-ddj400 https://github.com/fabiodj2/rx3-pi.git
cd rx3-pi
```

---

## Parte 3 — Configurar (`rx3.conf`)

```bash
./rx3 config init
```

Isso cria `rx3.conf` a partir do `rx3.conf.example`. Edite:

```bash
nano rx3.conf
```

Ajustes necessários (o resto pode ficar em `auto`):

```ini
[display]
# auto já deve detectar seu monitor 1920x1080 (PANEL foi mudado pra isso
# no config.py que veio no pacote) — só mude se ./rx3 doctor reclamar.
drm_device = auto

[audio]
# PRECISA CONFIRMAR — plugue o DDJ-400 e rode antes de editar:
#   cat /proc/asound/cards
# Vai aparecer algo como "1 [DDJ400]: USB-Audio - DDJ-400" — use o texto
# entre colchetes exatamente como aparece.
card = DDJ400

[controller]
# Confirme o nome exato com o controlador plugado:
#   amidi -l
# deve listar algo tipo "DDJ-400 MIDI 1" — meta o nome que aparecer ali.
midi_name = DDJ-400
# deixe "mapping" como está (work/Pioneer-DDJ-400.midi.xml) — o
# ./rx3 mapping (Parte 5) baixa esse arquivo sozinho.
```

---

## Parte 4 — Firmware (vocês já têm o 1.19)

Como você confirmou que já tem o firmware 1.19 sem problemas, pule pro
`./rx3 recover` apontando pros arquivos que você já tem, em vez de deixar
baixar da internet:

```bash
# Se você já tem os .zip oficiais da Pioneer/AlphaTheta baixados:
./rx3 recover --from /caminho/onde/estao/os/zips --offline

# Ou, se preferir deixar baixar de novo (não precisa se já tem):
./rx3 recover
```

Confira o resultado:

```bash
./rx3 doctor --stage recover
```

---

## Parte 5 — Montar o runtime, buscar o mapeamento, compilar

```bash
# Monta o diretório de runtime (chroot) a partir do firmware recuperado
./rx3 assemble

# Baixa o Pioneer-DDJ-400.midi.xml oficial do Mixxx (já reconfigurado
# no mapping.py pra isso, em vez do FLX6) e valida contra o ddj400-rx3.py
./rx3 mapping

# Compila: os helpers ARM64 nativos (rx3-fb-present, rx3-touch-bridge)
# E o shim ARM32 que roda dentro do chroot (usa arm-linux-gnueabi-gcc)
./rx3 build

# Instala o player patchado + shim dentro do runtime montado
./rx3 install
```

---

## Parte 6 — Checagem geral antes de rodar

```bash
./rx3 doctor
```

Isso confere tudo: firmware, build, runtime, dispositivos (display, touch,
áudio, MIDI). Resolva qualquer `FAIL` antes de seguir. Pontos que exigem
atenção especial no seu caso:

- **Toque**: antes de rodar de verdade, verifique a orientação dos eixos
  do seu touchscreen (isso está marcado como não confirmado no
  `DISPLAY-PORT-NOTES.md`):
  ```bash
  ls -l /dev/input/by-path/          # ache o device do seu touch
  apt install -y evtest
  evtest /dev/input/by-path/SEU-DISPOSITIVO
  ```
  Toque os 4 cantos físicos da tela e veja se X cresce da esquerda pra
  direita e Y de cima pra baixo. Se sair invertido/trocado, me avise que eu
  ajusto o `touch-bridge.c` (está comentado no código exatamente onde
  mexer).

- **Validação do runtime**:
  ```bash
  ./rx3 validate
  ```

---

## Parte 7 — Rodar

```bash
./rx3 start
```

Isso sobe player, display (`rx3-fb-present --fullscreen`), touch e a
ponte MIDI (`ddj400-rx3.py`) juntos. Acompanhe:

```bash
./rx3 status
```

Pra parar:

```bash
./rx3 stop
```

---

## Se algo quebrar

- **Tela cortada/deslocada**: a escala pillarbox é 27/20 com 96px de
  barra preta de cada lado — se sair diferente disso, o modo DRM que a
  Orange Pi escolheu pode não ser exatamente 1920x1080. Rode
  `cat /sys/class/drm/card0-*/modes` pra ver o que está disponível.
- **Sem áudio**: confira se `card` em `rx3.conf` bate exatamente com o
  nome entre colchetes de `cat /proc/asound/cards` — é case-sensitive.
- **MIDI não responde**: confira `amidi -l` de novo com o controlador já
  plugado ANTES de rodar `./rx3 start` (o `midi_name` no `rx3.conf` precisa
  bater com o nome ali).
- **Erros do `./rx3 doctor`**: a ferramenta é bem específica sobre o que
  falta — geralmente aponta o comando exato pra corrigir.

Qualquer coisa que travar, me manda o output de `./rx3 doctor` e do passo
que falhou que eu ajudo a debugar daqui.
