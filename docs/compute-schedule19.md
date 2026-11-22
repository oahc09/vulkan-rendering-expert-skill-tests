# Bounded compute scheduling decision / 有界计算调度

`checks19/decide_compute_schedule.py` is a one-shot JSON decision entry, not a
benchmark service or arbitrary project-command executor. Its example is explicitly
**synthetic caller-declared HOST evidence**, not a GPU performance capture.

```sh
python checks19/decide_compute_schedule.py \
 --request cases19/compute_schedule/declared-example.json \
 --devsandqueues /path/to/frozen-368/chapters/devsandqueues.adoc \
 --synchronization /path/to/frozen-368/chapters/synchronization.adoc \
 --resources /path/to/frozen-368/chapters/resources.adoc \
 --features /path/to/frozen-368/chapters/features.adoc \
 --fundamentals /path/to/frozen-368/chapters/fundamentals.adoc \
 --out /new/output-directory
```

All five specification files must match pinned SHA-256 at Vulkan-Docs commit
`fa30d4e312e843193601be7cb926c7e25d9ec885`. Raw anchor slices retain source
coordinates, but do not expand includes/conditional scope. These establish queue
creation/submission and memory-dependency concepts, **not performance thresholds**.
The gain threshold is explicit user policy, not a normative Vulkan requirement.

## Input contract

- `families` is advertised queue capacity. `created` separately records actual
  logical-device queue creation. Selection must refer to a created queue with the
  appropriate GRAPHICS/COMPUTE flag. Same-family different-index queues are distinct;
  the same queue is not an asynchronous alternative.
- `requirements` separately records support and enablement for each workload
  requirement. Empty means the caller's ordinary core-only workload has no extra
  feature requirements, not that all Vulkan features are enabled.
- Dependencies and lifetime are separate caller-proven obligations. Queue order,
  queue count, or a completed host fence does not prove a GPU dependency.
- Ordinary EXCLUSIVE cross-family use requires ownership proof in the explicitly
  selected baseline without implicit-transfer exceptions. CONCURRENT requires both
  selected families in the resource's actual creation list. This is not a complete
  resource legality, semaphore scope or maintenance9 validator.
- Full-frame paired measurements require identical device, driver, workload,
  resolution, shader, tools, clock domain, thermal-regime, input, warmup and paired-run-order identifiers; matching
  identifiers are caller declarations, not authenticated immutable capture proofs.
  All relevant queue completion and identical full-frame boundaries are required.
- At least three finite positive trial values per path are required. Median
  comparison is a bounded declared policy, not statistical significance. The explicit
  `max_observed_frame_regression_fraction` also limits observed worst-frame regression;
  this is not a p99 or sustained tail-latency estimate. A faster
  compute pass cannot outweigh a slower full frame: that result revokes the
  candidate to an independently verified baseline.
- Unknown performance preserves baseline; unverified baseline cannot be advertised
  as a valid fallback. Unresolved other objectives prevent selection. No scoring
  by vendor brand, assumed hardware overlap or unmeasured thermal/power benefit.

The sample's three identical cohort labels are examples only. Real callers must
supply their own evidence digest and provenance. Digest shape validation alone is
not capture authentication. Output `SELECT_MEASURED_CANDIDATE` is conditional on
these declarations, not proof that the assistant ran a GPU experiment.

## Boundaries

No workload is submitted by this decision entry. A separately reported current CPU
ICD queue inventory is capability/creation evidence only and cannot turn synthetic
measurements into actual async timings. No whole C2, physical hardware, sustained
thermal performance, queue-overlap or full release acceptance follows. All19
release remains BLOCKED. Changes to workload, driver, tools, dependency or resource
sharing require re-evaluation; continued execution is a separate authorized action.

## Optional actual queue observation

`--capability <queue_probe stdout JSON> --expected-capability-sha256 <externally checked digest>`
binds the request's advertised/created lists to that exact observation. This
version accepts only the one-device core probe with no enabled extra features or
extensions and requires an empty workload requirement list. Caller-selected queue
indices are deliberately not overwritten: requesting index1 on an actual count1
family is rejected, even though synthetic profiles elsewhere show improvements.
Dependency, lifetime, baseline validity and measurement remain caller declarations.
The probe's current CPU observation created one queue and submitted no work.

`queue_probe.c` can be compiled against the fixed official Vulkan headers and
loader and run with an explicitly chosen ICD. It creates only supported queues.
Its observation is not a whole system capability census or a benchmark. The
external digest binds bytes, not who obtained them; original compilation/runtime
provenance must be reviewed separately.
