# Fixed whole-run font fallback -> shaping -> packed atlas -> Vulkan

Dedicated ordered candidates: fixed DejaVu Serif face0, DejaVu Sans face0,
Noto Sans CJK Regular TTC **face2 SC**. Each exact size/hash is checked before
parsing. This dedicated adapter preregisters a 24 MiB bound for the 19,484,784-byte
TTC; the old platform probe's 16 MiB contract is unchanged. FreeType family confirms
face2 Noto Sans CJK SC, and both HB and FT use index2. Font bytes remain local.

Four fixed, explicitly segmented runs at 14px: `ffi`/LTR/en, `a+U0301`/LTR/en,
`سلام`/RTL/ar, `中文`/LTR/zh. Each entire run is shaped with a candidate face; any
missing glyph rejects the whole candidate. The next face reshapes the entire run,
not individual codepoints. Serif serves Latin/combining, Sans serves Arabic, and
CJK SC serves Chinese. In this fixed Serif version, ffi is **ff ligature + i**,
not a single ffi glyph. Combining input produces precomposed aacute, and is checked
against U00E1; this does not certify zero-advance combining-mark positioning.

`expected-shaping.json` freezes the full glyph IDs, UTF-8 clusters, positions,
font identity, upem, direction, language, and HB 10.2.0 version observed in the
first run before regression checks were added. It is an audited provider regression
baseline, **not an independent typographic correctness oracle**. Source text is
four newline-separated runs; recorded byte ranges/global clusters are arithmetic
mapping of this explicit segmentation, not automatic bidi analysis. There is no
paragraph ordering, line breaking, grapheme/script segmentation, emoji-color
fallback, or Android/Windows certification. U+10FFFF exhausting the chain is
explicitly rejected before GPU preparation. No assertion that the environment
lacks Chinese or emoji fonts is made.

FT loads each actual shaped GlyphID from exactly the receipt's face/hash/index.
Cross-face receipt/key mismatch is rejected before rasterizing. The resulting run
bitmaps (integer rounded positions, same-run coverage union) are bounded, packed
into one atlas, then reconstructed by four actual Vulkan vertex/UV quads. This is
run bitmap fallback, not per-glyph GPU layout. Independent screen reconstruction
uses original bitmap pixels/positions, not atlas pixels or generated UVs. All
pixels are checked at 1e-6; that verifies GPU delivery and linear premultiplied
composition, not FT raster quality or shaping semantics by screenshot.

Actual wrong-atlas-route negative samples the Latin atlas region for the Arabic
quad; auxiliary sentinels are checked separately before expected color rejection.
An **additional isolated identity diagnostic**, not a claimed natural business
fallback collision, renders Sans O GlyphID50 correctly and then Serif O GlyphID50
against the same Sans oracle. Both are legitimately shaped/rasterized with matching
receipts; renderer routing intentionally selects the wrong face's complete resource.
It does not bypass the adapter receipt guard. The output must differ visibly.

Base quad preparation performs historical draws separately. New evidence counts:
one four-run positive + wrong-route draw, one single-O positive + wrong-face draw.
Each case uses its own software Vulkan instance; no new cross-instance lifecycle
claim. The helper uses UNUSED/preserve auxiliary attachment fallback, not active MRT.
Raw source/tool/driver provenance and fonts remain local; published report is only
stripped numerical results. First-run local evidence is retained.
