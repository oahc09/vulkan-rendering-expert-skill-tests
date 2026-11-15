# TEXT18 original-plan gap ledger

This follows the owner's 2026-11-08 v1.0.18 plan, sections 6, 11 and 13.
It does not add product scope or weaken release gates.

For the current full original-plan status use
[text18-original-plan-completion-matrix.md](text18-original-plan-completion-matrix.md).
The table and dated increments below preserve progressive evidence; later increments
resolve only their explicitly stated earlier gaps, not the entire milestone.

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

## Bounded packing / descriptor-consumer split

A deterministic CPU shelf reference packs validated coverage rectangles with
padding, validates full batches before publication and preserves sealed pages.
Candidates use owner/revision checks, cancellation, snapshot copying and maximum
page/extent budgets; oversize/full failure leaves state unchanged. Twelve CPU
tests include overlap/padding, growth, atomic budget failure, cancellation,
foreign/stale batch and immutable snapshots. It is externally serialized and
not an optimal allocator or a secure parser of arbitrary mutated Batch objects.

Real trusted O/f/i glyph rectangles exercise two logical24x24 pages growing to
three; a canceled staging batch leaves published pages unchanged. Actual Vulkan
whole-page sampling/readback checks all three, max ROI7.15e-8 at1e-6 tolerance,
validation enabled. Packed-page PNG was viewed. This is distinct from rendering
UV-addressed glyph quads, filtering/mip safety or the separate pending descriptor
consumer experiment. It does not turn fixed-page experiments into full atlas
acceptance; target hardware/Live/platform limits stay open.

The independent descriptor fixture now submits actual fragment draws through
2 immutable descriptor sets bound to distinct images on one device. Each whole
submission is held behind an explicitly enabled timeline semaphore at the
ALL_COMMANDS stage; a real NOT_READY fence precedes host release and SUCCESS.
This proves pending submitted consumers, not that a shader was already running.
Page/set switching and destruction occur only after completion. Two patterns
are independently verified, and forged completion/old-page substitution fail.
The initial host-event approach failed validation (VUID-vkSetEvent-event-09543),
was not accepted and was replaced by the timeline mechanism. Raw failed evidence
is retained locally. This remains separate from packed-UV glyph draw integration,
multi-queue/device access and target-device qualification.

## Active-output and hard-clip increments

The separate active MRT fixture now uses three actual active color attachments
plus active D32. independentBlend is explicitly queried/enabled; velocity/ID
write masks are zero, depth writes disabled. Readback checks all sentinel pixels.
Legal auxiliary-write/depth-write negatives change real attachments and fail
an independent oracle. Depth compare ALWAYS does not test geometry occlusion.
The original UNUSED/preserve fallback is unchanged.

A separate bounded nested-clip fixture intersects a rectangle, circle and
rotated rectangle directly in its fragment shader. A CPU ray-crossing polygon
reference and circle arithmetic independently reconstruct expected coverage.
Each layer-bypass draw must be rejected. This hard pixel-center example is not
AA, stencil, arbitrary vector paths or production clip-stack integration.
Combined renderer lifecycle and real target/Live acceptance remain open.

## Same-process packed glyph lifecycle

A new combined fixture uses one Vulkan executable/device/queue with explicit
PageResources and independent SubmissionResources. Real packed vertex draws
consume the actually published page pointer. A stays pending while a distinct B
upload is queued and canceled; publishing pending/canceled/older generations and
pending retirement are refused before any invalid GPU action. After completion,
actual routing still draws A; the canceled page is retired and a new generation
uploads/publishes/draws before old A retirement. Legal wrong-page readback,
substituted stale bytes and forged events are rejected. A pending exception run
releases its gate and awaits all submissions before cleanup.

This is one controlled two-page cycle using scaled original glyph coverage,
not sustained language/variation churn, multi-device concurrency, production
allocation recovery or the active-MRT/clip experiments combined into one frame.
Raw failure/debug/environment evidence stays local; no target/Live claim.

## Real-content six-transition and affine diagnostics

A separate one-device executable now cycles seven distinct real shaped/rasterized
content pages over six cancel/publish/retire transitions (18 primary readback draws,
13 uploads). It releases completed submission objects each round and retains one
live page. Inputs cover O/ffi/Arabic and sizes14/20/24, including RTL. This is a
composited run-bitmap UV quad, not per-glyph layout. Language pass-through does not
prove locale-specific behavior. The trusted input has no variable axes; variation
is unverified for this run and remains a separate fixture requirement.

Actual half/unit/1.5-scale and quarter-turn bitmap sampling now has independent
pixel-center reconstruction and valid wrong-UV rejection. Nearest aliasing is
measured, not accepted as general font quality. Neither finite experiment supplies
multi-device/target-platform/Live or comprehensive original-plan acceptance.

## Fixed-font real axis execution

A separately verified OFL Roboto Flex input now supplies actual variable axes;
this does not relabel the earlier DejaVu no-axis run. A new adapter sends complete
matching design coordinates to HB and FT and reads both back. Seven Latin weight/
width configurations yield different actual coverage before six one-device
cancel/publish/retire transitions. Independent GPU readbacks and actual provider
mismatch negatives distinguish this from a metadata-only axis change. The font
remains execution-side only and is hash-guarded before parsing. Other fonts/axes,
locale semantics, general typography and real target/Live gates remain open.

## Actual fixed-font locale substitution

A locale fixture now pins one existing font's cyrl/SRB GSUB locl mapping and
asserts actual glyph IDs. Only ru/sr language changes for the same Cyrillic text,
size, direction and destination; repeated groups stay stable while their two
coverage images differ. Six actual same-device cancel/publish/retire transitions
verify eighteen readbacks and stale-language rejection. This closes a narrow
language-dependent path, not full locale/fallback/paragraph/platform acceptance.


### Bounded concave mesh increment

Actual ear-clipped triangle lists now cover one validated concave contour and
its mirrored winding, with six triangles/area960 per case. Independent ray-crossing
CPU reference, preserved sentinels and actual wrong-fan negatives pass. Holes
explicitly reject; general topology, curves-to-mesh quality and all 3D extrusion
features remain open. See the original-plan matrix and vector-mesh fixture scope.


### Synthetic COLRv0 color increment

Actual FT layer/three-palette parsing and coverage now feed Vulkan color-layer
composition. Independent fixed-geometry/palette reference checks linear blend,
sRGB decoding, and preserved sentinels, with legal wrong-color/missing-decode
GPU negatives. Synthetic two-layer scope only; not production emoji/COLRv1 or
independent text-opacity qualification. See fixture README and original matrix.


### Edge-colored MSDF experimental path

Actual trusted A/O outlines pass through pinned official msdfgen to a Vulkan
RGB-distance/median/bilinear shader, eight bounded scale/phase cases. Separate
sampling and independent outline references plus three wrong-shader/range GPU
controls execute. Coverage max difference0.3997 is within the pre-registered
permissive0.45 experimental bound, **not pixel identity or full typography
quality acceptance**. MTSDF, broader quality and target/Live gates remain open.
