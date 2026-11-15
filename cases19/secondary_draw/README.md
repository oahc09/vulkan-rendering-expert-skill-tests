# Dynamic-rendering secondary draw / 次级命令缓冲绘制

Runnable CPU Vulkan 1.3 fixture: create actual RGBA8 image/view and graphics
pipeline, record a secondary at SECONDARY level with RENDER_PASS_CONTINUE and
VkCommandBufferInheritanceRenderingInfo, then begin primary dynamic rendering
with CONTENTS_SECONDARY_COMMAND_BUFFERS, execute secondary, transition/copy,
wait fence, and independently compare all 16 pixels. The fragment pattern
`x < 1 + y % 3` is nonconstant and distinguishes transpose and axis reversal.

Secondary binds its own graphics pipeline. Vertex/fragment stages, fixed
viewport/scissor, topology, color write mask and sample count are pipeline
state, not assumed inherited primary state. Shader and C outputs are checked
against an independent Python row/column reference. All channels use 0/255.

```
export VK_DRIVER_FILES=/path/to/lvp_icd.json
export VK_LAYER_PATH=/path/to/validation/layers
export LD_LIBRARY_PATH=/path/to/tool/libraries
export MESA_SHADER_CACHE_DISABLE=true
python -O cases19/secondary_draw/run.py --tools /path/to/tools \
 --include /path/to/include --loader /path/to/libvulkan.so.1 \
 --validusage /path/to/validusage.json --output FRESH_DIRECTORY
```

The format-negative uses inheritance=BGRA8 and pipeline=BGRA8 so recording its
own secondary draw is legal. The primary actual view remains RGBA8. Only
`VUID-vkCmdExecuteCommands-imageView-06028` is expected at execute. Its Validation
callback aborts the void command; there is no fabricated VkResult. The primary
is reset/discarded without submission. Exit 0 means the negative was rejected
as expected, not that mismatched execution succeeded. The wrong-output mode
actually compares the rendered pixels against opposite expected colors and
returns 6. Expected inverted values are source evidence, not a raw expected
pixel field.

Actual CPU device, API/feature enablement, limits, image format/usage, allocations,
primary attachment, secondary inheritance, pipeline and execute configuration
are recorded. Existing attachment/pipeline gates are reused for the positive
path; the secondary gate separately matches inheritance and primary view.
Pinned validusage 1.4.309 exact entry and source/tool/binary/SPIR-V/raw hashes
are retained. Tool validation is not general shader semantic reflection.

This is an authored fixture, not an external production bug or repair. No
multithreaded recording, concurrent secondary execution, pending reset/reuse,
legacy render passes, multiview, depth/stencil or full VK03/VK10 acceptance is
claimed. A failure of device-idle cleanup terminates nonzero without destroying
possibly pending Vulkan objects; no driver-hang recovery has been injected.
