# Frozen same-pass vector + shared world scene

Keep all previous Scene B shared-world geometry/light/camera resources unchanged.
After each receiver/L/occluder/O camera sequence, append ONE actual support-quad
draw in the same renderpass, active MRT, ALWAYS/depth-write-off. Screen-space
path union alpha .35, RGB(.1,.85,.35), premultiplied over once.
Outer rectangle(12,8)-(44,40), inner(18,15)-(36,33), stroke endpoints(22,22),
(34,29), radius2. Hard pixel-center area membership, no AA. Paths are not uploaded
CPU masks. Shader independently classifies fixed source geometry and clip stack.

Three clips unchanged from prior clip lab: half-open rect12..43,10..37,
circle center30,25 radius15, polygon(18,8),(48,18),(40,42),(10,32).
CPU source winding/parity, analytic closest-segment distance and polygon crossing
are independent from shader's rectangular membership, dot-product and halfplanes.
Normal opposite-inner nonzero retains hole. Additional B views explicitly use
same-inner evenodd(hole), same-inner nonzero(solid), opposite-inner evenodd(hole).

Before any candidate GPU draw, reference preflight: each clip bypass changes
35/89/40 pixels, filled-hole changes256, round-to-butt changes12, path-only292,
stroke-only68, retained hole256. Initial design-only long-line cap difference0
was rejected by CPU preflight before GPU setup; the above short line is frozen.
World negative shadow/label projection errors remain observable after overlay.

Five positive full views, seven legal negative views: original bypass-shadow,
wrong-label-camera, three clip bypasses, filled-hole and butt-cap. All retain
original real scene depth and exact aux independently before color error is
considered. Full color/depth1e-6, zero exclusions, no new quality threshold.
Twelve camera passes reuse same scene/Device/light image; each has five draws.
One light producer. No general curves/dashes/joins/world-vector, stencil/AA,
perspective/near/negative-scale integration or full Scene B claim.

## Reference correction, not geometry/threshold change
First run retained five positive mismatches at pixels(28,11),(31,12),(34,13),
(37,14),(40,15), exactly on the rotated clip's first finite segment. The inherited
shader used closed cross>=0, while the new CPU crossing rule omitted boundary.
CPU now includes a point iff it lies on a finite segment (cross0 and bounded dot)
or has nonzero winding. New clip差集36/91/35, path-only297; remaining counts
unchanged. Original counts above and first failed outputs remain historical.
No GPU shader, source geometry, threshold or excluded-pixel rule changed.

Historical clip CPU reference already included finite closed boundaries; this
new reference rewrite omitted that existing rule, now restored.
