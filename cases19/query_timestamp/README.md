# Ordinary timestamp query lifecycle (bounded VK12)
Original in-repository deliberate fault injection, not an external production defect.

Compile and run with the established CPU ICD / Validation environment:
```
python -O cases19/query_timestamp/run.py --include HEADERS --loader LOADER --validusage VALIDUSAGE_1_4_309 --output FRESH_DIRECTORY
```
The runner pins the original validusage SHA and verifies actual Validation 1.4.309 identity, compile/runtime exit codes, exact diagnostic phase and IDs, post-cleanup errors, and byte hashes. Failure or missing prerequisites never generate a successful summary. Artifacts remain local.

Each mode creates an ordinary two-slot TIMESTAMP pool. A command-buffer reset is submitted and its fence completes BEFORE polling. Unwritten slots return VK_NOT_READY with availability zero; result words are not interpreted. A later submission writes TOP_OF_PIPE, fills 1024 words, writes BOTTOM_OF_PIPE, establishes transfer-write→host-read dependency and completes a fence. Compatible HOST_VISIBLE|HOST_COHERENT memory maps and all 1024 words must equal42. Two timestamps must be available. This proves the bounded lifecycle/content path, not a duration or pure-fill timing claim.

Three separate callback-aborted host reads test stride alignment00815, undersized data00817 and prohibited timestamp PARTIAL09439. These are expected invalid calls, not successful API calls. Their process exit0 means expected observation and safe cleanup. No invalid call reaches the ICD. No deliberate GPU hang is used.

`tools/query19.py` separately checks ordinary result width/stride/size, write-slot prerequisites, scope/generation and modular interpretation. Actual runtime records are consumed without an independently justified wrap upper bound, deliberately yielding UNKNOWN_WRAP. CPU synthetic wrap, stale-generation and different-clock negatives are not device experiments. A caller-provided same-clock assertion/upper bound is an input obligation, not established by this policy itself. TOP/BOTTOM timestamps depend on implementation and pipeline stages and must not be reported as isolated fill GPU cost. CPU ICD timestamps are not physical GPU performance.

Not covered: calibrated timestamps, cross-queue clocks, host query reset, occlusion/statistics/performance query layouts, mobile/hardware timing, unsupported-device success, or full VK12 acceptance. Noncoherent memory is not substituted: this probe explicitly requires compatible coherent host-readable memory. Exact schema2 validusage is the VUID source; prose lifecycle semantics require separately pinned queries.adoc, not an invented VUID.

## Acceptance split and source cohorts
- Real device API path (software ICD only): command-reset fence completion, unwritten NOT_READY/availability0, two writes, transfer content oracle, host result availability; callback-aborted00815/00817/09439. The probe emits actual get/write/range arguments, not runner-invented defaults. The runner feeds those emitted arguments into the rules and compares exact VUID lists.
- CPU semantic controls: query index/range boundaries, 32/64 result layout, unknown support, unavailable state, stale generation/different scope, same-clock requirement, wrap ambiguity, overwide values. These are not additional real-device experiments. This slice interprets elapsed values only from64-bit results and a separately justified same-clock/elapsed upper bound; actual data intentionally lack that bound.
- Retained snapshot tests bind the raw-run summary to source/runner/rule hashes. They are not a new invocation. Fresh actual evidence is required after modifying those files.
- Prose source: Khronos Vulkan-Docs tag `v1.4.309`, `chapters/queries.adoc`, Git blob `fb4d544cba26c0bbbe982c1a82dbf45fc06d28fb`. Generated validusage metadata revision is not assumed to be a Vulkan-Docs commit. No latest1.4.368 denominator is silently mixed into this309 cohort.

This is a standalone query-family runner. The existing five-chain delivery bundle
remains five chains; its previous successful handoff does not silently include
this new query experiment. Full VK12 and original M0–M6 gates are not closed.
