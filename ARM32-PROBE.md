# ARM32 compatibility probe on an ARM64 Orange Pi

`rx3-arm32-probe` is a dynamically linked ARMv7 executable. It is linked
against the same ARM32 libraries recovered from RX3 firmware and installed at
`/usr/local/bin/rx3-arm32-probe` inside the runtime.

Run it on the target board after build/install and with the DDJ-400 connected:

```bash
./rx3 stop
sudo -v
./rx3 probe
```

The launcher temporarily prepares the same `/dev/snd` and `/proc/asound`
mounts used by the player, applies `RLIMIT_RTPRIO=95` and unlimited memlock,
enters the firmware chroot, drops to the configured player UID/GID/groups and
executes the ARM32 binary through `/lib/ld-linux.so.3`. Mounts are released on
success or failure. `./rx3 start` repeats this probe automatically.

Expected result:

```text
PASS arm32-pointer-size
PASS pthread-futex
PASS sched-rr
PASS mlock
PASS posix-mqueue
PASS alsa-4ch-44100-s16
RESULT PASS (0 failures)
```

The checks establish:

- native AArch64 kernel compatibility with ARMv7 userspace;
- working ARM32 dynamic loader and firmware libraries;
- thread creation and contended pthread synchronization (futex path);
- real-time scheduling after privilege dropping;
- locked memory under the player's inherited limits;
- POSIX message-queue syscalls used by the firmware;
- ARM32 ALSA library/ioctl compatibility with the DDJ-400's four-channel,
  44.1 kHz, signed 16-bit playback profile.

This is a compatibility gate, not a claim that every proprietary player path
has been exercised. A PASS should be followed by the player startup and
physical master/cue, display, touch and MIDI acceptance tests.
