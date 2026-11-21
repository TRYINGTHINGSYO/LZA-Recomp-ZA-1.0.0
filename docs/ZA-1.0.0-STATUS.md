# Experimental Z-A 1.0.0 port

This branch is development groundwork, **not a working 1.0.0 release**. The
upstream runtime's supported Z-A version remains 2.0.2. Do not remove its version
checks or run its 2.0.2 hooks against 1.0.0.

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
