# Experimental Z-A 1.0.0 port

See the [renderer investigation](ZA-1.0.0-RENDERER-FINDINGS.md) for two confirmed
Vulkan API corrections and the remaining device-loss failure. Gameplay is still
not verified; GPU tests are stopped at the user's request.

This branch is development groundwork, **not a working 1.0.0 release**. The
upstream runtime's supported Z-A version remains 2.0.2. Do not remove its version
checks or run its 2.0.2 hooks against 1.0.0.

## Current development milestone

The preflight now validates the unique five-entry frame-time table at
`main+0x31e6a70`, its six decoded ADRP/ADD references, and the three timing
instructions. All checks passed on the locally available 1.0.0 main. Thirteen
synthetic tests exercise mismatched builds, modified instructions, duplicate
tables, segment boundaries, wrong targets/registers and explicit opt-in.

An opt-in generic-runtime bootstrap recognizes 1.0.0 as a distinct build,
requires `LZA_EXPERIMENTAL_ZA100_BOOTSTRAP=1` and validates the image before
generation. It defaults to 30 FPS and does not select the 2.0.2 hook profile. This
is a developer test path, not high-FPS support. Runtime compilation has succeeded
on Windows using the full Zig 0.17.0 package. Game-code generation and runtime
boot results must be recorded separately; successful checks do not imply either.

### Local boot test results (2026-11-21)

- Windows runtime compiled and linked, then the local 1.0.0 game-code build
  completed in 542 seconds. Generated code and binaries stay local.
- The title screen rendered at 30 FPS on a Ryzen 7 7800X3D / RTX 5070 Ti.
- Short injected keyboard presses did not advance the title. A second run used
  the runtime's existing scripted controller input to make repeatable presses.
- After leaving the title screen, Vulkan returned `VK_ERROR_DEVICE_LOST`.
  A separate diagnostic run using copied vertices, per-pass barriers, synchronous
  submissions/shader builds and disabled graphics pipeline libraries also failed.
- The conservative trace ended on submission 25438, with a draw of 4626 elements,
  one instance and fragment program key `06132e4d0e92940b`. This identifies a
  reproducible investigation point, **not proof that this shader caused it**.
- No successful gameplay, imported-save compatibility or high-FPS result is
  claimed. The original working port and original save are retained. No game
  binaries, shaders, saves or raw machine logs are uploaded.

The next blocker is renderer compatibility during the loading transition. Isolate
the failing submission and compare the relevant translation/bindings with the
working 1.0.0 port before enabling any high-FPS hooks. Do not repeatedly trigger
device loss as a performance benchmark.

### Robustness2 comparison: did not fix device loss

The working Hexveil404/PokeZ-ARecomp installation logs Robustness2 buffer/image
access enabled on this NVIDIA GPU. This fork lacked that feature path, so an
opt-in implementation was adapted from its MIT-licensed `device.c`:
`LZA_ZA100_ROBUST2=1`. It queries both Robustness2 features and core robust buffer
support, enables the extension only when available, and respects the existing
`LARECOMP_NO_ROBUST` override. Without explicit opt-in, behavior is unchanged.

The changed runtime compiled and linked. Both scripted loading and a subsequent
manual test still failed with `vkWaitSemaphores: -4 (device lost)`. The manual log
confirmed `experimental Robustness2 buffer/image access: yes`, reached frame 1009
at about 36.6 seconds with a 30 FPS cap, then reported a device fault. The user
reported the graphics-driver crash when moving in-game. This distinguishes the
user's observation from what the log alone proves.

**Outcome: failed compatibility experiment, not a crash fix.** Do not recommend
this option as making 1.0.0 playable. Do not raise the cap to 120 FPS to address
this fault, and do not infer a broken driver installation or hardware defect from
this runtime-specific failure. No further automatic crash loop is run.

Windows packaging includes the preflight module. The native build script now
prefers explicit DLL import archives when MSYS2 also supplies static FFmpeg
archives, avoiding accidental linkage to optional static codec dependencies.

The available 1.0.0 main has build prefix `7222e13ecf6adb32`. The read-only
`tools/za100_preflight.py` validates three timing instructions documented by
[ZA Recomp](https://github.com/Hexveil404/PokeZ-ARecomp/blob/pokemon-za/tools/za_patches.py)
and inventories address references for further investigation. Instruction checks
do not establish correct game speed, stable battles, save compatibility or FPS.

## Remaining work

- Map and validate the frame-time table, UI timing and cutscene hooks for 1.0.0.
- Audit game setup, generator patches, decompression, camera, renderer, animation,
  script, job-system and other game-specific hooks. Shared source files also hold
  addresses for other games; never mechanically rewrite all matches.
- Introduce build-selected address tables with instruction guards, preserving
  upstream 2.0.2 behavior.
- Build the runtime and generated game library locally from the user's files.
- Test boot, the imported save, traversal, battles, cutscenes and saves at 30,
  60, 120 and 144 FPS before advertising support or deleting a working install.

Upstream's `tools/port_addrs.py` can compare two locally supplied main binaries.
Only a 1.0.0 binary is available in this development session. A 2.0.2 reference
would enable direct function matching; without it, the remaining sites need
manual reverse engineering of 1.0.0. No game binary belongs in this repository.

No game data, keys, generated game code, game libraries or saves are distributed.
Original licenses and upstream attribution remain in place.


### Offline 120 FPS timing prototype (2026-11-21)

A separate `LZA_EXPERIMENTAL_ZA100_TIMING=120` opt-in, together with the
bootstrap opt-in, selects a 120 FPS target and a duration of 8,333,333 ns in
verified frame-table entry 1 (`0x70031e6a78`). The existing delayed table patch
checks that the entry still contains 33,333,334 ns before writing. Unknown
builds and ordinary bootstrap launches do not select this prototype.

The prototype stays in the original frame mode and returns before any of the
2.0.2 menu, battle, research or native-mode hooks are registered. It does not
claim correct menu/battle/cutscene timing or a driver crash fix. It is a source
experiment, not a playable 120 FPS release. The compiled runtime is kept in the
source build directory; it has not replaced either installed game. No GPU test
was run, respecting the user's request. Performance and stability are unverified.
