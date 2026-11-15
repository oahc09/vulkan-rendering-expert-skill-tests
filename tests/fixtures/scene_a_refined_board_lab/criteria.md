# Registered refinement, before new GPU draws

Original Scene A seven rows, glyph IDs, positions, 26.6 transforms and alpha
contracts are unchanged. Original 1x evidence and six unsupported rotations remain
historical results, not overwritten. New output is uniformly65x65. All original
transforms gain exactly+8px y output translation. New square-rotate90 uses the
same original center(32.5,24.5) and this+8y; no per-row fitting or rescaling.
Original rotate90 entries stay unsupported for monochrome rows as historical
labels; the new square-rotate90 explicitly tests the larger common output.

MSDF source becomes260x196 (4x each axis), generated from original outline through
Projection(4) and Range(4) in shape units, equivalent to16 source texels and4
original screen pixels. Shader samples at4x source coordinates and retains
linear4 integration. Bitmap source/data remain original65x49, packed into the
same larger band storage without resampling. The16-band RGBA32F upload payload
is13,045,760 bytes versus815,360:16x, not a free performance improvement.

Prior worst pixel source(25,23), output now(25,31), variable-light halfphase:
actual glyph553 straight stem x[24.5,25.3125], y[22.75,32]. Phase+.5 gives exact
pixel area.8125 and alpha.609375. Old1x MSDF alpha.123046875, error.486328125;
old texel median at(24,23)=.5 and(25,23)=.453125: neither contains positive
interior distance. This is spatial source undersampling, not composition error.
The reference16x grid is exact on this registered straight-edge anchor.

Keep bitmap1e-6/MSDF.004 sampling thresholds, zero exclusion. Record full-case
outline quality max/ROI/edge and phase residuals, plus before/after anchor.
No universal visual quality PASS is introduced. Whole-tile MAE is not ROI MAE.
Two actual double-alpha/wrong-range negatives and independent aux preservation
remain mandatory. Original-outline sampled reference remains independent of
MSDF atlas, but not an independent platform shaper or exact curved-area oracle.
Perspective and hardware performance remain unmeasured.
