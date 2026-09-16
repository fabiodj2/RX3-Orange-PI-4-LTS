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

## Parte 1 — Obter a branch integrada

Isso roda em qualquer máquina com `git` e acesso à sua conta GitHub (o
mais simples é no seu Mac, onde você já deve estar logado).

```bash
# A branch já contém a base completa do xsploit/rx3-pi e as adaptações.
git clone --branch orangepi4-ddj400-integrated \
  https://github.com/fabiodj2/RX3-Orange-PI-4-LTS.git
cd RX3-Orange-PI-4-LTS
```

Não extraia `orangepi4-ddj400-port.tar.gz` sobre o repositório: o pacote
antigo continha somente a camada customizada e podia sobrescrever correções
mais novas do projeto original.

---

## Parte 2 — Preparar a Orange Pi

SSH na Orange Pi (`ssh root@192.168.15.10`, pelo IP fixo que você já usa).

```bash
# Dependências de build (cross-compilador ARM32 + libs nativas ARM64
# pro rx3-fb-present/rx3-touch-bridge, que rodam NA Orange Pi em ARM64)
apt update
apt install -y build-essential pkg-config libdrm-dev libfreetype-dev \
  gcc-arm-linux-gnueabi binutils-arm-linux-gnueabi libc6-dev-armel-cross linux-libc-dev \
  python3 python3-cryptography unzip libarchive-tools alsa-utils util-linux git

# Confirme o cross-compilador instalado
arm-linux-gnueabi-gcc --version
```

```bash
# Clonar o SEU fork, branch que você acabou de criar
cd ~
git clone --branch orangepi4-ddj400-integrated \
  https://github.com/fabiodj2/RX3-Orange-PI-4-LTS.git
cd RX3-Orange-PI-4-LTS
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
# auto deve detectar o conector que anuncia exatamente 1920x1080.
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
# deve listar algo tipo "DDJ-400 MIDI 1" — use uma parte única do nome.
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
./rx3 selftest
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

O lançador aplica `RLIMIT_RTPRIO=95` e `RLIMIT_MEMLOCK=unlimited` antes de
entrar no chroot. Isso é necessário porque o player cria threads `SCHED_RR`
(prioridade 36 observada no diagnóstico da Orange Pi). Não edite
`/etc/security/limits.conf` para contornar esse ponto: a execução por
`sudo chroot --userspec` não abre uma nova sessão PAM confiável para aplicar
esse arquivo.

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
