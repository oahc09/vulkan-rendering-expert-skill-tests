# Synthetic COLRv0 → actual GPU colors

`VULKAN_TEXT18_COLRV0=1 python -m pytest -c tests/pytest.ini tests/test_text18_colrv0_lab.py`
requires existing FreeType/freetype-py, fontTools generator interpreter
(`TEXT18_FONTTOOLS_PYTHON`, default python), and established Vulkan toolchain.
No downloads or prebuilt font redistribution. Integration marker/lazy provider
imports keep normal static CI independent of these capabilities.

The generated font is deliberately **synthetic**, not a production emoji font.
It contains a base A glyph with two ordered COLRv0 layers (rectangles at font
coordinates[0,0,600,600] and[300,300,900,900], UPEM1000). Three CPAL palettes use primary-color endpoints plus a third palette with
RGB(51,102,153)/255 and(204,51,102)/255, and alpha128/255 and192/255. Actual FreeType
FT_Get_Color_Glyph_Layer enumerates glyph IDs/color indices, FT_Palette_Data_Get
bounds palette/entry counts, and FT_Palette_Select provides BGRA colors. Actual
FT glyph rasterization at20px yields coverage. Known layer identity and decoded
palette values must match generator intent. This is provider parsing, not JSON
standing in for a font. No text shaping claim: the charmap selects a single base.

Two masks upload in RG of an RGBA32F texture. Real Vulkan shader samples the
coverage, composites ordered layers with premultiplied alpha, then hardware
blends onto the fixed linear background. Independent CPU expectation is based
on predeclared integer rectangle positions and palette constants, not provider
coverage buffers. Every output channel must differ by≤1e-6; ID/velocity remain
exact via existing UNUSED/preserve overlay fallback. All three palettes are positive cases. A legal GPU run with swapped layer colors must be rejected; pytest also
rejects substitution of the other palette's readback. Input sizes/finiteness
are checked and existing output folders refused.

The provider-derived CPAL RGB values are explicitly sRGB-decoded to linear
before GPU composition; alpha is not gamma-decoded. Independent CPU expectation
decodes predeclared raw CPAL constants. A real GPU draw bypassing decoding of
the third palette must fail. Primary endpoints alone cannot validate this path.
Separate text opacity is not tested, only CPAL alpha. This fixture does NOT test
foreground-color index0xFFFF, COLRv1
paint graphs, gradients, transforms, SVG, bitmap emoji, variable color fonts,
production typography, platform support, or target-device performance. Counts
are two fixed layers; this is neither arbitrary layer complexity nor a complete
color-font renderer. No active MRT/depth combined claim.

The helper's source modifications are checked for occurrence count, RGBA sample
and transfer support are queried, SPIR-V compiled/validated, and Vulkan validation
required. Subprocesses120s/pytest180s, existing bounded submit helper; no full
allocation/device-loss proof. Raw font/tool/driver/source receipts remain local.
