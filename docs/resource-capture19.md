# Two-SSBO capture and bounded contract adapter

This reuses `cases19/binding_choice`'s traditional-set two-epoch compute workload.
The shader, two buffers, 64-word inputs and independent full-output reference are
unchanged. Optional fifth probe argument names a fresh JSONL capture file; push
capture is unsupported. With no fifth argument the original set/push comparison
still uses the same oracle, call counts and result codes. Historical receipts
remain bound to their old source revisions, not silently updated.

`checks19/run_resource_capture.py` compiles/validates/disassembles the real shader,
compiles the real probe, runs ordinary set → push → set recovery, then captured
set good and second-epoch wrong-output. The latter really changes one expected
value and exits 6. No pending update/free or invalid GPU submission is injected.

## What is captured, and what is not

The optional stream records API result observations, requirements2 (including
requiresDedicatedAllocation), actual bind sizes/type/offset, descriptor slots,
complete input/sentinel host-write arrays, recording and submission identities,
fence completion, host read, unmap/destroy/free and final result. Resource lifetime
generation stays 1; content and recording epochs are 0 and 1. One real CB submit
contains **both** READ input and WRITE output references. No fictitious second
submit or omitted input reference is used. IDs are fixed source-cohort array slots,
not a general interception layer. Descriptor buffer ordinals/ranges derive from
actual descriptor structures. Shader READ/WRITE access is a source-reviewed static
mapping, not an API-reflection observation. Generic API strings are fixed source
call-site labels, not a complete argument or handle capture.

Schema 2 is a **fixed source-cohort sequence adapter**, not a general multi-resource
lifecycle solver. It rechecks the existing binding output gate and memory bind/free
contracts. It does not execute or claim composition of all seven HOST families.
Schema 1's existing semantics are unchanged. The capture branch additionally
queries dedicated requirements and blocks if its non-dedicated scope is unmet.

The second epoch is fence completion → full coherent HOST rewrite of both buffers
→ fresh recording/submission. It is not a fabricated compute-to-compute barrier.
The existing input HOST barrier is checked as part of this exact fixture, not
asserted as universally necessary: coherent pre-submit writes can use submission's
host-domain operation. Actual output shader→HOST dependency and fence wait precede
readback. The fixed single-thread, inventory-completeness and pipeline/allocation
validity premises are still explicit external obligations.

Default authority is UNRESOLVED, even after successful capture and output checks.
`CAPTURE_RECHECKED` / exit 0 means **capture verification completed**, not that
contract obligations were established. `contract_states` reports this separately.
An explicit declarations file can produce CONSISTENT_DECLARED_TRACE, never
VERIFIED authority or complete Vulkan legality. Source/log hashes bind bytes, not
truth, unauthenticated instrumentation or missing concurrency. No performance,
physical-GPU, full L1/L2 or release claim follows.

## Run

```sh
python checks19/run_resource_capture.py \
  --toolchain /path/to/scene19-toolchain.json \
  --skill-root /path/to/paired-skill \
  --spec-root /path/to/frozen-vulkan-docs \
  --expected-tests-head FULL_TESTS_SHA --expected-skill-head FULL_SKILL_SHA \
  --output /fresh/output --budget-seconds 120 --step-seconds 60
```

The shared toolchain has exact keys tools/include/loader/icd/layer_path/library_path/
validusage. The validusage path is accepted for config compatibility but is not
used as a 309 VUID proof here; fixed original binding normative prose is verified.
Actual linked loader, ICD/layer libraries, complete supplied include-header tree,
compiler, shader tools, source and streams are hashed and rechecked. No arbitrary
commands are accepted. Strict mode checks exact clean paired heads and committed
source bytes before importing helpers. `--development` is explicitly non-strict.
Execution budgets start after preflight, not before hashing. Cancellation and
step/global budgets control only this run's owned process groups; failure is
BLOCKED and recovery requires a fresh output directory.

Optional declarations file (these are caller claims, not capture-derived facts):

```json
{
  "complete_single_thread_inventory": "CALLER_DECLARED",
  "allocation_and_pipeline_validity": "CALLER_DECLARED",
  "host_coherent_submission_scope": "CALLER_DECLARED"
}
```

Pass `--obligations FILE --expected-obligations-sha256 SHA256` explicitly. Without
it all three obligations remain UNRESOLVED. Never infer declarations from PASS.

HOST mutation tests start from complete real captured positive records, then
re-index events after deleting a wait, changing generations/references, moving a
free early or corrupting outputs and their summary. These are evidence-validator
negatives, not real GPU misuse or proof that all forged logs can be detected.
