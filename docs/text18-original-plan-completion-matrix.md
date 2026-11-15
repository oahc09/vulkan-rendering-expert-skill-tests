# v1.0.18 original-plan completion matrix

Current concise delivery status: [TEXT18 current delivery audit](text18-current-delivery-audit.md). This file preserves incremental history.

> **Historical baseline warning:** early tables and dated priority lists below describe their stated old heads. They are not the current missing-feature list. Read the latest appended experiment and current-plan audit for subsequent bounded coverage. C1-C4 remain partial; M4 remains BLOCKED.

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


## Explicit surrounding-scene state handoff (bounded)

A new synthetic-coverage diagnostic executes pre-scene, coverage overlay and
post-scene draws in one actual command buffer/renderpass/submission. The post
draw explicitly rebinds its compatible pipeline, descriptor, vertex buffer,
viewport and scissor after the overlay changes all five. Each omission plus
all-five omission is a separate legal GPU negative; validation errors are not
accepted as a successful negative. Three active color attachments retain exact
velocity/ID sentinels. Independent CPU rectangle/nearest-sample/ordered-over
reference and unchanged1e-6 tolerance cover visible stage-specific and overlap
regions rather than merely checking a blank background.

This is three draw stages in **one VkRenderPass**, not three renderpasses or
cross-pass restoration. Synthetic coverage isolates binding-state correctness,
not new font-quality evidence. Scene draws are opaque; only overlay blends.
Push constants are explicitly set each time, but index buffers, stencil, depth,
blend constants and every possible renderer dynamic state are not covered.
Nor is this handoff fixture automatically combined with the earlier pending
atlas lifecycle, despite those independent tests passing.


The handoff positive maximum RGBA error is2.265e-8. Its visible regions are
2705 pre-only,160 overlay-visible,8 post-over-overlay and312 other post pixels.
The six omitted-state controls change320/320/140/124/304/480 pixels respectively
while validation and auxiliaries remain clean. An initial build-adapter shader
filename collided with the inherited startup shader; the dedicated final shader
filename fixed that conflict without changing references or tolerance. The
failed validation attempt is retained locally, not counted as accepted evidence.

## Fixed-camera phase-sequence dynamic-quality diagnostic

Two histories select the existing bitmap/MSDF representations through actual
scale0.85/1.15 warmup draws. Both then hold scale1.05 while scanning17 identical
phase positions0…1px in1/16px increments, so34 positive measured draws compare
the same geometry without mixing scale change into the phase diagnostic. Two
warmups and one legal wrong-representation draw are counted separately.
Foreground/edge ROI error, worst coordinates and coverage, same-phase mode
difference and geometry-subtracted neighboring-phase residual are measured.

This reveals a larger MSDF linear4 discrepancy than the earlier short sequence:
maximum exact-area coverage error≈0.0436968 at phase0.125, pixel(32,15).
Maximum neighboring-phase geometry-subtracted residual≈0.0340552 occurs over
0.625→0.6875 at(33,15). These worse observations remain visible. No algorithm or
quality threshold was changed to conceal them. Numerical GPU sampling/over
checks still pass; that does **not** establish dynamic-quality acceptance.

The new bitmap path explicitly texelFetches already-target-pixel coverage instead
of filtering it again; its small transport error is not improved font quality,
and the older LINEAR bitmap experiment is unchanged. Bitmap remains generated
from the same exact reference, whereas MSDF is compared independently to original
polygon area. Limited CPU point resampling can help investigate approximation
error, but is neither an actual GPU improvement nor a full-frame/general method
recommendation. Status remains **MEASURED_NOT_QUALIFIED**; no perceptual flicker,
rotation/perspective, platform-hinted full quality board, target-device or Live
qualification is implied.

## Pending atlas lifecycle with surrounding scene handoff

The actual single-queue pending atlas consumer now executes pre-scene, packed
real-glyph overlay with three hard clips, and post-scene in the same command
buffer/renderpass/submission. This is one combined execution path, not a sum of
independent earlier experiment results. Existing pending publication/retirement
rejection, canceled-page retention, replacement generation and controlled pending
exception cleanup remain exercised. Each submission owns its targets, vertex
buffer, fence and readback; immutable scene resources outlive all consumers.

Independent CPU composition retains visible overlay and post-over-overlay pixels.
Actual canceled-descriptor routing and omitted post-state rebinding are legal GPU
negative controls; auxiliary attachments are checked even for wrong-color images.
A stale-generation readback mutation is also rejected. Existing 1e-6 tolerance is
unchanged. Three positive images require nine scene/overlay draws; the diagnostic
wrong-route image adds three draws. One scene setup upload and three atlas uploads
are separate from these four render submissions.

This closes a bounded local conjunction of §7.2–7.4, not the entire M3/scene-C
stress requirement. The gate is ALL_COMMANDS pending, not a shader already running.
One renderpass, one queue, synthetic opaque surrounding scene and three finite
hard clips do not establish arbitrary renderer-state restoration, depth/stencil,
HDR/temporal reconstruction, general transparency order, allocation/device-loss
fault safety, multithreading, real Surface behavior or target-device performance.
Generation2 still attenuates the same glyph coverage, not a new locale run. The
separate dynamic MSDF quality result remains MEASURED_NOT_QUALIFIED; physical
Android/Windows/mobile GPU and semantic Live remain external unverified gates.

## Dual logical-device pending independence and higher-grid quality diagnostic

The new dual-device path holds A's actual submitted draw behind a timeline gate
(value0, fence NOT_READY checked five times) while B independently completes
initial upload/render, canceled candidate handling, new-generation upload/render.
B continues rendering after A's controlled pending-scope failure releases its gate,
waits for completion and destroys A. Three B images are checked independently;
wrong canceled B routing, stale readback/event mutation and foreign-device page
publication/draw rejection before command recording are negative controls. A's
post-release image is not read back: its evidence is bounded completion/cleanup,
not an A image-quality assertion. This is two logical Devices in the same software
implementation, not two physical GPUs, real Surfaces, simultaneous shaders or
arbitrary failure/leak qualification. Auxiliary preservation uses the older UNUSED
fallback, not the separate active-MRT experiment. Replacement still scales the
same glyph coverage; complete multilingual asynchronous stress remains partial.

The higher-grid experiment runs the original fixed-phase linear4 GPU baseline,
then actual linear8/linear16 modes against the identical atlas, transforms and
history schedule. Each mode has34 measured positive frames,2 warmups and1 legal
wrong-route draw; modes use separate process/device instances. Independent CPU
sampling checks keep original .004 MSDF/1e-6 bitmap tolerances. Quality separately
uses exact original-polygon pixel area, foreground/edge ROI and geometry-subtracted
adjacent-phase residuals. It remains MEASURED_NOT_QUALIFIED, with no new pass gate.

Observed worst exact-area residuals: linear4 .043696754, linear8 .013053457,
linear16 .012661063. Worst neighboring-phase residuals: .034055169, .010916074,
.006532144 respectively. Improvement is not uniform: linear16 is worse than
linear4 at phases .25/.5/.75 by about .00044, and worse than linear8 at9 of17
phases. Those results are retained, not replaced by an aggregate-only claim.
The grids imply16/64/256 texture samples per pixel, not measured GPU time, energy
or mobile feasibility. Full glyph sets, transforms, perceptual temporal quality,
real platform raster providers and physical device/Live gates remain open.

## Exact sibling dependency execution and actual upload backpressure

A fixed manifest now makes CORE17's independent tests4fc46/Skill068a pair and
original contract/gate hashes executable dependencies of TEXT18 CI. The added
job runs the unchanged CORE17 versioned gate and Skill17 self-checks after clean
full-history/exact-head/ancestry checks. It does not merge the sibling branch,
retarget either PR, rewrite the old release contract, or upgrade the six partial
links to equivalent semantic acceptance. DEPENDENCY_STATIC_PAIR_PASS is only the
pinned static pair; cumulative merged acceptance and Live remain unclosed.

The new upload-budget fixture connects §7.6 limits to actual Vulkan submissions,
not only a CPU budget helper. Its declared experimental capacity is one12740-byte
65x49 R32F payload per epoch and one in-flight upload. Three cycles exercise
18 reasoned rejections with unchanged pre/post state, including malformed input,
overflow, epoch exhaustion and pending-capacity exhaustion. Cancel does not free
pending capacity; a new epoch does not erase in-flight work. Real completion
allows retry, while already-charged epoch bytes remain until the next epoch.
Seven uploads are accepted, six actual rendered images use unchanged1e-6 oracles.

On completed submissions, actual staging/readback/vertex/image/framebuffer/fence
and command-buffer resources are released, page upload references cleared, and
submission objects removed. Each cycle returns to one page, zero submissions and
zero resident staging payload/handles. These are observable fixture resources,
not total VkMemory allocation/driver VRAM or process leak measurements. It is a
fixed-size single-owner experiment, not arbitrary allocation-failure rollback,
production concurrency, font-service cache accounting or device-loss recovery.
Earlier dynamic quality remains MEASURED_NOT_QUALIFIED; physical platforms,
target-device performance, actual host and semantic Live remain unverified.

## Actual shaped-glyph to representation routing bridge

A fixed trusted face is checked before parsing. Actual HarfBuzz GlyphID47 (L)
selects its FreeType outline, whose verified six straight edges feed the existing
bounded triangulator and closed front/back/side extrusion. Actual Vulkan geometry
is checked against ray intersection of the original source contour, not the
triangulated output. Actual GlyphID50 (O), with two quadratic contours, is rejected
by that limited triangulator and routed to a real FreeType bitmap/Vulkan planar
fallback, preserving62 enclosed zero-coverage pixels. This is actual routing and
output, not only a fallback label.

Wrong GlyphID41 (F) geometry is really drawn and rejected against L's source
reference; an actually drawn hole-filled O mask is rejected. The latter is a
wrong-mask negative, not a tested forced solid-O extrusion. Auxiliary checks also
cover the negative images. Existing numerical tolerances are unchanged. The
mesh's normalized24px unhinted outline and fallback's existing20px hinted bitmap
are separate declared representations, not equivalent layout/depth/3D quality.

This closes only the bounded provider→representation connection in §6.2/6.4.
It does not close full scene-B: stroke/cap/join, wider near-plane/perspective and
AA clip behavior, world-label policies, shadows and a second view remain local
implementation gaps rather than hardware blockers. General/mixed-script quality
and CPU font-cache/performance accounting also remain incomplete. Actual
Android/DirectWrite providers, physical target devices, semantic Live/host and
cumulative branch integration are separate external/dependency conditions. No
claim is made that only external conditions remain or that more finite glyph
examples would alone complete these milestones.

## Bounded opaque stroke/cap/join Vulkan path

The original §6.1/§11B stroke gap now has a finite executable implementation:
screen-pixel width for one/two straight segments; butt/square/round caps and
bevel/miter joins. Miter ratio is tip distance divided by half-width; a value
above the declared limit falls back to bevel. Curve/dash, unsupported join and
invalid/over-budget inputs reject before GPU execution. Round caps use64 segments.

Six generated stroke meshes are actually drawn with opaque same-color union;
segments/caps can overlap, so this is not a nonoverlapping mesh or transparent
stroke proof. Independent projection/distance/convex-region reference uses the
original path and cap/join request, not emitted GPU triangles. Wrong square-cap
and ignored-miter-limit meshes are actually drawn and rejected outside both
predeclared boundary guards. Non-target attachment checks include negative paths.

Status is BOUNDED_INTERIOR_PASS only. The predeclared .01px guard conservatively
covers analytic primitive boundaries, including internal union edges; its bound
exceeds the maximum r4/N64 circle sagitta plus fixed .005px raster reserve. Original
1e-6 composition tolerance is unchanged outside that guard. All excluded pixels
and errors are published: polyline cases retain8 excluded pixels each and full
image error up to .8, rather than hiding hard-edge mismatch as full pixel accuracy.

This is an actual authored-path GPU capability, not complete SVG or font-stroke
support. Curved/dashed strokes, round joins, general topology, AA, transparency,
world-coordinate widths/perspective and target-device behavior remain unsupported
or unverified. Other original world/quality/platform/Live/dependency gaps remain
as previously listed; this finite increment does not close the complete milestone.

### Bounded stroke boundary diagnosis and analytic fallback (2026-11-15)

The preceding mesh experiment remains `BOUNDED_INTERIOR_PASS`: each of the three
polyline cases has eight guarded pixels but only (42,35) fails (error 0.8).
Three pixel centers lie on the same exact terminal cap line; only one is absent.
An 8-bit nearest-grid diagnostic is consistent with the observed split, not proof
of the driver's private rounding algorithm, and not a portable top-left rule.

`text_stroke_boundary_lab` adds an explicit support-quad/analytic-fragment fallback,
not a repair claim for pure mesh rasterization. The original six paths and all
expected pixel classifications are unchanged (3,185 pixels compared per case).
Nine actual Vulkan images (six original, three reversed polylines) pass full-image
color/depth tolerance 1e-6 with zero exclusions; maximum error 2.384185793e-8.
Actual wrong-cap, ignored-miter-limit and open-end negatives detect respectively
36, 18 and 3 pixels. Omitting fallback reproduces all three original mesh failures.
Active auxiliary attachments are checked exactly before composition failures.
The round cap is analytic here, unlike the old 64-segment mesh approximation.

This closes only the tested hard pixel-center opaque coverage boundary. It does
not qualify transparent/AA strokes, curves/dashes, general vector paths, device
portability, Android/Windows or Live. The prior GLSL constant-array compile failure
is retained locally; fixed three-slot storage preserves COUNT-limited semantics.
Source and stripped numerical evidence only are published. Overall Draft/BLOCKED,
Skill/candidate pins and the non-main base/dependency chain remain unchanged.

### Bounded straight-stroke exact-area AA (2026-11-15)

For original-plan §5.3 coverage/opacity composition and §13.2 subpixel quality,
`text_stroke_area_lab` adds sixteen actual Vulkan draws: horizontal/4:3 straight
paths, butt/square caps, width 5, four quarter-pixel translations each. GPU clips
a rectangle against the pixel box in local coordinates and computes area; CPU
independently integrates exact rational vertical slices from the original path.
This is a limited exact-area reference, not a supersampling match or universal
text AA oracle. Composition keeps 1e-6; the separate 1e-6 area check was registered
before running this bounded experiment, not invented as an original-plan global
quality gate. No pixels are excluded. Actual premultiplied blending uses opacity
0.75 and stored background alpha 0.5; coverage is inferred from output alpha.

Sixteen outputs have maximum composition error 7.153e-8, inferred area error 0,
and zero depth-preservation error; auxiliary MRTs are exact. Four phase groups
retain area/reference temporal deltas. Fifteen frames have partial pixels; the
unchanged horizontal-square phase 1 is an integer-edge binary control. Actual
hard-center negative produces coverage error 0.502604; double-alpha negative
produces color error 0.224832 with correct coverage. Depth and auxiliary checks
are independent and cannot masquerade as expected negative detection.

Initial inherited depth writes and tiny clipping roundoff, plus an incorrect
all-frames-must-have-partial-pixels test expectation, are retained locally and
documented. Fixes disable depth writes, use implicit-line intersections with
exact clip-axis coordinates, and recognize the existing integer-edge control
without changing case coordinates or tolerances. This is not round/join/curve AA, transparent overlapping strokes,
MSAA or world-space/perspective qualification. Overall Draft/BLOCKED and branch
pairing remain unchanged; target devices and semantic Live remain unverified.

### Bounded perspective world-label path (2026-11-15)

Original-plan §6.4/Scene B now has a fixed real world-space text path beyond
previous affine fixtures: trusted-font HarfBuzz GlyphID50 O -> FreeType coverage
bitmap -> padded atlas -> tilted world XYZ/UV quad with actual clip.w=Z and
perspective-correct interpolation. Four actual images use two distances under
the same camera and constant world extents, with separate depth-tested and
always-on-top policies; neither label mode writes depth. A normal mesh rectangle
is drawn first in the same pass and writes actual depth. CPU camera rays intersect
the original plane and sample original cropped glyph data, not uploaded vertices.

All four full-image color results pass 1e-6 with zero guards (max8.457e-8);
depth preservation max2.649e-8 and auxiliary MRT exact checks are independent,
including negatives. Nonzero glyph ROI shrinks348->183 at greater distance;
occluded nonzero pixels131/67 and projected hole pixels171/93 are observable.
Trusted source O has62 enclosed zero pixels; identity, font hash, provider clipping
and nearest sampler are asserted. Wrong always-on-top and noperspective are real
GPU negative draws with color errors0.525/0.6, not mocked pipeline flags.

Near-plane and nonfinite inputs reject before new GPU setup with exact error
reasons. This does not implement near-plane crossing/clipping, constant-pixel
size/billboard modes, a second camera view, shadows, broad font quality or target
platform/Live acceptance. Same camera at two distances is not a second view.
Overall Draft/BLOCKED, exact version pairing and sibling/non-main dependencies
remain unchanged; other original-plan local and external gaps remain explicit.

### Real near-plane clipping with bounded sampling fallback (2026-11-15)

A separate `text_near_clip_lab` leaves the earlier conservative rejection fixture
unchanged. Same real shaped O and world XY now exercise cross-near z=.875+.5*x,
on-near z=1, and positive-w entirely outside-near z=.5+.125*x. Unclipped triangles
are submitted directly; Vulkan clips against near1 with depth clamp disabled.
Independent CPU Fraction camera rays intersect the original plane, apply clip
domain and sample original glyph data. Input remains finite w>.125; behind-eye
and arbitrary complex topology are not implemented.

Original hardware-perspective NEAREST sampling is NOT_QUALIFIED on this software
backend: cross-near has one pixel (45,10) error0.148235. A separate real GPU UV
readback shows source row2.999999552965164 versus exact3 (source x161/18), explaining
the discontinuous texel choice. On-near and outside-near hardware cases pass.
This failure remains recorded; it is not repaired by moving geometry or widening
1e-6. A distinct fixed-rational-camera/plane integer-ray texelFetch fallback avoids
that sampling discontinuity. It performs no near test/discard: actual clipping
still exclusively happens in Vulkan. Integer intermediate maximum7754040 fits
int32; independent review exhaustively matched9555 pixel mappings to Fraction.

Three fallback images have max composition8.457e-8, depth2.649e-8 and zero guards;
nonzero glyph ROI479/1761/0 respectively. Two actual label-only wrong vertex-clamp
variants expose incorrectly retained glyph output (errors0.6/0.0141176), while
scene depth and auxiliary MRT checks remain independent and pass. One additional
UV diagnostic draw is not counted as a positive. Nonpositive-w and NaN reject
before GPU setup with exact reasons. Only source/stripped numerical evidence is
published; original failures and full receipts remain local. Draft/BLOCKED,
branch pairing and target-device/Live limitations persist; this does not qualify
general perspective NEAREST, arbitrary camera planes, shadows or second views.

### True second camera with shared serial resources (2026-11-15)

`text_second_camera_lab` keeps the real O glyph, world geometry, atlas image,
descriptor and vertex buffer unchanged under one TextLab/Vulkan Device. Camera A
is the original origin/basis. Camera B has origin(.5,.125,-.25), right(24/25,0,7/25),
up(0,1,0), forward(-7/25,0,24/25): actual translation plus ~16.26-degree yaw, not a
second glyph distance. An80-byte ink/view push-constant block drives the vertex
view transform and fragment composition. A/B each render scene occluder then
label in depth-tested or always-on-top mode. Five serial submissions (four
positive, one negative) complete before target/readback reuse. The same atlas
image is reuploaded with identical data every draw; no once-only-upload or
parallel-view performance claim is made.

Independent CPU rays start at the respective camera origin/basis and intersect
original world planes/glyph data; source geometry does not derive from GPU matrix
or vertex buffers. Four full-image results pass1e-6 without guards: maxcolor
8.457e-8, B scene-depth max8.997e-8, auxiliary MRT exact. A hidden/visible glyph
pixels131/217 versus B174/136 prove observable parallax/occlusion changes. A real
negative keeps scene B correct but pushes camera A only for the label; color
error0.6 is detected after independent depth/aux checks. Source identity/hashes
and readback receipts remain local; publishable report contains minimal numbers.

This closes only a bounded planar-label second-camera experiment. Shadowing,
second-view finite extruded typography, simultaneous views/Surfaces and general
camera/font quality remain separate. Draft/BLOCKED, precise version pairing and
non-main sibling dependency chain remain; target-platform and Live are unverified.

### Actual glyph depth producer and hard-shadow receiver (2026-11-15)

`text_shadow_lab` shapes trusted-font L (GlyphID47), obtains its real straight
outline and builds a20-triangle closed front/back/side prism. A real D32 attachment
pass writes orthographic-light depth using(x+.5z,y+.25z,z/16). After an explicit
attachment-write to fragment-read transition, the same Device's receiver shader
directly samples that image. No CPU readback/reupload bridges the two passes;
readback occurs only after consumption. CPU independently intersects original
source-contour cap/side planes to obtain nearest light-ray depth, without using
emitted triangles or GPU depth. Receiver is a fixed full-screen plane
parameterization atz10, bias0, hard shadow; its offset(5,2.5) uses explicit integer
nearest lookup and out-of-map lit semantics.

All pixels retain1e-6/no guards: positive D32 error1.4851e-7, RGBA2.3842e-8,
213 shaded receiver pixels. Wrong F caster (GlyphID41/36triangles) changes both
producer depth and output color; bypassing comparison retains correct producer
depth but causes0.6 color error. Receiver depth .375 is an independent protection
sentinel, NOT actual z10 camera depth; velocity/ID active MRTs are exact. Negative
categories and cleanup validation must pass before reporting overall PASS.

First missing explicit validation receipt and optional PNG-library failures are
retained locally. Final code checks cleanup validation and uses the existing
standard-library PNG path; no numerical/case changes were needed. Scope excludes
general world receiver meshes, visible caster material/lighting, soft shadows,
arbitrary bias or self-shadowing and complete Scene B/device/Live qualification.
Version pins, Draft/BLOCKED state and the non-main dependency chain are unchanged.

## Bounded multilingual whole-run fallback chain (after bacd8a39)

Fixed trusted DejaVu Serif -> DejaVu Sans -> Noto Sans CJK SC TTC face 2 is now selected by real whole-run HarfBuzz missing-glyph results. Dedicated fixed-hash 24 MiB TTC adapter leaves the old 16 MiB probe unchanged. Four explicitly segmented runs at 14 px cover `ffi` (actual ff+i), combining a+acute (precomposed aacute), Arabic joining/RTL clusters, and Chinese. HarfBuzz and FreeType use the identical selected face/index; cross-face receipt mismatch is rejected before rasterization. Frozen complete shaping receipts are provider regression baselines, not independent typography certification.

Run bitmaps are packed into one atlas and delivered by four actual Vulkan UV quads. Original run pixels, not atlas/UV data, drive independent composition reference. Full-frame/ROI error is 7.252544687030849e-8 against unchanged 1e-6; 475 nonzero ROI pixels and zero clipped samples. Actual wrong-route GPU output differs by 0.599999998509884. Separate legitimate Sans/Serif O GlyphID50 resources exercise wrong-face renderer selection: correct output error 7.152557379708213e-8 and wrong-face error 0.2800000062409569. Auxiliary sentinels are independently checked before expected negative color rejection. This helper uses unused/preserve auxiliary attachment routing, not a new active-MRT claim. Missing whole-chain coverage is rejected before GPU preparation.

This closes a previously absent executable face-selection/identity/delivery chain, not all Scene A. Explicit segmentation/direction and cropped integer-positioned run images are not paragraph bidi, baseline-aligned paragraph layout, general mark placement, emoji color fallback, MSDF multilingual quality or platform typography certification. Actual software Vulkan evidence is not target-device acceptance. Only source, reviewed fixed regression data and sanitized numeric output are published; fonts and raw provenance remain local.

## Current original-plan status after bounded fallback chain (not release acceptance)

The early tables and old numbered priorities in this document are historical snapshots, not a current absence list. Later experiment sections supersede only their precise bounded scope. No local experiment changes the original plan's acceptance bar.

- **C1 partial:** Linux HarfBuzz/FreeType fixed-font run shaping, locale/variation experiments and the bounded ordered whole-run fallback chain have executable receipts. Explicit input runs and directions are not paragraph itemization, Unicode bidi layout, general grapheme fallback or Android/Windows platform typography certification.
- **C2 partial:** bitmap, MSDF and bounded synthetic color paths, representation switching and phase sequences have real software-Vulkan evidence. Full Scene A's same-condition multilingual/emoji/variable-font representation board remains incomplete. Dynamic MSDF quality remains MEASURED_NOT_QUALIFIED; the near-clip hardware-NEAREST counterexample remains recorded, not overwritten by the bounded integer-ray fallback.
- **C3 partial:** bounded vector fill, stroke, exact-area straight-line AA, shaped straight-outline extrusion, world labels, near-plane clipping fallback, second camera and a real depth-producer/shadow-sampler chain now execute. They do not constitute the complete shared Scene B, general lit text materials, arbitrary outline triangulation or general-purpose shadow filtering.
- **C4 partial:** packed atlas, pending retirement/cancellation, upload-budget backpressure, two-device ownership and selected same-pass lifecycle/handoff cases execute. The complete real-content Scene C and full font-service cold/hot cache/cost accounting remain local integration work; temporal/HDR/motion interface consumption is not closed by constant auxiliary sentinel preservation.
- **External/branch conditions:** physical Android Adreno/Mali and available Windows target measurements, platform Java/JNI/DirectWrite integration, semantic TEXT18 Live evaluation and actual external host discovery remain unverified. The CORE17 sibling dependency has an exact independent static gate, not a merged cumulative semantic certification. TEXT18's base remains the existing v1.0.16 source-review branch, not main.

M1–M3 remain partial and M4 remains BLOCKED. Small bounded lab success is not completion of the full plan, and not every remaining gap requires unavailable hardware.

## Bounded real paragraph bidi + whole-run fallback (after ce3147ee)

The previously explicit-only direction experiment is now complemented by one real mixed logical paragraph, `A سلام 12!`, executed at base LTR and RTL. Actual FriBidi computes embedding levels and logical/visual maps. Independent ICU checks every level/map entry for the same input; two separate official Unicode 15.1 test vectors additionally check the FriBidi ABI and UBA mapping, not this paragraph's glyph image. The official corpus is read locally only after a fixed SHA check; it is not redistributed.

The renderer obtains continuous-level logical substrings, preserves their logical order when passing them to HarfBuzz, applies ordered whole-run face fallback, and places shaped runs in library-derived visual order. The fixed audited input has at most one strong script per run; this is not a general script itemizer. It does not feed presentation-form/reordered strings back into the shaper or reverse RTL glyphs twice. At 10 px, both base cases retain a 50.859375 px shaped line advance including spaces, original crop offsets and shared baseline, with no clipping. ICU independently rebuilds reference run order and cursor positions rather than reusing candidate destinations; HB glyph positions and FT coverage remain common providers, not independently certified typography.

Each base has four packed run quads. Full image/ROI error is 7.152557379708213e-8 against unchanged 1e-6; each has 175 nonzero ROI pixels, zero clipped samples. Actual GPU negatives render logical-order placement and wrongly LTR-shaped RTL runs against the unchanged reference; independent auxiliary sentinels must remain intact before color failure is accepted. These are real draws, not only CPU rejected inputs. The inherited helper preserves unused auxiliary attachments, not a new active-MRT result.

This supplies bounded automatic paragraph-direction analysis, not complete Scene A, multiline wrapping, all UBA conformance, grapheme/script itemization, general control/isolate handling, punctuation-mirroring or mark-placement certification. The standalone renderer rejects inputs outside its exact audited paragraph; the lower map probe's bounded BMP scope is separate. Physical target devices and semantic Live remain unverified. C1-C4 remain partial and M4 remains BLOCKED; prior no-paragraph statements describe the old explicit-run experiment, not this new finite two-base path.

## Real emoji presentation selector and color delivery (after b2954848)

A fixed complete heart+VS cluster now requests text (FE0E) or emoji (FE0F) presentation and dispatches to the corresponding trusted face/shaping/resource path. The local fixed-hash Unicode 15.1 variation-sequence file validates these two presentation requests; it is not redistributed. Missing-glyph detection alone cannot select the presentation: the emoji font can return a color heart even for FE0E. The full original cluster, including the selector, reaches HarfBuzz; VS16 yields actual Noto Color Emoji GlyphID168, while the text face yields DejaVu Sans GlyphID4076 plus zero-advance default-ignorable GlyphID3. This is an explicit two-cluster policy, not general Unicode grapheme fallback.

The previously used bundled FreeType lacks PNG decoding for this font. The experiment uses a separate absolute-path system FreeType library and separate handles, leaving the old library/environment unchanged. Actual BGRA strike 136x128 is independently checked against FontTools CBDT extraction + a PNG decoder: integer encoded premultiplication `(channel*alpha+127)//255` matches every source byte exactly. Source fonts and embedded PNGs remain local.

Candidate BGRA is unpremultiplied in encoded sRGB, decoded to linear, then premultiplied again. The independent PNG oracle reconstructs the quantized source and color conversion without calling the candidate converter. A predeclared nearest source-center mapping displays the entire strike at 34x32; this is an explicit finite sampling contract, not minification-quality certification. Actual RGBA32F texture delivery and Vulkan premultiplied over blending use opacity .75 exactly once. Text style has a separate existing grayscale provider reference, not an independently certified typeface image.

VS16 full-frame maximum error is 6.724376688804767e-8 and VS15 is 7.152557379708213e-8 against unchanged 1e-6, with zero excluded pixels. Actual skip-sRGB-decode negative differs by 0.21526829972383427; wrong-text-resource selection differs by 0.6749999985098839. Auxiliary attachments are independently protected before positive/negative classification. The wrong-resource case includes different resource placement/size, so it is not a same-layout typography comparison. This fullscreen textured-bitmap consumer is not a new packed-glyph/active-MRT lifecycle result.

C2 gains actual production-font bitmap emoji evidence beyond the earlier synthetic COLRv0 case. Full emoji/ZWJ/skin-tone coverage, mixed-paragraph emoji integration, COLRv1/SVG-font paths, broad fallback and complete Scene A remain open or explicitly unsupported. C1-C4 remain partial, M4 BLOCKED; software Vulkan does not replace target platforms or Live semantic evaluation.

## Actual existing temporal output consumed by HDR text overlay (after 3e9bb51a)

This increment connects the existing unchanged hybrid-quality `temporal.comp` scalar-visibility computation to an actual fragment-stage SSBO consumer on the same VkDevice. It is not a new TAA algorithm, not full RGB temporal reconstruction, and does not include the old experiment's spatial filter. Controlled authored raw/depth/class inputs isolate the consumer contract. The subsequent scene draw maps temporal visibility to linear RGB values above one; a second draw composites actual HarfBuzz/FreeType O or F coverage into the same target. Active velocity/ID and depth are protected independently.

Four frames cover initial reset, integer pan, static continuation and reset. Two normal sequences differ only in initial UI content (O/F); their actual first output images must differ, but every accumulated/history buffer must be byte-identical. History is saved by GPU compute from scene accumulation, not copied back from CPU. There are fence waits and intermediate diagnostic CPU readbacks; no readback feeds the scene or history GPU consumer. Explicit compute/fragment/transfer barriers and descriptor ownership remain part of the exercised path.

CPU reference recursively maintains clean ideal history rather than accepting candidate history as ground truth. Original temporal/history tolerance stays 1e-5. The text consumer is independently checked at 1e-6 from validated GPU accumulation; ideal end-to-end error is separately reported, not conflated with stage-local correctness. Zero excluded pixels. The diagnostic PNG uses CPU tone mapping only to view readback; the tested positive GPU output remains linear HDR with no final output encoding stage.

Actual negative history-save samples the rendered overlay and applies the inverse scene mapping. Its initial non-UI region must remain numerically clean while UI-region history changes; following temporal frames must disagree with the clean oracle. Thus the negative is not merely a wrong scene offset outside the text. A separate premature tone-map shader must fail only the color-consumer contract while temporal/history remain valid. These are legal Vulkan operations, not use-after-free injection.

The first local run failed validation because already-owned compute pipelines were manually destroyed twice; ownership was corrected and the failure evidence retained. An incomplete inverse mapping was caught during review before any successful negative execution and corrected before the passing run. No validation error or earlier failure was hidden by changing thresholds.

This closes a bounded screen-UI temporal/HDR interface gap, not world-text motion, real HDR display/output encoding, complete mixed Scene A/C, font-service cold/hot cost accounting or platform acceptance. C1-C4 remain partial; M4 remains BLOCKED, with device/Live conditions distinct from remaining local integration work.

Measured positive maxima: temporal/history 3.6954879711892374e-8, stage-local consumer 2.1913472325607586e-7, ideal end-to-end 2.266729581812399e-7, linear RGB peak 2.5475001335144043. Initial pollution control is 2.9802322387695312e-8 outside UI and 0.0949999988079071 inside UI; later temporal error reaches 0.05600000619888307. Premature tone mapping yields consumer error 1.7581844925880432 while temporal/history remain valid.

### Bounded CPU font-service cold/hot cost ledger (original §7.1, §13.1)

A new single-owner diagnostic cache calls actual trusted HarfBuzz shaping and FreeType per-glyph grayscale rasterization. Separate layout and glyph caches use provider versions, font hash/face index, generation and the relevant fixed-domain request options. Unsupported representation/variation/style configuration is outside this API, not silently accepted. Twelve application-cache-clear rounds each produce one HB run and two unique FT glyphs for OFF; repeated F reuses a glyph. Each following hot request produces neither. Independent entry-point spies and direct uncached shaping/bitmap production verify reuse and exact returned bytes. This is cache correctness, not independent font typography quality.

Size changes regenerate coverage while preserving layout; locale changes reshape but reuse identical glyphs; generation changes both. Capacity-one eviction requires real production again. Returned objects cannot mutate cached values. Actual poisoned 24px cache entries containing old 20px coverage are rejected by comparison with fresh 24px production. Strict finite integer budgets reject invalid inputs. Oversize coverage is not published, although the already-completed layout can remain: no transactional batch rollback claim.

Observed owned coverage peak was 1,368 bytes, with tracked glyph/layout entries and coverage returning to zero on clear. Metadata/object overhead, retained timing telemetry, native font allocations and process memory are not included; this is not leak freedom or whole-instance memory stability. The cache is not connected to the separately tested Vulkan upload-budget path, so the result does not establish combined Scene C churn.

Frozen 12-sample cold-request p50/p95/p99: 5.864414/8.634697/8.634697 ms; hot-request: 0.030095/0.031989/0.031989 ms. These are local observations, not speed gates or statistically stable tail latency. Shape timings include file I/O/hash and HB setup/destruction, raster includes FT face creation and coverage copy. Each cold round records its actual shape/raster samples; hot stage counts are zero. No OS-cache purge/process cold start is claimed. JNI, GPU upload/draw, total frame, native heap, sustained thermal/power and target-device performance remain UNMEASURED. Previous full-suite results are not relabeled as current-head evidence.

Sixteen local tests passed at the frozen stage. Initial test invocation failed before collection due to missing VULKAN_SKILL_ROOT and was rerun with the existing explicit environment. C1-C4 remain partial; M4 remains BLOCKED. Remaining local integration and external device/Live constraints remain separate.

### Scene C subset: real CPU cache products consumed by pending Vulkan churn

The new font-cache-churn experiment directly packs actual cached HB/FT per-glyph coverage into the seven GPU inputs: O20/g1, hot O20/g1, F20/g1, hot F20/g1, O24/g1, hot O24/g1, O20/g2. CPU face generation is separate from GPU page generation (published 0,2,...12). The last request regenerates despite identical visual bytes; the three hot requests execute zero HB/FT producers. Each cache receipt is checked against uncached production, and fresh coverage/dimensions supply the GPU CPU-reference rather than reusing cached pixels as expected values.

One actual Vulkan process/device performs six replacement cycles, eighteen positive draws and thirteen uploads, including pending candidate cancellation, retained old-page consumption, fresh publication, stale-generation refusal and retirement only after completion. Two NOT_READY fences substantiate the pending events. Each steady point has one live/page object and zero owned submission resources. A separate actual GPU lifecycle intentionally routes the F atlas into an O slot and fails composition; a copied retirement trace is also rejected after corruption. Positive and negative auxiliary readbacks are checked before color. Original 1e-6 tolerance and zero exclusions remain. Source/provenance and raw images remain local; reviewed source and minimal numerical results are published.

CPU coverage peak is 876 bytes, and clears to zero before GPU execution; this is not a native heap/VRAM metric. The frozen run passed one opt-in integration test (18.10 seconds), with eighteen positive images at approximately 7.15e-8 maximum linear error. Actual O/F/size-change previews were inspected. This joins producer output to a real lifecycle consumer, not two independent report successes.

Limits remain explicit: sequential CPU pre-generation followed by GPU execution, not overlapping CPU/GPU scheduling; hot requests still upload and do not prove GPU upload avoidance; fixed 65x49 page replacement, not growing atlas capacity; single logical device and no Surface; UNUSED/preserve auxiliary attachments, not active MRT; fixed top-left single-glyph sprites, not bearing/advance-based layout. The wrong-resource control has differing glyph dimensions, not equal-layout quality. Full Scene C growth, dual-output ownership and sustained workloads are not established by this subset. C1-C4 remain partial, M4 BLOCKED; target-device/Live and remaining local integration are still distinct.

### Scene C subset: shared hot-cache inputs, independent outputs and active MRT

A new single-process execution consumes verified hot-cache pages 1/3/5 (O20/F20/O24) from the real CPU provider cache, with zero new shaping/raster calls on those requests. Actual uncached references remain the expected pixels. Two simultaneously live TextLab/Engine instances have distinct logical VkDevice handles and independent GPU resources; CPU masks/vertices are checked immutable. They use the same configured software implementation, not separate physical GPUs or real window Surfaces. Source/page ownership guards reject foreign publication/draw before recording GPU commands.

Output A uploads O20, then its old draw remains behind a real ALL_COMMANDS timeline gate. A's pause guard refuses an additional draw without changing submission count. B independently completes O20, cancels a completed F20 candidate, publishes O24 and renders it while A's fence is still NOT_READY and timeline counter zero. A is released and waited before its old image is captured and A safely destroyed. B continues on the same device/page. A is rebuilt on a separate logical device and renders F20; B continues unchanged. This establishes independent progress under the tested gate, not simultaneous shader execution. B cancellation is after upload completion, not pending B cancellation.

All color/velocity/ID attachment references are active. independentBlend is checked/enabled, while non-target write masks preserve exact auxiliary values despite the fragment shader emitting changed values. Six positive images pass fresh-reference comparison at 1e-6 with maximum error 7.152557379708213e-8 and zero exclusions. One actual wrong-resource image is rejected. A separate valid bad-write pipeline repeats all seven images and every auxiliary check fails as intended, with validation otherwise clean. Original glyph previews and size changes were viewed.

The frozen opt-in run passed in 28.73 seconds. Three logical devices are constructed, peak two simultaneously live; validation is checked after destruction. Submission objects remain owned until the tested output's cleanup rather than being claimed zero after every B draw. No native allocator/VRAM leak or arbitrary device-loss guarantee follows. Inputs are sequentially pre-generated; their preparation's separate churn draws are not counted as this stage's six positives. Fixed page size, no atlas expansion; no depth/stencil/clip; g1 CPU inputs only and not a new dual-device face-generation test. Full Scene C, physical devices and semantic Live remain incomplete; C1-C4 partial/M4 BLOCKED stay unchanged.
