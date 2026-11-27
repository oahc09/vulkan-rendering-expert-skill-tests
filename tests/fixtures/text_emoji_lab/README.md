# Real fixed emoji presentation / color bitmap path

Noto Color Emoji is fixed to the trusted 11,260,748-byte file and SHA-256 before
parsing. Actual HB receives the complete U+2764+FE0F cluster and yields GlyphID168.
U+2764+FE0E routes to fixed DejaVu Sans and yields 4076 plus a zero-advance default
ignorable glyph3. Neither selector is stripped. The explicit whole-cluster policy
recognizes only those two strings; it is **not automatic missing-glyph fallback**:
a text face may support the base heart but cannot fulfill color-presentation intent.
Actual request-cluster dispatch invokes that policy, selects the font, shapes the
unmodified cluster and chooses its bitmap production path. Other sequences are refused. This is not complete emoji, ZWJ, skin tone, or Unicode
presentation coverage. The locally hash-checked official Unicode15.1
emoji-variation-sequences.txt confirms the two presentation declarations; it does
not certify either font's rendering. No Unicode dataset is copied here.

The historical bundled FreeType cannot decode this font's PNG strike. This new
adapter explicitly loads the absolute system FreeType shared-library path, uses
only its own handles, and leaves the old environment/libraries untouched. Loading
the basename instead may reuse the already loaded bundled library by SONAME and
is not used. Actual system decode yields 136x128, pitch544, BGRA pixelmode7 at109ppem.
The fixed bitmap is real CBDT font content, not a synthetic COLR font.

Independent system Python FontTools extracts CBDT glyph uni2764 and Pillow decodes
its embedded PNG straight RGBA. Before GPU work, all provider bytes must exactly
match integer BGRA premultiplication `(PNG_channel*alpha+127)//255` and unchanged
alpha. This rounding rule was determined and frozen in a pre-implementation audit;
it is not a universal FreeType version guarantee. Source gate is byte-exact, not
an enlarged image tolerance. GPU oracle independently reconstructs that quantized
representation from PNG, never the provider's uploaded floating RGBA.

Correct color contract: encoded premult BGRA -> divide RGB by alpha (zero alpha
canonical zero) -> sRGB EOTF -> multiply linear RGB by alpha. Upload linear premult
RGBA, then shader multiplies all four channels by text opacity .75 exactly once.
Vulkan fixed-function blending is ONE / ONE_MINUS_SRC_ALPHA over the existing linear BG.
The historical auxiliary fallback is UNUSED/preserve, not active MRT.

The entire strike is resampled on CPU at preregistered nearest centers (4x+2,4y+2)
into 34x32, destination(15,8), then uploaded in a 65x49 RGBA texture and consumed by
actual Vulkan. No source area is cropped, but nearest reduction loses samples;
this is **not downsampling quality or GPU scaling validation**. Text-presentation
positive uses its natural grayscale glyph at existing bitmap-provider placement,
not a claim that both presentations have equal design metrics.

Two actual GPU negatives: omit sRGB decode, and route VS16 to the grayscale text
resource (font, natural size and placement all differ; this is not a controlled
same-layout selector-only image-quality comparison). Both compare to the independent emoji oracle; all auxiliary sentinels
are checked before expected color mismatch. Positive full images retain1e-6 and
zero guards, including partial alpha. Source bytes, extracted PNG/font derivatives,
provider receipts and environment provenance remain local. Published evidence is
only source and stripped numerical summary. Not platform or full Scene A acceptance.

Sources: https://freetype.org/freetype2/docs/reference/ft2-basic_types.html
(BGRA premultiplied sRGB), https://www.unicode.org/reports/tr51/ (presentation
selectors), https://www.unicode.org/Public/15.1.0/ucd/emoji/emoji-variation-sequences.txt .
