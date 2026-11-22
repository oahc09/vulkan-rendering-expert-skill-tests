# Original Amber #951: shared buffer backing across descriptor bindings

This is an upstream historical engineering reproduction with an already-public
repair, **not a blind model task**. It is separate from the #1119 depth-barrier
candidate, whose original required feature remains unavailable on this device.

## Frozen original project and workload

- Repository: https://github.com/google/amber (Apache-2.0).
- Original parent: `aaac58d5009e8f6b33e2723258dc1542854d09a4`.
- Upstream repair: `8c3bfef40c2387944fdc81746e2e3249e4da5566` (#951).
- Original added test: `tests/cases/compute_one_buffer_in_multiple_bindings.amber`.
- Test SHA256: `a192e19956bbd352bb08f27060e2d11ee46def51054b8e1c326364a3b612a6be`.

The original workload uses one logical buffer in six bindings over three sets:
two UBO, two SSBO and uniform/storage texel views. It dispatches compute and
checks three independently selected regions. The workload and original EXPECTs
are read unchanged from the upstream fix commit and used for both engine versions.
A pre-fix codebase lacking the added test is not a reason to invent a replacement.

## Explicit build boundary

Both original engine source archives are immutable. They share the same compiler,
Vulkan headers, independently built Shaderc and read-only preexisting GLSLang /
SPIRV-Tools libraries. This is a **same-dependency contemporary reconstruction**,
not a claim that the exact 2021 DEPS toolchain was recreated. Imported-target CMake
sidecars are build assembly outside the original tracked engine sources.
Both builds use `-include cstdint` to accommodate an old missing transitive header
under the current compiler. The original compile failure must remain in evidence;
this shared compatibility option is not attributed to the #951 resource fix.

CTS source/build products are read-only. New Shaderc and Amber objects and logs
live in separate build directories. No output is written into the CTS build.

## Acceptance to establish with actual execution

1. Query the real selected device, RGBA32F texel format bits, descriptor/range
   limits, buffer offsets and compute queue. Capability success is not execution.
2. Run the original workload against the pre-fix complete Amber Vulkan CLI.
   Require the original resource-output aggregation error or a specific numerical
   oracle mismatch, not an unsupported-feature,
   compilation, launch or infrastructure error. If the engine fails before
   EXPECT evaluation, report that exact boundary rather than inventing values.
3. Run the exact same bytes against the fixed CLI with the same dependencies and
   ICD. Require all original EXPECTs to pass.
4. Re-run the original against the pre-fix CLI to demonstrate rollback behavior.
5. Separately run a clearly labeled wrong-EXPECT mutant on the fixed CLI to
   establish that the verifier detects a wrong numerical answer. The mutant does
   not replace the original workload and is not called an upstream reproduction.
6. Preserve raw streams, exits, source/build/tool/driver hashes and exact commands.
   Layer silence is not proof of whole Vulkan synchronization correctness.

## Scope and remaining gates

A successful run proves this historical resource-sharing regression on the tested
software ICD and reconstruction, not every resource alias/synchronization policy.
The source, public patch and reference assertions are already known, so this is
not an independent unseen solver task. Physical/mobile/second-driver, thermal and
performance behavior, original historical toolchain, C0/C1 whole semantic closure,
36 final tasks and Release/Live seals are not established by this case.

## Observed original-engine result

The fixed shared-dependency build was executed with current llvmpipe. The four
actual exits are **1 / 0 / 1 / 1** for before / after / rollback / wrong-EXPECT.
The old engine executes the compute command but fails during output aggregation:
`BufferBackedDescriptor::MoveResourceToBufferOutput() output buffer is not empty`.
It does not reach the three EXPECT checks, so no old numerical mismatch is claimed.
The fixed engine reaches and passes all three original ProbeSSBO checks. Returning
to the old binary repeats the original aggregation failure. The separately labeled
mutant changes only the first expected component from 2 to 3; the fixed engine
rejects it with a verifier mismatch at component 0 (actual 2, expected 3).

Both engine cohorts emit the retained DimBuffer/OpTypeSampledImage warning under
this contemporary compiler/driver combination. The old failure and rollback also
report cleanup VUID 05137. The successful fixed execution had no ERROR in that
observed stream, but this is not a complete synchronization-validation proof;
these four runs are not a SyncVal acceptance campaign. All stderr is retained,
including warnings; none is filtered to manufacture clean output.

The actual upstream repair deduplicates transfer resources by logical Buffer,
aggregates usage before initialization and reads each logical output once. It
retains the nonempty-output guard. Thus the observed repair is not achieved by
removing the error assertion or changing the original expected answer.
