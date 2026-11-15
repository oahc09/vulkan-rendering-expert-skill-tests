# Finite multilingual same-layout representation board

This is one registered seven-row offscreen quality board, not another isolated A/O
calibration. Chinese (SC face 2), ffi (actual ff+i), combining a+acute, a real
mixed Latin/Arabic/digit paragraph, real VS16 heart, and two complete RobotoFlex
axis instances use frozen HB positions. FriBidi and ICU agree on the paragraph.
For monochrome rows the same per-glyph 26.6 FT placement produces both unhinted
bitmap and outline; there is no per-representation fit, reshaping, or ink-height
normalization. Empty glyphs preserve advance. Original outlines feed the pinned
MSDF generator without single-glyph normalization. Whole-run fallback is finite,
not arbitrary paragraph typography or platform certification. Ofi shapes to two
glyphs including a fi ligature. Heart uses actual system FT color decoding with
independent CBDT PNG byte checking, and is explicitly bitmap-only fallback.

Each valid tile is rendered in one persistent logical Vulkan Device, reuploading
one 16-band RGBA texture between draws. Bands represent distinct glyph layers,
not production atlas allocation. Manual per-band bilinear sampling prevents
cross-band bleed. Per-glyph premultiplied over is accumulated and then Vulkan
fixed-function blending composites over the shared linear background. Aux images
are UNUSED/preserve, not active MRT. No depth, Surface, physical-GPU performance,
shadow, or production cache claim is made.

Frozen criteria precede candidate draws. The fixed left-aligned layout causes
all six monochrome 90-degree full-footprint tests to exceed the 49px height;
both columns remain UNSUPPORTED_CLIPPING, not fitted or silently cropped. Heart
rotation fits. Perspective is UNMEASURED. Four other transforms are common to
all monochrome rows. The final board is assembled from this run's real readbacks,
not a synthetic replacement for Vulkan rendering.

CPU sampling reference uses independent double arithmetic over original uploaded
values (emoji uses independently decoded PNG), not GPU readbacks. Original source
outline curves are flattened at 64 subdivisions, and nonzero winding coverage
is sampled at 16x16 per pixel separately for each glyph before alpha-over. This
is a sampled geometric quality reference, not exact area or an independent
layout/shaper. FT hinting is disabled. Shared provider identity/metrics do not
constitute independent typography quality certification. Quality and phase
residuals are MEASURED_NOT_QUALIFIED; bitmap 1e-6 and MSDF linear4 .004 gates only
validate implementation sampling/composition. No exclusions or threshold changes.
Edge ROI is union of per-glyph partially covered pixels. Phase diagnostics
subtract original-outline reference changes from actual alpha changes.

The first run failed bitmap bidi minification at 1.305590075773e-6 against 1e-6.
Its full evidence is retained locally. Fixed scale 3/4 now derives texel indices
and rational remainders before interpolation, avoiding center-subtraction float
cancellation; geometry, reference, thresholds and cases are unchanged. This is a
bounded fixed-transform numerical implementation, not general perspective.
Actual double-alpha and wrong-MSDF-range shader negatives must fail their
respective composition gates while independently preserving auxiliary images.

Opt-in: TEXT18_SCENE_A_BOARD=1, TEXT18_VARIABLE_FONT and TEXT18_MSDF_SOURCE point
to verified execution-side dependencies. Fonts and generated font resources are
not committed. Full dependency/provider/tool/driver receipts remain local; public
report contains only numeric results and explicit limitations.
