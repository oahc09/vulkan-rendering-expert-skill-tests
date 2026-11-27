# MSDF subpixel integration diagnostic

This separate experiment preserves the published single-sample baseline and its
unchanged acceptance thresholds. It freshly runs that baseline, then uses the
same atlas, glyphs, eight transforms and Vulkan harness with a different shader:
two measured modes: binary16 uses 256 LINEAR texture samples/pixel and binary
median sign area integration; linear4 uses 16 samples and subpixel linear
coverage integration. Both execute all eight cases with their own CPU sampling
oracle and an actual sRGB-negative draw (16 positive and 2 negative draws).
Output is MEASURED_NOT_QUALIFIED, never a full text-quality/performance PASS.
No target hardware cost, mobile budget or general-font guarantee is established.

Compare both the original 16×16 outline sample reference and (for linear-contour
A only) exact polygon/pixel clipping area. Against the 16×16 reference the native
A error fell from ~0.3997 to ~0.00390625 in exploratory runs; against exact polygon
area its maximum error remained ~0.03077. Same-grid agreement is not exact area
agreement. Curved O still uses subdivided Beziers and sampled coverage, not an
analytic curve area oracle. No library defect is asserted: center-distance to
coverage approximation and sampled distance-field reconstruction are distinct.

The CPU oracle reconstructs both new shaders, with a fixed .004 coverage
tolerance (one of 256 sign samples near float boundaries). The premultiplied-over reference also checks all four RGBA channels using this
fixed budget. This is only sampling/composition agreement. A real sRGB shader negative must disagree. Range is irrelevant to the binary16 sign test (but used by linear4). No
wrong-range negative is claimed for either mode. Sentinel preservation is the
UNUSED overlay fallback, not active MRT. The executable and dependencies are
freshly built by the hash-approved baseline; its local provenance is retained.

Run with the existing trusted Vulkan environment and pinned local msdfgen:

```
python tests/fixtures/text_msdf_integration_lab/run_lab.py --out NEW_DIRECTORY \
  --font APPROVED_DEJAVU_SANS --msdf-source PINNED_MSDFGEN
```

Opt-in test: VULKAN_TEXT18_MSDF_INTEGRATION=1, TEXT18_MSDF_SOURCE set.

The now-reproducible linear4 subpixel *linear coverage* GPU mode (16 texture
samples/pixel) also reduced error. On A its maximum difference from exact polygon
area was ~0.01238–0.01955, lower than this 16×16 binary method's ~0.01800–0.03077.
It agreed less closely with the 16×16 sampled reference, illustrating same-grid
reference bias. Therefore this fixture is not an assertion that 256 samples is
necessary, optimal, or a production recommendation. Lower-cost coverage methods
still need performance/quality qualification.

The regression assertion concerns only per-case maximum error against the old
16×16 sampled reference. ROI MAE and exact A polygon-area differences are reported
measurements, not additional pass gates. Improvement in these fixed maxima does
not establish overall visual-quality improvement across fonts or transforms.
