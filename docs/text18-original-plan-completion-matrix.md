# v1.0.18 original-plan completion matrix

Assessment against the owner's **2026-11-08 Text, Vector & 2D/3D Composition** plan, not a reduced replacement plan. Evidence baseline: Skill `c0b62a19938a6b9cfce2ea6a5ce18f91b91e6344`, tests `8d75091cc8041e056f050522c310bcb17642362e`. Later incremental results must identify their own commit. **Overall BLOCKED / Draft; M3 in progress.** A local missing implementation is not a device blocker.

Legend: **bounded pass** = only the stated executable contract passed; **partial** = missing original-plan scope; **local open** = implementable here, not yet done; **external unverified** = actual platform/device/model/host not available. Knowledge/static checks never promote an execution layer.

## Milestones and original sections

| Plan reference | Current evidence | Status and outstanding work |
|---|---|---|
| §1, §9, §15 architecture/routing/package | 21 changed Skill files, unchanged 200 runtime file budget; deterministic package and routing tests | Bounded static/package pass; actual host discovery/read not verified |
| §2, §10 M0 baseline | Exact Skill16 and Skill18 CI cohorts; immutable old release contract; TEXT18 candidate contract | Partial: tests base is `feat/v1.0.16-source-review`, not main; CORE17 #10 remains separate; six partial mappings cannot be declared cumulative acceptance |
| §3, §18 sources | Frozen cited knowledge and sources checked statically | Not proof of each API's execution or all recent platform support |
| §4.1 C1 units/IDs/runs | Glyph identity/width/generation CPU negatives; actual Linux HarfBuzz single-run glyphs and positions | Partial: paragraph bidi, real fallback/font switches and complete multilingual semantics remain local open |
| §4.2 Android Java/JNI | Knowledge/contract only | External unverified: no actual Java/JNI platform invocation; not supplied by Linux HarfBuzz |
| §4.3 DirectWrite | Knowledge/contract only | External unverified: no actual DirectWrite run/outline/bitmap |
| §4.4 beyond-64k/new tables | Wide-ID and range contracts | Partial: real capable provider and new font format fixtures unavailable/unverified; uint32 storage is not provider support |
| §5.1–5.4 bitmap | HarfBuzz→FreeType grayscale→actual Vulkan readback for O/ffi/Arabic; fixed 1e-6 blend tolerance | Bounded pass; color glyph/emoji, variable font, MSDF/MTSDF implementation/comparison are local open, not device-only blockers |
| §5.2 filtering/data | Scalar linear oracle; actual packed UV quads, nearest sampling and bounded padding | Partial: bilinear/mip bleed, fractional geometry, distance range/derivatives remain local open |
| §5.3 temporal quality | 12/20px O with four post-hint quarter-pixel phases; area/centroid bounds preregistered | Partial: bounded nearest half/1/1.5 scale and quarter-turn added; arbitrary angles, perspective and comparative representation board remain open |
| §6.1–6.2 path subset | CPU M/L/Q/C/Z bounded flattening, holes, two fill rules, finite affine, controlled reject; five masks through Vulkan | Bounded mask fallback pass; triangulation, stroke/cap/join/dash and broader topology are local open |
| §6.3 clipping | Actual rectangle/circle/rotated-rectangle shader intersection; independent CPU reference and each-layer bypass negatives | Bounded hard fixed clip pass; arbitrary path/AA/stencil/variable clip stack and scene ordering remain local open |
| §6.4 world/3D | Knowledge only | Local open: world labels, near-plane clipping, finite extrusion/bevel, depth/shadows/second view |
| §7.1 key/packing | Finite keys; CPU shelf padding, batch atomicity, sealed-page snapshots, two→three real-glyph logical pages | Bounded packing and actual per-glyph UV-quad pass; not full renderer layout |
| §7.2–7.3 lifecycle | 64 generations/128 readbacks; two actual pages, canceled upload/publication, replacement and retirement; failures retain ownership | Bounded single-queue and combined two-page quad lifecycle pass; six-transition real run/size/direction churn added; long stress and locale/variation semantics remain open |
| §7.4 consumers | Two immutable sampled descriptor sets and pending timeline-gated fragment submissions; real fence status | Bounded pass; not shader-already-running, multi-queue or multi-device proof |
| §7.4 multi-engine | CPU boundaries described | Local open: two real Vulkan devices/outputs, shared CPU cache and independent GPU handles, pause/rebuild/destruction |
| §7.4 MRT | Active 3-color plus D32 write protection and legal wrong-output negatives; old fallback preserved | Bounded pass; stencil, actual occlusion, rendergraph/world ordering remain local open |
| §7.5 temporal/HDR | Linear composition checked numerically | Local open: full temporal/HDR handoff and world-motion experiment |
| §7.6 budgets/security | Bounded path/work/atlas input checks, controlled failures, no redistributed system font | Partial: CPU font-service memory and complete cold/hot resource accounting; fixture handle counts are not driver leak proof |
| §8 capability fallbacks | Explicit knowledge and CPU reject paths | Partial: each unimplemented renderer fallback needs execution before support claims |
| §10 M1 | Single-provider host implementation above | Partial, not all platforms/languages |
| §10 M2 | Bitmap and bounded vector mask above | Partial: MSDF/color/world/mesh/clip local open |
| §10 M3 | Current primary milestone | In progress: integration and combined stress gaps above |
| §10 M4 | Split exact-pair CI and local labs | Blocked: cumulative dependency, full labs, semantic Live and target/host gates |
| §11A quality board | Latin ligature, Arabic single run, O phase, same font/raster conditions | Partial: Chinese, mixed bidi, emoji, variable fonts, representations and transformations missing |
| §11B vector/world | Five generated masks, holes/curves/negative scale; hard nested shader clip | Partial: strokes, general/AA clips, world meshes/shadows/second view missing |
| §11C churn/overlay | Combined two-page lifecycle plus six-transition real content/size/direction churn | Partial: locale/axis semantics, two engines, active outputs and long stress not run |
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
| Host Unit | CI 237 CPU; bounded lifecycle/packing contracts and GPU integration tracked separately | Production threading and full renderer integration |
| Platform Integration | Linux trusted HarfBuzz/FreeType bridge only | Android JNI and Windows DirectWrite |
| Shader Unit | Actual compiler/SPIR-V tools in opt-in labs | Unimplemented paths |
| Vulkan Integration | Actual software Vulkan upload/draw/readback, packed quads, controlled pending consumers, active MRT/depth write protection and hard clips | Sustained churn/multi-device, depth occlusion/stencil/full renderer |
| Live Model | No model command configured, explicit SKIP | All TEXT18 semantics and final cohort behavior |
| Visual Quality | Narrow fixed ROI/phase oracle; selected rendered images inspected | Full board, independent font outline quality, display/color calibration |
| Device | None | Adreno/Mali/Windows sustained device performance |
| Package/Host | Deterministic package, exact pin/clean checks | Actual external host discovery/read |

## Pre-registered criteria (§13.1)

1. Semantics: limited fixed-provider run checks only; fallback/paragraph and Live remain unverified.
2. Composition: independent linear over reference and 1e-6 ROI tolerance; do not relax after failure.
3. Retirement: pending/final consumers and cancellation tested without illegal use-after-free.
4. MRT: active velocity/ID/depth write protection verified; stencil/occlusion and production integration remain open.
5. Geometry: bounded flattening and mask hole tests; no triangle/index acceptance yet.
6. Dynamic quality: phase-only area ≤5%, centroid error ≤0.15px, blend ≤1e-6; not all transforms.
7. Stability: fixed fixture inventories and controlled cleanup; no global allocator/driver leak claim.
8. Performance: reliable GPU timings, thermal/power and complete p50/p95/p99 breakdown **UNMEASURED**.

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
