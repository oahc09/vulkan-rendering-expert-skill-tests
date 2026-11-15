# Text Vector Lab: candidate scaffold, not a renderer

CPU contracts in `tests/text_host_contracts.py` explicitly simulate identity,
provider range validation, pending upload publication, snapshots and independent
consumer completion points. They do not parse a font, call Java/DirectWrite,
implement shaping or run Vulkan. Synthetic glyph numbers imply no font license.

`coverage.frag` is a minimal linear coverage fragment shader. Compile with
`pytest tests/test_v1_0_18_shader.py`; missing real compiler/validator is SKIP.
Use UNORM data coverage, linear text RGB, premultiplied output and compatible
ONE / ONE_MINUS_SRC_ALPHA blend state. Compilation alone proves none of those
host states. This shader is not a complete pipeline or proof of MRT protection.

Still unimplemented: Text Quality Board, Vector & World Text (including hole
triangulation and finite extrusion), Atlas Churn & Overlay actual Vulkan
harness, image/readback comparison and platform bridges. No actual render images
were produced or inspected. These are explicitly UNIMPLEMENTED, not empty PASS.

Before visual execution pre-register font/provider/hash/license, dimensions,
DPI, transform sequence, glyph ROI, reference type, format quantization/tolerance,
edge jitter metric, geometry error/budgets and MRT sentinels. Do not choose passing
thresholds after seeing output. Native platform fonts may differ legitimately;
never compare their glyph IDs across fonts as equivalent. Do not redistribute
system fonts.
