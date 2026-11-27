# Registered compact storage and explicit fallback, before GPU

Reuse frozen seven-row original outlines/bitmap/shaping and common refined
65x65 transformations. Per-glyph crop uses original outline bounds expanded by
three screen pixels, outward integer rounding and intersection with65x49.
Color heart crop is fixed[14,7,50,41]. Store full RGB/RGBA, not glyph compression.
Vertical packing has a one-row metadata header, width=max(3*glyphcount,cropwidth),
height=1+sum(cropheight). Budget is actual W*H*16 including all header/padding.
Separate row texture/Device, shared across that row's transformations, not one
persistent Device across the entire board. Source generation is reused/frozen
CPU material; this does not reduce source MSDF generation work or CPU peak RAM.

High diagnostic budget400000 selects4x MSDF for each monochrome row.
Finite diagnostic budget200000 selects4x iff packed resource fits, otherwise
original bitmap at1x iff that resource fits. It never consults output quality.
Budget4096 must reject all seven rows before GPU resources are constructed.
These are reproducible experiment budgets, not production mobile recommendations.
Actual binding/upload/storage dimensions must equal the chosen plan. Tight
packing is not adaptive density: only4x or bitmap fallback, no invented2x policy.

Compare compact4x GPU with full4x CPU sampling reference and historical same
layout readback metrics. Bitmap gate1e-6/MSDFgate.004 remain, zero exclusions;
report degraded bitmap geometry errors rather than calling fallback equivalent.
Wrong metadata changes source origin by one screen pixel via a legal shader
and must produce a composition failure while auxiliary data remain preserved.

Old16x geometric quality reference is retained, with a separate exact local
anchor: ! glyph4 bar[54.546875,55.15625]x[28.71875,29.953125], halfphase output
pixel(55,37). Exact area=.609375*.953125 and alpha=.43560791015625.
Old16x alpha=.3955078125; GPU4x=.4482421875. True local error=.01263427734375,
not the old reference-relative.052734375. This is reference quantization
classification, not a rendering improvement. Perspective is the next step and
must not be claimed by this first compact-storage stage.

## Appended perspective contract, before perspective GPU execution
Same resources receive an additional real six-vertex projected quad:
source q=(x-32.5,y-24.5), w=1+q.x/128, output center(32.5,32.5)+.75*q/w.
All source-plane w remain positive, minimum.74609375; no near-eye crossing.
No per-row fit. Fragment source coordinate is the stable inverse homography,
not a claim of hardware varying interpolation. MSDF footprint is the symmetric
two-axis screen-range approximation from the local inverse Jacobian L1 row norms;
this is not exact anisotropic area integration. CPU derives local derivatives by
symmetric finite differences of independent inverse mapping, and source outlines
are projectively transformed for geometric coverage. Existing tolerances remain.
A legal shader using affine inverse while the quad stays genuinely projected
must fail color reference with preserved auxiliary images. Perspective bitmap
and color follow identical geometry/layout, no special post-failure fitting.
