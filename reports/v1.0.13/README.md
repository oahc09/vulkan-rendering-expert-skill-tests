# v1.0.13 — pinned implementation and bounded evidence

**Restricted candidate, not full release acceptance.** Skill candidate
`d4965f77365b4cd78692e60d048929040ba65c8b`, tree
`4fc6d80a2115c20186ed372207c49a9e70344ae2`; clean tests checkpoint
`346dd1dac894054463ed634db634f2689555dbd0`, tree
`2c2bf02cb42580779e08f8c546bff6327572f0d7` ran the recorded pytest suite.
This report-only commit follows it; do not substitute its identity for the run.
Exact requirements, baselines and source hashes: docs/v1.0.13-{traceability,
plan-source,sources}.json and docs/update-plan-v1.0.13.md.

## Observed gates

| Layer | Actual evidence | Verdict and boundary |
|---|---|---|
| Static | 213 pytest cases; check-skill; host-contract | PASS; text/route/contracts, not device behavior |
| HostUnit Python | 34 CPU fixtures | PASS; isolated invariants, not production resource manager |
| HostUnit C++ | lab-host.jsonl, 10 scenarios | PASS; actual compiled host fixture, no driver-failure injection |
| ShaderUnit | build9 + shader-manifest.json, six GLSL | PASS glslang/SPIR-V validation and ABI offsets/strides; not full reflection certification |
| Snapshot | 4 historical fixtures | PASS; not new model behavior |
| Live Model | 64 cases skipped; availability command exit 2 | BLOCKED: no configured observable model command; no calls or tokens invented |
| Vulkan Integration | lab-manifest.json, four raw runs | PASS on llvmpipe CPU ICD; 1k/10k/100k/forced-low, validation/sync-validation errors 0 |
| Mobile/Scale | docs/v1.0.13-device-matrix.json | UNVERIFIED: no physical Adreno/Mali; CPU timings cannot establish mobile speedup/thermal behavior |
| Skill unit/package | skill-unit.txt and package-a/b.json | 24 unit tests PASS; 200 package entries; two ZIPs identical and CRC checked |

Full pytest: **251 passed / 64 skipped**, pytest.txt. Command:
`VULKAN_SKILL_ROOT=/path/to/pinned/skill python -m pytest -q tests`.
Package ZIP SHA256 `df6bdb0041f4ff886d9f85a6c6e45243d9a478d810066dadf49a3ce5c7bf78ef`,
941953 bytes. Public package reports are path-redacted derivatives. Package evidence is independent of the experiment evidence archive.

Live availability used `run_live_model_behavior.py --expected-skill-sha
 d4965f77365b4cd78692e60d048929040ba65c8b --require-live --check` with a new output
folder. The runner checks absent command **before candidate identity**; this skip
manifest is availability evidence only, not SHA-bound Live acceptance.
No original12/v1.0.8 savings, old40/v1.0.12 regression, ENG13 tokens or repeated
semantic stability verdict can be computed without real authorized model runs.
Old40 prompts and original12 denominator remain immutable; 24 new ENG13 cases
each carry positive/negative input variants. See acceptance.md for actual commands.

## Actual Vulkan experiment and evidence preservation

Final experiment source `3dd7a63f5772a29caa05f768f32a45fc14490c3d` was clean;
binary SHA256 `4dfd1b939a0923cd2dc7c4703a84f1603076b032087720630ea9c758a48fa83d`.
Every fixture hash in lab-manifest.json was verified against final source bytes.
Do not relabel this run as a later report commit. Run stdout/stderr, manifest, toolchain package versions/checksums and build/shader
reports are here as disclosure-safe public copies. Internal absolute execution
roots are replaced with <workspace>/. redaction-provenance.json records original
and public hashes for changed files; original raw evidence is retained privately.
Unchanged source/artifact hashes in the lab manifest still identify original data,
not automatically a redacted public representation.
Three original RGBA8/uint32-ID sample pairs are encoded losslessly in
representative-raw-images.json; sidecars specify size, flags and format.
Full 1462-artifact raw image/ID evidence was independently archived and hashed;
archive-provenance.json records its identity. **Hashes are not a claim that all
raw images are committed to Git.** No tool binaries or third-party source dump
are in this change.

Coverage: CPU no-cull and fair frustum baseline; fixed slots; queried/enabled
indirect Count; constrained fallback; guarded capacity/zero counts; four serialized
views; real depth-to-HiZ compute with NPOT65x49 normal/reversed depth and CPU
reference checks; three residency-aware LODs; particle ping-pong/compaction and
indirect instancing; additive versus CPU-sorted alpha; PipelineCache cold/warm/merge.
See fixture README for exact algorithm, counters, tolerances and command options.

Diagnostic wall/GPU timings include synchronized readbacks/validation and are not
fair performance comparisons. NOT_RUN: native Mesh/task, async queues,
PipelineBinary/GPL, Android surfaces, true simultaneous multiview teardown,
long-running allocation-failure cleanup, perspective/MSAA/alpha-test occluders,
compressed KTX transcoding and physical-device thermal/power/latency testing.
LOD triangles intentionally share silhouette; this is not mesh-quality evaluation.
Python/C++ host contract fixtures do not turn these gaps into device passes.

## Preserved failures and corrections

historical-failures preserves failed and follow-up outputs; public copies are
subject to the same disclosed path-redaction policy (no changes needed there):
v3 vertex storage buffer lacked readonly/NonWritable and triggered 9 validation
errors; v4 corrected the declaration. v5 particle coarse-LOD geometry emitted
extra triangles; v6 used degenerate extra triangles for the particle path.
Final v9 rebuild/rerun binds the clean source and has zero validation errors.
Initial report-integration attempt selected a nonexistent sample flag and stopped
before pinning; its pre-pin suite correctly failed the release contract once
(250 pass/64 skip). The sample selection and explicit pin were then corrected;
pytest.txt is the final clean pinned result, not that rejected provisional run.

Remaining acceptance: configure an authorized observable model adapter, run
64-case smoke and repeated stability with manual semantic review, old40 comparison
and independent ENG13 metrics; execute native mobile/device matrix. Keep these
blocked gates explicit; submit reviewed PRs without claiming automatic acceptance.

Execution SHAs above identify local executed checkouts. Connector publication may
recreate commits with different remote SHAs but identical Git trees/file bytes;
these local SHAs are not promises of resolvable GitHub commit URLs. Remote artifact
source equivalence must be verified by tree and fixture_files hashes. Remote PR
identity is recorded by the publisher separately, without a self-referential
report-SHA rewrite.
