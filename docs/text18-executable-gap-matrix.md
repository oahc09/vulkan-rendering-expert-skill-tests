# TEXT18 original-plan gap ledger

This follows the owner's 2026-11-08 v1.0.18 plan, sections 6, 11 and 13.
It does not add product scope or weaken release gates.

| Condition | Executable coverage | Remaining gap |
|---|---|---|
| C1 glyph/cluster/positions/lifetime | Actual Linux HarfBuzz trusted single-run tests | Android JNI, DirectWrite, full paragraph bidi/fallback |
| C2 bitmap Vulkan | 13-frame synthetic Vulkan lab; font end-to-end increment tracked separately | Full quality board, emoji/variable fonts, MSDF, rotations/perspective |
| C3 bounded path | CPU M/L/Q/C/Z mask fallback, affine, nonzero/evenodd, holes | Tessellation, strokes/caps/dash, nested clips, world labels, extrusion |
| C4 retirement | CPU lifecycle plus single-queue pending transfer consumers | Sampled-descriptor retirement, continuous churn, multiple engines |
| Linear over/ROI | Fixed 1e-6 blend tolerance and tamper rejection | Target display/color management and full visual review |
| Output protection | Separate overlay UNUSED/preserve velocity/ID | Active MRT independentBlend, depth/stencil |
| Package | Exact Skill pin, 200-file budget, deterministic package | Cumulative CORE17/TEXT18 integration after dependency resolution |
| Live/devices | Not run | Real models/host, Android/Windows/mobile GPU/thermal performance |

## Bounded vector fallback

The CPU module is a mask fallback, not a triangle-fan tessellator. It retains
holes instead of making solid triangles. Accepted finite closed M/L/Q/C/Z paths
are in screen space after nonsingular affine transformation. De Casteljau
subdivision accepts a segment when all controls are within default 0.125 pixels
of its finite chord. The convex-hull property bounds curve-to-chord distance.
Independent dense polynomial tests check quadratic/cubic examples, not all
perspective error, bidirectional silhouette distances or raster area error.

Defaults: 32 contours, 512 edges, depth16, 65536 pixels, 4x4 samples and 8000000
sample/edge operations. Exceeding budgets rejects, never truncates. Intersecting,
touching, degenerate and adjacent-backtracking contours reject. No SVG parser,
stroke, topology repair, perspective, clip nesting or extrusion is implied.

Coverage is point-sampled, not analytic area integration. Fractional rectangle
checks use grid-aligned independent area references. Curve approximation tests
do not prove antialias quality for all inputs. Loop budgets are not an OS
resource sandbox; untrusted inputs need isolation.

## Evidence discipline

Failed CI and prior results remain historical. Exact current pair results are
recorded in PR9/14. Old release-contract and base16 remain unchanged. Sibling
CORE17 #10 is not folded in; six partial mappings remain partial. Fonts and raw
environment logs stay local; only source and minimum numeric summaries publish.
Software Vulkan/CPU tests never substitute for real-device or Live gates.

## Current-environment end-to-end increment

The added independent bitmap fixture now joins HarfBuzz shaping by glyph ID,
FreeType 2.13.2 grayscale raster via freetype-py 2.5.1, and the existing real
Vulkan staging/sample/blend/readback implementation. Three trusted local
DejaVuSans runs (O, ffi, Arabic) yield 1/1/3 glyphs, with no missing/clipped
samples. Five self-generated path cases exercise evenodd/nonzero holes,
quadratic/cubic contours and negative scale through CPU masks to Vulkan.
All eight cases stay below the preregistered 1e-6 linear/ROI threshold; current
max 7.15255738e-8. Validation is required, sentinels unchanged. Actual Arabic,
ffi and cubic-path PNGs were viewed. Font outline/raster quality itself has no
independent typography oracle and is NOT accepted by this composition test.

18 CPU path tests pass; actual E2E opt-in test includes malformed coverage,
readback tampering and refusing existing output without changing its bytes.
Official freetype-py is execution-side only; no font or third-party binary is
added to either repository. The same old13-frame GPU lab remains unchanged.

## Controlled churn and phase regression increment

An independent 64-generation single-slot image-transfer lab reuses persistent
buffers, command buffers, fences and timelines. Two consumers per generation
are held pending by explicit host gates; until B completes reuse is refused.
Every generation's 2 independent raw readbacks are checked against its own
pattern. Fixed fixture object counts and bounded cleanup are not GPU-driver
allocator leak proof or a production atlas. Packing/expansion/cancel, sampled
renderer consumers, shared CPU cache across engines and multi-device lifecycle
remain open. Prior two-generation fixture is unchanged.

The actual bitmap experiment additionally tests O at12/20px in four post-hint
quarter-pixel translations through Vulkan. Before running, narrow regression
bounds were fixed at 5% area drift, .15px centroid shift error and 1e-6 blend
error. First results: max relative area drift .000712657, centroid .00544121px,
blend7.15256e-8; these are not a complete Text Quality Board acceptance. Actual
12px output was viewed. No rotation/perspective/MSDF/platform substitution.

## Bounded page growth/cancellation increment

A new CPU AtlasPages reference keeps page identity separate from slot generation,
reserves monotonic upload timeline values across pages, rejects backward route
publication, preserves captured old-page consumers, and enforces page/payload
budgets before atomic backend allocation. Cancellation stops new routing, not
GPU work; the page remains owned until upload and all captured consumers retire.
An uploaded but unpublished candidate retains ownership until explicit publish
or cancel; collection cannot erase pending publication. Disposal failures retain
ownership for retry. Allocator/disposer callbacks must
be atomic on failure; partially completed backend operations need their own
cleanup. Payload bytes describe R8 logical coverage, not VRAM commitment.
Twenty-one CPU tests include failed allocation/disposal, canceled pending capacity,
stale identity/face, signal alias/regression and old snapshots during growth.
The reference is externally serialized and is not a production atlas allocator.

The separate actual Vulkan growth fixture uses two distinct image pages, with
old consumers held pending while a candidate upload is canceled at the host
publication layer. The upload still completes and is diagnostically read back;
actual published routing continues to read the old page. After retirement the
canceled page is really destroyed. A replacement page uploads and publishes,
then the old page is destroyed. This is bounded page-count growth, not extent
resizing, rectangle packing, sampled draw bindings, multiple GPUs or driver
allocation/leak qualification. Live and target-device gates remain independent.
