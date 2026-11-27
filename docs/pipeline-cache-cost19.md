# Ordinary pipeline-cache persistence and cost decision

`checks19/run_pipeline_cache_cost.py` compiles the repository's fixed no-op shader,
validates/disassembles SPIR-V, and runs the fixed small C probe on the CPU ICD.
It creates an empty cache and compute pipeline, retrieves the full opaque data,
writes a fresh file, reads it back and compares every byte before recreating a
cache and another pipeline. No dispatch, queue submission or frame is executed.

```sh
python checks19/run_pipeline_cache_cost.py \
 --tools /official-tools/bin --include /official-headers/include \
 --loader /official-loader/libvulkan.so.1 \
 --icd /selected/icd.json --libdir /selected/driver-libraries \
 --pipelines /frozen-368/chapters/pipelines.adoc --out /fresh/evidence
```

Source, compiler/SPIR-V tools, official core header, loader, ICD manifest/library,
binary, SPIR-V, logs and complete cache blob are hashed. This is a bounded cohort,
not a full transitive shared-library or operating-system freeze. No validation
layer is enabled, so it makes no zero-VUID or SyncVal certification claim. A
failed/truncated `vkGetPipelineCacheData` (including INCOMPLETE) fails closed;
this single-threaded fixture does not implement concurrent cache export retries.

## Compatibility is separate from origin and benefit

Ordinary version-one headers are parsed as little-endian bytes: 32-byte header,
version, vendorID, deviceID, and 16-byte pipelineCacheUUID. The driver version is
not a header member; exact driver equality is an extra conservative application
policy. A matching header does not authenticate or validate arbitrary opaque
payloads. The full original export length/hash and declared origin must agree.
Cache data are not universal cross-driver binaries, pipeline binaries, GPL or
shader-object serialization.

Frozen Vulkan-Docs 1.4.368 `pipelines-cache-header` explicitly distinguishes header
structure clauses from API valid usage. Incompatible ordinary Vulkan cache data
are ignored (empty cache), not a promised validation error; Vulkan SC differs.
Our header mutations are **HOST application-policy negatives only**, never passed
to Vulkan. The original retrieved-byte source and size obligations (00768/00769)
remain distinct; passing the header filter does not waive them.

## Cost policy and unknowns

The probe reports monotonic **CPU call intervals** for two
`vkCreateComputePipelines` calls. It does not time GPU work or establish a cache
hit. Empty application cache does not mean a truly cold driver, filesystem or
compiler. Fixed cold-then-restored order can be biased by implicit cache/warmup.
The stored blob's bytes are storage size, not resident GPU memory.

By default the decision is UNKNOWN because no workload/output baseline is
verified. Even when a caller declares a verified baseline, missing comparable
first-frame and steady-state evidence yields NEEDS_MEASUREMENT, not a speedup
claim. Optional `--policy policy.json --measurement measurement.json` supplies
**caller-declared separate evidence**, never relabels these two observations as
performance trials. See `tools/pipeline_cache_decision19.py` for exact schemas.

Selection requires identical explicit cohort labels (device/driver/workload,
shader/input/resolution, tools, clock, thermal, warmup/run-order protocols), at
least three paired samples, output equality, storage budget and resolved other
costs. A faster creation call cannot hide a worse first frame or observed worst
steady frame. Median/observed maxima are simple declared policy statistics, not
significance tests or sustained tail-latency predictions. No brand heuristic,
quality, startup, power, resident-memory or full C2 promise is inferred.

## Copyable input examples

`cases19/pipeline_cost/policy-example.json` and
`synthetic-measurement-example.json` are **fabricated HOST control values**, not
measurements of this CPU device. Their `baseline_verified: true` is a demonstration
caller assertion, not the probe's verdict. To exercise the conditional branch,
append these paths as `--policy` and `--measurement` to the command above. The
report preserves the real probe under `observation` and labels the separate caller
measurement as not derived from that probe. Do not submit the example as evidence
of real performance. Replace every cohort label, trial and source digest with
reviewed project measurements before considering an actual rollout.

The default run (without these files) keeps baseline validity unknown and selects
nothing. A stored 32-byte header-only blob is legal evidence of retrieval and
round-trip, but does not demonstrate compiled code payload or a cache hit.
