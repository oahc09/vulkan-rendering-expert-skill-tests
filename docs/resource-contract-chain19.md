# Bounded cross-contract resource review

This is a HOST declaration checker, not a Vulkan event capture, validation layer,
GPU test, or complete Vulkan legality proof. It addresses a concrete gap: the
existing helpers accept separately declared prerequisites, so independently good
results do not ensure that the allocation, resource generation, descriptor
consumer and completion evidence refer to the same objects.

## Frozen implemented sub-denominator

`tests/fixtures/contract-registry19.json` freezes seven existing families and 23
semantic entry points, plus 21 explicitly classified implementation helpers.
Unknown added functions are rejected, not automatically called helpers. Module
bytes, function AST, signatures, original executable controls, 368 raw normative
maps, separate 309 VUID coordinates and existing Skill anchors are bound. Every
entry lists concrete owned prerequisites, but these remain **partial predicates**,
not exhaustive Vulkan obligations. The CLI executes all seven original commands
(125 controls), recomputes their reports and rebuilds the entire registry mapping.
A status string or indexed VUID does not complete a semantic scope, L1/L2, or the
497 Registry scopes. The two frozen normative versions are not interchangeable.

## User trace scope

The fixed JSON format accepts ordinary single-device/single-queue, non-sparse,
non-aliasing buffers and one-slot ordinary storage-buffer descriptors. No UAB,
descriptor buffer, sparse/external/protected resources or arbitrary user command
is supported. Buffer logical size and memory requirement size are separate.
Every recording is submitted at most once; explicit rerecording is required for
another submit. The tool does not implement general command-buffer reuse flags.

Four families are composed: memory binding/free, descriptor write/copy references,
ordinary dependency facts, and timeline snapshot semantics. Pipeline layout
compatibility remains an explicit subject-bound caller obligation. The original
layout, image-copy and image-layout controls are executed and inventoried, not
silently composed into this buffer workload.

`proofs` have `CALLER_DECLARED` or `UNRESOLVED` authority only. A complete-trace
statement binds the canonical scope/allocation/buffer/event bytes, not just event
IDs. Other statements bind exact objects, allocation generation, event IDs and
ranges. Matching evidence bytes proves integrity relative to the supplied hash,
not that the assertion is true. There is no VERIFIED-adapter escape hatch.
No omitted field is invented from old GPU reports.

The model derives ordinary descriptor consumers, recording invalidation,
submission references and known completion from the declared trace. Replacing a
descriptor does not retire an old submission. Updating a pending ordinary set is
rejected; updating a recorded set invalidates that recording until rerecorded.
A timeline counter predicate cannot mark all consumers complete. Binding memory
cannot establish a RAW dependency. Free while still bound may satisfy the
limited retirement obligations, but subsequent resource use is rejected. Copying
an undefined/dead descriptor token is not proof that reading through it is valid.

Results are `CONSISTENT_DECLARED_TRACE`, `OBLIGATIONS_NOT_ESTABLISHED`, or
`REJECTED_DECLARED_TRACE`, with an event index and reason. They are never actual
GPU proof. A consistent trace may end with pending work; it does not assert that
all resources have been retired or destroyed.

## Reproducible input and execution

The small `tests/fixtures/resource-contract-chain19.json` is an authored HOST
example, not an external project or captured run. Its evidence blob is exactly:

```
Caller declaration fixture, not a captured Vulkan event log.
```

Include a final newline, hash it, and save it under `<evidence-root>/<sha256>.bin`.
Supply an independently expected trace digest. All external inputs must be
regular files, not symlinks/FIFOs. Output must be a new directory.

```
python checks19/check_resource_contract_chain.py \
  --docs-root <frozen-Vulkan-Docs-368> --validusage <fixed-309-validusage.json> \
  --skill-root <paired-Skill-checkout> \
  --expected-tests-head <exact-Tests-SHA> --expected-skill-head <exact-Skill-SHA> \
  --trace tests/fixtures/resource-contract-chain19.json \
  --expected-trace-sha256 <expected-input-digest> \
  --evidence-root <local-declarations> --output <fresh-review-directory>
```

Strict mode requires clean paired revisions and exact committed executable bytes.
`--development` is explicitly a development receipt, not a published/strict run.
Exit 0 means only that the fixed controls and bounded declaration checks passed;
unknown/rejected traces and preflight failures return nonzero. Existing reports,
source changes, unknown functions, missing obligations, changed report contents,
wrong identities and bool/float-as-generation substitutions are negative controls.
No failure is described as a real Vulkan diagnostic unless separately executed.

The declared scope excludes dedicated allocations and buffers requiring dedicated allocation. `ORDINARY_ALLOCATION_VALID` includes this premise; the checker does not query dedicated requirements. Optional dedicated preference is not an allocation validity obligation and is not modeled.

`record_use` is an abstract rerecord declaration; it is not evidence of actual command-buffer reset, Begin/End calls or command-pool lifecycle execution.
