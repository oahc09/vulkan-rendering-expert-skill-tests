# Transparent Scene Lab (v1.0.15)

Original MIT synthetic correctness fixture. Reuses Engine Scale Lab's Vulkan
instance/device/allocator/descriptor/command/fence/validation facilities by inclusion;
does not modify that fixture. Requires its Vulkan 1.2 test harness capabilities,
which are not claims about the engine's minimum baseline. 65×49 offscreen output.

## Reproduce

Dependencies: C++17 compiler, Vulkan loader/development headers, glslangValidator,
spirv-val, Python 3, a Vulkan 1.2 implementation. Optional Khronos validation layer.
Set `VULKAN_SDK_PREFIX`, `GLSLANG`, `SPIRV_VAL`, `LD_LIBRARY_PATH`,
`VK_DRIVER_FILES`, `VK_LAYER_PATH` for a locally extracted SDK if needed.

```
python3 tests/fixtures/transparent_scene_lab/run_matrix.py --out /tmp/transparent-new-run
python3 tests/fixtures/transparent_scene_lab/verify_artifacts.py /tmp/transparent-new-run
```

Runner and executable refuse existing output directories. Compiles and validates
all SPIR-V. Raw commands, tool versions, device/layer metadata, source SHA-256,
original generated PLY/binary hashes, image outputs and artifact hashes are saved.
No private models, downloaded assets or training dependencies.

## Actual executed paths and fixed acceptance thresholds

- Sorted instanced raster: straight linear RGB, source RGB factor SRC_ALPHA,
  destination ONE_MINUS_SRC_ALPHA; alpha ONE / ONE_MINUS_SRC_ALPHA. Zero clear.
  Standard orthographic depth test LESS_OR_EQUAL, depth writes disabled for
  transparency, enabled for opaque mesh. Stable CPU back-to-front center sort.
  Two red/blue orderings give (.5,0,.25,.75) / (.25,0,.5,.75).
- RGBA8, RGBA16F, RGBA32F capability checks require attachment, blend and transfer
  source bits, then image-usage support through resource allocation. Independent
  absolute max tolerances fixed before first run: .009 / .003 / 1e-5 respectively.
  FP64 CPU oracle evaluates the actual ellipse and each compositing layer. This
  does not emulate implementation-specific blend rounding bit-for-bit. FP32
  also checks 2/8/32/128 layers at opacity .01 with the same 1e-5 tolerance.
- WBOIT: constant weight 1, FP16/F32 conditional two single-attachment raster
  passes. Accum clear 0, additive ONE/ONE for RGB and alpha; reveal clear 1,
  ZERO/ONE_MINUS_SRC_COLOR (alpha ZERO/ONE_MINUS_SRC_ALPHA). Does not require or
  enable independentBlend. GPU compute resolves `accum.rgb/accum.a*(1-reveal)`,
  alpha `1-reveal`; zero accum is guarded. Host readback/upload bridges the passes,
  explicitly synchronized, rather than an optimized on-device image chain.
  Both colors resolve to .375: this differs from sorted reference by .125.
  `--disable-wboit` exercises a deliberate sorted-only fallback, not missing-device
  emulation. Unsupported actual formats have separate skip records.
- Gaussian instancing: 3-sigma axis-aligned ellipse, exp(-4.5*r²), discard outside
  ellipse. A strict generated PLY profile is decoded to the binary vertex SSBO.
  Raster quads include a conservative one-pixel margin; the analytic fragment
  ellipse discard keeps the original profile (prevents subpixel edge snapping
  from truncating a nonzero tail). Quad area estimates include this margin.
  Two sets, preserved local IDs and generations, linear material colors. Fixed
  count with doubled footprint and sequential shifted views show separate count,
  clipped quad area, unclipped ellipse area, sample coverage and layer sum estimates.
- Mixed opaque mesh: actual depth attachment occludes translucent splats. A separate
  nearest-contributing (alpha >= .01) depth-writing pass stores set/local/generation
  and depth proxy in FP32, matched to an independent CPU rule. IDs are diagnostics,
  not blended IDs or a claim that a Gaussian has an opaque surface. IDs are limited
  to exactly representable float integers. Generation is data, not lifecycle stress.
- Effects: actual opaque raster snapshot copied back and uploaded as a distinct
  readonly SSBO, offset by three pixels; offscreen falls back to unshifted pixel.
  Compute reads opaque depth, mapped by the explicit orthographic [0,1] → [0,10]
  world-unit convention. Finite homogeneous volume [2,6], sigma=.35, 8/16 samples,
  analytic `exp(-sigma*distance)` CPU oracle; no early cutoff. Soft particle z=3,
  fade distance 1.5, opacity .2. Fog is split into front [2,3] and back [3,6]
  segments around the particle, both opaque-depth-clamped. Output alpha stores
  volume transmittance, excluding particle alpha. Shifted-depth discontinuities
  greater than .01 world units fall back to the original sample, conservatively
  rejecting silhouette pulls. Independent negatives distinguish foreground pulls
  and the incorrect particle-in-front-of-all-fog ordering. This is a heuristic,
  not a general visibility proof. Snapshot is opaque-only; no nested refraction claim.
  Max effect error 2e-6 and step-size invariance 2e-6.

## Negatives and bounds

Profile parser rejects unknown profile, nonfinite/negative covariance, malformed
schema, duplicate ID and over-capacity inputs. GPU fixture rejects >128 instances
before memcpy/draw (observable `OVERFLOW`, nonzero exit). This is NOT a per-pixel
linked-list overflow test and no linked-list OIT is implemented. Pixel verifier
perturbs each central result and proves rejection. Source and artifact manifests
are checked on subsequent verification, with mismatch mutation checks. Existing
output reuse is rejected without modifying the recorded run.

## Explicit unverified scope

No perspective covariance Jacobian, arbitrary rotation, near-plane splitting,
GPU radix sort, SH renderer, large-scene streaming, temporal history, weather
simulation, multiview concurrency, bounded fragment storage, background LOD,
Android device, thermal/power or sustained performance acceptance. Coverage is
CPU geometric sampling, never a hardware invocation counter. This is a minimal
raster/compute correctness reference, not a production graphics engine.
