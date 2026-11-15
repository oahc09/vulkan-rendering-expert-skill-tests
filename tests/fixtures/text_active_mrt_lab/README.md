# Active MRT and depth-write protection: actual Vulkan

A real render pass has all three RGBA32F color references active: color,
velocity, ID. None is VK_ATTACHMENT_UNUSED and no preserve fallback is used.
A fourth D32_SFLOAT image is an active depth attachment. The shader explicitly
outputs all three color locations. The normal pipeline enables premultiplied
blending/writes only for color; velocity and ID have colorWriteMask=0 and
blending disabled. This requires independently queried/enabled independentBlend.
D32 depth-attachment and transfer source/destination format features are queried.

All images are prefilled with known constants using transfer clears. The draw
produces expected linear color .52 while velocity (.125,-.25,.5,1), ID
(37,91,12,1) and depth .375 must remain unchanged at every pixel. Depth testing
is enabled with ALWAYS and depth writes disabled: this tests write protection,
NOT correct occlusion/depth testing against scene geometry, early/late fragment
behavior across pipelines, stencil, reversed Z or rendergraph integration.

Two legal negative pipeline configurations execute with validation enabled:
- Auxiliary active color write masks become RGBA: ID must actually become
  (4,3,2,1) and the independent sentinel oracle must reject the run.
- Depth writes become enabled: actual depth becomes fullscreen vertex depth 0,
  and the independent depth oracle must reject the run.

These are valid Vulkan wrong-output experiments, not invalid-use diagnostics.
The normal color maximum absolute tolerance is predeclared 1e-6; sentinels are
exactly representable and must match exactly. A separate corrupt readback test
rejects depth tampering. Shader SPIR-V is compiled and validated with official
tools; raw local receipts record source, generated helper, tool and driver hashes.

The fixture generates output-only helper copies from unchanged text_vector_lab
and engine_scale_lab, replaces exact single-occurrence hook sites, and enables
independentBlend only after querying its feature. Old UNUSED/preserve tests are
untouched and cannot substitute for this active-MRT test. No publication or
performance claim is made for Android/Windows GPUs. Processes are bounded by
120s (each child) and 180s (outer pytest); Vulkan submission wait is bounded by
the reused helper. Exhaustive allocation/device-loss fault cleanup is not tested.

```
python tests/fixtures/text_active_mrt_lab/run_lab.py --out /new/output
VULKAN_TEXT18_ACTIVE_MRT=1 python -m pytest -c tests/pytest.ini tests/test_text18_active_mrt_lab.py
```

Use the same explicit official compiler/SDK/ICD environment as text_vector_lab.
Missing independentBlend or D32 support fails, not an unreported fallback.
All raw evidence stays local. No existing docs, reports or fixtures are modified.
