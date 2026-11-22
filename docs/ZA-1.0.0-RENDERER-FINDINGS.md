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
