# Depth occlusion → 4× color resolve → fragment postprocess

Use the same explicit tools, include, loader, validusage and fresh-output CLI flags as `msaa_sample`:

```
python -O cases19/depth_msaa_sample/run.py --tools TOOL_BIN --include VULKAN_INCLUDE --loader LIBVULKAN --validusage VALIDUSAGE_1_4_309 --output FRESH_DIRECTORY
```

Actual queried D32_SFLOAT optimal depth-attachment and framebuffer depth sample masks must include 4×. A distinct depth image transitions UNDEFINED→DEPTH_STENCIL_ATTACHMENT_OPTIMAL with EARLY|LATE_FRAGMENT_TESTS and depth read/write access, clears to 1, and uses static LESS test + writes. The first draw writes near z=.25/red only where x<1+y%3 (discard elsewhere). The second draw writes far z=.75/cyan full-screen. Depth must preserve the seven near pixels, exposing far pixels elsewhere. Color resolves by AVERAGE to a distinct single-sample RGBA8 image, then the existing combined sampler postprocess reorders `.brga` and writes a third color image. An independent CPU per-pixel depth simulation checks all 16 final pixels. The two fixed depth constants are shader-source facts, not a GPU depth-plane readback.

Controls:
- `good`: intended occlusion, exit 0.
- `depth-format`: supported D16 pipeline format vs actual D32 view; sole frozen 1.4.309 Draw VUID 08914, callback abort and whole command-buffer discard before any submission, exit 0 for the expected rejection.
- `depth-disabled`: legal rendering with depth test disabled, actual far color overwrites all pixels and intended occlusion oracle fails (exit 4), with no Validation error. This changes rendering behavior, unlike merely changing a reference.
- `wrong-output`: same correct rendering but a genuinely changed expected channel fails (exit 6).

All resources remain live through a successful fence wait. CPU ICD/coherent host output only. No stencil, depth bounds, depth resolve, depth-plane/sample-plane readback, hardware performance, geometric edge-AA quality, arbitrary shader proof, concurrent queues, or full VK10 acceptance. Older render_sample/msaa_sample sources are unchanged.

## Explicit sample-count variants

`--samples 1` executes the same shader/near-far sequence at 1×, renders directly to the sampled source image, uses no color resolve, and allocates no unused multisample-color image. `--samples 4` retains the original behavior and remains the default. All four controls run for either choice. Only requested sample support is required (the 1× path does not require 4× support).

Each successful `vkAllocateMemory` emits its actual allocationSize/type receipt. The aggregate is the sum of simultaneously live, explicit application allocations in this scene. It is **not** GPU residency, memory-budget usage, peak VRAM, total process/driver memory, timing, thermal state or bandwidth. Comparing equal endpoint pixels in this full-coverage scene cannot establish general edge-AA equivalence.
