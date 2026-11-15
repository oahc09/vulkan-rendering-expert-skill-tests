# Bounded stateful bitmap / MSDF switching

One actual shaped A glyph from the hash-approved font supplies a single normalized
outline and fixed layout. Bitmap means exact polygon/pixel intersection coverage
of this unhinted linear outline, not a platform-hinted FreeType raster or an entire
Text Quality Board. MSDF uses the same source outline and pinned official generator,
with the already examined linear4 shader. No font/source redistribution.

One VkDevice retains two separately created legal images, descriptor sets and
pipelines. A ten-frame scale/phase sequence actually selects and binds the resource
and pipeline indicated by a persistent state. Initial state is bitmap. At scale
<=.9 choose bitmap; at >=1.1 choose MSDF; strictly between retain preceding state.
Thus identical1.05 scales produce distinct routes depending on history. These
numbers are prewritten laboratory scheduling conditions, not universal typography
quality thresholds. There is no cache-service/reuse claim: the current selected
image is safely uploaded after the previous draw completed each frame.

The bitmap is rasterized in target pixel coordinates for the same source shape,
scale and phase, while MSDF samples the canonical atlas through the corresponding
inverse transform. Neither representation changes glyph identity/layout. Exact A
area is an independent reference for MSDF but also the bitmap's source; therefore
bitmap agreement validates transport/composition, not a second independent
rasterizer. The bitmap composition tolerance remains1e-6 from the bitmap lab;
linear4 sampling/composition uses its earlier.004 tolerance. Reference quality
errors are measured, never substituted as a new pass gate. The output status is
MEASURED_NOT_QUALIFIED and old baselines/criteria remain unchanged.

At fixed hold frame2, immediately after the correct bitmap draw, a legal wrong
MSDF resource/pipeline is actually drawn without changing the state. Both the
state-derived route mismatch and expected bitmap pixel difference must reject it.
This does not inject invalid Vulkan usage. UNUSED velocity/ID preservation is
checked; active MRT/depth/combined pending consumers are separate experiments.
No rotation, perspective, platform-hinted comparison, temporal quality acceptance,
mobile performance or complete renderer-state restoration is claimed.

Run with the existing trusted toolchain:
```
python tests/fixtures/text_representation_switch_lab/run_lab.py \
 --out NEW_DIRECTORY --font APPROVED_DEJAVU_SANS --msdf-source PINNED_MSDFGEN
```
Opt in VULKAN_TEXT18_REPRESENTATION_SWITCH=1 with TEXT18_MSDF_SOURCE.

Adjacent-frame reports subtract the exact geometric-reference coverage change
from the observed same-pixel coverage change, reporting max and union-foreground
ROI MAE residual. No acceptance threshold is added. This separates known geometry
motion from representation error changes but is not a perceptual flicker metric
or motion-compensated temporal analysis.
