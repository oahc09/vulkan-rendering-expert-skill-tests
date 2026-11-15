# v1.0.18 original-plan completion matrix

Assessment against the owner's **2026-11-08 Text, Vector & 2D/3D Composition** plan, not a reduced replacement plan. Evidence baseline: Skill `c0b62a19938a6b9cfce2ea6a5ce18f91b91e6344`, tests `e2e730f75a6e0e79d3b74833c082953e6a83ef41`. Later incremental results must identify their own commit. **Overall BLOCKED / Draft; M3 in progress.** A local missing implementation is not a device blocker.

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
| §5.2 filtering/data | Scalar linear premultiplied oracle, nearest sampling and bounded padding | Partial: packed UV draw, bilinear/mip bleed, distance range/derivatives need executable coverage |
| §5.3 temporal quality | 12/20px O with four post-hint quarter-pixel phases; area/centroid bounds preregistered | Partial: shrinking, rotation, perspective and comparative representation board local open |
| §6.1–6.2 path subset | CPU M/L/Q/C/Z bounded flattening, holes, two fill rules, finite affine, controlled reject; five masks through Vulkan | Bounded mask fallback pass; triangulation, stroke/cap/join/dash and broader topology are local open |
| §6.3 clipping | Knowledge only | Local open: nested stencil/mask clips, nonrectangular clip and ordering |
| §6.4 world/3D | Knowledge only | Local open: world labels, near-plane clipping, finite extrusion/bevel, depth/shadows/second view |
| §7.1 key/packing | Finite keys; CPU shelf padding, batch atomicity, sealed-page snapshots, two→three real-glyph logical pages | Bounded pass; whole-page readback does not yet render per-glyph UV quads |
| §7.2–7.3 lifecycle | 64 generations/128 readbacks; two actual pages, canceled upload/publication, replacement and retirement; failures retain ownership | Bounded single-queue pass; combined renderer-level asynchronous packing/churn remains local open |
| §7.4 consumers | Two immutable sampled descriptor sets and pending timeline-gated fragment submissions; real fence status | Bounded pass; not shader-already-running, multi-queue or multi-device proof |
| §7.4 multi-engine | CPU boundaries described | Local open: two real Vulkan devices/outputs, shared CPU cache and independent GPU handles, pause/rebuild/destruction |
| §7.4 MRT | Separate overlay UNUSED/preserve velocity and ID sentinels | Partial: active MRT and depth/stencil protection are local open; not complete attachment acceptance |
| §7.5 temporal/HDR | Linear composition checked numerically | Local open: full temporal/HDR handoff and world-motion experiment |
| §7.6 budgets/security | Bounded path/work/atlas input checks, controlled failures, no redistributed system font | Partial: CPU font-service memory and complete cold/hot resource accounting; fixture handle counts are not driver leak proof |
| §8 capability fallbacks | Explicit knowledge and CPU reject paths | Partial: each unimplemented renderer fallback needs execution before support claims |
| §10 M1 | Single-provider host implementation above | Partial, not all platforms/languages |
| §10 M2 | Bitmap and bounded vector mask above | Partial: MSDF/color/world/mesh/clip local open |
| §10 M3 | Current primary milestone | In progress: integration and combined stress gaps above |
| §10 M4 | Split exact-pair CI and local labs | Blocked: cumulative dependency, full labs, semantic Live and target/host gates |
| §11A quality board | Latin ligature, Arabic single run, O phase, same font/raster conditions | Partial: Chinese, mixed bidi, emoji, variable fonts, representations and transformations missing |
| §11B vector/world | Five generated masks, holes/curves/negative scale | Partial: strokes, nested clips, world meshes/shadows/second view missing |
| §11C churn/overlay | Separate bounded packing/growth/churn/descriptor experiments | Partial: real changing glyph/size/locale/axis stream combined with two engines and active outputs not run |
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
| Host Unit | CI 237 CPU; local aggregate 148 selected tests | Production threading and combined renderer integration |
| Platform Integration | Linux trusted HarfBuzz/FreeType bridge only | Android JNI and Windows DirectWrite |
| Shader Unit | Actual compiler/SPIR-V tools in opt-in labs | Unimplemented paths |
| Vulkan Integration | Actual software Vulkan upload/draw/readback/controlled pending consumers | Active MRT/depth, multi-device and packed quads at this baseline |
| Live Model | No model command configured, explicit SKIP | All TEXT18 semantics and final cohort behavior |
| Visual Quality | Narrow fixed ROI/phase oracle; selected rendered images inspected | Full board, independent font outline quality, display/color calibration |
| Device | None | Adreno/Mali/Windows sustained device performance |
| Package/Host | Deterministic package, exact pin/clean checks | Actual external host discovery/read |

## Pre-registered criteria (§13.1)

1. Semantics: limited fixed-provider run checks only; fallback/paragraph and Live remain unverified.
2. Composition: independent linear over reference and 1e-6 ROI tolerance; do not relax after failure.
3. Retirement: pending/final consumers and cancellation tested without illegal use-after-free.
4. MRT: UNUSED/preserve only; active velocity/ID/depth not accepted.
5. Geometry: bounded flattening and mask hole tests; no triangle/index acceptance yet.
6. Dynamic quality: phase-only area ≤5%, centroid error ≤0.15px, blend ≤1e-6; not all transforms.
7. Stability: fixed fixture inventories and controlled cleanup; no global allocator/driver leak claim.
8. Performance: reliable GPU timings, thermal/power and complete p50/p95/p99 breakdown **UNMEASURED**.

Priority local work: actual packed UV glyph quads, then active output/depth protection and combined bounded renderer lifecycle. Other original-plan local gaps stay visible; they must not be mislabeled as hardware blockers. Retain original failed host-event validation evidence and prior failing CI. Only source and stripped numerical summaries publish; raw logs/environment/font evidence stay local.

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
