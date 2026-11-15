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
| C2 representations / Scene A | Actual bitmap/color/MSDF delivery; same-layout multilingual, emoji-fallback and two-variable-instance board with fixed scaling/phase comparisons | The finite board and high-density refinement are measured, including all seven rows in a new common square rotation output. Perspective and remaining visual-quality qualification are incomplete. |
| C3 vector/world / Scene B | Bounded fills/strokes/AA, straight-outline extrusion, world planes, near clipping fallback, second view and depth-produced hard shadow sampling | Shared complete Scene B and joint visual regression remain incomplete. Arbitrary triangulation/curve AA/bevel/general lighting are unverified boundaries, not additional mandatory product scope. |
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
address the board's remaining measured quality errors / unmeasured perspective
under common conditions, or integrate original Scene B. The new common square
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
