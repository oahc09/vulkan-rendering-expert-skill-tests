# Bounded nested fragment clipping

Actual fragment shader tests an axis-aligned rectangle, circle and rotated
rectangle in sequence. Their intersection clips an unmodified uploaded coverage
texture. This is not a CPU-premasked texture pretending to exercise GPU clipping.
The independent CPU oracle uses pixel-center circle arithmetic and ray crossings
through four polygon vertices, not the shader's four edge half-plane expressions.
It compares every output/ROI to a fixed 1e-6 linear-over tolerance. Three valid
negative GPU draws independently bypass one clip layer and must be rejected.
A bounding box alone is explicitly not accepted as the curve/rotated boundary.

One hard sample per pixel, fixed geometry and no antialiasing only. This is not
a general path parser, stencil implementation, arbitrary nested-clip stack,
production clip allocator, soft edge or MSAA test. Non-target attachments use the
unchanged UNUSED/preserve overlay fallback. Active MRT/depth is a separate lab.
No target mobile platform/performance or integrated glyph lifecycle claim.

Compile/validate the shader and derive an output-local header from unchanged
TextLab, then reuse the unchanged bitmap draw executable source. Child processes
are bounded to120s, pytest wrapper180s. Validation is mandatory. Existing output
directories reject. Raw source/tool/environment evidence stays local; only small
numerical summaries may be published. No font or third-party binary is bundled.

```
VULKAN_TEXT18_CLIP=1 python -m pytest -c tests/pytest.ini tests/test_text18_clip_lab.py
```

Use the explicit Vulkan toolchain/ICD environment documented in the original
text_vector_lab. Software Vulkan validates this fixture only, not mobile speed.
