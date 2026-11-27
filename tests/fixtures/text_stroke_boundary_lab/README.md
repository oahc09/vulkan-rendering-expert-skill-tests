# Closed analytic stroke boundary fallback (not a pure-mesh repair)

The earlier `text_stroke_lab` and its failed boundary evidence remain unchanged.
Of eight guarded pixels in each original polyline, seven were already correct;
only pixel (42,35) differed by 0.8. Centers (42.5,35.5), (39.5,36.5) and
(36.5,37.5) all satisfy the terminal butt-plane dot product exactly zero, but
only the first was absent from actual mesh rasterization. Thus changing one
inclusive comparison into a top-left convention does not explain all three.

The runner queries actual `subPixelPrecisionBits` and records original analytic
endpoint offsets, a nearest-reported-grid quantization model and the three real
GPU coverage results. This model illustrates why an oblique edge can move across
some ideal boundary samples. It is NOT proof of the driver's exact quantizer.
The [Vulkan rasterization specification](https://docs.vulkan.org/spec/latest/chapters/primsrast.html)
guarantees consistent shared-edge ownership, not one universal top-left rule.
No framebuffer or case translation is used to avoid the boundary.

The new route deliberately uses a fixed viewport support quad plus a fragment
analytic-coverage predicate. Original path coordinates, caps, widths and miter
limits are unchanged. Non-normalized dot/cross operations implement closed
segment boundaries; round caps now use analytic circles, not the earlier
64-segment polygon approximation. Joins in the shader use offset-line
intersection and triangle union; CPU joins use angle-bisector construction and
convex-polygon halfplanes. CPU reference never reads emitted mesh or shader
results. Before Vulkan runs, all 3,185 pixel classifications in each of the six
old cases must agree with the old analytic reference. This prevents an oracle
change from concealing the original defect. Three reversed polyline cases also
exercise orientation invariance.

Nine real positive outputs require full-frame color and D32 depth error <=1e-6,
**zero exclusions** and exact active velocity/ID preservation. They are hard
pixel-center opaque union tests, not AA, area coverage, transparent overdraw,
world stroking or a general SVG implementation. The original limited input scope
remains finite straight/two-segment screen-space paths. The old mesh path is
rerun and must still expose its original full-frame boundary failure when this
fallback is omitted. Three additional legal GPU negatives are wrong cap,
ignored miter limit and an incorrectly open terminal boundary. All negative
readbacks check auxiliaries before interpreting the expected color/depth error.

The helper is asserted to load `coverage.frag`; generated SPIR-V and local build
receipts are hashed. Each subprocess has a timeout. Initial failed shader build
(constant dead branch indexed the third element of a two-slot array) is retained
locally; corrected generated arrays have three slots with COUNT controlling real
segments. No case, image tolerance or boundary expectation changed for that fix.

```
VULKAN_TEXT18_STROKE_BOUNDARY=1 python -m pytest -c tests/pytest.ini tests/test_text18_stroke_boundary_lab.py
```
Old mesh and new fallback evidence are separate. Passing this bounded fallback
does not qualify the old mesh boundaries or all fonts/joins/caps/platforms. Raw
logs, generated binaries and environment provenance stay local; only source and
stripped numeric summaries are publishable.
The required reproduction of the old mesh failure is specific to the configured
software implementation in this diagnosis. A different driver that does not
reproduce it must be reported as a different diagnostic outcome, not accused of
violating Vulkan or forced to fail through a shifted case.
