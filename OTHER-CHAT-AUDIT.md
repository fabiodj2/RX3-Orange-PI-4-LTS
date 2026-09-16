# Audit of the previous Orange Pi bring-up

This note separates terminal evidence from hypotheses made in the earlier
Claude/Gemini conversations.

## Evidence retained

- Target: Orange Pi 4 LTS, RK3399, Armbian 26.8.3 trixie, aarch64.
- Kernel uses 4 KiB pages and successfully executes an ARM32 probe.
- RX3 firmware/player pin is 1.19 and the runtime validates its hashes.
- HDMI DRM mode is 1920x1080; the USB touchscreen is detected.
- ALSA identifies the controller as `DDJ400`; MIDI is visible as DDJ-400.
- Four-channel `speaker-test -D hw:DDJ400 -c 4 -r 44100` reached channel
  playback, so the two-channel `Invalid argument` result was not proof of a
  broken USB driver.
- Normal startup repeatedly exited after the shim printed
  `completed-frame publisher installed`.
- A manual run printed `UniNo=0x0000000d, Val=0xfffffffb` and ended in
  `SIGSEGV`.
- In the captured `strace`, immediately before that error, the player created
  a thread and `sched_setscheduler(..., SCHED_RR, {36})` failed with `EPERM`.

## Important limitation of the captured strace

The command shown in the conversation was:

```sh
strace -f /root/pdj/rbp-pi -a
```

It omitted `LD_PRELOAD=/lib/fbshim.so`, so it did not reproduce the same
process launched by `./rx3 start`. It is useful evidence for the player's
real-time requirement, but cannot prove that ALSA, DRM, or the shim caused the
integrated startup failure.

On 32-bit ARM, syscall 283 is `connect()`. The observed
`SYS_283(...) = -1 ENOENT` therefore does not demonstrate an ALSA timer error;
it is compatible with an absent Unix socket and needs a correctly decoded,
shim-enabled trace before interpretation.

## Rejected unsupported conclusions

The available logs do not establish any of the following:

- an RK3399/Armbian ALSA timer emulation bug;
- a required fixed linker base for `fbshim.so`;
- a missing `pi-clock.bin` inside `root/pdj` (the patcher embeds its code into
  `rbp-pi`; it is not a runtime sidecar requirement);
- a missing `/var/run/fb.conf`;
- a loopback/hostname failure;
- a need to ignore a player process that has actually exited;
- a need to replace direct ALSA with PulseAudio.

## Corrected launch behavior

The integrated launcher now runs the privileged portion as:

```sh
sudo prlimit --rtprio=95 --memlock=unlimited -- chroot --userspec=... ...
```

The limits are established before `chroot --userspec` drops privileges, so
the native player can create its priority-36 `SCHED_RR` thread. This is more
deterministic than editing `/etc/security/limits.conf`, because this launch
path does not create a normal login session for the target user.

`./rx3 doctor` performs a harmless privileged `prlimit ... true` probe and
blocks startup with a specific explanation if the board cannot grant those
limits. Startup failures now report the actual exit status or terminating
signal.

## Next hardware acceptance test

Use a clean checkout of the integrated branch. Do not reuse the manually
edited `rx3`, `launch.py`, runtime `asound.conf`, fake network files, or
`fb.conf` from the earlier attempts.

Run:

```sh
./rx3 stop
./rx3 selftest
./rx3 doctor
./rx3 start
```

If startup still fails, preserve all four files in `work/state/logs/` and the
complete new failure message. Do not suppress the liveness check: a dead
player cannot be made functional by allowing the display/MIDI helpers to
continue.
