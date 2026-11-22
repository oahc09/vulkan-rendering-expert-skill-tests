# Four-family resource suite / 四族有界交付

Fixed entry `checks19/run_resource_suite.py` executes device_address, ray_query, robust_buffer and headless_wsi, always all four or non-success. It does not expand the existing five-chain diagnostic bundle or turn v1.0.19 release status green.

```
python -O checks19/run_resource_suite.py \
 --expected-tests-head FULL_TESTS_SHA --expected-skill-head FULL_SKILL_SHA \
 --skill-root SKILL_CHECKOUT --toolchain TRUSTED_PATHS_JSON \
 --output FRESH_DIRECTORY --total-budget 300 --step-timeout 90
```
Trusted toolchain JSON has exactly seven absolute path keys: tools/include/loader/icd/layer_path/library_path/validusage. It cannot supply arbitrary commands, runner source, shell fragments or optional family skip. Canonical output may reside under a caller-selected symlinked ancestor; all internal source/artifact paths and symlinks are rejected if escaping their canonical root.

Before importing any helper: explicit two HEADs, Skill clean/version, candidate BLOCKED pair, original plan hash and exact committed bytes of entry/verifier/supervisor/four rules/four source cohorts are checked. Development mode only exempts the two new suite Python files; its result explicitly says DEVELOPMENT and is not final published-pair evidence. No dirty Skill/pair exception.

Every child runs under existing session/group supervisor with finite total/per-step budgets, cancellation-file/SIGINT support, raw root stdout/stderr and process cleanup facts. Successful source/tool/evidence hashes are rechecked at the end. Missing capability, unexpected exit, timeout, cancellation, extra/missing case, malformed records, mismatched identity, changed source or log cannot count as success. Partial index retains verified families and pending list; summary is explicitly non-success on failure. This is not GPU hang/device-loss recovery testing, and descendants escaping the supervisor's process group are outside its documented guarantee.

Independent raw verifier rechecks exact stage diagnostics, complete source/binary/shader/tool log binding, fixed1.4.309 normative corpus and excerpts, bounded SPIR-V structure, enabled features/memory/rules, full CPU output and negative outcomes. Case lifecycle records are reconstructed from raw stdout and compared to report; report cannot supply commands. Shader checks remain bounded presence/layout checks with manual source review, not general reflection. Explicit tool binaries/headers/manifests are hashed, not all transitive OS shared libraries.

- BDA: pointer table→64-word transform and guards, no stale/OOB execution.
- Ray query: one BLAS/TLAS→hit/miss, finite distance tolerance, no RT pipeline/SBT.
- Robustness2: protected ordinary SSBO+NULL read/write, no disabled robustness OOB.
- WSI: two generations/four clears, coherent full pixels, explicit present-fence retirement; no physical display/window resize.

Each child has a distinct run UUID and independent logical resources. Matching CPU/vendor/driver/API/Validation identity means only a common reported software cohort, not shared VkDevice or cross-family causal execution. Video/optical/tensor/cooperative families remain unavailable. Output `resource-index.json` and bilingual `SUMMARY.md` are audit artifacts, not signed attestation or full-domain acceptance.
