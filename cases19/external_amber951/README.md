# Original Amber #951 build assembly / 原工程装配

This is **not** vendored engine code or a replacement reproducer. Both full Amber
CLI/runtime sources are the original commits in `build-cohort.json`. The original
regression test comes from the fixed revision at
`tests/cases/compute_one_buffer_in_multiple_bindings.amber`. Its SHA is pinned.
The upstream fix was known before this work; this is not blind repair.

## Rebuild layout (local sources, no automatic network)

Choose an absolute `$BASE` you own. Provide these already verified sources:

- `$BASE/amber951-before-src`: original parent commit, with genuine Git metadata.
- `$BASE/amber951-after-src`: original fix commit, with genuine Git metadata.
- `$BASE/cts-build/_deps/shaderc-src` and
  `$BASE/cts-src/external/{glslang,spirv-tools,spirv-headers}/src`: exact dependency
  revisions in `build-cohort.json`, all read-only.
- Existing glslang/SPIRV static libraries at the relative paths in that JSON.
  The historical run reused these libraries read-only; it did not rebuild CTS.
  A new machine must build the pinned dependencies separately and independently
  verify the new cohort rather than assuming binary reproducibility.

Copy `support.cmake` to an otherwise empty support directory as `CMakeLists.txt`.
Configure it with `-DBASE="$BASE" -DCMAKE_BUILD_TYPE=Release` and build target
`shaderc` in `$BASE/amber951-build-support/build`. This builds only shaderc and its
utility sources; imported glslang/SPIRV targets point at existing libraries.

For each original Amber source tree, create the previously absent dependency
assembly directories `third_party/{shaderc,glslang,spirv-tools}` with **empty
CMakeLists.txt files** (targets are supplied by the enclosing sidecar). Symlink
`third_party/spirv-tools/include` to the pinned SPIRV-Tools include directory and
`third_party/spirv-headers` to its pinned original source. No tracked Amber file
is edited. Preserve/record real dependency Git identity for version generation;
version labels alone are not provenance evidence.

Copy `engine.cmake` to a separate empty directory as `CMakeLists.txt`. Configure
one build tree per variant with:

```
cmake -S <engine-sidecar> -B "$BASE/amber951-before-build" \
  -DBASE="$BASE" -DVARIANT=before -DCMAKE_BUILD_TYPE=Release \
  -DOFFICIAL_VULKAN_INCLUDE=<official-include-root> \
  -DVULKAN_LOADER_LIBRARY=<official-loader-library> \
  -DCMAKE_CXX_FLAGS="-include cstdint"
mkdir -p "$BASE/amber951-before-build/src"
cmake --build "$BASE/amber951-before-build" --target amber -j2
```

Repeat with `after`. The common forced standard header repairs an old transitive
include assumption under the newer compiler; it changes no tracked engine file.
The enclosing sidecar uses a static-link rescan group for modern compiler-library
cycles. The historical failed build attempts remain local evidence, not passes.

## Execution and interpretation

The fixed replay entry is `checks19/run_external_amber951.py --artifact-root
<recorded-local-artifact-root> --out <fresh-directory>`. It requires the original
local `final-manifest.json` and exact recorded source/library/binary hashes. This
is deliberately **not** a generic runner for arbitrary rebuilds. New builds
require a new independently audited manifest/cohort.

The sequence is original-before → original-after → original-before rollback →
fixed-binary with a separately labelled wrong-EXPECT mutant. Original input stays
unchanged. Old runtime fails while collecting shared buffer output **before** the
three EXPECT checks. Fixed runtime passes all three; changing the first expected
2 to 3 produces a real verifier failure. Both versions emit the recorded
OpTypeSampledImage/Buffer driver warning; old error cleanup additionally emits
05137. Logs are retained, never presented as zero-diagnostic validation.

Software Vulkan only. No physical-GPU, performance, blind-repair, full CTS,
SyncVal-completeness or release-completion claim. Replay child environment is
explicit, not inherited (`LD_PRELOAD` and unrelated Vulkan overrides omitted).
