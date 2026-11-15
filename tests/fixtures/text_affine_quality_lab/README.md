# Bounded bitmap affine sampling diagnostics

Actual packed O glyph vertex quads render at scales0.5,1,1.5 and a90-degree
quarter turn at1.5. The GPU consumes transformed xy vertices and packed atlas UVs.
The independent CPU oracle maps destination pixel centers back to original glyph
pixels and evaluates nearest sampling; it does not read the GPU vertex buffer.
Quarter-pixel origins and exact quarter-turn transforms are fixed before running.

Pre-registered gates: every linear color/ROI sample absolute error≤1e-6; total
coverage area inferred from readback alpha differs from the CPU reference by≤1e-3.
Known ID/velocity sentinels remain exact. A valid GPU draw with a one-texel UV
shift must fail the independent oracle; readback corruption is also rejected.
Each output is saved and actual images are inspected during validation.

Normalized area change relative to original bitmap area is a diagnostic only,
NOT a typography quality acceptance threshold. Matching nearest reconstruction
can still reproduce nearest aliasing. This does not demonstrate optimal hinting,
linear/mip filtering, arbitrary angle/perspective, temporal-transform stability,
MSDF/color/variable-font quality, platform correctness or mobile performance.
The original glyph comes from the approved trusted-font preparation path and
no font is redistributed. Three extra preparation/negative checks are distinct
from this experiment's four positive affine draws and one negative draw.

The unchanged packed-quad runner prepares the input and compiled Vulkan binary.
This fixture creates only new vertex buffers/output directories; original source
and evidence are untouched. Software Vulkan validation must be enabled; no silent
fallback. Subprocesses120s; outer test240s. Raw driver/font/tool/source provenance
is retained locally. Only stripped numerical summaries publish.

```
VULKAN_TEXT18_AFFINE=1 python -m pytest -c tests/pytest.ini tests/test_text18_affine_quality_lab.py
```

Use the explicit Vulkan toolchain/ICD and trusted font dependencies of packed quad.
