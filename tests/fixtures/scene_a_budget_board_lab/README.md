# Compact Scene A storage, explicit byte-budget fallback, bounded perspective

This stage preserves the prior full4x and original1x experiments. It separately
classifies the remaining worst reported pixel: ! stem at halfphase output(55,37)
has exact area39/64*61/64, alpha.43560791015625. The16x reference had.3955078125;
the actual4x GPU had.4482421875. Thus exact local error is.01263427734375,
not the reference-relative.052734375. The old metric is preserved, not relabeled
as a GPU improvement. Other curved-area metrics still use the same sampled
outline reference and remain MEASURED_NOT_QUALIFIED.

Fresh trusted HB/FT layouts must match prior immutable row identity. Official
pinned msdfgen generates full4x CPU sources before the crop. Glyph bounds plus
three screen pixels are rounded outward; source origin and crop rectangles are
encoded exactly in a header, followed by vertical packed images. The GPU actually
allocates/binds images at each row's chosen dimensions. Numeric oracle samples
uncropped original layers and never consumes packing metadata. Historical full4x
GPU readbacks are separately compared with maximum deltas; that comparison is
historical, not a fresh full4x GPU run here.

Budget400000 selects4x for all monochrome rows. Budget200000 chooses4x for
combining/variable-light but explicit bitmap fallback for Chinese/ffi/bidi/
variable-heavy. Emoji retains color-bitmap fallback. Budget4096 rejects all rows
before Vulkan construction. Selection uses only requested image W*H*16 bytes,
including header and padding, never output quality. These fixed budgets are
experimental inputs, not product/mobile thresholds. Tight storage is not an
adaptive density algorithm. No2x claim is made. All fallback quality degradation
is reported rather than claiming bitmap equals4x MSDF.

W*H*16 is actual requested format payload/upload size, not
VkMemoryRequirements.size, driver alignment or total VRAM. Full-source CPU
production is not optimized here; CPU peak/native allocator/overall end-to-end
memory is unmeasured. Each row/budget has its own logical Device, sharing one
compact texture across its transformations. There is no whole-board simultaneous
resource peak or cross-Device lifecycle claim.

Perspective is one fixed real six-vertex projected quad, w=1+(x-32.5)/128,
scale.75 and outputcenter(32.5,32.5). Sourcew is positive throughout. Stable
fragment inverse homography reconstructs texture positions; this is NOT hardware
varying interpolation certification. MSDF uses local inverse-Jacobian L1 row
norms to estimate a symmetric screen-distance range, not exact anisotropic area.
CPU sampling derives footprint by finite differences; the separate original
outline is projectively transformed for geometric coverage. Both budgets and all
seven rows execute this condition. The same frozen layout has no per-row fit.

Bitmap1e-6/MSDF.004 numerical gates, zero exclusions, remain unchanged.
Aux images are independently checked UNUSED/preserve, not active MRT. Actual
wrong-origin and affine-inverse shaders are legal negative controls; they must
fail composition while auxiliary data remain intact. Full-tile metrics must not
be presented as ROI errors or universal visual qualification. Real mobile
hardware, general perspective/near-plane topology, Surface, and performance
budgets remain unmeasured.

Run requires a prior actual refined board output as TEXT18_REFINED_BOARD_SOURCE
for historical manifest/readback comparison, plus TEXT18_VARIABLE_FONT and
TEXT18_MSDF_SOURCE trusted execution-side inputs. No font or derived atlas is
published. Full logs, image resources and environment fingerprints remain local.

The first perspective run failed emoji composition at1.0528854150204658e-6
against unchanged1e-6. Its partial readbacks/log remain local. The fixed camera
now computes bitmap/color pixel-center texel coordinates by integer numerator/
denominator and remainder before interpolation, eliminating cancellation from
adding and subtracting the source center. Independent inverse reference and
geometry remain unchanged. The wrong-inverse shader explicitly bypasses this
correct fast path, so the negative is not accidentally repaired.
