# GPU render-to-texture → sampled fragment postprocess

Repository-authored controlled experiment, not an external production bug.

Run `python -O cases19/render_sample/run.py --tools TOOL_BIN --include VULKAN_INCLUDE --loader LIBVULKAN --validusage VALIDUSAGE_1_4_309 --output FRESH_DIRECTORY` with the pinned CPU ICD and Validation layer environment used by other cases19 runners.

Pass 1 draws a non-symmetric endpoint RGBA8 pattern into a GPU-only source image. Pass 2 samples that exact view at pixel centres with normalized nearest/clamp, explicit LOD 0, and rearranges `.brga` into a distinct output image. Both images use queried COLOR_ATTACHMENT | SAMPLED | TRANSFER_SRC usage (21). Source remains GENERAL; an explicit COLOR_ATTACHMENT_OUTPUT/COLOR_ATTACHMENT_WRITE → FRAGMENT_SHADER/SHADER_READ dependency supplies visibility. GENERAL alone does not synchronize. Source STORE preserves the produced contents. Final transfer readback verifies all 16 pixels against an independent CPU reference. Intermediate source pixels are not separately read back.

Modes: good (0); missing-dependency with shader-access heuristic ON (unique SyncVal RAW, callback abort and discard, 0); wrong-output (actual changed expectation fails, 6); same missing-dependency with heuristic OFF (no hazard detected, no submission, 5, **not a passing detection**). SyncVal shader-access analysis is heuristic, not GPU-AV or full shader reflection. No invalid work is submitted.

Scope: one CPU ICD, one queue, RGBA8_UNORM endpoint colors, one mip/layer/sample, two fullscreen pipelines with no depth/blend/resolve. No hardware performance, filtered/interpolated precision, cross-queue, feedback loop, display, or full-domain acceptance. Prior smoke default-OFF non-detection and v2 verifier's old usage17 scope mismatch are retained failures; v3 validates actual usage21 without rewriting it.
