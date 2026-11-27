# Hybrid Quality Lab (minimal executable companion)

Original MIT fixture, no external assets, models or SDKs. Reuses Engine Scale
Lab's Vulkan instance/device choice, allocations, layout, synchronization,
render pass, compilation target and cleanup through an included translation
unit with its entry point renamed. No changes to that fixture are required.
The adapter is necessary because culling alone cannot express shadow signals,
per-pixel history or an independently enabled query device.

## Run, with installed compiler/Vulkan tools

```sh
python3 tests/fixtures/hybrid_quality_lab/run_matrix.py --out /tmp/new-hybrid-run
```

The output must not exist. `CXX`, `GLSLANG`, `SPIRV_VAL` and optional
`VULKAN_SDK_PREFIX` select installed tools; scripts never download/install.
The optional SDK prefix uses include and lib/x86_64-linux-gnu directories.
It links the Linux Vulkan loader SONAME, which also works with a rootless SDK
whose `libvulkan.so` development symlink lacks its target in the SDK prefix.
Use `VK_DRIVER_FILES` / `VK_LAYER_PATH` to select the actual ICD/layers.
Missing tools fail rather than becoming a false pass. A run without validation
layers is explicitly identified in the device log; it is not validation proof.

## What actually executes

- C1: real triangle rasterization into D32 shadow depth, normal Z (clear=1,
  less-or-equal), procedural alpha-tested fence, stationary contact slab and
  a camera-offscreen caster still present in the light frustum. World extent
  and light projection are fixed; no unstable frustum fitting. Nearest sampled
  3x3 PCF, explicit outside-frustum lit behavior, depth bias scaled to shadow
  texel size in this fixed normalized scene. This is one directional-light
  orthographic baseline, not CSM/atlas or a universal bias recipe.
- Camera receivers are two **analytic** planes, not a full rasterized courtyard.
  Compute samples the actual raster shadow map. The color composites use a
  constant analytic environment-probe fallback, including a reflective strip;
  this is not SSR or a production prefiltered environment map.
- C3: real GPU compute history reprojection, bounds/depth/normal-class/radiance
  rejection, neighborhood clamp and edge-aware 3x3 spatial filtering. Host
  reference checks every temporal/spatial result to 1e-5. Scalar visibility
  remains linear and exposure-independent; exposure is applied only afterward.
  History buffers are copied on the host only after a fence completes. This
  serialized reference intentionally does not claim frames-in-flight testing.
- C2: query feature/extension/AS/BDA/deferred-host-operations gate, an independent
  device enabling only required features, six-triangle BLAS and one-instance
  TLAS; aligned separate scratch allocations and explicit host/build, BLAS/TLAS
  and AS/compute dependencies. Query runs in a normal compute pipeline, no RT
  pipeline, SBT, TraceRays or RT shader stage. Two independent dispatches test
  shadow early-out and closest-hit single-reflection proxy radiance. Nonopaque
  candidates use the same procedural fence UV/cutoff as raster. A CPU analytic
  rectangle-ray oracle checks every hit/miss and closest material color.
  All referenced inputs, scratch and AS objects stay alive through the fence.
  No update/compaction or address-republication experiment is claimed.
- Missing query capability keeps the raster/temporal path. The harness also
  forces baseline on query-capable devices to exercise an explicit fallback.
  OMM KHR/EXT advertisement is recorded independently; neither branch is
  implemented. Neither absence nor header availability is a passing OMM test.

## Sequence, diagnostics and acceptance

Seed 0, 65x49, 12 frames: static, integer-pixel slow pan, camera cut, changed
light, animated cutout translation, generation-reset trigger, changed exposure
and pause-reset trigger. Labels ending `reset_only` are deliberately **not**
actual LOD eviction/reload or application suspension. No skin deformation,
rapid camera rotation, resize/render-scale transition, second View or SDK
upscaler runs in this minimal fixture. Query uses the matching initial scene
only, not all animated raster frames. These remain plan coverage gaps.

Each frame saves raw/temporal/filtered visibility, shadow/receiver depth,
history weight and raw/filtered color. Raw query float32 results and PGM
previews are separate. `frames.jsonl` records exact camera/light/exposure,
resets, history use, shadow coverage, oracle result and filter/raw MAE.
MAE is diagnostic, not evidence that smoothing is better. Fixed acceptance:
finite [0,1] visibility; both lit/shadowed pixels; zero history use on resets;
both accepted/rejected history samples; zero temporal/spatial and query oracle
mismatches; zero validation errors when the layer is available. PPMs apply a
simple Reinhard/gamma preview transform, not a calibrated display pipeline.

The shadow PCF and binary query signals have different reconstruction filters;
do not demand pixel identity or infer a speedup from them. Raw CPU submit /
readback durations include artifact work and are only diagnostic wall time,
not GPU timestamps or mobile frame-time/power/thermal results. The reused
constructor's pipeline/cache line includes initialization unrelated to this
experiment. No performance claims are made.

The harness preserves build/run logs, command return codes, versions, Git
HEAD/tree and dirty status, source hashes and artifact hashes. Input manifests
bind an uncommitted run to its precise source bytes, not to a later clean SHA.
Existing build/run output refusal is tested. Failed intermediate attempts must
be kept separately when reporting experiments. Final release evidence should
rerun against the committed candidate. Hardware RT, Android visual quality,
multiframe AS lifetime and OMM remain unverified.

## Evidence verifier and negative checks

`python3 tests/fixtures/hybrid_quality_lab/verify_artifacts.py OUTPUT_DIR`
independently reopens files, verifies source/artifact hashes and exact run-file
inventory, validates command codes, image dimensions/lengths, finite query
floats, frame records and refusal snapshots without trusting `summary.json`.
The matrix invokes it automatically. `verification.json` is a derived result
excluded from the hashed inventory, along with the manifest itself.
Five temporary-copy negatives must fail verification: missing, extra, corrupted,
NaN metadata even with a recalculated hash, and a timeout masquerading as output
refusal. Existing-directory rejection requires exit 1, the exact refusal
message, and unchanged target-file hashes. Timeouts are never accepted.
All GPU readback components and CPU oracle intermediates are checked finite
before comparisons or integer image conversion. Query checks all four expected
RGBA channels, including both hits and misses.

## Opt-in cross-driver shadow coverage QA

This pair is separate from the legacy matrix (and from the ALL19/E2E19
evidence). Both variants keep the 65×49 courtyard, 12 frames, moving alpha
cutout, camera/light changes and history controls. They add the same fixed
light-space shear jitter: 0, ±1/8 and ±1/4 shadow texel.

- `--shadow-jitter` preserves the original floating-point geometry and
  interpolated cutout. Use it to inspect edge-sensitive differences, not as a
  cross-driver byte equality gate.
- `--shadow-golden` places this authored axis-aligned fixture's projected
  edges on texel boundaries and tests alpha coverage at the integer texel
  center with a rational seven-stripe rule. It enables a strict golden check
  without requiring the float stress path to become artificially identical.
  Do not snap arbitrary production meshes to reproduce this result.

Neither flag changes the default build. Query execution is disabled by the
variant binary itself; its separate algorithm uses the original material.

With the same compiler, loader and layer, run each on two installed ICDs,
substituting actual manifest paths. Use fresh output directories and preserve
both stdout and stderr:

```sh
L=tests/fixtures/hybrid_quality_lab
"$L/build.sh" /tmp/shadow-float-build --shadow-jitter
"$L/build.sh" /tmp/shadow-golden-build --shadow-golden
VK_DRIVER_FILES="$ICD_A" /tmp/shadow-float-build/hybrid_quality_lab /tmp/shadow-float-build/shaders /tmp/shadow-float-a
VK_DRIVER_FILES="$ICD_B" /tmp/shadow-float-build/hybrid_quality_lab /tmp/shadow-float-build/shaders /tmp/shadow-float-b
VK_DRIVER_FILES="$ICD_A" /tmp/shadow-golden-build/hybrid_quality_lab /tmp/shadow-golden-build/shaders /tmp/shadow-golden-a
VK_DRIVER_FILES="$ICD_B" /tmp/shadow-golden-build/hybrid_quality_lab /tmp/shadow-golden-build/shaders /tmp/shadow-golden-b
python3 "$L/check_integer_shadow_oracle.py" /tmp/shadow-golden-a --second-driver /tmp/shadow-golden-b
```

The CPU oracle derives depth independently from rectangle coverage, rational
texel-center alpha and nearest blocker ordering. It checks all 38,220
shadow-depth preview texels per driver. With a second driver the checker also
requires all 96 previews (eight per frame) to match byte for byte. This checks
the fixture's 8-bit readback previews, not arbitrary float buffers or display
quality. Require two identified ICDs for a cross-driver claim and an enabled
validation layer for the zero-validation-error claim. The source and logs can
establish which drivers ran; a pair of directory names cannot.

In a replay on Lavapipe and SwiftShader, the golden lane and independent
oracle matched. The float lane differed by up to 204/255 in shadow depth and
40/255 in filtered RGB channels at the selected inputs. Neither is a
performance measurement or a production quality threshold. As a sensitivity
check, compile only the golden fragment shader with its discard removed
(to a separate build directory): the two drivers can still agree while the
CPU oracle rejects the lost cutout. A GPU-only comparison cannot detect a
shared bug. These bounded checks do not validate Android, cascades, morph
shadows, arbitrary filter inputs or a second physical GPU.
