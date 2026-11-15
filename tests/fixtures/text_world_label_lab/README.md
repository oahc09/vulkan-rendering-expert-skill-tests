# Bounded world-space shaped O label with true perspective UV

This fixture fills the world-label gap in plan6.4; earlier affine glyph and
orthographic extrusion experiments do not prove it. The trusted local face is
size/SHA256 checked before parsing. Actual HarfBuzz must return exactly GlyphID50
for O; FreeType loads that glyph at20px. Receipt face hash, ID, missing/clipped
counts are checked. The nonempty crop must retain enclosed zero-coverage hole
pixels identified on the original provider bitmap, not on GPU output. No font
is published and this is not a system-font quality certification.

One packed glyph has fixed world extent x[-1,1.25], y[-1.125,1.375], on plane
z=z0+.25*x. The actual vertex shader outputs clip=(x,y,(10/9)*z-10/9,z), hence
perspective divide and perspective-correct UV are real GPU operations. Camera
near1/far10 and two z0 values2.75/3.75 are preregistered before GPU work. This is
**constant world size, one camera at two distances**, NOT constant pixel size,
billboard certification or a second view. All case coordinates stayed unchanged
through the successful initial run. No excluded edge guard is used.

Each output is one command submission and one render pass: draw an ordinary
opaque world rectangle with depth LESS/write enabled, then draw the label with
depth writes disabled. Label variants choose LESS (occluded) or ALWAYS
(always-on-top). The rectangle has world bounds(.125,1.625,-1.375,1.625) at z2;
its real color/depth survive subsequent text writes. Three active color
attachments preserve velocity/ID with disabled write masks. Actual sampler
configuration must remain nearest, not silently become linear/mip-filtered.

CPU pixel-center rays intersect the original plane, map directly to the original
cropped glyph's pixels, and reconstruct linear premultiplied over. It does not
read uploaded vertices, packed atlas output, shader UVs or GPU clip coordinates.
The occluder is independently ray-intersected. Depth is checked before any
negative color-error interpretation; auxiliary values must be exact. Per-output
nonzero visible/hidden ROI and projected hole counts are reported. Real coverage
shrinks with distance as required by world-size policy, not a quality regression.
Every pixel uses the unchanged1e-6 composition/depth gate, with no exclusions.

Actual legal negative draws use wrong ALWAYS policy and noperspective UV
interpolation. Their resource lifetimes and depth/auxiliary protections remain
valid; only wrong color output qualifies the negative. Input near-plane/nonfinite
coordinates are rejected before output/GPU construction. The finite submitted
triangles have affine z, so checking every vertex bounds the entire surface.
The conservative input guard z>1.125 is not a clipping algorithm: near-crossing
planes are rejected, not rendered or silently truncated. Far/coordinate/UV
bounds are likewise finite. No shadow, second view, general near-plane clipping,
full world typography, lighting, hardware platform or Live claim is made.

The original helper fixtures are unchanged; new generated helpers use checked
single replacement hooks. Shader and binary hashes/provider receipts stay local.
Waits/subprocesses are bounded. Prior preparation outputs are not counted among
the four positive world draws and two actual negative draws. Only source and
stripped numerical summaries are publishable.

```
VULKAN_TEXT18_WORLD_LABEL=1 python -m pytest -c tests/pytest.ini tests/test_text18_world_label_lab.py
```
