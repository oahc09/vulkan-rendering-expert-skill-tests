# External historical task preparation: fence timeout width

This is a **public-answer development regression**, not an external blind solve.
The development workers read the upstream patch before implementing the harness.
It does not count as one of the 36 final tasks passing.

## Immutable provenance and scope

- Repository: https://github.com/KhronosGroup/Vulkan-Samples
- Upstream fix: `02d3010a3517620e7eedd919217e169c4a188de3` (PR #1328).
- Immediate parent: `dca8e0842417ef14440135ee48a09870a05d5bff`.
- Original files: `framework/fence_pool.cpp` and `framework/fence_pool.h`.
- Apache-2.0 headers are retained in extracted original files. Input source is
  read from exact Git objects, not the checkout or a reconstructed excerpt.
- The original class is compiled with explicit test doubles replacing helpers,
  Device and Vulkan API dispatch. The test observes the `vkWaitForFences` argument
  boundary. This is not a full Vulkan-Samples build or GPU timeout experiment.

The original 32-bit wrapper truncates a caller's 64-bit duration. The upstream
fix changes both declaration/definition and default width. A finite short timeout
is legal Vulkan usage; the failure is preservation of caller policy, not an
invented validation VUID. The fixed 1.4.368 fence prose defines nanoseconds and
implementation-dependent accuracy. A maximum uint64 value is conventional
near-indefinite waiting, not proof of success or an uninterruptible API guarantee.

## Reproduction entry

```sh
python checks19/run_external_fence_task.py --source-repo /path/to/Vulkan-Samples-git \
  --headers /path/to/pinned-vulkan-include --out /path/to/fresh-output
```

The input repository must contain both exact commit objects and their parent
relationship. The complete official 1.4.309 header cohort is hash-pinned; a
similarly named arbitrary header tree is rejected. The runner performs no network
fetch or upstream modification. It records commands, bounded subprocess timeouts,
stdout/stderr, input/implementation hashes and repository/pair state. Local dirty
runs remain labeled development state; they cannot establish a released pair.
The output includes extracted source with original copyright notices; retain
Apache-2.0 licensing on redistribution. Required tools: Git, Python 3 and g++.
No Vulkan driver is linked into this HOST test.

## Reproduction and regression contract

Build/run both immutable originals, preserving compiler identity, both output
streams, commands, source hashes and executable hashes. Check default, zero,
UINT32_MAX, UINT32_MAX+1, UINT64_MAX, returned success/timeout/device-lost codes,
and empty/reset-empty behavior. The old version must fail the **fixed** oracle;
merely reproducing an expected old trace is not a repair regression test.
The repaired version must pass that same fixed oracle. A changed source object,
missing commit, wrong upstream parent or reused output directory is not accepted
as this task's result. Result-code injection is an explicit HOST test double,
not a claim that a real device lost or timed out.

Rollback means selecting the original parent and obtaining the observed truncated
trace again; it is not a recommendation to revert upstream or publish a defect.
No action is taken on the upstream repository. Delivery goes only to the two
user-authorized Skill repositories and their existing draft PRs.

## Blind-task preparation boundary

A future independent operator must choose an uncontaminated solver and separate
project/root-cause/repair-history cohorts. The solver-facing input must exclude
fix commit/title/diff, harness hidden assertions and reviewer rubric. This
repository deliberately publishes the answer for reproducible development, so
its package is not itself a blind task. Hash manifests authenticate bytes only,
not reviewer identity, access isolation or absence of model training exposure.

## Alternate original engineering candidate, not executed

Google Amber fix `a76118c1c79ae5615e6684bc3fa267e20c14baf2` (PR #1119), parent
`0d349d7792e96c587ad76111d33c4e62ab2359b0`, adds EARLY_FRAGMENT_TESTS to a depth
attachment barrier. The upstream commit names `dEQP-VK.depth.ez_fs_clamp`.
The original CTS input at `5bb4c7e83acea0fc73e3333625e4f20542e584d0` is
`external/vulkancts/data/vulkan/amber/depth/ez_fs_clamp.amber`, SHA256
`a4f44509cfe7138e830c70f198a4c15654b8200d47149e381eae20754567e63b`.

A real capability query on current llvmpipe (API 1.4.305) found depthClamp=1 and
fragmentStoresAndAtomics=1, but depthClampZeroOne=0 and its extension not advertised.
The original input requires that missing feature. Status is
**FEATURE_UNAVAILABLE_NOT_RUN**: neither Amber revision was built, the original
oracle was not executed, and no before/after SyncVal result exists. Do not remove
the requirement, rewrite the shader/oracle, or reinterpret a quiet output as a
successful upstream reproduction. A supported device and complete old Amber
build dependencies are needed before this original candidate can proceed.

## Remaining original-plan gates

C0/C1 whole semantic-family coverage and contradiction review are incomplete.
This task only improves original-source preparation and a narrow executable HOST
regression. Full engineering integration, target GPU/driver failure reproduction,
independent Live/blind model delivery, physical/mobile/thermal coverage and final
four seals are unchanged. All 36 final tasks remain UNVERIFIED; Release BLOCKED.
