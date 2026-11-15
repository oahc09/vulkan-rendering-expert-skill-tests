# TEXT18 current delivery audit: partial candidate, not release acceptance

This is the current concise index for the owner's v1.0.18 plan (§11, §13).
It does not replace historical evidence, add product scope or lower thresholds.
The long [completion matrix](text18-original-plan-completion-matrix.md) remains
an append-only experiment history; its early absence lists are historical.

## Exact pairing and delivery

- Skill candidate: `c0b62a19938a6b9cfce2ea6a5ce18f91b91e6344`, draft Skill PR #14.
- Executable tests baseline for this audit: `e130cb1fc8c7a3301f712d332dc44a4833a54c60`, draft tests PR #9.
- Tests base remains `feat/v1.0.16-source-review@528ba9ea7b417684c1066aceabd9a79cae4cd05b`, **not main**.
- CORE17 sibling PR #10 remains independently pinned at `4fc46c4788cfaf4836037b66fa17d403970395d3`. Its static dependency result is not merged semantic acceptance. Six partial mappings and zero equivalence reuse remain unchanged.
- Old v1.0.16 contract remains paired with Skill `416f4a6c0c887dee72bcc6dca13ce9c857d7957f`; it is not relabeled TEXT18.
- Candidate release status remains BLOCKED. No merge, retarget, release or deployment is performed.

## Current plan coverage, without counting examples as milestones

| Plan area | Implemented and evidenced bounded scope | Still incomplete |
|---|---|---|
| C1 provider/run semantics | Actual Linux HB/FT, fixed-font fallback, bounded mixed-paragraph bidi checked against ICU, emoji VS15/VS16, variable-font experiments | Android Java/JNI and Windows DirectWrite; provider capability/fallback coverage. Finite inputs do not establish general Unicode layout; all font formats are not a new requirement. |
| C2 representations / Scene A | Actual bitmap/color/MSDF delivery; same-layout multilingual, emoji-fallback and two-variable-instance board with fixed scaling/phase comparisons | The finite board and high-density refinement are measured, including all seven rows in a new common square rotation output. One fixed bounded perspective and explicit byte-budget fallback are now measured; general perspective and remaining visual-quality qualification are incomplete. |
| C3 vector/world / Scene B | Bounded fills/strokes/AA and clipping plus a shared world-text core joining one visible/casting L prism, an O label, ordinary occluder/receiver, one immutable light map and two oblique views; now a fifth same-pass screen-vector draw with bounded fill rules, round-cap stroke and three nested clips | Shared complete Scene B and joint visual regression remain incomplete. Arbitrary triangulation/curve AA/bevel/general lighting are unverified boundaries, not additional mandatory product scope. |
| C4 cache / Scene C | Real CPU cache ledger; resident online producer and dual offscreen outputs now integrate natural packed-page growth, pending cancel/retry, immutable old UV snapshots, active MRT and pause/destruction/rebuild | The integrated fixed 8-to-9 instance / two-page sequence is bounded; continuous locale/variation/size workloads, scale tiers, sustained stress and whole-chain costs remain incomplete. |
| Temporal / HDR boundary | Actual scalar temporal SSBO consumed by linear HDR scene then UI, with history pollution and early-tone-map negatives | World-text motion and full-scene interface consumption remain unverified. Full RGB TAA and physical HDR-display certification are outside this bounded test, not new reimplementation requirements. |
| Package / static | Exact pair guard, deterministic whitelist package, unchanged routing and 200-file runtime limit | Actual external host discovery and semantic model behavior. |

**M1-M3 remain partial; M4 remains BLOCKED.** Local gaps above are not all
hardware blockers. This Skill upgrade is also not authorization to build an
unbounded production UI/font engine, full SVG implementation or new renderer.

## Evidence entry points

All entries below are source/tests plus sanitized numeric reports. Raw receipts,
fonts, binaries and environment/driver logs remain local and are not redistributed.

- `tests/fixtures/text_fallback_lab`, `text_bidi_lab`, `text_emoji_lab`: explicit provider and routing scope.
- `reports/history/text18-msdf-integration-public`, `text18-phase-integration-public`, `text18-phase-sequence-public`: dynamic representation evidence and remaining qualification limits.
- `tests/fixtures/text_near_clip_lab`, `text_second_camera_lab`, `text_shadow_lab`: limited world-space evidence, including preserved failures.
- `tests/fixtures/font_cache_cost_lab`: application-cache cold/hot HB/FT accounting, not process/OS cold or native heap.
- `tests/fixtures/font_cache_churn_lab`: actual cache products to one-device lifecycle; CPU pre-generation, fixed pages, UNUSED/preserve auxiliaries.
- `tests/fixtures/font_cache_dual_mrt_lab`: actual hot products to dual offscreen devices with active three attachments; B cancellation occurs after its upload finishes. No depth/clip/growth in that path.
- `tests/fixtures/text_temporal_hdr_lab`: scalar temporal/HDR/UI isolation, not full RGB TAA.
- `docs/text18-core17-dependency-gate.md` and the candidate contract: independent dependency and blocked release semantics.

## Preserved failures / incomplete qualification

- Dynamic MSDF is MEASURED_NOT_QUALIFIED. A successful fixed glyph is not a replacement for the failed dynamic series.
- Near-plane hardware-NEAREST texel-boundary counterexample remains recorded. Bounded integer-ray texel selection is a separate fallback, not evidence that general hardware sampling was fixed.
- Temporal stage's first double-destruction validation failure was fixed with single ownership; original failure retained. No ignored validation errors or loosened tolerance.
- Missing physical-device, platform-bridge and Live execution cannot be inferred from CPU contracts, shader compilation, software Vulkan or historical snapshots.

## Next decisions and stop rule

Do not automatically add more one-glyph/one-pass combinations. The concentrated
resident Scene C service and seven-row Scene A board now have bounded executable
evidence, not complete scene qualification. Highest-value local follow-up must
address the board's remaining measured quality / reference limitations under
common conditions, or integrate original Scene B. One fixed perspective is now
measured; it does not certify general perspective or near-plane typography. The new common square
output now accommodates every row's rotation; old clipping rejections remain
historical evidence.
Do not replace these gaps with further unrelated one-glyph examples. No general
allocator, full Unicode layout engine or new universal quality threshold is
required by this audit.

External blockers are specific: actual Android/JNI and Windows DirectWrite runs;
Adreno/Mali and available Windows hardware; real Surface/host integration;
authorized model wrapper for TEXT18 Live, original answers/usage and semantic
review; eventual dependency/base integration. No access or hardware is fabricated.
This stage stops at an honest partial candidate and audit, not a claim that these
conditions are the only remaining work or that the original objective is met.

Rollback: keep existing branches/history. To undo an individual tests increment,
use a reviewed revert on that branch; do not force-reset shared branches or edit
old evidence. Skill runtime bytes and existing release contracts are unchanged
by these tests-only increments.

## Frozen cumulative verification

At executable baseline `e130cb1fc8c7a3301f712d332dc44a4833a54c60`,
paired with Skill `c0b62a19938a6b9cfce2ea6a5ce18f91b91e6344`, the accumulated
explicitly selected TEXT18 local suite completed **319 passed in 907.94 seconds**.
This includes the enabled software-Vulkan labs, new temporal/cache/dual-MRT
paths and host/contract/pair/package tests. It is not every historical repository
test, nor an Android/Windows/Live run. No failed dynamic-quality metric was
promoted to PASS: tests may correctly verify refusal or not-qualified outcomes.
Source tests and thresholds were unchanged for this consolidation run.

That executable head's CI run `43700378338` has three successful jobs: TEXT18
316 static / 351 CPU / 4 snapshot; legacy16 281 / 351 / 4; CORE17 dependency
307 static. These overlap with local tests and must not be summed as distinct
coverage. Live explicitly reports `SKIPPED: no model command configured`.
The software-Vulkan opt-ins are local results, not automatically executed in CI.
This audit-only documentation commit follows the measured executable head;
its own exact-head CI/pair checks are reported in the PR, without relabeling the
319-case execution as a run of a different commit.

Deterministic package verified twice in the local suite: 200 files, 1,076,029
bytes, SHA-256 `5484d42e7a73ffa4c11073b5ef16b76cdd39e23d5e9aa98b2d36ff110ae9061e`.
No raw evidence ZIP or font is uploaded by this audit.

## Concentrated Scene C integration update

The subsequent `scene_c_service_lab` implements the concentrated milestone
identified above for a frozen finite sequence. Actual F cache production occurs
after A pending acknowledgement; natural packed capacity grows from one to two
pages, both are consumed within one renderpass, and old UV snapshots remain
valid across cancellation/retry and independent output destruction/rebuild.
See its pre-registered `criteria.md` and the latest matrix section. The earlier
319-test frozen run and executable SHA remain historical results, not silently
reassigned to this new implementation. Full workload/physical-device/Live
acceptance remains incomplete; this does not create new general-product scope.

## Concentrated Scene A same-layout board

`tests/fixtures/scene_a_board_lab/criteria.md` freezes seven real-content rows
before candidate rendering: Chinese, ffi, combining a+acute, a fixed mixed bidi
paragraph, VS16 emoji and two full variable-axis instances. Complete shared HB
positions/face/axes/ppem and FT 26.6 origins feed both unhinted FT bitmap and
original outline / pinned RGB-MSDF, without per-glyph ink normalization.

The frozen local selection passes 8 tests (7 host plus one Vulkan integration)
in 67.43 seconds. There are 53 positive tiles: 24 bitmap, 24 MSDF and 5 color
emoji fallback; MSDF is explicitly inapplicable to the emoji. Original numerical
gates remain 1e-6 / .004 with zero excluded pixels. Worst numerical errors are
1.0654075721650003e-7 including emoji and 1.3627111936642677e-6 for MSDF.
The first bidi-minification bitmap failure (1.305590075773e-6 > 1e-6) remains
recorded. Fixed 3/4 inverse sampling now computes rational texel coordinates;
layout, reference and gates did not change. Actual double-alpha and wrong-range
negative shaders are rejected with errors .1499423325 and .1587432742.

Sampling PASS is not visual-quality qualification: maximum original-outline
alpha difference remains .486328125, and phase geometry-subtracted residuals
are reported separately. Per-image foreground/partial-glyph-edge ROI metrics
are available. Column-difference and phase MAEs are full-tile means, not ROI
quality scores. Six monochrome rotate90 cases remain UNSUPPORTED_CLIPPING in
both columns; emoji rotate90 fits. Perspective is UNMEASURED. The full board
was viewed, but remains MEASURED_NOT_QUALIFIED. Auxiliary images are UNUSED /
preserve, not active MRT, and no hardware timing/energy conclusion follows.

Source and sanitized numeric report are committed; fonts, generated font
resources, raw readbacks and provider/environment receipts stay local. This
increment does not relabel the earlier 319-case cumulative run as a run of the
new board head. Exact-head regression and CI results are reported in PR #9.

## Scene A source-density root cause and complete square rotation

`scene_a_refined_board_lab/criteria.md` independently registers a refinement;
the original board and historical unsupported cases are unchanged. The original
maximum (.486328125) is explained by an exact straight-stem anchor: glyph 553's
.8125-pixel-wide stem has exact alpha .609375 at the half-phase target pixel,
while the 1x MSDF returns .123046875. Both adjacent source samples lack positive
interior distance, so interpolation loses the thin stroke. This is spatial
representation undersampling, not a demonstrated shaping/composition/reference
failure or an established msdfgen library defect.

Official generation now uses 4x projection, 260x196 source and a shape-unit
range of 4 (16 source texels, unchanged 4 original-screen pixels). Fragment
integration remains linear4. New output is uniformly 65x65 with +8 output-y
translation; square-rotate90 is pure rotation, not per-row fitting/rescaling.
All seven rows fit this new rotation, while the old six monochrome rejection
labels remain explicitly historical.

Frozen selection: 8 passed in 127.85 seconds, with 66 actual positive tiles,
zero numerical exclusions and unchanged sampling tolerances. Original worst
anchor error becomes exactly zero; maximum MSDF outline-alpha difference across
the refined board is .052734375. All 24 historically matched MSDF cases improve
both maximum error and foreground ROI MAE. Bitmap maximum differences are
unchanged, not claimed fixed. Baseline report SHA and canonical layout receipts
are checked; before/after refers to historical frozen 1x results, not a same-run
1x execution. Exact-head related regression separately reruns both fixtures.

Quality remains MEASURED_NOT_QUALIFIED: remaining MSDF error, bitmap error,
curved-outline reference approximation, perspective and target platforms are not
closed. Worst MSDF phase residual is .0236661434173584; full-tile phase means are
not ROI scores. Two actual shader negatives and auxiliary preservation still
apply. Payload capacity increases from 815,360 to 13,045,760 bytes (16x); this is
an explicit storage/upload tradeoff, not measured VRAM or mobile throughput.
No font, generated resource, raw environment log or image is uploaded.

## Scene A compact storage, budget fallback and bounded perspective

The remaining old .052734375 maximum includes geometric-reference quantization.
At the ! bar half-phase pixel, exact rectangular area gives alpha .43560791015625,
versus old 16x16 reference .3955078125 and GPU .4482421875. Exact local GPU error
is .01263427734375. This reclassifies one error, not a new rendering improvement
or permission to overwrite old metrics or relax gates.

`scene_a_budget_board_lab/criteria.md` independently freezes per-glyph crop
bounds plus three source-screen pixels, exact metadata and vertical packing.
Full 4x MSDF sources are still freshly generated; source CPU peak/work is not
optimized. Requested source image/upload payload now includes the actual packed
W*H*16 header/padding. Per monochrome row it is 101,184–369,600 bytes, versus the
prior 13,045,760-byte band capacity. This is tight storage, not adaptive density
or measured VkMemoryRequirements/VRAM savings. Each row/budget has an independent
logical Device, sharing its compact image across transforms.

A declared 400,000-byte probe budget selects 4x for all monochrome rows. At
200,000 bytes Chinese/ffi/bidi/variable-heavy explicitly fall back to bitmap;
combining and variable-light retain 4x, and emoji retains color bitmap. A 4096
budget rejects all seven rows before GPU creation. The policy consults resource
cost only, not quality-oracle output; these are experiment inputs, not mobile
product thresholds. Bitmap fallback is a quality tradeoff, not equivalence.

The frozen 10-test selection passed in 138.42 seconds. There are 86 actual
positive images: 72 existing conditions plus 14 new perspective cases. All 72
match the historical full-texture GPU image for their CORRESPONDING selected
representation (MSDF, bitmap or color) with zero float delta, not bitmap-vs-MSDF
equivalence. All numerical gates remain 1e-6/.004, zero exclusions. Actual
wrong-origin and wrong-affine-inverse shaders fail (.5624999285/.5999999985),
with auxiliary preservation separately checked. The latter also worsens the
independent geometric MAE from .00030038295 to .01772499302.

Perspective uses a real projected six-vertex quad, fixed scale .75 and
w=1+(x-32.5)/128, positive over the source. Fragment inverse homography and a
local inverse-Jacobian AA estimate are checked against CPU inverse/finite
differences, while separately projected source outlines provide geometric
coverage. This does not certify hardware varying interpolation or exact
anisotropic area. The first emoji perspective error 1.0528854150204658e-6
failed 1e-6; fixed-camera rational texel indexing fixes cancellation without
changing layout, reference or gate. First failure evidence remains local.

High-budget perspective maximum outline-alpha error is .040109872817993164;
low-budget bitmap fallback reaches .2594186067581177. Neither is renamed
qualified. Curved-area references remain approximations. The earlier Scene A
inputs, scaling, rotation, phases and this bounded perspective are now represented
in executable comparisons; this is not complete physical-platform, general
text quality or Live acceptance. The next concentrated local milestone should
be chosen from original Scene B/C gaps rather than adding arbitrary glyph cases.


## Shared Scene B world-text core (2026-11-15)

Frozen criteria and implementation: `tests/fixtures/scene_b_shared_world_lab`;
minimal results: `reports/history/text18-scene-b-shared-world-public/numerical-summary.json`.
The same actual HB/FT L vertex buffer is rendered into the light D32 image once
and as visible extrusion in both views. Both camera passes consume that same
immutable image directly, together with ordinary receiver/occluder geometry and
a complete actual O coverage bitmap. No composition of historical screenshots
or CPU shadow reupload. One Device; two oblique/shear parallel ray directions,
not perspective or orthonormal camera rotations. The glyph image is reuploaded
per view; this is not an upload-once optimization claim.

Independent original-contour ray intersections and original bitmap sampling
check every camera color/depth pixel, plus independent light-map depth.
Pre-GPU reference requires visible cap, side, receiver shadow, visible and hidden
label in both cameras. Frozen local 2 host + 1 GPU tests passed (12.90 seconds):
max color 1.2734357e-7, scene depth 2.9702516e-7, light depth 1.4851258e-7,
against unchanged 1e-6 with zero excluded pixels. Actual bypass-shadow and
stale-label-camera negatives produce .600000012 and .225000024 color error
while scene depth and active auxiliary attachments remain protected. Initial
compile failure from an inherited main-macro collision was retained locally
and corrected without changing scene criteria or thresholds.

This closes a bounded shared world-text core, NOT complete Scene B. Original
path/fill/stroke/cap, nested clip, near-plane and negative-scale cases remain
separate rather than jointly integrated here. No sustained stress, arbitrary
allocation/device-loss cleanup, physical target-device/Surface or Live claim.
C1-C4 and M1-M3 remain partial; M4 remains BLOCKED. Exact-head post-publication
regression and CI receipts are recorded in PR comments; the earlier 319-test
cumulative receipt belongs only to e130cb1, not this stage. Branch/base and
Skill c0b62 pairing are unchanged.


## Scene B same-pass vector integration (2026-11-15)

`tests/fixtures/scene_b_vector_overlay_lab` extends the shared world executor,
not a stitched image: one Device/light image, twelve serial camera passes,
five real draws each. The fifth draw is a support quad with analytic hard
pixel-center rectangular-ring/straight-stroke union, one alpha .35 composition,
and three fragment clip layers. It is screen-space, ALWAYS/depth-write-off;
world depth and active auxiliary outputs are independently retained.

Five positive full views cover both cameras, opposite-inner nonzero/evenodd
and same-inner nonzero/evenodd. Same-inner nonzero visibly fills the hole.
Independent CPU oriented winding, closest-segment distance and finite-edge plus
ray-crossing clip reference checks full composition. Seven actual negatives
bypass each clip, fill the hole, change round to butt, bypass shadow or use
stale label camera; depth/aux are validated before color rejection.

First candidate run failed at five exact rotated-clip edge pixels because the
new CPU reference omitted finite closed-boundary inclusion already present in
the old clip reference and GPU shader. That reference migration defect was fixed
and host-tested without changing rendering, coordinates, tolerance or exclusions.
First failure and initial preflight counts remain recorded. Corrected clip
difference counts are36/91/35, wrong-hole256, wrong-cap12.

Frozen local validation: 3 host + 1 actual GPU tests passed in19.11seconds;
positive color max8.1956387e-8, scene depth2.9702516e-7, light depth1.4851258e-7.
Unchanged1e-6 whole-image gate, zero excluded pixels. Seven negative color errors
range .225000024 to .600000012 while protected attachments/depth remain valid.
Minimal report: `reports/history/text18-scene-b-vector-overlay-public/numerical-summary.json`.

Still not complete Scene B: round frames, quadratic/cubic paths, more general
controlled contours, near/negative-scale integration and remaining original
scene combinations are not closed. No general SVG, world-space path, AA,
perspective, real Surface/device or Live claim. Original branch dependency,
Skill c0b62 pair and partial/BLOCKED milestones unchanged. Exact-head selected
regression/CI receipts follow in PR comments, not inferred from this local run.


## Scene B true perspective / near / reflected object joint route (2026-11-15)

New `scene_b_perspective_lab` keeps the real shared-world shadow producer,
visible L prism, ordinary meshes, O label and vector fifth draw in each camera
pass. Actual clip.w=viewZ replaces shear. Two translated cameras are used in
three complete variants: normal near1, near22 crossing the prism, and object
x'=65-x applied to both visible and shadow vertices. Each variant uses its own
Device, with internally shared resources. Fifteen positive views and21 inherited
negatives are exercised, plus separate wrong-near and wrong-caster-model variants.

Independent original-contour rays select surviving cap/side intersections after
near clipping, not just the nearest rejected front hit. GPU receives uncut
triangles; no fragment near discard substitutes for fixed-function clipping.
Fraction source-plane references independently check specialized rational texel
reconstruction. The original hardware-nearest limitations are not declared fixed.

Retained failures: initial near/B hardware-interpolated depth1.0312789373e-6
exceeded1e-6; initial reflected/A source right-edge inclusion also failed color
(.5749999881) and depth(.0146519537). The finite route explicitly reconstructs
fragment projection depth and enforces the ordinary rectangle's original half-open
source domain. Geometry, reference, near value and tolerances did not change.
This is not a general raster/depth precision repair. Boundary enumeration finds
two excluded-right-edge center ties (normalA pixel52, reflectedA pixel12), no
included boundary centers in the registered views. An initially incomplete host
expectation omitted the normal tie and failed before correction; it is retained.
Discard cannot restore missing raster support; no arbitrary transform claim.

Frozen6 tests passed in24.79seconds: color max1.2814999e-7, near scene depth
6.7365107e-7, normal/reflected depth9.362803e-8, light depth4.0233136e-7.
Original1e-6/zero exclusions retained. Inherited negatives keep correct scene
depth; wrong-near deliberately changes projection and fails both color/depth,
while wrong-caster fails shadow/color but preserves camera depth. These distinct
negative categories are not conflated. Minimal report is under
`reports/history/text18-scene-b-perspective-public/`.

PR#9 was verified merged at head0e3870f into its source-review base. This work
is an independent closeout increment, not an update to the closed PR. It does
not alter CORE17 pins or the separately assigned v1.0.19 work. Raw evidence stays
local. Remaining original Scene B round/quadratic/cubic path scope and wider
combined quality are incomplete; no real Surface/physical-device/Live acceptance.
Milestone partial/BLOCKED labels are not promoted by these bounded passes.

Closeout publication base: source-review merge90b2df2c49c65512d52928ca81051e4e5b2b6cc3
includes merged PR#10 head e8bcb1b1. Its gate isolation/workflow changes are
preserved byte-for-byte. Existing pinned historical CORE17 dependency is not
silently updated; current merged CORE17 is checked by its own current job.
