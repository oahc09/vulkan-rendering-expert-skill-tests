# Scene A board preregistration, before candidate GPU execution

Seven real-content rows, same immutable layout in both representation columns:
Chinese 中文 at18px (NotoSansCJK SC face2); ffi at20px; a+U0301 at20px;
fixed mixed paragraph A سلام 12! at10px (FriBidi with ICU mapping cross-check);
heart U+2764 FE0F production color bitmap (registered 136x128→34x32);
RobotoFlex Ofi at18px with wght100/wdth75 and wght900/wdth125, full remaining
axis defaults identically supplied/read back through HB and FT.
Latin/Arabic use trusted ordered fallback as existing fixtures. Actual input
identities, complete advances/offsets, language/direction, face indices, font
hashes and full axes are frozen once before generation. No per-glyph ink-height
normalization and no re-shaping separately for bitmap/MSDF.

Each monochrome row uses a65x49 tile, baseline(6,32), per-glyph shaped pen/offset translation
quantized once to FreeType 26.6. Real unhinted FT coverage and outline are read
from the same loaded glyph/transform, not an area-generated fake platform bitmap.
Emoji instead retains registered top-left(15,8) and34x32 dimensions.
Whitespace advances are retained though empty glyph images need no texture layer.
Per-glyph layers are composited in the same order; no global evenodd across
independent glyphs. At most16 nonempty glyph layers per row, each65x49.

Common transformations about tile center(32.5,24.5): native,0.75 uniform scale,
90degree rotation, xphase0.25 and xphase0.5. Complete original ink/outline bounds
are checked before GPU execution; an unsupported transform for any row is
explicitly marked UNSUPPORTED_CLIPPING in BOTH columns, never independently
fitted or silently clipped. Long mixed text may not fit the90degree tile.
Perspective is UNMEASURED in this board; existing separate evidence is not merged.

Monochrome rows have two actual GPU representations: FT grayscale bitmap
(manual bilinear fetch) and pinned official RGB-MSDF with existing linear4
subpixel integration. Emoji is explicitly color-bitmap-only, no fabricated
MSDF outline. Same background(.1,.2,.3,.5), ink(.9,.5,.2), opacity.75.
Color emoji uses its linear premultiplied colors and opacity.75 once.
Bitmap numerical composition threshold1e-6; MSDF linear4 sampling/composition
threshold.004. Existing stricter/different MSDF algorithms are not relabeled.
All pixels checked, zero numerical exclusions; auxiliary sentinels independently
exact. Strict numerical failures remain failures, not new tolerances.

Independent CPU sampling/over reconstructs each actual shader. Quality is
separate: original glyph outlines, nonzero per-glyph winding and64 subdivisions
per curved edge plus16x16 pixel supersampling, transformed identically. This is
sampled outline reference, NOT exact curve area or independent platform shaping.
Quality records full/foreground/edge ROI error and geometry-subtracted phase
residual, and per-mode differences. No new universal quality PASS threshold;
status MEASURED_NOT_QUALIFIED preserves prior MSDF results. Emoji source bytes
are independently checked against embedded CBDT PNG as existing experiment.

All tile images are fresh actual GPU readbacks from this board execution, with
same logical Device; contact sheets merely arrange those readbacks. No claims of
same-pass whole board, GPU timing, mobile budget, general scripts or full original
Scene A qualification. Two actual negative shaders double bitmap alpha and alter
MSDF range; numerical oracle must reject, auxiliaries separately preserved.
