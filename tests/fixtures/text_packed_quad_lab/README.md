# Actual packed-UV glyph vertex quads

Three real trusted-font glyph bitmaps (O/f/i), produced by the existing
HarfBuzz/FreeType adapter, are cropped and shelf-packed with one-pixel zero
padding into one 65×49 atlas. The Vulkan draw now consumes an actual vertex
buffer: six xy/uv vertices per glyph, three distinct destination positions,
and atlas-subrectangle UVs. The vertex shader uses location 0/1 attributes;
it does not reconstruct a fullscreen triangle with gl_VertexIndex.

The O quad extends two pixels past the viewport left edge. The oracle uses
original cropped glyph pixels and integer destination rectangles to reconstruct
expected output independently of the generated vertex-buffer/UV values or GPU
readback. It checks all pixels, nonzero-coverage ROI, outside-ROI background and
untouched ID/velocity sentinels at fixed 1e-6 linear absolute error. Actual
one-texel-shifted UVs are drawn in a negative run and must fail this oracle.
Out-of-range vertex UVs are rejected before creating GPU resources. Readback
corruption is also rejected. No illegal shader access is injected.

Scope is deliberately 1:1 integer quad geometry with nearest sampling. These
three glyphs have validated non-overlapping destination rectangles; overlapping
translucent glyph layers are explicitly out of this oracle scope. They are
positioned as a controlled test arrangement, not a shaped word
or paragraph. Does not establish fractional-size filtering, full shaped-run
placement, rotations/perspective, MSDF, mobile devices or performance. The same
preserved non-target overlay fallback as text_vector_lab is used.

The runner generates an output-only derivative header from unchanged TextLab:
vertex input binding/attributes and vertex-buffer draw are substituted, alongside
an explicit host-write→vertex-input barrier. Original fixture files are not
modified. Existing shaders and Vulkan setup are reused; official glslang and
spirv-val compile/validate the new vertex shader. All child processes have 120s
limits, outer pytest has 180s limit. Raw source/tool/driver provenance and font
receipts stay in the new local output directory. Font files are never bundled.

```
python tests/fixtures/text_packed_quad_lab/run_lab.py \
 --font /trusted/DejaVuSans.ttf --out /new/output
VULKAN_TEXT18_PACKED_QUAD=1 python -m pytest -c tests/pytest.ini tests/test_text18_packed_quad_lab.py
```

Use the explicit Vulkan toolchain/ICD environment and pinned freetype-py binding
from text_bitmap_lab. Validation must be enabled. Missing inputs or unsupported
paths fail rather than being relabeled as platform or visual acceptance.
