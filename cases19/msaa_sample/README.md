# 4× color resolve → fragment-sampled postprocess

Run with the same explicit tool paths and pinned CPU ICD environment as `render_sample`:

```
python -O cases19/msaa_sample/run.py --tools TOOL_BIN --include VULKAN_INCLUDE --loader LIBVULKAN --validusage VALIDUSAGE_1_4_309 --output FRESH_DIRECTORY
```

The first pipeline rasterizes the asymmetric endpoint RGB pattern into a distinct 4-sample RGBA8 attachment. Dynamic rendering AVERAGE-resolves to a distinct single-sample RGBA8 image. A COLOR_ATTACHMENT_OUTPUT / COLOR_ATTACHMENT_WRITE → FRAGMENT_SHADER / SHADER_READ barrier makes the resolve result available for a second pipeline's combined image sampler. The resolved image stays GENERAL. The second pipeline uses explicit LOD 0 nearest/clamp and `.brga`, rendering to a third single-sample image. All 16 final pixels are compared to an independent CPU reference. No CPU source-image upload is used.

Actual capability queries include format/usage sample-count masks, image extents/layers and framebufferColorSampleCounts. The multisample attachment uses COLOR_ATTACHMENT (16); resolve and output use COLOR_ATTACHMENT|SAMPLED|TRANSFER_SRC (21), queried as this union rather than pretending minimal per-resource usage. Device depth/stencil resolve properties are merely observed: **no depth/stencil path is executed**.

`good` exits 0. `single-source` allocates a real one-sample source but asks for AVERAGE resolve, provoking only frozen 1.4.309 `VUID-VkRenderingAttachmentInfo-imageView-06861`; the BeginRendering callback aborts, the entire command buffer is discarded, and no draw/submit follows. `wrong-output` really compares a flipped expected channel and exits 6. This is not a driver-fault negative.

Sample shading is disabled. Fullscreen coverage with constant per-pixel endpoint values verifies plumbing and resolve semantics, **not edge antialiasing quality or benefit**. Intermediate images and individual samples are not read back. CPU ICD/coherent host readback only; no hardware performance, depth, stencil, blending, sparse, aliasing, cross-queue, partial coverage, or full-domain claims. Existing single-sample `render_sample` remains unchanged.
