# Bounded explicit pre / overlay / post state handoff

One VkDevice, one submission and **one VkRenderPass** contain three ordered draws:
opaque pre-scene, transparent coverage overlay, opaque post-scene. These are three
draw stages within a single pass, not three render passes or cross-pass recovery.
RGBA32F color/velocity/ID are all active attachments. `independentBlend` is queried
and enabled; the two auxiliary write masks are zero and their readbacks must
preserve exact sentinels. No depth/stencil attachment is included.

Two compatible pipelines use the same descriptor/vertex/push-constant layouts.
The scene descriptor samples a constant .8 R32F image; overlay samples a .5
synthetic rectangular-ring mask, not a platform glyph. Separate full-NDC and
half-NDC quad vertex buffers, dynamic viewport and dynamic scissor make all five
state classes observable. The next scene draw explicitly rebinds pipeline,
descriptor, vertex buffer, viewport and scissor. Push constants are also explicitly
set for each draw but their omission is not separately tested.

Before GPU execution the independent CPU reference registers the exact rectangles,
nearest-sampled mask equation and sequential premultiplied composition, with the
existing 1e-6 tolerance. It reads neither GPU vertices nor generated shader data.
The final image retains 2,705 pre-only pixels and 160 visible-overlay pixels;
post-scene overwrites 8 nonzero-overlay pixels and 312 other pixels. Thus all three
stages contribute visible evidence, rather than a final full-screen overwrite
hiding the first stages. The scene alpha is 1; only overlay is transparent. This
is not general transparent-ordering verification.

Six negative executions keep Vulkan usage legal, skipping post-stage rebind of
one of the five state classes or all five. Each produces a different image and
must fail exactly the composition oracle while validation remains clean and both
auxiliaries remain unchanged. These are six diagnostic runs, not extra positive
evidence. The outer pytest also rejects a substituted diagnostic readback.

Run with the same trusted local Vulkan toolchain:
```
VULKAN_TEXT18_HANDOFF=1 python -m pytest -c tests/pytest.ini tests/test_text18_handoff_lab.py
```
Native fence wait is bounded by the shared helper, subprocess calls by 120 seconds
and the enclosing test by 240 seconds. Partial allocation/device-loss cleanup and
arbitrary renderer state are not certified. In particular index buffers, stencil,
depth, blend constants, pending glyph retirement, target hardware and Live remain
outside this experiment. The mask is synthetic state-diagnostic input, not new
font-quality evidence. No additional product acceptance threshold is introduced.

An initial local attempt reused the filename `scene.frag.spv`, colliding with the
inherited engine's startup shader and causing validation errors. The final
fixture instead uses `handoff_scene.frag.spv`, leaving startup shaders unchanged. This was a build-adapter naming conflict,
not a change to the reference, schedule or 1e-6 tolerance.
That failed attempt is retained locally and is not counted as successful evidence.
Raw shader/binary/tool/driver hashes and logs remain local; only minimal numerical
results are publishable.
