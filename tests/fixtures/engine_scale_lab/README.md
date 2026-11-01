# Engine Scale Lab — real offscreen Vulkan integration fixture

Original MIT C++17/GLSL. No commercial engine, external model, private capture,
window system, Camera, Android permission, root, cloud task or network service.
This is a deliberately small executable test, not another engine architecture.

## Build and execute

Prerequisites: C++17 compiler, Vulkan headers/loader, Vulkan 1.2 implementation,
`glslangValidator`, `spirv-val`, `spirv-dis`, Python 3 (manifest/runner only).
The optional `VULKAN_SDK_PREFIX` points to an already installed/extracted SDK prefix;
`GLSLANG`, `SPIRV_VAL`, `SPIRV_DIS`, `CXX` may select actual tools. Scripts never install
packages, fetch assets or change machines. Set a supported ICD normally. A software
ICD is valid **software Vulkan integration**, not mobile hardware performance.

```sh
./build.sh /tmp/scale-build
/tmp/scale-build/host_contracts
/tmp/scale-build/engine_scale_lab --instances 1000 --shaders /tmp/scale-build/shaders
# 1k / 10k / 100k / explicitly disabled firstInstance+MDI+Count, immutable new outputs:
python3 run_matrix.py --build /tmp/scale-build --out /tmp/scale-run-new
```

Use a new output directory per run. `--artifacts NEW_DIR` writes RGBA8 images, native
uint32 visible IDs and configuration sidecars; the matrix hashes every output.
Without this flag output still validates readbacks, but raw images are not persisted.
Validation is enabled if `VK_LAYER_KHRONOS_validation` exists; layer presence is recorded.
Set `VK_LAYER_ENABLES=VK_VALIDATION_FEATURE_ENABLE_SYNCHRONIZATION_VALIDATION_EXT` for
synchronization validation. Missing layers are not silently called validation PASS.
Fixture creation explicitly gates graphics+compute, descriptor/storage/workgroup
limits, coherent host-visible storage, D32 sampled depth and RGBA8 attachment support.
The fixture's Vulkan 1.2/coherent-memory/descriptor limits are not engine requirements.

## Reproducible scene and paths

Seed `0x5eed`, 65×49 NPOT output, 1k/10k/100k exact instances (no hidden reduction).
Orthographic bounds, one opaque half-screen wall and clear-depth holes. Four fixed
views cover approximately 100%, 50%, 10%, and zero visibility (actual counts logged).
Each view is serialized and scratch storage is reused only after its fence completes;
this is **not simultaneous multi-Surface presentation or Android lifecycle testing**.

- CPU no-cull instanced reference; CPU conservative frustum + **up to three LOD
  instanced draws**, not a deliberately slow per-object baseline.
- GPU sphere/AABB screen-extent frustum writes all fixed slots (hidden instanceCount=0).
- GPU atomic compaction and separate finalize clamp, real `vkCmdDrawIndirectCount`.
  Count feature is queried and enabled separately. Fixture conservatively uses fixed
  slots if `drawIndirectFirstInstance` is disabled. No MDI -> legal one-command calls
  with pushed base; no CPU readback is needed to determine draw count on this fallback.
- Optional LOD with hysteresis and resident coarse fallback. Three subdivisions of
  the **same triangular silhouette** (12/6/3 vertices) isolate correctness; they do not
  constitute production mesh quality testing. No unavailable LOD address is emitted.
- Current-frame actual wall depth draw -> sampled depth -> GPU NPOT pyramid -> cull.
  Ordinary Z max and reversed Z min include clear/far samples. Complete covered cells,
  safety epsilon, near-plane/viewport-crossing conservative acceptance. Full pyramid
  compared to independent CPU reduction and final image compared to **no-Hi-Z** drawing.
  No previous-frame depth/history is reused after camera movement.
- Particles: three real update dispatches ping-pong source/working SSBOs, deterministic
  spawn/kill mask, alive compaction. Count path generates a real instanced indirect
  command at the reserved slot. Unused LOD triangles degenerate. Additive rendering
  permits reordering; standard alpha deliberately retains CPU back-to-front ordering
  and is tested for deterministic output, not used as justification for opaque reorder.
- Guarded append capacity, zero capacity, overflow flag and explicit fixed-slot fallback.
  No silent claim that an intentionally truncated overflow image is equivalent.
- Real VkPipelineCache cold creation/serialization/reimport/merge, single-threaded host
  ownership; size/time recorded without asserting warm cache speedup or portable payload.

Command/count -> DRAW_INDIRECT dependency is distinct from objects/IDs/LOD -> vertex
and compute reads. Transfer reset precedes atomic operations. Each Hi-Z dispatch and
cull/finalize has device visibility. Particle ping-pong has read/write dependencies.
Host readback visibility is explicit, not a substitute for device-device dependencies.

## Evidence layers and limits

`host_contracts.cpp` tests **isolated C++ contracts**: pending-upload cancellation,
obsolete generations, shared-owner retirement, bounded new+old budget, cache envelope
corruption/device mismatch rejection, mip clamp not allocation release, conservative
scale bounds, Hi-Z holes and overflow-safe indirect ranges. These are not driver fault
injection, a KTX transcoder, a production streaming scheduler or actual Android teardown.

`verify_spirv.py` verifies compiled Object/Push/Draw offsets and strides, rejects a
mutated stride, and records source/include/bytecode hashes and actual compiler version.
`spirv-val` validates each actual binary. This is not complete shader reflection,
material-schema migration, every specialization combination or device validation.

Runtime asserts visible ID equivalence, resident command ranges, compact uniqueness,
count bounds, guard integrity, CPU/GPU pyramid equality and image equivalence.
Image tolerance is fixed **before execution**: exact bytes for opaque; ≤1 UNORM unit
for reordered additive color. The triangles use deterministic depths; no post-result
threshold relaxation. Standard alpha is compared only in preserved CPU order.

Timestamps require selected-queue `timestampValidBits` and use its wrap mask and
`timestampPeriod`. GPU intervals and host total are **diagnostic synchronized runs**:
validation, depth/image/ID readbacks and CPU reference work are included. Mixed-path
p50/p95/p99 in the runner are diagnostic only, not a fair speed comparison. No sustained
thermal/latency/mobile gain, bandwidth/overdraw counter, or 60-FPS claim is made.
Separate no-readback production profiling remains NOT RUN. Mesh/task, async queues,
Pipeline Binary/GPL native execution, perspective/MSAA/alpha-test occluders, arbitrary
animation/NaN geometry rasterization, compressed texture transcode and simultaneous
multi-output destruction are NOT RUN. Evidence from this fixture cannot certify them.

Construction failure exits the CLI; partially created handles may be reclaimed by the
process/driver, not by the successfully constructed object's destructor. Therefore
this fixture does not claim long-running allocation-failure recovery/leak acceptance.

## Official API references checked 2026-11-01

- [Indirect Count](https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdDrawIndirectCount.html)
- [Indirect draw](https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdDrawIndirect.html)
- [Synchronization examples](https://docs.vulkan.org/guide/latest/synchronization_examples.html)
- [Shader layout](https://docs.vulkan.org/guide/latest/shader_memory_layout.html)
- [Pipeline cache](https://docs.vulkan.org/guide/latest/pipeline_cache.html)

The Hi-Z/LOD algorithms are engineering choices with executable comparisons, not claims
that Vulkan mandates these algorithms. Generated meshes, shaders and fixtures are MIT;
no upstream code or runtime assets are copied into this directory.
