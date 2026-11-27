# CORE17 test reconstruction, not recovered historical evidence

This branch is a new reconstruction from the user's original
`Vulkan_Expert_Skill_v1.0.17_Vulkan全域覆盖与阶段验收开发计划_2026-11-08.md`
(SHA256 `2e72dfa5c46a29ccd02294dc01897c57aeda4d64c6df15c4c0afc8021d8e3470`).
It is NOT the lost local test candidate previously reported as 598 passed / 141
skipped. That count is not reused. Skill #13 explicitly disclosed that its
paired tests had not been published. Current branch/PR, Library title, task-note
and local unreachable-object inspection did not recover the original tests.
Absence from these sources does not prove no remote unreferenced object exists.

## Exact candidate and branch relationship

- Skill: `068a967038ce92a0d4f7c28e4dcdc70a1a3c7c4c` (merged #13,
  content commit `91393220aaf0ed9ab7aa089053598d988fcf609a`).
- Tests base: `528ba9ea7b417684c1066aceabd9a79cae4cd05b`, the v1.0.16 candidate.
- This is an independent branch; existing TEXT18 PR #9 base is unchanged.
- Tests #8 merged into the v1.0.15 branch, not main. Verified main snapshot
  `f8cadd3614f998b042b77293618323120bcb6d28` remains v1.0.14.
- The inherited release-contract.json remains v1.0.16. A separate
  core17-candidate-contract.json pins this reconstruction, never silently
  rewriting predecessor acceptance. No merge, release or base retarget occurs.

## Task registry

Original 120 prompt bytes are frozen against the published base. Plan §9.2
contains 24 capability tasks. Six old task groups provide partial related
coverage, but none establishes complete equivalence (e.g. FP16 lacks subgroup/
cooperative cases, Ray Query lacks the full pipeline path). This reconstruction
therefore registers 24 explicit paired inputs: 144 logical inputs cumulatively,
not the unrecovered historical claim of 138. The main Skill's older 6/18 mapping
claim describes its previous candidate and is not evidence for this new suite.
Evaluator rubrics remain separate with normal, capability-missing and recovery
directions. The existing runner is reused; no model call has occurred, and its
old --check gate is rejected for this cohort. Registration is not behavioral PASS.

## Frozen mechanical Registry inventory

Use the exact official XML URL/hash recorded in the numerical summary, then:

```
python tools/core17_registry_inventory.py --xml /local/vk.xml --out /new/inventory
```

The tool refuses wrong source bytes and existing output. It regenerates a full
machine-readable classification of all 730 extension records: 477 stable
Vulkan, 5 provisional, 242 disabled, 6 other/unspecified API. Twenty included
feature records represent the base/compute/graphics subdivisions of five core
versions, not 20 separate Vulkan versions. Deprecated/promoted/vendor entries
are not silently removed from the stable denominator. Require block/symbol attributes and require-local aliases are preserved;
remove blocks are recorded but not applied. Global command/type aliases are not
resolved. Direct required-symbol inventory is 833 commands, 3873
enums, 2490 types, deduplicated by category/name.

This is deliberately not called full coverage: transitive type/field/enum
closure, dependency-expression evaluation, L0 domain routing and L1/L2 semantic
review remain incomplete. Every record is UNREVIEWED. Registry counts are not
GPU, device, model or semantic evidence. Full generated XML-derived inventory
is reproducible locally; the repository publishes the compact numerical summary
and source hash, not environment logs or original raw evidence archives.

## Validation boundary

Run only the named reconstruction gates against the pinned Skill checkout:

```
VULKAN_SKILL_ROOT=/path/to/pinned-skill python -m pytest -c tests/pytest.ini \
  tests/test_core17_inventory.py tests/test_v1_0_17_registry.py tests/test_core17_pair.py
```

Inherited tests can still target their own old release contract. Do not weaken
old version assertions to manufacture a complete cumulative pass. New static
classification/registration checks and inherited CPU tests are separate layers.
No new shader/GPU coverage, Live semantic review, actual host or mobile device
acceptance is claimed. Gate K/B/P and release remain BLOCKED.

## Version-scoped CI correction and executable negatives

Initial PR head `0482bab` CI run 43669169807 failed because the inherited job
checked out the unchanged v1.0.16 release-contract SHA then ran the new CORE17
exact-pin assertion. That failure is retained, not rewritten as success.

CI now has two explicit profiles, both with read-only contents permission:
- `legacy16`: the original Skill pin and all 275 legacy static checks; the new
  CORE17 files are evaluated separately rather than against the wrong version.
- `core17`: the independent Skill17 pin and all static checks except the two
  named legacy16 version/release-pin nodes. These two unchanged tests still run
  in legacy16. Their version/routing/package/CRC/knowledge-budget checks are
  reproduced against the CORE17 pin, plus byte-identical double packaging.

No broad old suite is dropped or assertion weakened. Executable negative tests
reject mutable/wrong version pins, unsupported cohort fallback, dirty/hidden
Skill state, forged release PASS, incorrect frozen XML, and output overwrite.
The independent review confirmed the scope split and no workflow permission
expansion. All snapshot results remain historical; Live availability is not
semantic execution. No missing platform or GPU gate becomes PASS.

Local named commands:
```
python tests/run_versioned_gate.py --cohort legacy16 --skill /pinned/skill16
python tests/run_versioned_gate.py --cohort core17 --skill /pinned/skill17
```
Local verification before publishing: legacy16 static 275 passed;
core17 static 305 passed (251 not selected, including the 2 legacy-pin nodes);
each pairing Host CPU 123 passed and historical Snapshot 4 passed. Skill17
structure and 24 pack/host-contract unit tests also pass. These local results
are not a remote CI conclusion; PR records the later exact published result.
