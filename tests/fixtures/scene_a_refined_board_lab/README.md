# Registered spatial-resolution and rotation refinement

This new experiment retains the prior multilingual board and its failed-quality
measurements unchanged. The largest observed original error was variable-light
fi glyph553 at half-pixel phase. Its straight stem is x[24.5,25.3125],
y[22.75,32]; shifted by.5, pixel(25,23) has exactly.8125 covered area and
.609375 alpha. The original MSDF yielded.123046875 alpha, error.486328125.
The two adjacent source texel medians were.5 and.453125: neither captured an
interior positive distance. Higher fragment integration cannot recover that
missing source information. The original16x geometric reference is exact for
this straight-edge anchor; the new host test verifies the interval intersection.

The new source atlas has4x resolution in each axis. msdfgen Projection4 maps
unchanged shape coordinates into260x196; Range4 remains shape-space distance,
equivalent to16 source texels and4 original screen pixels. Per-glyph layout,
font, axes, FT bitmap, opacity and original outline reference are unchanged.
Manual bilinear source sampling accounts for density4. The shader still uses
linear4 integration, not more fragment samples. Bitmap/color data remain their
original65x49 arrays placed in larger storage without scaling or regenerating.

The16-band RGBA32F texture payload is13,045,760 bytes versus815,360 before:
16x storage/upload cost. This diagnostic makes no free-speed or device-memory
budget claim. One logical software Vulkan Device performs all tiles serially,
with repeated uploads. Auxiliary attachments remain UNUSED/preserve, not active
MRT. No physical-device/Surface/HDR/hardware-performance qualification is implied.

Output is now a common65x65 square. Original transforms receive exactly+8y
translation. A separately registered square-rotate90 uses the original tile
center and this same output translation; no per-row recentering, fitting or
rescaling. This accommodates the bidi row's49.5625-pixel outline width plus
its finite sampling footprint. Original six rotate90 unsupported labels remain
historical entries; only the new square-rotate90 entries claim actual execution.
Perspective remains unmeasured. Emoji still uses legitimate bitmap-only fallback.

Bitmap1e-6 and MSDF.004 composition/sampling gates are unchanged, zero exclusions.
Independent per-glyph nonzero outline reference is unchanged:64 subdivisions per
curved edge and16x16 coverage, not exact curved-area or independent typography.
Before/after max and ROI errors are reported for every matching row/condition;
the exact stem anchor is separate. Phase/column MAE uses the whole new4225-pixel
tile (not ROI), so must not be compared as the same denominator as the old3185
pixel full-tile averages. Maxima and per-image ROI errors remain visible.
No new universal quality acceptance threshold is introduced: quality remains
MEASURED_NOT_QUALIFIED even if the dominant source-resolution defect improves.
Both actual double-alpha/wrong-range negatives still require independent aux
preservation and color rejection. All source/font-derived artifacts and runtime
fingerprints remain local; only authored sources and minimal numeric results
are published.

Before/after numbers use the previously frozen original report, not a new1x
render during this run. Its exactSHA and each original row's canonical layout/
provider identity digest are fixed in baseline-identity.json and checked. The
new run checks those identities before GPU execution, including glyph metrics,
font face, full variation axes, outline and bitmap placement. This is regression
identity, not an independent typography oracle. The exact rectangular stem's
actual glyph ID and contour corners are likewise checked before generation.
