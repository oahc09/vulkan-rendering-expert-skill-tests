# Text Vector Lab: incremental, real offscreen Vulkan fixture

## Implemented and executed scope

`main.cpp` reuses the existing Engine Scale Lab device/memory/command helpers,
without changing them. It performs actual Vulkan operations:

1. Generate synthetic single-channel masks on CPU (not a system font).
2. Copy host-coherent staging bytes to an R32_SFLOAT sampled image.
3. Transition transfer writes to fragment sampling; issue a fullscreen draw.
4. Output linear premultiplied text into RGBA32F with ONE /
   ONE_MINUS_SRC_ALPHA blending over linear 0.2 background.
5. Copy the color and two non-target images to host readback and compare.

Frame 0 uses coverage 0.5 and opacity 0.8: expected linear RGB 0.52, alpha 1.
Frames 1–4 contain a rectangular O-like mask with a hole and 0, .25, .5, .75 px
shifts. CPU 4×4 sampling is the synthetic resource producer; GPU performs the
actual sampling and blend. Every pixel is checked at a predeclared 1e-6 absolute
linear tolerance. Hole center must retain background, stroke must be present.
PNG previews are sRGB encodings of readback, not replacements for raw floats.

The non-target attachment path is **explicit separate-overlay fallback**, not
active MRT independent blending. Renderpass/pipeline retain three color slots;
only slot 0 is used, references 1/2 are VK_ATTACHMENT_UNUSED and those framebuffer
attachments are explicitly preserved. Velocity (.125,-.25,.5,1) and ID
(37,91,12,1) sentinels are cleared before the pass and must remain exactly equal
in every pixel afterward. No claim is made for active MRT independentBlend,
depth/stencil preservation, dynamic rendering or production pass integration.

The thirteen page updates serialize with fence completion before next upload. This
is legal repeat upload/sample/readback, not concurrent atlas generation/churn.
No font binaries are bundled; glyph shape is self-generated and is not evidence
of shaping, DirectWrite/Android, MSDF, arbitrary vectors or typography quality.

## Reproduce

Provide official Vulkan headers, loader + ICD, C++17 compiler, glslangValidator
and spirv-val. Dependencies are never downloaded by the fixture. An extracted
header prefix may be selected with `VULKAN_SDK_PREFIX=/prefix/usr`; link uses the
installed Vulkan loader ABI. Set `VK_DRIVER_FILES` explicitly for the intended
implementation and `VK_LAYER_PATH` for validation layers when available.

```
python tests/fixtures/text_vector_lab/run_lab.py --out /new/absolute/output
VULKAN_TEXT18_LAB=1 python -m pytest -c tests/pytest.ini tests/test_v1_0_18_vulkan_lab.py
```

`GLSLANG`, `SPIRV_VAL` and `CXX` override executable paths. Existing output/build
directories are rejected without overwrite. Missing dependency/ICD or execution
failure is FAIL, not PASS. The opt-in pytest skips when not explicitly enabled.
Validation enabled state is logged; zero logged errors with no layer is not a
validation pass. Software Vulkan proves only this integration path, never mobile
performance or device certification. Compiler times are not performance evidence.

Artifacts include source/shader/binary hashes, test/Skill SHAs, dirty status,
compiler logs, device/driver properties, raw coverage/color/ID/velocity floats,
per-frame numerical results and previews. Independent Python checks reject
truncated/nonfinite readback, wrong color, lost hole or modified sentinels.

## CPU contracts and remaining gaps

`tests/text_host_contracts.py` separately simulates font identity, provider range,
publication and multi-consumer retirement; those are not Vulkan execution.

Still missing: actual platform Text Quality Board, MSDF/MTSDF quality,
vector triangulation/extrusion/clip/near-plane behavior, concurrent Atlas Churn,
actual active-MRT/depth protection, real Live semantic review and target devices.
Pre-register fonts, providers, license/hash, quality ROIs, reference types and
limits before those experiments. Never set passing thresholds after inspection.

## Synthetic coverage quality extension (TEXT18-06/09/10, plan §14)

Frames 5–8 check black, white, colored and translucent **premultiplied** linear
backgrounds; straight text color is multiplied by coverage × opacity once.
Opacities include 0, .25 and 1, and coverage ramps contain 0/.25/.5/.75/1.
Alpha is checked independently, not assumed opaque. Frames 9–12 use a small
7×7.5 pixel rectangular ring partially outside the left viewport edge, shifted
by 0/.25/.5/.75 pixels. This tests sampled mask composition at the viewport edge,
not Vulkan scissor/clip geometry, arbitrary vector clipping or font hinting.

The C++ producer uses 4×4 subpixel occupancy. The Python oracle independently
computes exact pixel/rectangle intersection areas from fixed geometry, and
checks uploaded mask bytes before checking every GPU RGBA value. These quarter
pixel aligned synthetic rectangles have exact area coverage under both methods.
All frames retain the predefined 1e-6 linear absolute tolerance. Reports include
nonzero-coverage ROI maximum error, fractional edge pixel count, coverage area
and alpha error; empty background cannot dilute the ROI result. Frame sequence
measurements do not prove animation perceptual quality or general temporal AA.
All comparisons use raw linear RGBA floats; PNG previews encode RGB as sRGB and
are not alpha-composited typography reference boards.
