# v1.0.18 original-plan completion matrix

Assessment against the owner's **2026-11-08 Text, Vector & 2D/3D Composition** plan, not a reduced replacement plan. Evidence baseline: Skill `c0b62a19938a6b9cfce2ea6a5ce18f91b91e6344`, tests `57a1aef66efa36784bb576d2919d9843ef786dd1`. Later incremental results must identify their own commit. **Overall BLOCKED / Draft; M3 in progress.** A local missing implementation is not a device blocker.

Legend: **bounded pass** = only the stated executable contract passed; **partial** = missing original-plan scope; **local open** = implementable here, not yet done; **external unverified** = actual platform/device/model/host not available. Knowledge/static checks never promote an execution layer.

## Milestones and original sections

| Plan reference | Current evidence | Status and outstanding work |
|---|---|---|
| §1, §9, §15 architecture/routing/package | 21 changed Skill files, unchanged 200 runtime file budget; deterministic package and routing tests | Bounded static/package pass; actual host discovery/read not verified |
| §2, §10 M0 baseline | Exact Skill16 and Skill18 CI cohorts; immutable old release contract; TEXT18 candidate contract | Partial: tests base is `feat/v1.0.16-source-review`, not main; CORE17 #10 remains separate; six partial mappings cannot be declared cumulative acceptance |
| §3, §18 sources | Frozen cited knowledge and sources checked statically | Not proof of each API's execution or all recent platform support |
| §4.1 C1 units/IDs/runs | Glyph identity/width/generation CPU negatives; actual Linux HarfBuzz single-run glyphs and positions | Partial: fixed-font ru/sr GSUB-dependent execution added; paragraph bidi, real fallback/font switches and complete multilingual semantics remain open |
| §4.2 Android Java/JNI | Knowledge/contract only | External unverified: no actual Java/JNI platform invocation; not supplied by Linux HarfBuzz |
| §4.3 DirectWrite | Knowledge/contract only | External unverified: no actual DirectWrite run/outline/bitmap |
| §4.4 beyond-64k/new tables | Wide-ID and range contracts | Partial: real capable provider and new font format fixtures unavailable/unverified; uint32 storage is not provider support |
| §5.1–5.4 bitmap | HarfBuzz→FreeType grayscale→actual Vulkan readback for O/ffi/Arabic; fixed 1e-6 blend tolerance | Bounded bitmap, synthetic COLRv0 and A/O MSDF experimental passes; production color glyph/emoji and full comparative quality remain local open; MTSDF is an unimplemented representation option, not an added mandatory gate; fixed variable-font weight/width execution has bounded evidence |
| §5.2 filtering/data | Scalar linear oracle; actual packed UV quads, nearest sampling and bounded padding | Partial: bounded bilinear MSDF with range/derivatives tested; mip bleed, general transforms/packing and complete quality board remain local open |
| §5.3 temporal quality | 12/20px O with four post-hint quarter-pixel phases; area/centroid bounds preregistered | Partial: bounded nearest half/1/1.5 scale and quarter-turn added; arbitrary angles, perspective and comparative representation board remain open |
| §6.1–6.2 path subset | CPU M/L/Q/C/Z bounded flattening, holes, two fill rules, finite affine, controlled reject; five masks through Vulkan | Bounded mask and simple concave ear-clipped triangle pass; general hole/curve mesh quality, stroke/cap/join/dash and broader topology are local open |
| §6.3 clipping | Actual rectangle/circle/rotated-rectangle shader intersection; independent CPU reference and each-layer bypass negatives | Bounded hard fixed clip pass; arbitrary path/AA/stencil/variable clip stack and scene ordering remain local open; fixed hard clips now also execute inside pending packed-glyph lifecycle |
| §6.4 world/3D | Bounded authored concave solid extrusion with actual front/side/depth readback | Partial: general shaped-font extrusion, near-plane clipping, bevel, world lighting/shadows/second view remain open |
| §7.1 key/packing | Finite keys; CPU shelf padding, batch atomicity, sealed-page snapshots, two→three real-glyph logical pages | Bounded packing and actual per-glyph UV-quad pass; not full renderer layout |
| §7.2–7.3 lifecycle | 64 generations/128 readbacks; two actual pages, canceled upload/publication, replacement and retirement; failures retain ownership | Bounded single-queue and combined two-page quad lifecycle pass; six-transition real run/size/direction churn added; bounded fixed-font axis churn added; long stress and broader locale/variation semantics remain open |
| §7.4 consumers | Two immutable sampled descriptor sets and pending timeline-gated fragment submissions; real fence status | Bounded pass; not shader-already-running, multi-queue or multi-device proof |
| §7.4 multi-engine | CPU boundaries described | Bounded serial dual-logical-device offscreen experiment now verifies independent GPU handles and pause/destroy/rebuild with shared immutable CPU glyph inputs; real Surfaces, concurrency and production cache ownership remain open |
| §7.4 MRT | Active 3-color plus D32 write protection and legal wrong-output negatives; old fallback preserved | Bounded pass; bounded authored-solid depth occlusion now tested separately; stencil and general rendergraph/world ordering remain local open |
| §7.5 temporal/HDR | Linear composition checked numerically | Local open: full temporal/HDR handoff and world-motion experiment |
| §7.6 budgets/security | Bounded path/work/atlas input checks, controlled failures, no redistributed system font | Partial: CPU font-service memory and complete cold/hot resource accounting; fixture handle counts are not driver leak proof |
| §8 capability fallbacks | Explicit knowledge and CPU reject paths | Partial: each unimplemented renderer fallback needs execution before support claims |
| §10 M1 | Single-provider host implementation above | Partial, not all platforms/languages |
| §10 M2 | Bitmap and bounded vector mask above | Partial: simple contour mesh added; world/general mesh/clip and full comparative quality remain local open; synthetic COLRv0 and A/O MSDF bounded experimental passes |
| §10 M3 | Current primary milestone | In progress: integration and combined stress gaps above |
| §10 M4 | Split exact-pair CI and local labs | Blocked: cumulative dependency, full labs, semantic Live and target/host gates |
| §11A quality board | Latin ligature, Arabic single run, O phase, same font/raster conditions | Partial: Chinese, mixed bidi, emoji, comparative representations and general transformations missing; one fixed variable-font axis path tested |
| §11B vector/world | Five generated masks, holes/curves/negative scale; hard nested shader clip | Partial: strokes, general/AA clips, shaped-font world meshes/shadows/second view missing |
| §11C churn/overlay | Combined two-page lifecycle plus six-transition real content/size/direction churn | Partial: broader locale/axis semantics, integrated two-engine asynchronous churn, clip and long stress not run; separate dual-device active-output lifecycle now tested; fixed-font weight/width cycles are bounded |
| §12 TEXT18-01…20 | 20 registered cases, paired controls/rubrics, static validation | Registration is not model behavior; all 20 semantic Live results unverified |
| §12.1 old cohorts | Preserved legacy contract and separate CI | Full accepted CORE17+TEXT18 union not established; no invented final scenario count |
| §13 layered gates | Static/CPU/shader/software-Vulkan and narrow ROI evidence | Not platform/model/device/host acceptance; see layer table below |
| §14 target matrices | No actual Android Adreno/Mali or Windows run | External unverified; software Vulkan cannot replace them |
| §16 boundaries | No UI framework/font redistribution/general SVG promise | Maintained; extension knowledge is not implementation |
| §17 implementation prompt | Original gates retained | No completion claim until remaining items are resolved or owner changes scope |
| §19 original read-only status | Original plan retained as historic planning evidence | New implementations are separate, not retroactive changes to original evidence |

## Layer disposition (not a single pass percentage)

| Layer | Verified scope | Not verified |
|---|---|---|
| Static | CI 281 legacy /316 text18; 24 Skill unit | Complete semantic source/API audit |
| Host Unit | CI 250 CPU; bounded lifecycle/packing contracts and GPU integration tracked separately | Production threading and full renderer integration |
| Platform Integration | Linux trusted HarfBuzz/FreeType bridge only | Android JNI and Windows DirectWrite |
| Shader Unit | Actual compiler/SPIR-V tools in opt-in labs | Unimplemented paths |
| Vulkan Integration | Actual software Vulkan upload/draw/readback, packed quads, controlled pending consumers, active MRT/depth write protection and hard clips | Sustained churn/multi-device, general depth ordering/stencil/full renderer |
| Live Model | No model command configured, explicit SKIP | All TEXT18 semantics and final cohort behavior |
| Visual Quality | Narrow fixed ROI/phase oracle; selected rendered images inspected | Full board, independent font outline quality, display/color calibration |
| Device | None | Adreno/Mali/Windows sustained device performance |
| Package/Host | Deterministic package, exact pin/clean checks | Actual external host discovery/read |

## Pre-registered criteria (§13.1)

1. Semantics: limited fixed-provider run checks only; fallback/paragraph and Live remain unverified.
2. Composition: independent linear over reference and 1e-6 ROI tolerance; do not relax after failure.
3. Retirement: pending/final consumers and cancellation tested without illegal use-after-free.
4. MRT: active velocity/ID/depth write protection verified; separate bounded extrusion verifies LESS occlusion; stencil and production integration remain open.
5. Geometry: bounded flattening/mask hole tests plus simple concave ear-clipped triangle and index/area checks; arbitrary holes/stroke/general shaped-font extrusion remain open.
6. Dynamic quality: phase-only area ≤5%, centroid error ≤0.15px, blend ≤1e-6; not all transforms.
7. Stability: fixed fixture inventories and controlled cleanup; no global allocator/driver leak claim.
8. Performance: bounded software renderpass timestamps and CPU submit/wait p50/p95 measured for three MSDF modes; target-device timings, thermal/power and full p99/cold-hot allocation breakdown remain **UNMEASURED**.

Priority local work after the bounded two-page lifecycle: sustained real glyph churn and additional original-plan renderer/quality gaps. Actual packed UV quads and active output/depth write protection now have bounded evidence, not whole-milestone acceptance. Other original-plan local gaps stay visible; they must not be mislabeled as hardware blockers. Retain original failed host-event validation evidence and prior failing CI. Only source and stripped numerical summaries publish; raw logs/environment/font evidence stay local.

## Packed-quad increment (candidate, pending exact-head CI)

The new `text_packed_quad_lab` supplies actual vertex attributes and six xy/UV
vertices per glyph, drawing three real O/f/i rectangles from one padded atlas.
Independent original glyph pixels and integer destination positions, rather than
GPU vertices, reconstruct the expected output. The partially offscreen O tests
viewport clipping. A valid Vulkan draw with one-texel-wrong UV is rejected by the
oracle; out-of-range UV input rejects before GPU setup; readback corruption
rejects. The rendered result was inspected. This advances the packed UV gap in
§5/§7/§13 beyond whole-page sampling; no fractional filtering, shaped-word layout,
MSDF or full asynchronous renderer claim follows. The priority after this bounded
pass remains active MRT/depth protection and combined lifecycle integration.

## Active MRT/depth and bounded nested clip increment

These bounded experiments advance two prior **local open** rows, not the
external platform/device gates. The current table incorporates the increments;
prior commit histories and evidence remain unchanged.

- **§7.4 / §13.1(4):** `text_active_mrt_lab` makes all three color references
  active, queries/enables independentBlend, and uses per-output write masks.
  An active D32 depth attachment is cleared/read back. Color changes while all
  3185 velocity/ID/depth pixels remain exact. Two legal negative pipelines enable
  auxiliary writes or depth writes: actual ID changes to(4,3,2,1) / depth to0 and
  the oracle rejects. Depth compare ALWAYS with write disabled proves preservation,
  **not occlusion**, stencil, rendergraph integration or full world-text behavior.
- **§6.3 / §11B:** `text_clip_lab` executes three nested hard clip predicates in
  the real fragment shader: rectangle ∩ circle ∩ rotated rectangle. The uploaded
  synthetic coverage is not CPU-premasked. Independent CPU polygon ray crossing,
  circle arithmetic and all-pixel linear composition reference check the result;
  bypassing each layer in a valid GPU draw must fail. Actual image inspected.
  This fixed pixel-center hard clip is **not** arbitrary path clipping, AA/MSAA,
  stencil, variable-depth clip stack or a combined glyph renderer.
- Both require enabled validation, fixed1e-6 tolerance and actual readback.
  Software Vulkan is not Android/Windows/mobile hardware or performance evidence.
  Combined asynchronous packed-glyph lifecycle, multiple outputs/devices,
  world-depth ordering and the other matrix gaps remain open.

## Same-process packed draw / lifecycle increment

`text_combined_lifecycle_lab` now joins real packed glyph vertex draws with
explicit page and submission resource owners in **one executable/device/queue**.
A's gated draw and canceled B upload have separate command buffers, fences,
staging/vertices/readbacks; draw targets/framebuffers are also separate. A real
published pointer is updated only after upload completion and rejects canceled
or older generations. `drawPublished` reads that pointer rather than selecting
a hardcoded correct page. The canceled candidate upload still finishes. A is
actually drawn again after cancellation; B is retired, recreated as generation2
with half-strength glyph coverage, uploaded, published and drawn. Old A retires
only after the actual consumers finish. Pending submissions are completed before
owned resources are destroyed, including a controlled pending-exception run.

The same-process flow has three accepted readbacks and one legal wrong-route
readback from a completed but canceled page. Independent original glyph pixels
and positions reject wrong routing, stale old-generation bytes and forged event
records. Host publication and pending retirement guards are exercised before
any invalid Vulkan operation. Object-state-derived events record routing and
live page counts; validation stays mandatory. No illegal use-after-free test.

This resolves the **minimal combined two-page cycle**, not the full §11C stress
scenario. Generation2 attenuates the same trusted glyph coverage, not a change
of language/variation/fallback. Sustained real glyph/size/locale/axis churn,
multiple engines/devices, active MRT/depth/clip combined with this flow,
production threading/allocator/device-loss recovery, and real-device/Live gates
remain open. Single queue means B upload waits behind gated A; no parallel GPU
execution or mobile performance claim. Atlas page counts exclude inherited
setup resources and do not establish driver/CPU service leak freedom.

## Six-transition real-content and affine sampling increment

`text_content_churn_lab` replaces the prior attenuated-coverage-only input with
seven genuinely different shaped/rasterized run inputs (O/ffi/Arabic, sizes14/20/24,
ltr/rtl, explicit en/ar/tr language values). Six transitions occur in one Vulkan
process/device/queue, with18 primary draws and13 uploads. Each transition has
pending old draw + canceled new-content upload, a real retained-old route draw,
then fresh upload/publication/new draw and retirement. Every round releases
completed submissions and ends with one live page object / zero submission
objects. Independent original raster pixels verify all18 outputs; stale readback
and publication-event mutation fail. These bounded fixture counts are not driver
or font-service leak qualification, nor multi-engine/thermal stress.

Each run is a composited bitmap packed into one padded UV quad, not newly proven
per-glyph geometry/layout. Language is passed to HarfBuzz but locale-specific
shape changes are **not** established. No variable axes exist in the trusted
DejaVu input or the368 TTF/OTF files inspected in the local font directory;
variation is **unverified for this run**, not a claim that no suitable official
variable-font fixture could be obtained later. Full locale/fallback/variation
semantics and target-platform execution remain open.

`text_affine_quality_lab` adds actual O quads at0.5/1/1.5 scale and90-degree rotation.
An independent inverse pixel-center nearest-sampling reference checks all color
and ROI samples at1e-6 and accumulated coverage area at1e-3 (fixed before runs).
Valid wrong UV and corrupted readback reject. Actual small and rotated outputs
were inspected. Normalized area change is an aliasing diagnostic, **not a font
quality gate**: reproducing nearest aliasing does not establish optimal filtering,
MSDF, arbitrary-angle/perspective or temporal-transform quality. Other original
plan gaps and device/Live/host requirements remain unchanged.

## Fixed-source real variation-axis churn increment

The absence of axes in the earlier local DejaVu run was a fixture limitation,
not a permanent platform blocker. A separate **execution-only** Roboto Flex font
was obtained from the Google Fonts organization upstream at immutable commit
`04263028f0fe6dbb0cac9df9fc69e3dd69668b26`, under SIL OFL1.1. The1,775,480-byte
font's Git blob identity and SHA256 were checked. The runner requires that exact
SHA256 before parsing. No font file is installed or included in either repository.
Earlier DejaVu evidence remains unmodified and still has no variation acceptance.

`text_variation_churn_lab` adds a separate adapter, leaving the old provider bridge
unchanged. All13 axis defaults+overrides are sent to **both** HarfBuzz and FreeType,
then design-coordinate readbacks must match exactly. Fixed shared float32/16.16
coordinates prevent silent quantization; unknown/nonfinite/range/bool inputs
reject. HB weight900 paired with FT weight100 deliberately rejects before raster.
Optical size remains explicit14, not an implicit function of20px text size.

Seven configurations of Latin Ofi change wght/width, produce seven distinct actual
coverage pages and measurable glyph advance changes, then feed six actual
same-process Vulkan transitions (18 primary draws /13 uploads). Independent source
pixels verify all readbacks, stale images and forged publication records reject,
and lifecycle checks/controlled resource retirement remain in force. This is
bounded actual variation execution, not just metadata variation. Source/tool/font
and full axis receipts stay local; only stripped numeric outcomes publish.

Remaining: locale-specific fallback/paragraph semantics, other axes/fonts/color
formats, comparative typography/MSDF quality, arbitrary transforms, production
multithreading and multiple devices/outputs, target-platform/device/Live/host
acceptance. The source input's OFL license is not a platform/vendor certification.

## Fixed-font language-dependent GSUB churn increment

`text_locale_churn_lab` advances beyond language-parameter pass-through. The
existing DejaVuSerif-Italic font is size/hash guarded before parsing. Independent
offline GSUB inspection identifies cyrl/SRB locl SingleSubst mappings for the five
Cyrillic letters `бгдпт`; actual HB glyph IDs must match those fixed-font mappings.
The same string,16px,ltr,destination(3,5) and font remain unchanged while only
ru/sr language alternates. The repeated ru pages match one another, repeated sr
pages match one another, and the two actual coverage hashes must differ.

Six same-process Vulkan transitions give18 primary draws/13 uploads using the
existing guarded cancellation/publication/retirement flow and independent raster
pixel references. Stale-language images and forged publication records reject;
actual Serbian-localized output was inspected. No font is downloaded or included.
This is evidence of one real language-dependent font substitution path, **not**
all-language correctness, fallback/paragraph bidi, every locale/font/provider,
real Android/Windows, typography quality or device/Live/host acceptance. Broader
original-plan gaps remain visible rather than being relabeled complete.


## Simple-contour Vulkan mesh increment

`bounded_vector_mesh` supplies bounded ear clipping after existing contour
validation, not a general triangle fan. One concave eight-vertex contour and
its mirrored winding each emit six triangles, conserve area960 and produce
960 covered pixels through actual vertex-buffer Vulkan draws. Independent
CPU point-in-polygon references check linear blend <=1e-6 and preserved
sentinels. Two actual wrong-fan draws fail; copied readback corruption rejects.
The rendered notch was inspected. Seven selected CPU/GPU tests passed.

Holes/multiple contours explicitly reject to the separately tested mask option;
this is not an integrated production fallback or a general hole tessellator.
Curve-to-mesh quality, strokes/caps, extrusion/bevel, world depth/shadows/second
view, full quality board and external platform/device/Live gates remain open.
Only source/docs and numerical summary publish.


## Synthetic COLRv0 color-glyph increment

`text_colrv0_lab` creates a disclosed synthetic two-layer COLRv0 font locally,
then actual FreeType parses glyph layers and three CPAL palettes and rasterizes
layer coverage. A real RGBA sampled texture and Vulkan shader perform ordered
premultiplied layer composition and hardware background blending. Independent
CPU expectations use predeclared rectangle geometry and raw palette constants,
not provider coverage or GPU-uploaded colors. The third palette includes
non-endpoint RGB, explicitly decoded from sRGB to linear; alpha is not decoded.

Three palettes satisfy 1e-6 per-channel error (maximum3.555e-8) and preserved
sentinels. Actual wrong-color and missing-sRGB-decode draws fail the oracle;
illegal input size/range reject before GPU setup, and a wrong-palette readback
copy rejects. Rendering was inspected. No generated/system font is uploaded.

This is a synthetic COLRv0 provider-to-GPU path, not production emoji or COLRv1
paint-graph/SVG/bitmap-color support. Separate text opacity, arbitrary layer
complexity, other color formats, active-MRT combination, full typography and
Android/Windows/device/Live acceptance remain unverified.


## Official edge-colored MSDF experimental increment

The new lab extracts trusted-font A/O outlines through HarfBuzz glyph identity
and FreeType, then uses official msdfgen core pinned to
`1874bcf7d9624ccc85b4bc9a85d78116f690f35b` (external local dependency, not
bundled). True edge-colored RGB distance values, not three copies of scalar
coverage, upload into linear RGBA32F and use bilinear median reconstruction
with derivative-based screen distance range. A=1 is padding, not MTSDF.

Eight positive draws cover scale0.75/1/1.5 and0.25px phase for A/O. An independent
CPU bilinear/median blend reference checks numerical execution; a separate
source-outline16x16 supersampled reference checks bounded coverage. The fixed
experimental limits were registered before first build: sampling2e-4, ROI
MAE0.04, edge MAE0.16, maximum coverage difference0.45. Actual worst sampling
error2.379e-6, ROI MAE0.01674, edge MAE0.02590, **maximum local coverage
difference0.3997**. The last metric is substantial: this is NOT pixel identity,
optimal small-text quality or complete original-plan acceptance.

Actual single-channel, wrong-sRGB and wrong-range GPU negatives reject. The
existing UNUSED/preserve sentinel path is unchanged, not an active-MRT combined
result. Padding/clip, pinned source/hidden-index flags and pre-parser font hash
guards are enforced. First two engineering failures (adapter count and missing
inherited shader) remain recorded; no numerical threshold was loosened.

Still open: sharper local corner agreement, complete representation comparison,
more scripts/fonts/transforms, arbitrary perspective/minification, MTSDF,
production atlas/churn integration for this path, Android/Windows/mobileGPU and
Live. Only adapter source/docs/stripped numbers publish; upstream source, font,
raw builds and machine provenance remain local.


## MSDF corner-coverage diagnosis and subpixel integration experiment

The prior A maximum coverage difference0.3997 is retained as baseline evidence.
It is not explained by a half-pixel alignment error or merely a coarse reference:
for the native worst pixel(32,15), original16x16 reference0.96875 converges to
0.96655 at64x64 and exact polygon clipping gives0.966512, versus GPU0.56905.
A large-scale pixel has matching true/MSDF center-distance reconstruction but
center-based coverage0.43024 versus exact pixel area0.81814. Thus center-distance
to area approximation itself loses sharp-corner coverage; sampled field/pseudo-
distance reconstruction contributes separately. No msdfgen library bug is claimed.

A separate fixture preserves the old generator/atlas, cases and original gates,
then compares actual GPU subpixel integration with independent CPU oracles:
16x16 binary distance sign (256 texture samples/pixel) and4x4 narrow linear
coverage (16 samples/pixel). Exact signed polygon clipping supplies an independent
A area reference; curved O still uses the earlier sampled curve reference.

The binary method closely follows the same16x16 reference, but A exact maximum
error remains about0.0180–0.0308. The lower-cost linear method reaches about
0.0124–0.0195 against exact A area, while agreeing less closely with the sampled
reference. This is why same-grid agreement cannot establish pixel identity or
rank methods by itself. Both are experimental measurements, **not** a replacement
for full quality/performance acceptance. Target-device cost, more glyphs/curves,
transform/perspective coverage, and production path integration remain unverified.

Public status is MEASURED_NOT_QUALIFIED, not a general quality PASS. All source
assumptions and sample costs remain explicit; old evidence is not overwritten.

A preliminary CPU diagnostic attempted a spatial ROI shortcut and clipped the
large A; that invalid diagnostic is retained locally and is not acceptance
evidence. The candidate oracle instead uses only a same-sign/saturation test
across all contributing bilinear texels, otherwise explicitly samples the full
pixel footprint. Neither reference nor GPU input is cropped by a guessed ROI.


## Progressive curve mesh increment

Eleven actual quadratic-cap triangle draws cover fixed scales0.5–1.125 with
quarter-pixel phase. Each frame regenerates screen-space flattened vertices;
19vertices/17triangles remain sufficient across this narrow interval. Dense
analytic curve samples stay within0.125px; original analytic fill checks linear
blend<=1e-6 outside a predeclared0.25px boundary guard. Guard counts/errors and
all hard-edge mismatches remain reported (up to41 pixels in one frame); this
is not pixel consistency, temporal stability or AA quality acceptance. Actual
stale-scale readback rejects. An initial test's mistaken expectation of changing
vertex counts was corrected without changing scales or numerical gates.


## Bounded solid vector extrusion

One authored concave U contour produces28 realxyz triangles: ear-clipped caps
and sides, with closed opposite-directed edge incidences and outward cap
orientation. An actual D32 LESS/write pipeline renders visible front/side faces
under a fixed affine oblique projection. An independent original-contour ray
reference, not triangle output, checks all color/depth pixels<=1e-6; normal and
reversed submission order agree. Maximum color2.384e-8/depth1.133e-7,600front
and315side pixels. Active auxiliary MRT write masks preserve sentinels. Actual
disabled-depth and corrupted-depth controls reject.

The initial cap orientation was inconsistent with sides while culling-off hid
it; review corrected winding and added directed-edge validation before publishing.
Back cap is submitted but not visible in this view. This is an authored vector
solid experiment, not general shaped-font extrusion, holes/bevel, lighting,
shadows, perspective/near-plane, second camera or full renderer integration.


## Software-only MSDF renderpass cost diagnostic

Timestamp capability, actual queue valid bits/period and query availability are
checked. A dedicated timestamp interval surrounds only the renderpass; upload
and readback are separate waited submissions. This includes renderpass and
raster/attachment costs, not pure fragment shader time. Three modes rotate
order, each5warmups then30measured cycles, with nearest-rank p50/p95/max. Every
draw checks full RGBA against its freshly validated preparation outside timing,
and sentinels remain exact. CPU submit/wait costs are separate; do not sum GPU
time and overlapping CPU wait. Unsupported capability records NOT_MEASURED.

The frozen prepublication local65x49 A/native software Vulkan run with validation
enabled gave GPU renderpass p50/p95 milliseconds: baseline0.505/0.784,
binary16 5.077/6.470, linear4 0.815/1.277. Raw samples and complete local
provenance remain available; public report omits environment identifiers. This
is not mobile performance, a frame budget, thermal/power result or general
claim of production speed. Earlier two local runs remain evidence, not silently
selected best values. No relative-speed assertion is used as a test gate.


## Exact-head stage reconciliation

At tests `57a1aef66efa36784bb576d2919d9843ef786dd1` paired with Skill
`c0b62a19938a6b9cfce2ea6a5ce18f91b91e6344`, the explicitly selected local
software-Vulkan/CPU experiment suite ran176passed/0skipped (363.81s). This is
not the entire original plan. CI43679678151 separately checked281legacy and
316TEXT18 static cases,250CPU,4historical snapshot and24Skill unit tests in
each appropriate cohort. Opt-in Vulkan labs are not exercised by that CI.
Both semantic Live steps explicitly skipped because no model command exists.

The final exact-head cost rerun was materially noisier than the frozen report:
renderpass p50/p95 ms baseline0.502758/2.673234, binary16 5.348178/8.597959,
linear4 0.803049/5.062994. These are separate retained runs, not a choice of the
best tail latency. No stable production performance conclusion follows.

Dependencies remain unchanged: TEXT18 testsPR9 is based on
`feat/v1.0.16-source-review@528ba9ea7b417684c1066aceabd9a79cae4cd05b`,
notmain. Its legacy release contract still pins Skill16
`416f4a6c0c887dee72bcc6dca13ce9c857d7957f`; its candidate pins Skill18c0b62.
CORE17 testsPR10 at `4fc46c4788cfaf4836037b66fa17d403970395d3` is a separate
sibling with six partial mappings, not silently included cumulative acceptance.
SkillPR14 and testsPR9 remain Draft/BLOCKED, without merge or base change.

Original §13.1 criteria remain unchanged. Two-device/output isolation and
combined active-MRT/clip lifecycle are local implementation gaps; actual
Android JNI, DirectWrite, target physical GPUs, sustained device performance,
external host discovery and semantic Live are external unverified gates.
Neither list can be erased by passing these finite software experiments.


### Remaining local priorities, without extra acceptance conditions

1. Original§7.4/§11C two engine/output isolation with shared read-only CPU
   inputs and independent GPU ownership, including pause/destroy/rebuild.
2. Original§7.3 mask producer→sample dependencies and§7.4 surrounding
   pre/overlay/post state rebind, active-output and clip behavior combined with
   lifecycle, rather than separately passing fixtures.
3. Original§5.1/§11A same-font/layout comparative bitmap versus the selected
   MSDF path under fixed transform/subpixel sequences, with actual stable
   representation switching and fallback. Independent algorithm experiments
   do not establish end-to-end switching or temporal quality.
4. Original§11B shaped glyph outline→finite world mesh/extrusion with the
   promised scene interactions, rather than only an authored U solid.

The plan selects MSDF/MTSDF and describes analytic curves as an optional
comparison path; implementing every representation is **not** a new acceptance
condition. Likewise, no general production UI/font framework is added. Existing
pre-registered reference conditions and limits stay fixed; missing measurements
remain missing instead of being replaced with new favorable thresholds.


## Bounded dual-logical-device active-output lifecycle

One process now creates A/B simultaneously with independent VkInstances,
VkDevices, queues, GPU images, descriptors, pipelines, command resources and
readbacks. Shared const CPU masks come from real HarfBuzz/FreeType O/ffi/Arabic
inputs. Each draw explicitly rebinds its own pipeline/descriptors. A pause
guard rejects without drawing, while B actually renders; after A destruction
B renders again; after A reconstruction both render. A controlled exception
after a fence-complete draw destroys A, and B continues successfully.

Eight positive readbacks retain the existing independent CPU over reference
at1e-6, max7.153e-8. All three color attachments are active: velocity/ID writes
are masked, D32 ALWAYS/no-write preserves.375. Wrong-input actual GPU output,
stale readback and forged lifecycle records reject. Three fixture devices
created/three destroyed and peak two live do not prove driver leak freedom.

This advances original§7.4/§11C without creating a new acceptance criterion.
It is a serial pair of logical devices using the same configured software Vulkan
implementation, not different physical GPUs, real window/Surface recreation,
concurrent scheduling, production shared font cache or arbitrary pending-failure
recovery. No cross-instance physical-device UUID identity claim is made.
Asynchronous atlas churn with clip/state handoff still needs combined evidence;
physical platform/device/Live gates remain unchanged and both PRs remain Draft.


## Integration evidence cannot be added arithmetically

The historical pending packed-glyph lifecycle, active-MRT, hard-clip and dual
logical-device experiments exercised different executables/resources. Passing
all of them did not establish a single combined renderer path. New integrated
experiments must name their actual command-buffer/resource ownership and their
independent reference. Likewise, separate bitmap/MSDF runs do not establish
stable representation switching, cache reuse or full dynamic quality.

Only the explicitly exercised conjunction may close a local matrix item. GPU
shader clip is not a GPU-produced mask image with producer→sample lifetime;
serial logical devices are not simultaneous GPU execution or real Surfaces;
a selected A outline is not the full multilingual hinted-font quality board.
Original§13.1 criteria and optional-representation boundaries remain unchanged.


## Joint pending-glyph / clip / active-MRT increment

A new pipeline now actually joins the previously separate conjunction in one
process/device/queue and draw submission: packed glyph vertex UVs, three hard
fragment-shader clip predicates and three active color attachments with queried
independentBlend/write protection, inside the real timeline-gated page
publication/cancellation/retirement engine. The GPU atlas remains unclipped.
Original glyph samples plus independent CPU clip predicates define the reference
at unchanged1e-6; three positive images have max error7.153e-8. Main flow has
four draws total including the required diagnostic canceled-page wrong route.

The fixed layout was chosen by CPU boundary analysis before the first joint GPU
run. Bypassing rectangle/circle/rotated rectangle exposes22/38/25 nonzero glyph
pixels;252 nonzero pixels remain visible in the positive. Each clip bypass and
incorrect auxiliary write mask runs a full legal GPU lifecycle and is rejected.
Pending exception cleanup, stale readback and publication-record tamper controls
remain explicit. Preparation/negative runs are not counted as positive frames.

This closes the **bounded conjunction**, not a general renderer. It has no
depth attachment, stencil/AA clip, GPU mask producer pass, pre/overlay/post scene
state restoration, dynamic font content, production allocation/device-loss
recovery or physical-device/Live evidence. The underlying generation2 still
attenuates the same trusted coverage. The earlier standalone experiments remain
historical evidence and are not retroactively labeled joint execution.


## Limited same-device bitmap/MSDF stateful routing

One real shaped A glyph supplies the same normalized linear outline/layout for
two separate GPU images, descriptors and pipelines retained by one VkDevice.
Ten scale/phase frames use a stateful selection rule fixed before execution:
start bitmap; scale≤0.9 selects bitmap, scale≥1.1 selects MSDF, between those
retain previous representation. Observed routes are0001110001. These are finite
experimental scheduling conditions, not universal typography acceptance limits.
Each selected image uploads only after the preceding draw completes; there is
no implemented cache service or asynchronous resource reuse claim.

Bitmap here is unhinted exact polygon/pixel-area coverage at the target transform,
not a platform-hinted raster. Its reference is also its generation source, so
near-zero area discrepancy verifies transport/composition rather than an
independent rasterizer. The same exact area reference is independent of the
MSDF representation. Existing bitmap1e-6 and MSDF linear4 0.004 sampling/over
tolerances are unchanged; measured maxima are9.758e-7 and3.230e-6 respectively.
The legal opposite representation is drawn immediately at hold frame2 without
changing state and rejected by both route and expected-pixel checks (.007329
pixel error versus the bitmap reference).

MSDF maximum coverage discrepancy from exact area is about0.02304 in this
sequence. Adjacent-frame same-pixel coverage changes minus exact geometric
changes are reported as residual max/union-foreground ROI MAE, without a new
pass threshold. This is not a perceptual flicker metric or motion-compensated
temporal acceptance. Output remains **MEASURED_NOT_QUALIFIED**. Previews were
viewed, but their intended scale/phase change does not prove imperceptible
representation switching. No rotation/perspective, platform-hinted comparison,
unsupported-provider fallback, multilingual quality board or target-device
performance has been established. UNUSED sentinel protection in this switching
path is not the new active-MRT/pending joint path described above.
