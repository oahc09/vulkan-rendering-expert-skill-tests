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
| C2 representations / Scene A | Actual bitmap and color-glyph delivery, MSDF production/consumption, fixed transforms and representation controls | One same-condition multilingual/emoji/variation quality board across representations; dynamic MSDF quality remains not qualified. |
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

Do not automatically add more one-glyph/one-pass combinations. The highest-value
remaining local integration milestone is original Scene C's **real packed-page capacity
growth with old published UV snapshots preserved**, together with the
existing cached producer and two-output lifecycle. It must specify original-plan
input/quality/reference conditions before execution and reuse the existing
framework rather than growing a new product. Repacking/resizing is not mandatory:
new-page growth or explicit budget rejection/fallback may be valid; do not add a
general allocator requirement to the original plan. Complete Scene A/B comparison boards
are separate concentrated milestones, not a checklist of further tiny examples.

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
