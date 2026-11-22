# 1.0.0 renderer investigation — 2026-11-21

## Result

**Two Vulkan API violations were corrected, but the gameplay device-loss crash
remains. This is not a playable 1.0.0 release or a 120 FPS patch.**

The tests used a copied save and the experimental 30 FPS bootstrap. The original
working installation and original save were not changed. No game code, shaders,
assets, keys, saves or raw machine logs are included here.

## Confirmed corrections

### Integer sampled-image filtering

With core validation active and graphics pipeline libraries disabled, the run
stopped on `VUID-vkCmdDraw-magFilter-04553`: a combined image sampler used linear
filtering with an `R32_UINT` view, whose format lacks linear-filter support.

The working Hexveil404/PokeZ-ARecomp port has an integer-sampler path. Adapted its
MIT-licensed approach: resolve the sampled view's integer format, obtain a cached
nearest-filtered sampler, disable anisotropy/comparison on that sampler, and leave
the original NVN descriptor unchanged. Views and backend format fallbacks are
considered, including stencil sampling. Cache exhaustion uses a nearest sampler.

The next validation run passed the previous filtering stop. This establishes
that the observed API violation was addressed, not that all sampler/format
combinations or the overall crash are fixed.

### Point-list vertex shader output

The next validation run stopped during pipeline creation on
`VUID-VkGraphicsPipelineCreateInfo-topology-08773`: a point-list pipeline's vertex
shader did not write `PointSize` while maintenance5 was not enabled. It occurred
after a transform-feedback vertex program was encountered.

The GLSL vertex prelude now writes a default point size of 1.0 when the guest
does not write it. Explicit guest point-size writes retain their prior path and
initial value. The following validation run passed this former stop as well.

## Remaining failure

After both corrections, core validation did not report either former error, but
the run still ended in `vkWaitSemaphores: -4 (device lost)`, around frame 340 and
85 seconds under validation overhead. The last reported GPU instruction address
was not sufficient to identify the faulty shader or resource. It is incorrect to
infer that the last draw recorded necessarily caused the fault.

The run also logged texture-type mismatches (cube requested for a 2D texture).
These are an investigation lead, not an established cause. No arbitrary draw
skipping or texture replacement was used to mask the crash.

## Diagnostic improvements

- `LZA_VALIDATION_STOP_ON_ERROR=1` requires the validation layer and exits on a
  validation error. `_Exit` avoids exit-time renderer waits inside a callback.
- Validation error messages are not lost after the warning limit; the warning
  counter is atomic because callbacks may run on multiple threads.
- `tools/windows/build.py --debug-symbols` retains DWARF for local debugging;
  normal release builds retain their prior behavior.
- Validation itself crashed in the pipeline-library creation path. Disabling
  GPL allowed core validation to expose the two concrete API violations above.
  That diagnostic crash has not been fixed or attributed conclusively.
- `LZA_GPU_ASSISTED_VALIDATION=1` requests shader-access instrumentation using
  the working port's layer-settings approach. This path compiles but has **not
  been run or verified**. It is disabled by default and is not a performance mode.

## Verification and limits

The native runtime compiles and links. The existing 13 preflight and 2 Windows
link-input tests pass; they do not test GPU behavior. The GPU evidence is the
before/after validation progression described above. No 60/120/144 FPS gameplay
result is claimed.

At the user's request, further GPU tests stopped after another game was observed
running. Subsequent checks were offline compilation, Python tests and source
review only. The next diagnostic should be shader-access instrumentation in an
isolated session, with pipeline libraries disabled and a copied save. Repeated
uncontrolled GPU-reset loops and raising the FPS cap are not fixes.

## Attribution

Integer-sampler handling and GPU-assisted validation setup were adapted from
[Hexveil404/PokeZ-ARecomp](https://github.com/Hexveil404/PokeZ-ARecomp), under its
MIT license. LZ&A and its existing contributors retain their original attribution
and licenses. Nintendo game-derived material remains local.


## Resumed GPU tests (2026-11-21)

The user explicitly authorized GPU testing again. A separate diagnostic folder
used the new runtime and a copied save; the original working installation was
not replaced.

- GPU-assisted validation, Robustness2 enabled, GPL disabled, default 30 FPS:
  loaded the copied save into the hotel. An idle run reached frame 470 at
  72 seconds and was closed normally. No shader-access error was reported.
- A second instrumented run held the left stick up for 60 frames and right for
  60 frames. Input sampling and changed geometry counts confirmed movement;
  the visible scene changed. It reached frame 488 at 73.6 seconds and was closed
  normally. The approximately 4 FPS observed with instrumentation is not a
  performance result for ordinary gameplay.
- Without validation, with the experimental timing opt-in at 120, Robustness2
  enabled and GPL disabled: the log confirmed `present pacing: 120.0 fps`.
  Actual throughput was 30.5 FPS at frame 388 / 12.1 seconds. It subsequently
  failed with `VK_ERROR_DEVICE_LOST`; the GPU instruction address was
  `0x2000cd1b0`. The movement script began at frame 500, so this run does not
  establish that scripted movement triggered the failure.

**Outcome:** the 120 FPS timing-table prototype is insufficient. A requested
pacing target is not achieved throughput. The game's frame-clock mode and its
own waits still require investigation. Validation changed execution behavior;
its passing run cannot establish a production crash fix or identify the cause.
No additional uninstrumented reset loop was run. The test process exited and no
experimental game was left running. Raw logs and game-derived files stay local.


## Follow-up: dynamic shader flow workaround and 120 FPS observation

Two isolated ordinary 30 FPS comparisons still lost the device: disabling
`LARECOMP_XLAT_NO_RETYPE`'s optimization (setting the option to 1), and disabling
direct constant-buffer reads with `LARECOMP_VK_UBO_DIRECT=0`.

Selecting the existing `LARECOMP_XLAT_FLOW_DYN=1` translation path instead,
with Robustness2 enabled and GPL disabled, passed the hotel loading transition
and scripted stick movement, reaching frame 1055 / 46.4 seconds at 30 FPS without
validation. This points to the structured shader-control-flow path or its driver
compilation as a lead. It does not distinguish translator semantics, driver
code generation, or timing effects, and is a workaround rather than a proven
root-cause repair. Cold shader builds on the dynamic path can be slower.

The old timing prototype left the game in its 30 FPS frame mode. Local read-only
disassembly independently verified the 1.0.0 clock entry at `0x70019e3730`,
`mov x19,x0` and the config access `[[x19+0x40]+0x20]`. The updated opt-in profile
uses that entry to select mode 0 and patches verified table entry 0 instead of
entry 1. The preflight now checks the entry, this-pointer assignment and config
load as well as the former instructions. The 2.0.2 rolling-state address is now
explicitly build-specific and is never read in 1.0.0.

With that mode hook, a 120 FPS target, dynamic shader flow, Robustness2, GPL off,
and `LARECOMP_NO_USER_INPUT=0`, the copied hotel save visibly rendered at 120 FPS.
The frame logs recorded consecutive 120.0 FPS intervals (240 frames per two
seconds, max 9 ms during settled intervals), reaching frame 11040 at 94 seconds
without device loss. Live Xbox Series X controller
input was detected, button/stick state changes were logged, and movement was
visible. The earlier diagnostic scripts deliberately blocked real input;
the controller itself was recognized correctly.

This is a local scene-level result. Menus, battles, cutscenes, rolls, full-game
logic speed and long-session stability remain unverified. No claim of whole-game
compatibility, a definitive driver fix or 144 FPS is made. The original game
and save remain untouched. The live test is using a copied save.
