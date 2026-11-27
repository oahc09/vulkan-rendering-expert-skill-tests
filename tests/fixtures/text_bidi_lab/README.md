# Fixed real paragraph bidi + font fallback + Vulkan

This is a new actual paragraph-map path, not the older manually presegmented-run
fixture. Fixed input is `A سلام 12!`, BMP only, with explicit paragraph base LTR
and RTL. System FriBidi resolves embedding levels and index permutations. Its
presentation-form/visual string output is deliberately ignored: each **original
logical substring** goes to HarfBuzz with resolved direction. Reversing a string
before RTL shaping would double-reorder it and is not done.

Independent ICU 76 resolves the same complete paragraph and must agree on every
level and visual logical index. The CPU screen reference reconstructs run intervals
and visual order separately from ICU, and computes pen advances from original HB
positions, never candidate destination/UV values. FT bitmap pixels are still the
source reference: this is not an independent raster or typography quality oracle.
Two separately identified official Unicode 15.1 BidiCharacterTest vectors verify
FriBidi level/permutation behavior on the longer Latin/Arabic/Hebrew bracket input.
Those vectors do **not** claim to be golden data for the rendered short paragraph.
The runtime reads the exact SHA-guarded local official test file; no Unicode test
data is copied into this repository. Source:
https://www.unicode.org/Public/15.1.0/ucd/BidiCharacterTest.txt
License: https://www.unicode.org/license.txt (original test-data copyright 2023).

For this fixed input, contiguous embedding-level spans contain at most one strong
script. That constraint is checked, not a general script itemizer. Each full run
uses existing ordered trusted-face fallback, then HB actual GlyphIDs/positions and
FT same face/index at **10px**. Original whitespace advances are retained even when
bitmaps are cropped; crop bearing is restored at the shared baseline. Baselines
are preregistered 16/36, left pen3, width<=59 (pen<=62), all nonzero pixels in the
65x49 viewport. No post-result positioning adjustment or tolerance widening.

Each base case is one actual four-run packed atlas and four UV quads. CPU source
coverage/linear premultiplied composition is checked at existing 1e-6, full image,
zero exclusions. The helper uses UNUSED/preserve auxiliary protection, not active
MRT. Actual legal GPU negatives use logical run order instead of visual order,
and reshape RTL runs incorrectly as LTR. Each negative must produce a color error;
auxiliary sentinels are verified first. Old quad preparation draws are separate,
not counted as new paragraph evidence. All shaping is on trusted, pinned bytes;
no system fonts are uploaded.

Independent native libraries and official dataset are required only by explicit
opt-in integration tests; pure host tests do not require ICU/FriBidi installed.
Missing dependencies are not semantic/GPU PASS. No general line wrapping, controls,
isolates, supplementary scalars, mirrored-bracket GPU rendering, arbitrary scripts,
full Pango layout, target-platform or all-UBA qualification is claimed. The fixed
input API rejects other paragraphs before native calls. This bounded renderer is
not a replacement for a production platform layout engine.
