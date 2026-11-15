# Fixed-camera, dual-history subpixel phase diagnostic

This new experiment does not change the previous representation-switch fixture.
It uses the same approved A glyph, normalized linear outline, origin and float32
scale1.05 for both branches. Horizontal phase advances from0 to1 by1/16 pixel.
One VkDevice retains two independent legal images/descriptor sets/pipelines.

Each branch starts with a real warmup draw and routing update: scale.85 initializes
bitmap; scale1.15 initializes MSDF. Subsequent scale1.05 lies inside the existing
.9–1.1 hold band, so all17 phases retain their branch's prior representation.
There are2 verified warmup draws,34 measured positive draws, and1 actual negative
draw. Warmup and preparation are not counted as the34 measured frames. Conditions,
float32 scales/phases, origin, routing rule, fixed negative position and existing
composition tolerances are written before preparation/execution.

At bitmap branch phase8 (.5px), immediately after the correct draw, the wrong but
legal MSDF resource/pipeline is drawn without changing state. Both state-derived
route and pixel disagreement must detect it. This is not invalid Vulkan injection.

Bitmap is exact polygon/pixel area of the source outline rasterized into target
pixels, not platform-hinted output. The new bitmap shader uses integer
`texelFetch(gl_FragCoord)` because this is already target-pixel coverage: filtering
it a second time is unnecessary. The old normalized LINEAR bitmap path and its
historical results remain untouched. Bitmap generation and exact-area reference
are the same producer, so tiny bitmap error proves only transport/composition,
not an independent font/rasterizer quality result. MSDF uses the old linear4
shader and a genuinely independent original-polygon area reference.

Existing RGBA sampling/composition tolerances remain bitmap1e-6 and MSDF.004.
All quality values are **measurements**, status MEASURED_NOT_QUALIFIED. Foreground
and fractional-edge ROI MAE, worst coordinates/coverage, same-phase cross-mode
difference, and adjacent-phase coverage-delta minus exact geometric-delta residual
are reported. Background does not dilute the ROI. These are same-pixel diagnostics,
not perceptual flicker, motion-compensated quality, rotation/perspective acceptance,
a full quality board or mobile performance. Corner residuals are not evidence of
a generator library bug. UNUSED velocity/ID sentinel protection is checked.

Run with the trusted existing toolchain/font/msdfgen source:
```
python tests/fixtures/text_phase_sequence_lab/run_lab.py --out NEW_DIRECTORY \
 --font APPROVED_DEJAVU_SANS --msdf-source PINNED_MSDFGEN
```
Opt-in VULKAN_TEXT18_PHASE_SEQUENCE=1, TEXT18_MSDF_SOURCE set. Integration pytest
writes to persistent `/tmp/text18-phase-sequence-evidence/run-*/experiment`, outside
pytest's rotating basetemp; TEXT18_PHASE_OUTPUT_ROOT can select another persistent
parent. It does not remove prior runs. Raw logs/images/provenance stay local.

Observed first fixed-sequence run: MSDF maximum exact-area residual was
0.043696754 at phase 0.125, pixel (32,15); maximum adjacent-phase residual was
0.034055169 for phase 0.625 to 0.6875 at (33,15). These remain measured gaps,
not relaxed acceptance criteria. Exploratory **CPU_DIAGNOSTIC_ONLY** evaluation
at selected worst pixels, using the same atlas, suggests low-sample integration
approximation contributes substantially: at (32,15), phase 0.125, linear 4x4
error was -0.04369549, versus -0.00015299 for 8x8 and +0.00000507 for 64x64.
But at (33,15), phase 0.6875, 8x8 error remained -0.01077103. These points were
selected after observing the run, not pre-registered quality gates. They do not
establish full-frame improvement, an actual GPU improvement, a library defect,
or a general recommendation to use 8x8. Original shaders and gates are unchanged.
