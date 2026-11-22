# Repeated external-history tasks: one bounded delivery loop

This milestone combines independently classified historical tasks and unchanged
upstream regression cases. It does not create more historical defects by counting
extra tests, and does not convert public repair history into blind model evidence.

## Original-plan stage check

| Stage | This milestone contributes | Still not established |
|---|---|---|
| M0 (still the sole in-progress stage) | Exact two-repository execution pair and fixed task/tool inputs | Complete stable semantic denominator and all inherited acceptance |
| M1/M2 | Explicit knowledge routes and task-specific source/oracle contracts | Whole L1/L2/SC conflict/depth coverage |
| M3 | Original historical repair, actual tool outputs, repeated before/after/regression checks | Independent unseen model engineering delivery and broad project generalization |
| M4 | Negative results and explicit scope, not a performance claim | Comparable real hardware quality/power/thermal gains |
| M5/M6 | Process controls, preserved partial evidence and readable replay record | Final 36 tasks, blind/Live, target devices and release seals |

No stage is promoted solely because this suite completes. Release remains BLOCKED.

## Fixed classes, not pooled success percentages

1. **FencePool historical timeout width**: unmodified original class with explicit
   HOST API/dependency test doubles. Actual compilation and boundary regression;
   not a driver/GPU wait or a full Renderer execution.
2. **Amber #951**: complete original engine Vulkan CLI on the fixed CPU software
   ICD. Old output-aggregation error precedes EXPECT; fixed three original EXPECTs
   pass; rollback reproduces old failure; separately labeled wrong-EXPECT mutant
   fails. Shared contemporary dependencies are not the historical DEPS toolchain.
3. **Related Amber upstream regressions**: unchanged inputs present in both
   revisions, executed against both. These are ordinary context regressions, not
   three new discovered defects, blind tasks or additional hardware coverage.
4. **Amber #1119 capability screen**: previous missing depthClampZeroOne result is
   explicitly not part of successful executions. It remains not run on the
   screened device, not silently counted as PASS or repaired by editing its input.

Each result keeps its source, tool, execution mode and oracle separate. There is
no cross-task shared VkDevice, resource graph, performance comparison or causal
GPU timeline implied by running them in sequence.

## Execution and evidence acceptance

Only fixed entries may run. Require explicit exact Skill/tests heads and a clean
paired source cohort before launch and again after completion. Each invocation
uses a fresh output root and unique run ID; no prior report is accepted as an
execution replacement. Revalidate raw streams and expected negative controls,
not only child status strings. Bind child reports to the current run paths, source
and tool/input hashes. Reject missing, mixed, tampered or unexpected evidence.

The supervisor owns only launched process groups. Total/per-step budgets and
cancellation must preserve completed verified prefix, the failed/interrupted step
and never-started tasks. Incomplete work cannot publish whole-suite success.
Cancellation proves bounded process handling, not real GPU hang/device recovery
or containment of escaped/new-session processes. Any recovery run starts fresh;
late artifacts from an earlier cancelled invocation do not acquire the new run ID.

The readable report must preserve warnings and historical cleanup diagnostics,
identify public-answer status, and list unresolved platform/Live/semantic gates.
Manifests bind recorded bytes but do not authenticate a hostile host or independent
reviewer identity. New binary/dependency cohorts need their own independent
validation rather than copying the old known-good manifest label.

## Fixed local entry / 固定本地入口

Create a local JSON config with exactly three absolute directory paths:
`artifact_root` (recorded Amber build/input/manifest assets), `fence_repo`
(original upstream Git objects), and `headers` (pinned official include cohort).
This config cannot select commands, cases, executable names or network targets.
Do not publish private path values. Then run:

```
python checks19/run_external_suite.py \
  --expected-tests-head <full-40-character-tests-commit> \
  --expected-skill-head <full-40-character-skill-commit> \
  --skill-root <clean-skill-checkout> --config <local-config.json> \
  --output <new-output-directory> --total-budget 180 --step-timeout 60
```

There is no dirty/development bypass. Both checkouts must be clean and the saved
pair must match. The fixed three-task sequence is Fence HOST → Amber #951 software
Vulkan → three unchanged neighboring regressions on both Amber revisions. Each
successful task is independently reverified from raw logs, sources, binary and
artifact hashes before the atomic `external-index.json` completed-prefix update.
The six neighboring executions are **not** six additional historical bugs.

`--cancel-file <path>` permits external creation of a cancellation marker. Watch
`verified` in the atomic index to cancel after a completed prefix. A cancelled or
budget-limited run remains incomplete, retains logs and pending tasks, and may
only be retried in a new output directory. The execution budget starts after
source/cohort preflight. Process supervision covers descendants remaining in the
launched process group, not arbitrary detached processes or GPU-hang recovery.

Historical exploratory related-regression v1 misclassified the original
`EQ_BUFFER` transcript as `ProbeSSBOCommand`; that was an observation-tool
predicate failure, not an Amber engine failure. Fresh v2 and this entry recognize
its actual `CompareBufferCommand` and preserve the old evidence separately.

## Fixed entry

```sh
python checks19/run_external_suite.py \
  --expected-tests-head <full-tests-sha> --expected-skill-head <full-skill-sha> \
  --skill-root <clean-paired-skill-checkout> --config <local-inputs.json> \
  --output <fresh-output-directory> --total-budget 180 --step-timeout 60 \
  --cancel-file <optional-local-cancel-file>
```

The local JSON has exactly `artifact_root`, `fence_repo`, `headers`, each an
absolute directory. Put the fresh output and cancellation file outside both
Git checkouts so they do not violate the deliberate clean-source gate.
`artifact_root` provides the original independently audited
Amber build/source/cohort evidence; `fence_repo` has the fixed upstream Git
objects; `headers` is the pinned official include cohort. No network fetch,
installation, driver change or external model call is performed. See the two
individual task documents and Amber reconstruction recipe for the inputs.

The total execution budget starts after fixed-source/tool preflight verification;
it is not a deadline for all initial filesystem hashing. A child timeout still
requires its owned process group to be reaped. Successful output is a bounded
suite result only. Source gates deliberately have no dirty-development bypass.

Related original inputs: compute_accumulated_ubo_definition (two Probe checks),
compute_dynamic_buffers (three Probe checks), draw_storagetexelbuffer (despite its
name, compute plus one CompareBuffer check). Each is identical in both upstream
revisions. A preliminary verifier misidentified CompareBuffer as Probe and marked
the trial unverified; that tool failure is retained, not counted as an engine
failure. Fresh corrected runs and independent checks establish the six actual
context regression executions without replacing the original workload.
