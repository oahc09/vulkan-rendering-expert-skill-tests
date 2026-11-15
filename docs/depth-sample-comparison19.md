# Fixed 1× → 4× → 1× depth-scene comparison

The command runs the existing depth scene, not arbitrary project commands. Every stage executes all four controls. It requires a fresh output directory, exact paired repository commits and the existing seven-path toolchain configuration. Sources are checked against the commits before helper imports and after execution. Explicit development mode exempts only named changed implementation files and cannot produce a strict receipt.

```
python -O checks19/compare_depth_samples.py \
  --expected-tests-head TESTS40SHA --expected-skill-head SKILL40SHA \
  --skill-root SKILL_CHECKOUT --toolchain TOOLCHAIN_JSON \
  --output FRESH_DIRECTORY --required-samples 1 --requested-bytes-budget 3000
```

Sequence: baseline1, candidate4, recovery1. The third stage must reproduce baseline facts **and per-object allocation requests**. Device/driver/API/queue/layer, shaders, workload and full pixel oracle must agree. This does not claim shared logical devices between runs.

Each scene is independently rechecked from raw stdout/stderr, not only a PASS summary: exact modes and VUID phase, actual source/binary/SPIR-V/tool/log hashes, pinned normative entry, sample topology, static depth state, dependencies, allocation receipts, image results and negative controls. No skipped/unsupported case becomes success. Timeout/cancel/partial results keep BLOCKED/CANCELLED index and remaining stages, rather than recommendation. Supervised monotonic timestamps are process-control evidence, never GPU performance samples. Process-group boundaries follow the existing supervisor; escaped sessions and GPU hangs are not claimed tested.

Decision semantics:
- required_samples=1: retain baseline if within budget, not default-upgrade to4.
- required_samples=4: select4 only for that explicit sample-count contract and budget, not because it is “better”.
- insufficient budget: no admissible path.
- `--require-edge-quality` or `--require-performance-gain`: NEEDS_MEASUREMENT; no unmeasured quality/performance recommendation.

Allocation totals cover explicit successful application requests, not resident/peak/heap/driver memory. Only fixed full-coverage endpoint pixel equality is measured. No edge-AA quality, GPU time, power, temperature, throughput, physical display or general C2/C5/full-release completion is asserted. Source, device, driver, tool, workload, policy or new quality/performance evidence requires revisiting the decision.
