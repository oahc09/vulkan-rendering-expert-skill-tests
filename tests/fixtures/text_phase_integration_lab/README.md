# Actual GPU higher-grid subpixel integration diagnostic

This experiment first executes the unchanged phase-sequence fixture as a fresh
linear4 baseline. It reuses its exact atlas, float32 transforms, target-pixel
bitmap inputs and compiled state-routing executable, changing only the MSDF
fragment shader in separate linear8 and linear16 shader directories. Each mode
runs in its own process/device; within each mode the two representation branches
share the actual Device and persistent resource/pipeline objects. This is not a
same-submission three-mode comparison.

Each mode executes the same 2 real history-initializing warmups, 34 measured
frames (17 identical horizontal phases per retained bitmap/MSDF state), and one
legal wrong-hold representation draw. The original routing events must match.
There are 102 measured positive frames across three modes, not 102 independent
layouts. Bitmap uses the original target-pixel texelFetch; the distance atlas and
its fixed range 4 are unchanged. Each new integration grid uses stratified pixel
subsamples and linear coverage scaled to each subpixel footprint, averaged over
64 or 256 samples rather than the original 16.

Independent CPU bilinear/median integration predicts all RGBA channels, retaining
MSDF tolerance .004 and bitmap 1e-6; exact auxiliary sentinels remain required.
The CPU shortcut only excludes pixels whose entire contributing atlas texel
range is already saturated with the correct sign and subpixel coverage margin.
Actual GPU image coverage is separately compared to exact original-polygon pixel
area, and adjacent-frame coverage deltas subtract exact geometry motion. Both
foreground and edge ROI errors and worst points are reported, not diluted by
background. The target-pixel bitmap and area reference have the same producer;
its small residual verifies storage/composition, not independent font quality.

All quality results remain MEASURED_NOT_QUALIFIED. No new quality threshold or
required improvement is imposed; regressions remain in the report. Existing
numerical gates are not loosened. Sample counts are static algorithmic work,
NOT measured latency, throughput, energy, mobile cost or a recommendation to use
256 samples. This fixed A, fixed-camera phase sweep is not rotation/perspective,
perceptual flicker or full dynamic-quality qualification. Prior CPU point studies
are motivation only; this fixture's comparisons use actual GPU readbacks.

Use the trusted toolchain/font/pinned msdfgen environment:
```
VULKAN_TEXT18_PHASE_INTEGRATION=1 TEXT18_MSDF_SOURCE=/trusted/pinned-msdfgen \
 python -m pytest tests/test_text18_phase_integration_lab.py
```
Outputs persist under /tmp/text18-phase-integration-evidence/run-*/experiment.
Raw images, inputs, source hashes and nested tool/driver receipts remain local.
Original fixtures are never edited. Minimum numerical reports may be published.

First measured sweep (not a new threshold): linear4 / linear8 / linear16 worst
exact-area errors were 0.043696754 / 0.013053457 / 0.012661063, and worst temporal
geometry-subtracted residuals 0.034055169 / 0.010916074 / 0.006532144. Higher-grid
worst points moved to (37,27), with substantial remaining error; more samples do
not remove all distance-field/reconstruction approximation. These fixed-sequence
extrema do not establish universal per-pixel improvement or a defect in msdfgen.
The unchanged per-case records, not these rounded extrema, are the evidence.
In particular, linear16 is NOT monotonically better: its per-frame maximum error
exceeds linear4 at phase .25/.5/.75 by approximately .000446/.000443/.000443, and
exceeds linear8 at 9 of the 17 phases. Linear8's per-frame maxima are smaller than
linear4 in this fixed sweep only. No mode is promoted to a general recommendation.
